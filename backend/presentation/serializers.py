from rest_framework import serializers

from presentation.models import Presentation


class PresentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Presentation
        fields = (
            'id',
            'title',
            'google_presentation_id',
            'url',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields
