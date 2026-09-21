from rest_framework import serializers

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
    class Meta:
        model = Document
        fields = (
            'id',
            'title',
            'doc_type',
            'grade',
            'subject',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'status',
            'created_at',
            'updated_at',
        )
