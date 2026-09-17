from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0002_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='questiongenerationjob',
            name='num_questions',
        ),
    ]
