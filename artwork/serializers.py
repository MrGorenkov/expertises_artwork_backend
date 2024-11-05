from rest_framework import serializers
from .models import Painting, Expertise, OrderItem
from django.contrib.auth.models import User

class PaintingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Painting
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    painting = PaintingSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = '__all__'

class ExpertiseSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField()
    manager = serializers.StringRelatedField()

    class Meta:
        model = Expertise
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super(UserSerializer, self).update(instance, validated_data)