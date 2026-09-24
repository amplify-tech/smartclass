import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0002_initial'),
        ('task', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='generation_job',
        ),
        migrations.DeleteModel(
            name='QuestionGenerationJob',
        ),
        migrations.AddField(
            model_name='question',
            name='generation_job',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='generated_questions',
                to='task.job',
            ),
        ),
    ]
