from rest_framework import serializers
from .models import Expertise, ExpertiseItem, Painting

class PaintingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Painting
        fields = ['id', 'title', 'img_path', 'short_description']

class ExpertiseItemSerializer(serializers.ModelSerializer):
    painting = PaintingSerializer()

    class Meta:
        model = ExpertiseItem
        fields = ['id', 'painting', 'result', 'comment']

class ExpertiseSerializer(serializers.ModelSerializer):
    items = ExpertiseItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField()
    manager = serializers.StringRelatedField()

    class Meta:
        model = Expertise
        fields = [
            'id', 'user', 'status', 'date_created', 'manager', 
            'date_formation', 'date_completion', 'author', 'items'
        ]
