from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """A user's AI chat. ``chat_type`` picks the handler that answers it."""

    class ChatType(models.TextChoices):
        PRESENTATION = 'presentation', 'Presentation'

    chat_type = models.CharField(max_length=32, choices=ChatType.choices)
    title = models.CharField(max_length=255, blank=True)
    # Handler-owned conversation state; only the chat type's handler knows its keys.
    context = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'conversations'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or f'Conversation {self.pk}'


class Message(models.Model):
    class Role(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    is_error = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'{self.role}: {self.content[:50]}'
