from django.contrib import admin

from .models import Document, DocumentChunk, Grade, Subject


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ('order', 'name')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    fields = ('chunk_index', 'page_number', 'text', 'embedding_model')
    readonly_fields = ('chunk_index', 'page_number', 'text', 'embedding_model')
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'doc_type',
        'grade',
        'subject',
        'status',
        'uploaded_by',
        'created_at',
    )
    list_filter = ('doc_type', 'status', 'grade', 'subject')
    search_fields = ('title', 'subject__name')
    raw_id_fields = ('uploaded_by',)
    inlines = (DocumentChunkInline,)


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = (
        'document',
        'chunk_index',
        'page_number',
        'embedding_model',
        'created_at',
        'updated_at',
    )
    list_filter = ('document__grade', 'document__subject', 'embedding_model')
    raw_id_fields = ('document',)
