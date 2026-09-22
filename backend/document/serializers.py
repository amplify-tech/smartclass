import os

from rest_framework import serializers

from document.constants import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_EXTENSIONS,
    MAX_UPLOAD_SIZE_BYTES,
)
from document.models import Document, Grade, Subject


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ('id', 'name', 'order')
        read_only_fields = ('id',)


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name')
        read_only_fields = ('id',)


class DocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id',
            'title',
            'file',
            'file_url',
            'doc_type',
            'grade',
            'subject',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'file_url',
            'status',
            'created_at',
            'updated_at',
        )
        extra_kwargs = {
            'file': {'write_only': True},
        }

    def get_file_url(self, obj):
        if not obj.file:
            return None
        url = obj.file.url
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def validate_file(self, value):
        raw_content_type = getattr(value, 'content_type', None) or ''
        content_type = raw_content_type.split(';', 1)[0].strip().lower()
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError(
                'Unsupported file type. Allowed types: PDF and plain text.',
            )

        _, ext = os.path.splitext(value.name or '')
        if ext.lower() not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                'Unsupported file extension. Allowed extensions: .pdf, .txt.',
            )

        if value.size > MAX_UPLOAD_SIZE_BYTES:
            max_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            raise serializers.ValidationError(
                f'File too large. Maximum size is {max_mb} MB.',
            )

        return value
