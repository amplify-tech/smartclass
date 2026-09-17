from django.conf import settings
from django.db import models


class Grade(models.Model):
    """School grade / class level, e.g. 7th, 8th, 9th."""

    name = models.CharField(max_length=32, unique=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'grades'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Subject(models.Model):
    """Academic subject, e.g. Maths, Science, English."""

    name = models.CharField(max_length=128, unique=True)

    class Meta:
        db_table = 'subjects'
        ordering = ['name']

    def __str__(self):
        return self.name


class Document(models.Model):
    """Teacher-uploaded class material used for RAG."""

    class DocType(models.TextChoices):
        LECTURE = 'lecture', 'Lecture material'
        BOOK = 'book', 'Book'
        DPP = 'dpp', 'DPP'
        PREVIOUS_YEAR = 'previous_year', 'Previous-year paper'

    class Status(models.TextChoices):
        UPLOADED = 'uploaded', 'Uploaded'
        PROCESSING = 'processing', 'Processing'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/%Y/%m/')
    doc_type = models.CharField(max_length=32, choices=DocType.choices)
    grade = models.ForeignKey(
        Grade,
        on_delete=models.PROTECT,
        related_name='documents',
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='documents',
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.UPLOADED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class DocumentChunk(models.Model):
    """Text chunk of a document, optionally with an embedding for retrieval."""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chunks',
    )
    content = models.TextField()
    chunk_index = models.PositiveIntegerField()
    embedding = models.JSONField(null=True, blank=True)
    page_number = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_chunks'
        ordering = ['document', 'chunk_index']
        constraints = [
            models.UniqueConstraint(
                fields=['document', 'chunk_index'],
                name='uniq_document_chunk_index',
            ),
        ]

    def __str__(self):
        return f'{self.document_id}#{self.chunk_index}'
