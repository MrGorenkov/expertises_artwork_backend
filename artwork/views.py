from django.shortcuts import get_object_or_404
from datetime import datetime
from dateutil.parser import parse
import uuid
import random
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import FormParser
from rest_framework.decorators import parser_classes
from artwork.models import Painting, Expertise, ExpertiseItem
from django.db.models import Q
from artwork.serializers import *
from .minio import add_pic, delete_pic
from .auth import AuthBySessionID, AuthBySessionIDIfExists, IsAuth, IsManagerAuth
from .redis import session_storage

@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([AuthBySessionIDIfExists])
def get_paintings_list(request):
    """
    Получение всех картин
    """
    user = request.user
    search_query = request.GET.get('title', '').lower()
    filter_paintings = Painting.objects.filter(title__istartswith=search_query)
    items_in_draft = 0
    draft_expertise = None

    if user is not None:
        draft_expertise = Expertise.objects.filter(
            user_id=user.pk, status=Expertise.STATUS_CHOICES[0][0]).first()
        if draft_expertise is not None:
            items_in_draft = draft_expertise.items.count()

    serializer = PaintingSerializer(filter_paintings, many=True)
    return Response({
        'paintings': serializer.data,
        'count': items_in_draft,
        'expertise_id': draft_expertise.id if draft_expertise else None
    }, status=status.HTTP_200_OK)

