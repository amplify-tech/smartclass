from rest_framework import serializers

from document.models import Document, Grade, Subject


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ('id', 'name', 'order')


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name')


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
