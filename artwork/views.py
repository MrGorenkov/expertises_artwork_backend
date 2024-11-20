from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Painting, Expertise, ExpertiseItem
from .minio import process_file_upload
from minio.error import S3Error
from django.utils.timezone import now
from django.db.models import Q
from .serializers import ExpertiseSerializer, ExpertiseItemSerializer, PaintingSerializer

User = get_user_model()


from django.db.models import Count

class PaintingViewSet(viewsets.ModelViewSet):
    queryset = Painting.objects.all()
    serializer_class = PaintingSerializer

    def get_fixed_user(self):
        # Получение пользователя для черновиков
        return User.objects.get_or_create(username=settings.FIXED_USERNAME)[0]

    def list(self, request):
        """
        Возвращает список картин с фильтрацией по названию.
        Дополнительно: ID заявки-черновика и количество картин в черновике.
        """
        # Фильтрация по названию
        queryset = self.queryset
        title_query = request.query_params.get('title', None)
        if title_query:
            queryset = queryset.filter(title__icontains=title_query)

        # Сериализация данных картин
        serializer = self.serializer_class(queryset, many=True)

        # Получение черновика для фиксированного пользователя
        fixed_user = self.get_fixed_user()
        draft_expertise = Expertise.objects.filter(user=fixed_user, status=1).annotate(
            item_count=Count('items')
        ).first()

        # Подготовка данных для ответа
        data = {
            'paintings': serializer.data,
            'expertise_id': draft_expertise.id if draft_expertise else None,
            'expertise_count': draft_expertise.item_count if draft_expertise else 0
        }
        return Response(data, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'])
    def add_to_draft(self, request, pk=None):
        painting = self.get_object()
        fixed_user = self.get_fixed_user()
        draft_expertise, created = Expertise.objects.get_or_create(
            user=fixed_user,
            status=1,
            defaults={'date_created': timezone.now()}
        )
        ExpertiseItem.objects.get_or_create(expertise=draft_expertise, painting=painting)
        return Response({'status': 'Painting added to draft expertise'})

    @action(detail=True, methods=['post'])
    def add_image(self, request, pk=None):
        painting = self.get_object()
        if 'image' not in request.FILES:
            return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES['image']
        object_name = f"painting_{painting.id}_{image_file.name}"
        url = process_file_upload(image_file, object_name)

        if isinstance(url, dict) and 'error' in url:
            return Response({'error': url['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        painting.img_path = url
        painting.save()

        return Response({'status': 'Image added', 'url': url})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.img_path:
            bucket_name = settings.MINIO_BUCKET_NAME
            object_name = instance.img_path.split('/')[-1]
            try:
                client.remove_object(bucket_name, object_name)
            except S3Error as e:
                return Response({'error': f"Failed to delete image: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        self.perform_destroy(instance)
        return Response({'status': 'Painting deleted'})

class ExpertiseViewSet(viewsets.ModelViewSet):
    queryset = Expertise.objects.exclude(status=3)  # Исключить удаленные
    serializer_class = ExpertiseSerializer

    def list(self, request):
        status_filter = request.query_params.get('status', None)
        date_start = request.query_params.get('date_start', None)
        date_end = request.query_params.get('date_end', None)

        queryset = self.queryset.filter(~Q(status=1))  # Исключить черновики

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_start and date_end:
            queryset = queryset.filter(date_formation__range=[date_start, date_end])

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        expertise = self.get_object()
        serializer = self.serializer_class(expertise)
        return Response(serializer.data)

    def update(self, request, pk=None):
        expertise = self.get_object()
        serializer = self.serializer_class(expertise, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def submit(self, request, pk=None):
        expertise = self.get_object()
        if expertise.status != 1:
            return Response({'error': 'Only drafts can be submitted'}, status=status.HTTP_400_BAD_REQUEST)

        required_fields = ['author', 'date_formation']
        missing_fields = [field for field in required_fields if not getattr(expertise, field)]
        if missing_fields:
            return Response({'error': f'Missing fields: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)

        expertise.status = 2
        expertise.date_formation = now()
        expertise.save()
        return Response({'status': 'Submitted successfully'})

    @action(detail=True, methods=['put'])
    def complete(self, request, pk=None):
        expertise = self.get_object()
        if expertise.status != 2:
            return Response({'error': 'Only submitted expertises can be completed'}, status=status.HTTP_400_BAD_REQUEST)

        expertise.status = 4
        expertise.date_completion = now()
        expertise.save()
        return Response({'status': 'Completed successfully'})

    @action(detail=True, methods=['put'])
    def reject(self, request, pk=None):
        expertise = self.get_object()
        if expertise.status != 2:
            return Response({'error': 'Only submitted expertises can be rejected'}, status=status.HTTP_400_BAD_REQUEST)

        expertise.status = 5
        expertise.date_completion = now()
        expertise.save()
        return Response({'status': 'Rejected successfully'})

    def destroy(self, request, pk=None):
        expertise = self.get_object()
        if expertise.status == 1:  # Only drafts can be deleted
            expertise.delete()
            return Response({'status': 'Deleted successfully'})
        return Response({'error': 'Only drafts can be deleted'}, status=status.HTTP_400_BAD_REQUEST)