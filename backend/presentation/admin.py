from django.contrib import admin

from .models import Presentation


@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'updated_at')
    search_fields = ('title', 'google_presentation_id')
    readonly_fields = ('google_presentation_id', 'url', 'created_at', 'updated_at')
