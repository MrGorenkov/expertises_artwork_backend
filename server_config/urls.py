from django.urls import path
from artwork import views
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.paintings_list, name='paintings_list'),
    path('painting_detail/<int:id>/', views.painting_detail, name='painting_detail'),
    path('expertise/<int:expertise_id>/', views.view_expertise, name='view_expertise'),
    path('add_to_expertise/', views.add_to_expertise, name='add_to_expertise'),
    path('delete_expertise/<int:expertise_id>/', views.delete_expertise, name='delete_expertise'),
    
    
]