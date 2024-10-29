from django.contrib import admin
from django.urls import path
from artwork import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.paintings_list, name='paintings_list'),  
    path('painting_detail/<int:id>/', views.painting_detail, name='painting_detail'),  
    path('orders/<int:order_id>/', views.view_order, name='view_order'),  
    path('add_to_order/', views.add_to_order, name='add_to_order'),  
    path('delete_order/<int:order_id>/', views.delete_order, name='delete_order'),  
    path('delete_order_item/<int:order_id>/<int:item_id>/', views.delete_order_item, name='delete_order_item'),  # Add this line
]
