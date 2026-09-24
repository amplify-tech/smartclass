from rest_framework import serializers

from .models import Job


class JobStatusSerializer(serializers.ModelSerializer):
    """Polling payload for React: status + payload + result/error."""

    job_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = Job
        fields = (
            'job_id',
            'task_type',
            'status',
            'payload',
            'result',
            'error',
            'retry_count',
            'created_at',
            'started_at',
            'completed_at',
        )
        read_only_fields = fields
