from django.contrib import admin

from .models import (
    Exam,
    ExamQuestion,
    Label,
    Option,
    Question,
    QuestionGenerationJob,
)


class OptionInline(admin.TabularInline):
    model = Option
    extra = 0
    fields = ('order', 'text', 'is_correct')


class ExamQuestionInline(admin.TabularInline):
    model = ExamQuestion
    extra = 0
    fields = ('order', 'question')
    raw_id_fields = ('question',)


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(QuestionGenerationJob)
class QuestionGenerationJobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'grade',
        'subject',
        'difficulty',
        'status',
        'created_by',
        'created_at',
    )
    list_filter = ('status', 'difficulty', 'grade', 'subject')
    raw_id_fields = ('created_by',)
    filter_horizontal = ('documents',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'question_type',
        'difficulty',
        'marks',
        'grade',
        'subject',
        'created_by',
        'created_at',
    )
    list_filter = ('question_type', 'difficulty', 'grade', 'subject', 'labels')
    search_fields = ('text',)
    raw_id_fields = ('created_by', 'source_document', 'generation_job')
    filter_horizontal = ('labels',)
    inlines = (OptionInline,)


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('question', 'order', 'text', 'is_correct')
    list_filter = ('is_correct',)
    raw_id_fields = ('question',)


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'school_name',
        'grade',
        'subject',
        'duration_minutes',
        'difficulty',
        'question_count',
        'total_marks',
        'created_by',
        'created_at',
    )
    list_filter = ('difficulty', 'grade', 'subject')
    search_fields = ('title', 'school_name')
    raw_id_fields = ('created_by',)
    inlines = (ExamQuestionInline,)
    readonly_fields = ('question_count', 'total_marks')


@admin.register(ExamQuestion)
class ExamQuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'order', 'question')
    raw_id_fields = ('exam', 'question')
