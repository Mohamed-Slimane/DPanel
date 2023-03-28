from django.urls import path

from djpanel import views
from djpanel.functions import super_required
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', super_required(auth_views.LogoutView.as_view()), name="logout"),

    path('', super_required(views.apps.as_view()), name="apps"),
    path('apps/new/', super_required(views.app_new.as_view()), name="app_new"),
    path('apps/<str:serial>/delete', super_required(views.app_delete.as_view()), name="app_delete"),
    path('apps/<str:serial>/config', super_required(views.app_config.as_view()), name="app_config"),
]
