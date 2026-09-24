from django.db import transaction
from rest_framework import serializers

from common.exceptions import ConflictError
from common.utils import dedupe_preserve_order
from exam.constants import (
    MAX_DOCUMENTS_PER_JOB,
    MAX_EXAM_DURATION_MINUTES,
    MAX_MARKS,
    MAX_MCQ_OPTIONS,
    MAX_QUESTIONS_PER_ADD,
    MAX_QUESTIONS_PER_JOB,
    MIN_MCQ_OPTIONS,
)
from exam.models import (
    Difficulty,
    Exam,
    ExamQuestion,
    Label,
    Option,
    Question,
    QuestionType,
)
from document.models import Grade, Subject
from task.models import Job


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ('id', 'name')
        read_only_fields = ('id',)

    def validate_name(self, value):
        name = value.strip()
        qs = Label.objects.filter(name__iexact=name)
        if qs.exists():
            raise serializers.ValidationError('A label with this name already exists.')
        return name


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ('id', 'text', 'is_correct', 'order')
        read_only_fields = ('id', 'order')


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
        extra_kwargs = {
            'marks': {'min_value': 1, 'max_value': MAX_MARKS},
        }

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

        if self.instance is not None:
            self._validate_grade_subject_change(attrs)

        return attrs

    def _validate_grade_subject_change(self, attrs):
        grade = attrs.get('grade')
        subject = attrs.get('subject')
        grade_changing = grade is not None and grade.pk != self.instance.grade_id
        subject_changing = subject is not None and subject.pk != self.instance.subject_id
        if not (grade_changing or subject_changing):
            return
        if self.instance.exam_placements.exists():
            raise ConflictError(
                'Cannot change grade/subject while this question is used on an exam.',
            )

    def _validate_mcq_options(self, options):
        if len(options) < MIN_MCQ_OPTIONS:
            raise serializers.ValidationError(
                {'options': 'Add at least two options.'},
            )
        if len(options) > MAX_MCQ_OPTIONS:
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


class QuestionGenerationJobSerializer(serializers.Serializer):
    """Validate create payload; represent task.Job in the legacy API shape."""

    id = serializers.IntegerField(read_only=True)
    grade = serializers.PrimaryKeyRelatedField(queryset=Grade.objects.all())
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    difficulty = serializers.ChoiceField(choices=Difficulty.choices)
    total_marks = serializers.IntegerField(min_value=1, max_value=MAX_MARKS)
    question_types = serializers.DictField()
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )
    document_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        write_only=True,
        required=False,
        default=list,
        max_length=MAX_DOCUMENTS_PER_JOB,
    )
    status = serializers.CharField(read_only=True)
    error_message = serializers.CharField(read_only=True)
    question_ids = serializers.ListField(
        child=serializers.IntegerField(),
        read_only=True,
    )
    created_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(
        read_only=True,
        allow_null=True,
    )

    def validate_description(self, value):
        return (value or '').strip()

    def validate_document_ids(self, value):
        return dedupe_preserve_order(value or [])

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

        if sum(cleaned.values()) > MAX_QUESTIONS_PER_JOB:
            raise serializers.ValidationError(
                f'total questions cannot exceed {MAX_QUESTIONS_PER_JOB}',
            )
        return cleaned

    def to_representation(self, instance):
        """Flatten task.Job (+ payload/result) for existing React clients."""
        if not isinstance(instance, Job):
            return super().to_representation(instance)

        payload = instance.payload or {}
        result = instance.result or {}
        question_ids = result.get('question_ids')
        if question_ids is None:
            question_ids = list(
                Question.objects.filter(
                    generation_job_id=instance.pk,
                ).values_list('id', flat=True),
            )

        return {
            'id': instance.id,
            'grade': payload.get('grade'),
            'subject': payload.get('subject'),
            'difficulty': payload.get('difficulty'),
            'total_marks': payload.get('total_marks'),
            'question_types': payload.get('question_types') or {},
            'description': payload.get('description') or '',
            'status': instance.status,
            'error_message': instance.error or '',
            'question_ids': question_ids,
            'created_at': instance.created_at,
            'completed_at': instance.completed_at,
        }


class ExamQuestionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = ExamQuestion
        fields = ('id', 'order', 'question')


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
        extra_kwargs = {
            'duration_minutes': {
                'min_value': 1,
                'max_value': MAX_EXAM_DURATION_MINUTES,
            },
        }

    def validate(self, attrs):
        if self.instance is None or self.instance.question_count == 0:
            return attrs

        grade = attrs.get('grade')
        subject = attrs.get('subject')
        if grade is not None and grade.pk != self.instance.grade_id:
            raise ConflictError(
                'Cannot change grade after questions have been added.',
            )
        if subject is not None and subject.pk != self.instance.subject_id:
            raise ConflictError(
                'Cannot change subject after questions have been added.',
            )
        return attrs


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
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        max_length=MAX_QUESTIONS_PER_ADD,
    )

    def validate_question_ids(self, value):
        return dedupe_preserve_order(value)


class ReorderItemSerializer(serializers.Serializer):
    exam_question_id = serializers.IntegerField(min_value=1)
    order = serializers.IntegerField(min_value=1)


class ReorderExamQuestionsSerializer(serializers.Serializer):
    items = ReorderItemSerializer(many=True, allow_empty=False)

    def validate_items(self, value):
        ids = [item['exam_question_id'] for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('Duplicate exam_question_id values.')
        orders = [item['order'] for item in value]
        if len(orders) != len(set(orders)):
            raise serializers.ValidationError('Duplicate order values.')
        return value
