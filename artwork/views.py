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
from django.utils import timezone
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

##################################################################

@api_view(['GET'])
def get_created_expertise(request):
    """
    Получение списка сформированных картин
    """
    status_filter = request.query_params.get("status")

    filters = ~Q(status=Expertise.STATUS_CHOICES[2][0])
    if status_filter is not None:
        filters &= Q(status=status_filter.upper())

    created_expertise = Expertise.objects.filter(
        filters).select_related("user")
    serializer = CreatedExpertiseSerializer(
        created_expertise, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_painting_expertise(request, pk):
    """
    Получение информации о заявке на экспертизу по ее ID
    """
    expertise = get_object_or_404(Expertise, pk=pk)
    
    # Исключаем удаленные заявки
    if expertise.status == Expertise.STATUS_CHOICES[2][0]:  # Удалено
        return Response("Expertise not found", status=status.HTTP_404_NOT_FOUND)

    serializer = FullPaintingExpertiseSerializer(expertise)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
def put_painting_expertise(request, pk):
    """
    Изменение автора экспертизы
    """
    try:
        expertise = Expertise.objects.get(id=pk, status=Expertise.STATUS_CHOICES[0][0])
    except Expertise.DoesNotExist:
        return Response("Экспертиза не найдена или не находится в статусе черновика", status=status.HTTP_404_NOT_FOUND)
    
    serializer = PutPaintingExpertiseSerializer(expertise, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['PUT'])
def form_painting_expertise(request, pk):
    """
    PUT сформировать создателем (дата формирования). Происходит проверка на обязательные поля
    """
    try:
        expertise = Expertise.objects.get(id=pk, status=Expertise.STATUS_CHOICES[0][0])
    except Expertise.DoesNotExist:
        return Response("Экспертиза не найдена или не находится в статусе черновика", status=status.HTTP_404_NOT_FOUND)

    serializer = FormPaintingExpertiseSerializer(expertise, data=request.data, partial=True)
    if serializer.is_valid():
        expertise.status = Expertise.STATUS_CHOICES[1][0]  # Предполагаем, что 1 индекс для 'Сформировано'
        expertise.date_formation = timezone.now()
        expertise.save()
        return Response(FormPaintingExpertiseSerializer(expertise).data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
def are_valid_comments(expertise_id):
    expertise = get_object_or_404(Expertise, id=expertise_id)
    expertise_items = ExpertiseItem.objects.filter(expertise=expertise)
    
    for item in expertise_items:
        if not item.comment:
            return False
    return True


@api_view(['PUT'])
def resolve_painting_expertise(request, pk):
    """
    Закрытие заявки на косметическое средство модератором
    """
    expertise = Expertise.objects.filter(
        pk=pk, status=2).first()  # 2 - Сформировано
    if expertise is None:
        return Response("Косметическое средство не найдено или статус неверный", status=status.HTTP_404_NOT_FOUND)

    serializer = ResolveExpertiseSerializer(
        expertise, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    expertise.date_completion = datetime.now()
    expertise.manager = SINGLETON_MANAGER
    expertise.save()

    serializer = CreatedExpertiseSerializer(expertise)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['DELETE'])
def delete_painting_expertise(request, pk):
    """
    Удаление косметического средства
    """
    expertise = Expertise.objects.filter(id=pk,
                                                  status=1).first()
    if expertise is None:
        return Response("CosmeticOrder not found", status=status.HTTP_404_NOT_FOUND)

    expertise.status = 3
    expertise.save()
    return Response(status=status.HTTP_200_OK)


####################################################

@api_view(['PUT'])
def put_painting_in_expertise(request, expertise_pk, painting_pk):
    """
    Изменение данных о картине в экспертизе
    """
    expertise_item = ExpertiseItem.objects.filter(
        expertise_id=expertise_pk, painting_id=painting_pk).first()
    if expertise_item is None:
        return Response("Картина в экспертизе не найдена", status=status.HTTP_404_NOT_FOUND)

    serializer = ExpertiseItemSerializer(
        expertise_item, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_painting_in_expertise(request, expertise_pk, painting_pk):
    """
    Удаление картины из экспертизы
    """
    expertise_item = ExpertiseItem.objects.filter(
        expertise_id=expertise_pk, painting_id=painting_pk).first()
    if expertise_item is None:
        return Response("Картина в экспертизе не найдена", status=status.HTTP_404_NOT_FOUND)

    expertise_item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

############################

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