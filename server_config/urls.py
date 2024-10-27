from django.contrib import admin
from django.urls import path
from artwork import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.paintings_list, name='paintings_list'),  # Отображение списка картин
    path('painting/<int:id>/', views.painting_detail, name='painting_detail'),  # Детали картины
    path('view_order/<int:order_id>/', views.view_order, name='view_order'),  # Просмотр заявки
    path('add_to_order/', views.add_to_order, name='add_to_order'),   
    path('create_order/<int:request_id>/', views.view_order, name='view_order'),  # Отображение состава заявки
    path('delete_order/<int:id>/', views.delete_order, name='delete_order'),  # Удаление заявки
]
