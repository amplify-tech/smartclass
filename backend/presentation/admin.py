from django.contrib import admin

from .models import Conversation, Message, Presentation


@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'conversation', 'updated_at')
    search_fields = ('title', 'google_presentation_id')
    readonly_fields = ('google_presentation_id', 'url', 'created_at', 'updated_at')


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('role', 'content', 'presentation', 'is_error', 'created_at')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'updated_at')
    search_fields = ('title',)
    inlines = [MessageInline]
