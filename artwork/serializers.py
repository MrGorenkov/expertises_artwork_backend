from rest_framework import serializers
from .models import Painting, Expertise, ExpertiseItem
from django.contrib.auth.models import User

class PaintingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Painting
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class CreatedExpertiseSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username')

    class Meta:
        model = Expertise
        fields = ['id', 'user', 'status', 'date_created',
                  'date_formation', 'date_completion', 'manager', 'author']


class ExpertiseItemSerializer(serializers.ModelSerializer):
    painting = PaintingSerializer()

    class Meta:
        model = ExpertiseItem
        fields = ['painting', 'comment', 'result']


class PutPaintingExpertiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expertise
        fields = ['author']
        read_only_fields = ['pk', 'user', 'status', 'date_created', 'date_formation', 'date_completion', 'manager']

class FormPaintingExpertiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expertise
        fields = ['pk', 'user', 'status', 'author', 'manager', 'date_created', 'date_formation', 'date_completion', 'items']
        read_only_fields = ['pk', 'user', 'status', 'manager', 'date_created', 'date_completion']

    def validate(self, data):
        instance = self.instance
        if not instance.author:
            raise serializers.ValidationError("Author is required to form the expertise.")
        if not instance.items.exists():
            raise serializers.ValidationError("At least one painting item is required to form the expertise.")
        return data


class ResolveExpertiseSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if data.get('status') not in (4, 5):  # 4 - Завершено, 5 - Отклонено
            raise serializers.ValidationError("Invalid status")
        return data

    class Meta:
        model = Expertise
        fields = '__all__'
        read_only_fields = ["pk", "date_created", "date_formation",
                            "date_completion", "user", "manager", "author"]
        

class PaintingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Painting
        fields = ['pk', 'title', 'img_path', 'short_description', 'description']



class ExpertisePaintingSerializer(serializers.ModelSerializer):
    painting = PaintingSerializer()

    class Meta:
        model = Painting
        fields = ['title', 'comment']


class FullPaintingExpertiseSerializer(serializers.ModelSerializer):
    items = ExpertiseItemSerializer(many=True, read_only=True)
    user = serializers.CharField(source='user.username')
    manager = serializers.CharField(source='manager.username', allow_null=True)

    class Meta:
        model = Expertise
        fields = ['pk', 'user', 'status', 'author', 'manager', 'date_created', 
                  'date_formation', 'date_completion', 'items']
        
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        instance.save()
        return instance