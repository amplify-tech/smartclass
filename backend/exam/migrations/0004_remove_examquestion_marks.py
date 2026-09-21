from django.db import migrations


def refresh_exam_totals(apps, schema_editor):
    Exam = apps.get_model('exam', 'Exam')
    ExamQuestion = apps.get_model('exam', 'ExamQuestion')
    for exam in Exam.objects.all().iterator():
        placements = ExamQuestion.objects.filter(exam_id=exam.pk).select_related(
            'question',
        )
        exam.total_marks = sum(eq.question.marks for eq in placements)
        exam.question_count = placements.count()
        exam.save(update_fields=['total_marks', 'question_count'])


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0003_remove_exam_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='examquestion',
            name='marks',
        ),
        migrations.RunPython(refresh_exam_totals, migrations.RunPython.noop),
    ]
