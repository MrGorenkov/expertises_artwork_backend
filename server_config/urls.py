from django.urls import path, include
from rest_framework.routers import DefaultRouter
from artwork.views import PaintingViewSet, ExpertiseViewSet

router = DefaultRouter()
router.register(r'paintings', PaintingViewSet)
router.register(r'expertises', ExpertiseViewSet, basename='expertise')

urlpatterns = [
    path('', include(router.urls)),
]