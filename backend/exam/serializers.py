from rest_framework import serializers

from exam.models import (
    Exam,
    ExamQuestion,
    Option,
    Question,
    QuestionGenerationJob,
    QuestionType,
)


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ('id', 'text', 'is_correct', 'order')


class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, required=False)

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
            'correct_answer',
            'source_document',
            'generation_job',
            'options',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'source_document',
            'generation_job',
            'created_at',
            'updated_at',
        )

    def create(self, validated_data):
        validated_data.pop('options', None)  # TODO: create Option rows for MCQ
        return Question.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('options', None)  # TODO: sync Option rows
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


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
            'grade',
            'subject',
            'difficulty',
            'total_marks',
            'status',
            'exam_questions',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'total_marks', 'created_at', 'updated_at')


class ExamListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = (
            'id',
            'title',
            'grade',
            'subject',
            'difficulty',
            'total_marks',
            'status',
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
