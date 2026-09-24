from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'task_type',
        'status',
        'retry_count',
        'created_by',
        'created_at',
        'started_at',
        'completed_at',
    )
    list_filter = ('status', 'task_type')
    search_fields = ('task_type', 'error')
    raw_id_fields = ('created_by',)
    readonly_fields = (
        'created_at',
        'started_at',
        'completed_at',
        'result',
        'error',
        'retry_count',
    )
