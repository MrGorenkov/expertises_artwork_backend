from django.urls import path
from artwork import views
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),

    path('paintings', views.get_paintings_list, name='paintings_list'),
    path('paintings/', views.PaintingView.as_view(),name='painting_post'),
    path('paintings/<int:pk>/', views.PaintingView.as_view(), name='painting_detail'),
    path('paintings/<int:pk>/add/', views.post_painting_to_expertise, name='add_to_draft'),
    path('paintings/<int:pk>/add_image/', views.update_painting_image, name='update_painting_image'),

]