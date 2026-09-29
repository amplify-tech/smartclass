from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('role', 'content', 'is_error', 'created_at')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'chat_type', 'created_by', 'updated_at')
    list_filter = ('chat_type',)
    search_fields = ('title',)
    inlines = [MessageInline]
