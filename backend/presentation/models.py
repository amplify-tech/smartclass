from django.conf import settings
from django.db import models


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'presentations'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title
