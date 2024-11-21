from django.shortcuts import get_object_or_404
from datetime import datetime
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from artwork.models import Painting, Expertise, ExpertiseItem
from django.db.models import Q
from artwork.serializers import *
from .minio import add_pic, delete_pic


SINGLETON_USER = User(id=1, username="admin")
SINGLETON_MANAGER = User(id=2, username="manager")


@api_view(['GET'])
def get_paintings_list(request):
    """
    Получение всех картин
    """
    title_query = request.GET.get('painting_title', '').lower()

    draft_expertise = Expertise.objects.filter(
        user_id=SINGLETON_USER.id, status=Expertise.STATUS_CHOICES[0][0]).first()

    filter_paintings = Painting.objects.filter(
        title__istartswith=title_query)

    serializer = PaintingSerializer(filter_paintings, many=True)

    expertise_count = draft_expertise.items.count() if draft_expertise else 0

    return Response(
        {
            'paintings': serializer.data,
            'expertise_count': expertise_count,
            'expertise_id': draft_expertise.id if draft_expertise else None
        },
        status=status.HTTP_200_OK
    )


class PaintingView(APIView):
    """
    Класс CRUD операций над картиной
    """
    model_class = Painting
    serializer_class = PaintingSerializer

    # Возвращает данные о картине
    def get(self, request, pk, format=None):
        painting_data = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(painting_data)
        return Response(serializer.data)

    # Добавляет новую картину
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Изменение информации об картине
    def put(self, request, pk, format=None):
        painting = self.model_class.objects.filter(pk=pk).first()
        if painting is None:
            return Response("Картина не найдена", status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(
            painting, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Удаление элемента вместе с изображением
    def delete(self, request, pk, format=None):
        painting = get_object_or_404(self.model_class, pk=pk)
        if painting.img_path:
            deletion_result = delete_pic(painting.img_path)
            if 'error' in deletion_result:
                return Response(deletion_result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        painting.delete()
        return Response({"message": "Картина и его изображение успешно удалены."}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def update_painting_image(request, pk):
    """
    Добавление или замена изображения для картины по его ID.
    """
    painting = get_object_or_404(Painting, pk=pk)

    image = request.FILES.get('image')
    if not image:
        return Response({"error": "Файл изображения не предоставлен."}, status=status.HTTP_400_BAD_REQUEST)

    if painting.img_path:
        delete_pic(painting.img_path)

    result = add_pic(painting, image)

    if 'error' in result.data:
        return result

    painting.img_path = f"http://localhost:9000/web-img/{painting.id}.png"
    painting.save()

    return Response({"message": "Изображение успешно добавлено/заменено."}, status=status.HTTP_200_OK)
@api_view(['POST'])
def post_painting_to_expertise(request, pk):
    """
    Добавление картины в заявку на экспертизу
    """
    painting = Painting.objects.filter(pk=pk).first()
    if painting is None:
        return Response("Картина не найдена", status=status.HTTP_404_NOT_FOUND)
    expertise_id = get_or_create_expertise(SINGLETON_USER.id)
    data = ExpertiseItem(expertise_id=expertise_id, painting_id=pk)
    data.save()
    return Response(status=status.HTTP_200_OK)


def get_or_create_expertise(user_id):
   
    old_expertise = Expertise.objects.filter(
        user_id=user_id, status=Expertise.STATUS_CHOICES[0][0]).first()

    if old_expertise is not None:
        return old_expertise.id

    new_expertise = Expertise(
        user_id=user_id, status=Expertise.STATUS_CHOICES[0][0])
    new_expertise.save()
    return new_expertise.id