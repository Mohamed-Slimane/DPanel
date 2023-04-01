from django.urls import path

from dpanel.app import views as app_views
from dpanel.postgres import views as postgres_views
from dpanel.mysql import views as mysql_views
from dpanel.functions import super_required
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', super_required(auth_views.LogoutView.as_view()), name="logout"),

    # Apps
    path('', super_required(app_views.apps.as_view()), name="apps"),
    path('apps/new/', super_required(app_views.app_new.as_view()), name="app_new"),
    path('apps/<str:serial>/ssl/new/', super_required(app_views.app_ssl_new.as_view()), name="app_ssl_new"),
    path('apps/<str:serial>/delete', super_required(app_views.app_delete.as_view()), name="app_delete"),
    path('apps/<str:serial>/config', super_required(app_views.app_config.as_view()), name="app_config"),

    # Postgres
    path('postgres/', super_required(postgres_views.databases.as_view()), name="postgres_databases"),
    path('postgres/new/', super_required(postgres_views.database_new.as_view()), name="postgres_database_new"),
    path('postgres/<str:serial>/delete/', super_required(postgres_views.database_delete.as_view()), name="postgres_database_delete"),
    path('postgres/<str:serial>/download/', super_required(postgres_views.database_download.as_view()), name="postgres_database_download"),

    # Mysql
    path('mysql/', super_required(mysql_views.databases.as_view()), name="mysql_databases"),
    path('mysql/new/', super_required(mysql_views.database_new.as_view()), name="mysql_database_new"),
    path('mysql/<str:serial>/delete/', super_required(mysql_views.database_delete.as_view()), name="mysql_database_delete"),
    path('mysql/<str:serial>/download/', super_required(mysql_views.database_download.as_view()), name="mysql_database_download"),
]