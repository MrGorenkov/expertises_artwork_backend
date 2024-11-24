from django.urls import path
from artwork import views
from django.contrib import admin

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from artwork import views

schema_view = get_schema_view(
    openapi.Info(
        title="Create expertises API",
        default_version='v1',
        description="API for creating expertises",
        contact=openapi.Contact(email="sgrenkov39@gmail.com"),
        license=openapi.License(name="RIP License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny,],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger',
         cache_timeout=0), name='schema-swagger-ui'),


##################################################################

    path('paintings', views.get_paintings_list, name='paintings_list'),
    path('paintings/', views.PaintingView.as_view(),name='painting_post'),
    path('paintings/<int:pk>/', views.PaintingView.as_view(), name='painting_detail'),
    path('paintings/<int:pk>/add/', views.post_painting_to_expertise, name='add_to_draft'),
    path('paintings/<int:pk>/add_image/', views.update_painting_image, name='update_painting_image'),

##################################################################

path('painting_expertise', views.get_created_expertise,
         name='painting_expertise'),
    path('painting_expertise/<int:pk>', views.get_painting_expertise,
         name='painting_expertise'),
    path('painting_expertise/<int:pk>/put/', views.put_painting_expertise,
         name='painting_expertise_put'),
    path('painting_expertise/<int:pk>/form', views.form_painting_expertise,
         name='painting_expertise_form'),

    path('painting_expertise/<int:pk>/resolve', views.resolve_painting_expertise,
         name='painting_expertise_resolve'),
    path('painting_expertise/<int:pk>/delete', views.delete_painting_expertise,
         name='painting_expertise_delete'),

#################################################

    path('painting_in_expertise/<int:expertise_pk>/<int:painting_pk>/put', views.put_painting_in_expertise,
         name='painting_in_expertise_put'),
    path('painting_in_expertise/<int:expertise_pk>/<int:painting_pk>/delete', views.delete_painting_in_expertise,
         name='painting_in_expertise_delete'),

#################################################

    path('user/create', views.create_user, name='user_create'),
    path('user/login', views.login_user, name='user_login'),
    path('user/logout', views.logout_user, name='user_logout'),
    path('user/update', views.update_user, name='user_update'),

]