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


class Label(models.Model):
    """Topic tag for bank questions, e.g. optics, electricity."""

    name = models.CharField(max_length=64, unique=True)

    class Meta:
        db_table = 'question_labels'
        ordering = ['name']

    def __str__(self):
        return self.name


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
    labels = models.ManyToManyField(
        Label,
        blank=True,
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
        indexes = [
            models.Index(
                fields=['grade', 'subject'],
                name='idx_question_grade_subject',
            ),
        ]

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        marks_may_change = update_fields is None or 'marks' in update_fields
        old_marks = None
        if self.pk and marks_may_change:
            old_marks = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list('marks', flat=True)
                .first()
            )

        super().save(*args, **kwargs)

        if old_marks is not None and old_marks != self.marks:
            self.refresh_related_exam_totals()

    def refresh_related_exam_totals(self):
        """Recompute cached totals on exams that place this bank question."""
        for exam in Exam.objects.filter(
            exam_questions__question_id=self.pk,
        ).distinct():
            exam.refresh_totals()

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
    """Teacher-assembled exam paper."""

    title = models.CharField(max_length=255)
    description = models.TextField(
        blank=True,
        help_text='Exam instructions shown on the printed paper.',
    )
    school_name = models.CharField(
        max_length=255,
        help_text='Institution name printed at the top of the exam paper.',
    )
    duration_minutes = models.PositiveSmallIntegerField(
        help_text='Allowed time for the exam, in minutes.',
    )
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
    # Cached aggregates from bank question marks; never user input.
    total_marks = models.PositiveSmallIntegerField(default=0)
    question_count = models.PositiveSmallIntegerField(default=0)
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

    def refresh_totals(self, *, save=True):
        """Recompute cached totals from bank question marks on placements."""
        aggregates = self.exam_questions.aggregate(
            marks=models.Sum('question__marks'),
            count=models.Count('id'),
        )
        self.total_marks = aggregates['marks'] or 0
        self.question_count = aggregates['count'] or 0
        if save:
            self.save(update_fields=['total_marks', 'question_count', 'updated_at'])
        return self.total_marks, self.question_count

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
