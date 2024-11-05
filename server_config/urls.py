from django.urls import path
from artwork import views

urlpatterns = [
    path('paintings/', views.get_paintings_list, name='get_paintings_list'),
    path('paintings/<int:pk>/', views.PaintingView.as_view(), name='painting_detail'),
    path('paintings/<int:pk>/image/', views.update_painting_image, name='update_painting_image'),
    path('paintings/<int:pk>/add-to-order/', views.post_painting_to_order, name='post_painting_to_order'),

    path('orders/', views.get_created_orders, name='get_created_orders'),
    path('orders/<int:pk>/', views.get_order, name='get_order'),
    path('orders/<int:pk>/update/', views.put_order, name='put_order'),
    path('orders/<int:pk>/form/', views.form_order, name='form_order'),
    path('orders/<int:pk>/resolve/', views.resolve_order, name='resolve_order'),
    path('orders/<int:pk>/delete/', views.delete_order, name='delete_order'),

    path('orders/<int:order_pk>/paintings/<int:painting_pk>/', views.put_painting_in_order, name='put_painting_in_order'),
    path('orders/<int:order_pk>/paintings/<int:painting_pk>/delete/', views.delete_painting_in_order, name='delete_painting_in_order'),

    path('users/create/', views.create_user, name='create_user'),
    path('users/login/', views.login_user, name='login_user'),
    path('users/logout/', views.logout_user, name='logout_user'),
    path('users/update/', views.update_user, name='update_user'),
]