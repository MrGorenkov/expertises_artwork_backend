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
from artwork.models import Expertise, OrderItem, Painting
from django.db.models import Q
from artwork.serializers import PaintingSerializer, ExpertiseSerializer, OrderItemSerializer, UserSerializer
from .minio import process_file_upload, delete_file

SINGLETON_USER = User(id=1, username="admin")
SINGLETON_MANAGER = User(id=2, username="manager")

@api_view(['GET'])
def get_paintings_list(request):
    """
    Получение всех картин
    """
    search_query = request.GET.get('painting_title', '').lower()

    draft_order = Expertise.objects.filter(
        user=SINGLETON_USER, status=Expertise.STATUS_CHOICES[0][0]).first()

    filter_paintings = Painting.objects.filter(
        title__istartswith=search_query)

    serializer = PaintingSerializer(filter_paintings, many=True)

    return Response(
        {
            'paintings': serializer.data,
            'count': draft_order.items.count() if draft_order else 0,
            'order_id': draft_order.id if draft_order else None
        },
        status=status.HTTP_200_OK
    )

class PaintingView(APIView):
    """
    Класс CRUD операций над картиной
    """
    model_class = Painting
    serializer_class = PaintingSerializer

    def get(self, request, pk, format=None):
        painting_data = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(painting_data)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        painting = self.model_class.objects.filter(pk=pk).first()
        if painting is None:
            return Response("Painting not found", status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(
            painting, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        painting = get_object_or_404(self.model_class, pk=pk)
        if painting.img_path:
            deletion_result = delete_file(painting.img_path)
            if 'error' in deletion_result:
                return Response(deletion_result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        painting.delete()
        return Response({"message": "Картина и ее изображение успешно удалены."}, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
def update_painting_image(request, pk):
    """
    Добавление или замена изображения для картины по ее ID.
    """
    painting = get_object_or_404(Painting, pk=pk)

    image = request.FILES.get('image')
    if not image:
        return Response({"error": "Файл изображения не предоставлен."}, status=status.HTTP_400_BAD_REQUEST)

    if painting.img_path:
        delete_file(painting.img_path)

    result = process_file_upload(image, f"{painting.id}.png")

    if 'error' in result:
        return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    painting.img_path = result
    painting.save()

    return Response({"message": "Изображение успешно добавлено/заменено."}, status=status.HTTP_200_OK)

@api_view(['POST'])
def post_painting_to_order(request, pk):
    """
    Добавление картины в заказ
    """
    painting = Painting.objects.filter(pk=pk).first()
    if painting is None:
        return Response("Painting not found", status=status.HTTP_404_NOT_FOUND)
    order_id = get_or_create_order(SINGLETON_USER.id)
    data = OrderItem(expertise_id=order_id, painting_id=pk)
    data.save()
    return Response(status=status.HTTP_200_OK)

def get_or_create_order(user_id):
    """
    Получение id заказа или создание нового при его отсутствии
    """
    old_order = Expertise.objects.filter(
        user_id=user_id, status=Expertise.STATUS_CHOICES[0][0]).first()

    if old_order is not None:
        return old_order.id

    new_order = Expertise(
        user_id=user_id, status=Expertise.STATUS_CHOICES[0][0])
    new_order.save()
    return new_order.id

@api_view(['GET'])
def get_created_orders(request):
    """
    Получение списка сформированных заказов
    """
    status_filter = request.query_params.get("status")

    filters = ~Q(status=Expertise.STATUS_CHOICES[2][0])
    if status_filter is not None:
        filters &= Q(status=status_filter.upper())

    created_orders = Expertise.objects.filter(
        filters).select_related("user")
    serializer = ExpertiseSerializer(
        created_orders, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_order(request, pk):
    """
    Получение информации о заказе по его ID
    """
    filters = Q(pk=pk) & ~Q(status=Expertise.STATUS_CHOICES[2][0])
    order = Expertise.objects.filter(filters).first()

    if order is None:
        return Response("Order not found", status=status.HTTP_404_NOT_FOUND)

    serializer = ExpertiseSerializer(order)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
def put_order(request, pk):
    """
    Изменение темы заказа
    """
    order = Expertise.objects.filter(
        id=pk, status=Expertise.STATUS_CHOICES[0][0]).first()
    if order is None:
        return Response("Заказ не найден", status=status.HTTP_404_NOT_FOUND)
    serializer = ExpertiseSerializer(
        order, data=request.data, partial=True
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def form_order(request, pk):
    """
    Формирование заказа
    """
    order = Expertise.objects.filter(
        id=pk, status=1).first()
    if order is None:
        return Response("Заказ не найден", status=status.HTTP_404_NOT_FOUND)

    if not order.items.exists():
        return Response("В заказе должна быть хотя бы одна картина", status=status.HTTP_400_BAD_REQUEST)

    order.status = 2
    order.date_formation = datetime.now()
    order.save()

    serializer = ExpertiseSerializer(order)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
def resolve_order(request, pk):
    """
    Закрытие заказа модератором
    """
    order = Expertise.objects.filter(
        pk=pk, status=2).first()  # 2 - Сформировано
    if order is None:
        return Response("Заказ не найден или статус неверный", status=status.HTTP_404_NOT_FOUND)

    serializer = ExpertiseSerializer(
        order, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    order.date_completion = datetime.now()
    order.manager = SINGLETON_MANAGER
    order.save()

    serializer = ExpertiseSerializer(order)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['DELETE'])
def delete_order(request, pk):
    """
    Удаление заказа
    """
    order = Expertise.objects.filter(id=pk,
                                     status=1).first()
    if order is None:
        return Response("Order not found", status=status.HTTP_404_NOT_FOUND)

    order.status = 3
    order.save()
    return Response(status=status.HTTP_200_OK)

@api_view(['PUT'])
def put_painting_in_order(request, order_pk, painting_pk):
    """
    Изменение данных о картине в заказе
    """
    painting_in_order = OrderItem.objects.filter(
        expertise_id=order_pk, painting_id=painting_pk).first()
    if painting_in_order is None:
        return Response("Картина в заказе не найдена", status=status.HTTP_404_NOT_FOUND)

    serializer = OrderItemSerializer(
        painting_in_order, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_painting_in_order(request, order_pk, painting_pk):
    """
    Удаление картины из заказа
    """
    painting_in_order = OrderItem.objects.filter(
        expertise_id=order_pk, painting_id=painting_pk).first()
    if painting_in_order is None:
        return Response("Картина не найдена", status=status.HTTP_404_NOT_FOUND)

    painting_in_order.delete()
    return Response(status=status.HTTP_200_OK)

@api_view(['POST'])
def create_user(request):
    """
    Создание пользователя
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_user(request):
    """
    Вход
    """
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(username=username, password=password)
    if user is not None:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Выход
    """
    request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_user(request):
    """
    Обновление данных пользователя
    """
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Не забудьте добавить соответствующие URL-маршруты в urls.py