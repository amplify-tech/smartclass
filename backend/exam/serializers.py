from django.db import transaction
from rest_framework import serializers

from exam.models import (
    Exam,
    ExamQuestion,
    Label,
    Option,
    Question,
    QuestionGenerationJob,
    QuestionType,
)


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ('id', 'name')
        read_only_fields = ('id',)


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ('id', 'text', 'is_correct', 'order')
        read_only_fields = ('id', 'order')

    def validate_text(self, value):
        text = (value or '').strip()
        if not text:
            raise serializers.ValidationError('Option text is required.')
        return text


class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, required=False)
    labels = LabelSerializer(many=True, read_only=True)
    created_by_id = serializers.IntegerField(read_only=True)
    label_ids = serializers.PrimaryKeyRelatedField(
        source='labels',
        many=True,
        queryset=Label.objects.all(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Question
        fields = (
            'id',
            'question_type',
            'text',
            'difficulty',
            'marks',
            'grade',
            'subject',
            'labels',
            'label_ids',
            'correct_answer',
            'source_document',
            'generation_job',
            'options',
            'created_by_id',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'source_document',
            'generation_job',
            'created_by_id',
            'created_at',
            'updated_at',
        )

    def validate(self, attrs):
        question_type = attrs.get(
            'question_type',
            getattr(self.instance, 'question_type', None),
        )
        options_provided = 'options' in attrs
        options = attrs.get('options') or []

        if question_type == QuestionType.MCQ:
            creating = self.instance is None
            switching_to_mcq = (
                self.instance is not None
                and self.instance.question_type != QuestionType.MCQ
                and attrs.get('question_type') == QuestionType.MCQ
            )
            if creating or switching_to_mcq:
                if not options_provided:
                    raise serializers.ValidationError(
                        {'options': 'MCQ requires at least two options.'},
                    )
                self._validate_mcq_options(options)
            elif options_provided:
                self._validate_mcq_options(options)
        elif options_provided and options:
            raise serializers.ValidationError(
                {'options': 'Only MCQ questions may include options.'},
            )

        return attrs

    def _validate_mcq_options(self, options):
        if len(options) < 2:
            raise serializers.ValidationError(
                {'options': 'Add at least two options.'},
            )
        if len(options) > 6:
            raise serializers.ValidationError(
                {'options': 'At most six options are allowed.'},
            )

        correct_count = sum(1 for opt in options if opt.get('is_correct'))
        if correct_count != 1:
            raise serializers.ValidationError(
                {'options': 'Exactly one option must be marked correct.'},
            )

    @staticmethod
    def _replace_options(question, options):
        question.options.all().delete()
        if not options:
            return
        Option.objects.bulk_create(
            [
                Option(
                    question=question,
                    text=opt['text'],
                    is_correct=bool(opt.get('is_correct', False)),
                    order=index,
                )
                for index, opt in enumerate(options, start=1)
            ],
        )

    @transaction.atomic
    def create(self, validated_data):
        options = validated_data.pop('options', [])
        labels = validated_data.pop('labels', None)
        question = Question.objects.create(**validated_data)
        if labels is not None:
            question.labels.set(labels)
        if question.question_type == QuestionType.MCQ:
            self._replace_options(question, options)
        return question

    def _request_user(self):
        request = self.context.get('request')
        return getattr(request, 'user', None) if request else None

    @transaction.atomic
    def update(self, instance, validated_data):
        options = validated_data.pop('options', None)
        labels = validated_data.pop('labels', None)
        user = self._request_user()

        # Public bank: non-owners get a clone instead of mutating shared rows.
        if user and instance.created_by_id != user.id:
            return self._clone_for_user(
                instance,
                validated_data,
                options=options,
                labels=labels,
                user=user,
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if labels is not None:
            instance.labels.set(labels)

        if instance.question_type != QuestionType.MCQ:
            instance.options.all().delete()
        elif options is not None:
            self._replace_options(instance, options)

        return instance

    def _clone_for_user(self, instance, validated_data, *, options, labels, user):
        clone_fields = (
            'question_type',
            'text',
            'difficulty',
            'marks',
            'grade',
            'subject',
            'correct_answer',
            'source_document',
        )
        create_kwargs = {
            field: getattr(instance, field) for field in clone_fields
        }
        create_kwargs.update(validated_data)
        create_kwargs['created_by'] = user
        create_kwargs['generation_job'] = None

        question = Question.objects.create(**create_kwargs)

        if labels is not None:
            question.labels.set(labels)
        else:
            question.labels.set(instance.labels.all())

        question_type = question.question_type
        if question_type == QuestionType.MCQ:
            if options is not None:
                self._replace_options(question, options)
            else:
                Option.objects.bulk_create(
                    [
                        Option(
                            question=question,
                            text=opt.text,
                            is_correct=opt.is_correct,
                            order=opt.order,
                        )
                        for opt in instance.options.all()
                    ],
                )
        return question


class QuestionGenerationJobSerializer(serializers.ModelSerializer):
    document_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        write_only=True,
        required=False,
        default=list,
    )
    question_ids = serializers.PrimaryKeyRelatedField(
        source='questions',
        many=True,
        read_only=True,
    )

    class Meta:
        model = QuestionGenerationJob
        fields = (
            'id',
            'grade',
            'subject',
            'difficulty',
            'total_marks',
            'question_types',
            'description',
            'document_ids',
            'status',
            'error_message',
            'question_ids',
            'created_at',
            'completed_at',
        )
        read_only_fields = (
            'id',
            'status',
            'error_message',
            'question_ids',
            'created_at',
            'completed_at',
        )

    def validate_question_types(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError(
                'expected object like {"mcq": 2, "short": 3}',
            )

        valid = {c.value for c in QuestionType}
        cleaned = {}
        for key, count in value.items():
            q_type = str(key).lower()
            if q_type not in valid:
                raise serializers.ValidationError(f'invalid type: {key}')
            try:
                count = int(count)
            except (TypeError, ValueError):
                raise serializers.ValidationError(f'invalid count for {key}')
            if count < 1:
                raise serializers.ValidationError(f'count for {key} must be >= 1')
            cleaned[q_type] = cleaned.get(q_type, 0) + count

        if sum(cleaned.values()) > 50:
            raise serializers.ValidationError('total questions cannot exceed 50')
        return cleaned


class ExamQuestionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = ExamQuestion
        fields = ('id', 'order', 'marks', 'question')


class ExamSerializer(serializers.ModelSerializer):
    exam_questions = ExamQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Exam
        fields = (
            'id',
            'title',
            'description',
            'school_name',
            'duration_minutes',
            'grade',
            'subject',
            'difficulty',
            'total_marks',
            'question_count',
            'status',
            'exam_questions',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'total_marks',
            'question_count',
            'created_at',
            'updated_at',
        )

    def validate_school_name(self, value):
        name = (value or '').strip()
        if not name:
            raise serializers.ValidationError('School name is required.')
        return name

    def validate_duration_minutes(self, value):
        if value is None or value < 1:
            raise serializers.ValidationError(
                'Duration must be at least 1 minute.',
            )
        return value


class ExamListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = (
            'id',
            'title',
            'school_name',
            'duration_minutes',
            'grade',
            'subject',
            'difficulty',
            'total_marks',
            'question_count',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'total_marks',
            'question_count',
            'created_at',
            'updated_at',
        )


class AddExamQuestionsSerializer(serializers.Serializer):
    question_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
    )


class UpdateExamQuestionSerializer(serializers.Serializer):
    order = serializers.IntegerField(required=False, min_value=1)
    marks = serializers.IntegerField(required=False, min_value=1)


class ReorderItemSerializer(serializers.Serializer):
    exam_question_id = serializers.IntegerField()
    order = serializers.IntegerField(min_value=1)


class ReorderExamQuestionsSerializer(serializers.Serializer):
    items = ReorderItemSerializer(many=True, allow_empty=False)
