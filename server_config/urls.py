from django.contrib import admin
from django.urls import path
from artwork import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.paintings_list, name='paintings_list'),
    path('search/', views.paintings_list, name='search'),
    path('painting/<int:id>/', views.painting_detail, name='painting_detail'),
    path('order/', views.view_order, name='order_summary'), 
]

