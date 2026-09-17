from django.contrib import admin

from .models import (
    Exam,
    ExamQuestion,
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
    fields = ('order', 'question', 'marks')
    raw_id_fields = ('question',)


@admin.register(QuestionGenerationJob)
class QuestionGenerationJobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'grade',
        'subject',
        'difficulty',
        'num_questions',
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
    list_filter = ('question_type', 'difficulty', 'grade', 'subject')
    search_fields = ('text',)
    raw_id_fields = ('created_by', 'source_document', 'generation_job')
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
        'grade',
        'subject',
        'difficulty',
        'total_marks',
        'status',
        'created_by',
        'created_at',
    )
    list_filter = ('status', 'difficulty', 'grade', 'subject')
    search_fields = ('title',)
    raw_id_fields = ('created_by',)
    inlines = (ExamQuestionInline,)


@admin.register(ExamQuestion)
class ExamQuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'order', 'question', 'marks')
    raw_id_fields = ('exam', 'question')