class PaintingView(APIView):
    """
    Класс CRUD операций над картиной
    """
    model_class = Painting
    serializer_class = PaintingSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsManagerAuth()]

    def get(self, request, pk=None, format=None):
        if pk is not None:
            painting_data = get_object_or_404(self.model_class, pk=pk)
            serializer = self.serializer_class(painting_data)
            return Response(serializer.data)
        else:
            return get_paintings_list(request._request)

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        painting = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(painting, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        painting = get_object_or_404(self.model_class, pk=pk)
        if painting.img_path:
            deletion_result = delete_pic(painting.img_path)
            if 'error' in deletion_result:
                return Response(deletion_result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        painting.delete()
        return Response({"message": "Картина и его изображение успешно удалены."}, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsManagerAuth])
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
    if 'error' in result:
        return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    painting.img_path = f"http://localhost:9000/web-img/{painting.id}.png"
    painting.save()
    return Response({"message": "Изображение успешно добавлено/заменено."}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def post_painting_to_expertise(request, pk):
    """
    Добавление картины в заявку на экспертизу
    """
    painting = get_object_or_404(Painting, pk=pk)
    expertise_id = get_or_create_expertise(request.user.id)
    data = ExpertiseItem(expertise_id=expertise_id, painting_id=pk)
    data.save()
    return Response(status=status.HTTP_200_OK)

def get_or_create_expertise(user_id):
    """
    Получение id экспертизы или создание новой при ее отсутствии
    """
    old_expertise = Expertise.objects.filter(
        user_id=user_id, status=Expertise.STATUS_CHOICES[0][0]
    ).first()
    if old_expertise:
        return old_expertise.id
    new_expertise = Expertise(
        user_id=user_id, status=Expertise.STATUS_CHOICES[0][0]
    )
    new_expertise.save()
    return new_expertise.id

@api_view(['GET'])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def get_created_expertise(request):
    """
    Получение списка сформированных экспертиз
    """
    status_filter = request.query_params.get("status")
    formation_datetime_start_filter = request.query_params.get("formation_start")
    formation_datetime_end_filter = request.query_params.get("formation_end")

    filters = ~Q(status=Expertise.STATUS_CHOICES[2][0])  # Исключаем удаленные

    if status_filter:
        filters &= Q(status=status_filter.upper())
    if formation_datetime_start_filter:
        filters &= Q(date_formation__gte=parse(formation_datetime_start_filter))
    if formation_datetime_end_filter:
        filters &= Q(date_formation__lte=parse(formation_datetime_end_filter))

    if not request.user.is_staff:
        filters &= Q(user=request.user)

    created_expertise = Expertise.objects.filter(filters).select_related("user")
    serializer = CreatedExpertiseSerializer(created_expertise, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def get_painting_expertise(request, pk):
    """
    Получение информации о заявке на экспертизу по ее ID
    """
    filters = Q(pk=pk) & ~Q(status=Expertise.STATUS_CHOICES[2][0])
    expertise = Expertise.objects.filter(filters).first()
    if expertise is None:
        return Response("Экспертиза не найдена", status=status.HTTP_404_NOT_FOUND)
    serializer = FullPaintingExpertiseSerializer(expertise)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def put_painting_expertise(request, pk):
    """
    Изменение автора экспертизы
    """
    expertise = get_object_or_404(Expertise, id=pk, status=Expertise.STATUS_CHOICES[0][0])
    serializer = PutPaintingExpertiseSerializer(expertise, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def form_painting_expertise(request, pk):
    """
    Формирование экспертизы
    """
    expertise = get_object_or_404(Expertise, id=pk, status=Expertise.STATUS_CHOICES[0][0])
    if not expertise.author:
        return Response("Поле 'Автор' должно быть заполнено", status=status.HTTP_400_BAD_REQUEST)
    expertise.status = Expertise.STATUS_CHOICES[1][0]
    expertise.date_formation = datetime.now()
    expertise.save()
    serializer = CreatedExpertiseSerializer(expertise)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsManagerAuth])
@authentication_classes([AuthBySessionID])
def resolve_painting_expertise(request, pk):
    """
    Закрытие заявки на экспертизу модератором
    """
    expertise = get_object_or_404(Expertise, pk=pk, status=2)
    
    # Генерация случайного результата
    random_result = random.choice([True, False])
    
    # Определение нового статуса на основе случайного результата
    new_status = Expertise.STATUS_CHOICES[3][0] if random_result else Expertise.STATUS_CHOICES[4][0]
    
    serializer = ResolveExpertiseSerializer(expertise, data={'status': new_status}, partial=True)
    if serializer.is_valid():
        serializer.save()
        expertise.date_completion = timezone.now()
        expertise.manager = request.user
        expertise.save()
        
        # Обновление всех связанных ExpertiseItem
        ExpertiseItem.objects.filter(expertise=expertise).update(result=random_result)
        
        return Response(CreatedExpertiseSerializer(expertise).data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def delete_painting_expertise(request, pk):
    """
    Удаление экспертизы
    """
    expertise = get_object_or_404(Expertise, id=pk, status=1)
    expertise.status = 3
    expertise.save()
    return Response(status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def put_painting_in_expertise(request, expertise_pk, painting_pk):
    """
    Изменение данных о картине в экспертизе
    """
    expertise_item = get_object_or_404(ExpertiseItem, expertise_id=expertise_pk, painting_id=painting_pk)
    serializer = ExpertiseItemSerializer(expertise_item, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def delete_painting_in_expertise(request, expertise_pk, painting_pk):
    """
    Удаление картины из экспертизы
    """
    expertise_item = get_object_or_404(ExpertiseItem, expertise_id=expertise_pk, painting_id=painting_pk)
    expertise_item.delete()
    return Response(status=status.HTTP_200_OK)

@swagger_auto_schema(method='post',
                     responses={
                         status.HTTP_201_CREATED: "Created",
                         status.HTTP_400_BAD_REQUEST: "Bad Request",
                     },
                     manual_parameters=[
                         openapi.Parameter('username',
                                           type=openapi.TYPE_STRING,
                                           description='Username',
                                           in_=openapi.IN_FORM,
                                           required=True),
                         openapi.Parameter('email',
                                           type=openapi.TYPE_STRING,
                                           description='Email',
                                           in_=openapi.IN_FORM,
                                           required=True),
                         openapi.Parameter('password',
                                           type=openapi.TYPE_STRING,
                                           description='Password',
                                           in_=openapi.IN_FORM,
                                           required=True)
                     ])
@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([FormParser])
def create_user(request):
    """
    Создание пользователя
    """
    username = request.POST.get('username')
    email = request.POST.get('email')
    password = request.POST.get('password')

    if not username or not password:
        return Response({'error': 'Поля username и password обязательные!'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = UserSerializer(
        data={'username': username, 'email': email, 'password': password})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post',
                     responses={
                         status.HTTP_200_OK: "OK",
                         status.HTTP_400_BAD_REQUEST: "Bad Request",
                     },
                     manual_parameters=[
                         openapi.Parameter('username',
                                           type=openapi.TYPE_STRING,
                                           description='username',
                                           in_=openapi.IN_FORM,
                                           required=True),
                         openapi.Parameter('password',
                                           type=openapi.TYPE_STRING,
                                           description='password',
                                           in_=openapi.IN_FORM,
                                           required=True)
                     ])
@api_view(['POST'])
@parser_classes((FormParser,))
@permission_classes([AllowAny])
def login_user(request):
    """
    Вход
    """
    session_id = request.COOKIES.get("session_id")
    if session_id and session_storage.exists(session_id):
        session_storage.delete(session_id)
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(username=username, password=password)
    if user is not None:
        session_id = str(uuid.uuid4())
        session_storage.set(session_id, username)
        response = Response(status=status.HTTP_201_CREATED)
        response.set_cookie("session_id", session_id, samesite="lax")
        return response
    return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post',
                     responses={
                         status.HTTP_204_NO_CONTENT: "No content",
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                     })
@api_view(['POST'])
@permission_classes([IsAuth])
def logout_user(request):
    """
    Выход
    """
    session_id = request.COOKIES["session_id"]
    if session_storage.exists(session_id):
        session_storage.delete(session_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_403_FORBIDDEN)

@swagger_auto_schema(method='put',
                     request_body=UserSerializer,
                     responses={
                         status.HTTP_200_OK: UserSerializer(),
                         status.HTTP_400_BAD_REQUEST: "Bad Request",
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                     })
@api_view(['PUT'])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def update_user(request):
    """
    Обновление данных пользователя
    """
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)