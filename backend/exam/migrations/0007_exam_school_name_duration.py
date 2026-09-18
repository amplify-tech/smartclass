from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0006_restore_exam_cached_totals'),
    ]

    operations = [
        migrations.AddField(
            model_name='exam',
            name='duration_minutes',
            field=models.PositiveSmallIntegerField(
                default=60,
                help_text='Allowed time for the exam, in minutes.',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exam',
            name='school_name',
            field=models.CharField(
                default='School',
                help_text='Institution name printed at the top of the exam paper.',
                max_length=255,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='exam',
            name='description',
            field=models.TextField(
                blank=True,
                help_text='Exam instructions shown on the printed paper.',
            ),
        ),
    ]
