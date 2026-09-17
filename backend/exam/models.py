from django.conf import settings
from django.db import models

from document.models import Document, Grade, Subject


class Difficulty(models.TextChoices):
    """Fixed difficulty levels (enum, not a DB table)."""

    EASY = 'easy', 'Easy'
    MEDIUM = 'medium', 'Medium'
    HARD = 'hard', 'Hard'


class QuestionType(models.TextChoices):
    """Fixed question kinds (enum, not a DB table)."""

    MCQ = 'mcq', 'MCQ'
    SHORT = 'short', 'Short answer'
    LONG = 'long', 'Long answer'


class QuestionGenerationJob(models.Model):
    """One teacher request to generate questions (async via Celery)."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='question_generation_jobs',
    )
    grade = models.ForeignKey(
        Grade,
        on_delete=models.PROTECT,
        related_name='generation_jobs',
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='generation_jobs',
    )
    difficulty = models.CharField(max_length=16, choices=Difficulty.choices)
    total_marks = models.PositiveSmallIntegerField()
    question_types = models.JSONField(
        help_text='Counts per type, e.g. {"mcq": 2, "short": 3}',
    )
    description = models.TextField(
        blank=True,
        help_text='Teacher prompt used by the LLM when generating questions.',
    )
    documents = models.ManyToManyField(
        Document,
        blank=True,
        related_name='generation_jobs',
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'question_generation_jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f'Job {self.pk} ({self.status})'


class Question(models.Model):
    """Reusable question-bank entry."""

    question_type = models.CharField(max_length=16, choices=QuestionType.choices)
    text = models.TextField()
    difficulty = models.CharField(max_length=16, choices=Difficulty.choices)
    marks = models.PositiveSmallIntegerField()
    grade = models.ForeignKey(
        Grade,
        on_delete=models.PROTECT,
        related_name='questions',
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='questions',
    )
    correct_answer = models.TextField(
        blank=True,
        help_text='Model answer for short/long; optional note for MCQ.',
    )
    source_document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
    )
    generation_job = models.ForeignKey(
        QuestionGenerationJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='questions',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'questions'
        ordering = ['-created_at']

    def __str__(self):
        return self.text[:80]


class Option(models.Model):
    """One MCQ choice for a question (typically four per MCQ)."""

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options',
    )
    text = models.CharField(max_length=512)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = 'question_options'
        ordering = ['question', 'order']
        constraints = [
            models.UniqueConstraint(
                fields=['question', 'order'],
                name='uniq_question_option_order',
            ),
        ]

    def __str__(self):
        return self.text[:80]


class Exam(models.Model):
    """Teacher-assembled exam paper (draft or finalized)."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        FINALIZED = 'finalized', 'Finalized'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    grade = models.ForeignKey(
        Grade,
        on_delete=models.PROTECT,
        related_name='exams',
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='exams',
    )
    difficulty = models.CharField(
        max_length=16,
        choices=Difficulty.choices,
        blank=True,
    )
    total_marks = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exams',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'exams'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ExamQuestion(models.Model):
    """Ordered placement of a bank question on an exam."""

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='exam_questions',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name='exam_placements',
    )
    order = models.PositiveSmallIntegerField()
    marks = models.PositiveSmallIntegerField(
        help_text='Marks for this question on this exam (may differ from bank).',
    )

    class Meta:
        db_table = 'exam_questions'
        ordering = ['exam', 'order']
        constraints = [
            models.UniqueConstraint(
                fields=['exam', 'question'],
                name='uniq_exam_question',
            ),
            models.UniqueConstraint(
                fields=['exam', 'order'],
                name='uniq_exam_question_order',
            ),
        ]

    def __str__(self):
        return f'Exam {self.exam_id} Q{self.order}'
