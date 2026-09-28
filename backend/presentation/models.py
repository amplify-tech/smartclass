from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """A teacher's presentation chat."""

    title = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='presentation_conversations',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'presentation_conversations'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or f'Conversation {self.pk}'


class Presentation(models.Model):
    """A Google Slides presentation created by a teacher through SmartClass."""

    google_presentation_id = models.CharField(max_length=128, unique=True)
    title = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='presentations',
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presentations',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'presentations'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class Message(models.Model):
    USER = 'user'
    ASSISTANT = 'assistant'
    ROLE_CHOICES = ((USER, 'User'), (ASSISTANT, 'Assistant'))

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()
    # The presentation an assistant reply created or changed.
    presentation = models.ForeignKey(
        Presentation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    is_error = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'presentation_messages'
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'{self.role}: {self.content[:50]}'
