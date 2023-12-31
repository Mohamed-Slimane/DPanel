from django.urls import path

from dpanel.app import views as app_views
from dpanel.mysql import views as mysql_views
from dpanel.setting import views as setting_views
from dpanel.functions import super_required
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('logout/', super_required(auth_views.LogoutView.as_view()), name="logout"),
    path('password/change/', super_required(auth_views.PasswordChangeView.as_view(template_name='account/password-change.html', form_class=auth_views.SetPasswordForm)), name="password_change"),
    path('password/change/done', super_required(auth_views.PasswordChangeDoneView.as_view(template_name='account/password-change-done.html')), name="password_change_done"),

    # Apps
    path('', super_required(app_views.apps.as_view()), name="apps"),
    path('apps/new/', super_required(app_views.app_new.as_view()), name="app_new"),
    path('apps/<str:serial>/restart/', super_required(app_views.app_restart.as_view()), name="app_restart"),
    path('apps/<str:serial>/ssl/new/', super_required(app_views.app_certificate_new.as_view()), name="app_ssl_new"),
    path('apps/<str:serial>/user/new/', super_required(app_views.app_user_new.as_view()), name="app_user_new"),
    path('apps/<str:serial>/delete/', super_required(app_views.app_delete.as_view()), name="app_delete"),
    path('apps/<str:serial>/config/', super_required(app_views.app_config.as_view()), name="app_config"),
    path('apps/<str:serial>/certificate/', super_required(app_views.app_certificates.as_view()), name="app_certificates"),
    path('apps/<str:serial>/files/', super_required(app_views.app_files.as_view()), name="app_files"),
    path('apps/<str:serial>/files/ajax/', super_required(app_views.app_files_ajax.as_view()), name="app_files_ajax"),
    path('apps/files/upload/ajax/', super_required(app_views.app_files_ajax_upload.as_view()), name="app_files_ajax_upload"),
    path('apps/files/zip/extract/ajax/', super_required(app_views.extract_zip.as_view()), name="app_zip_extract"),
    path('apps/files/remove/', super_required(app_views.file_remove.as_view()), name="app_file_remove"),
    path('apps/files/edit/', super_required(app_views.file_edit.as_view()), name="app_file_edit"),

    path('restart/nginx/', super_required(app_views.nginx_restart.as_view()), name="nginx_restart"),
    path('restart/uwsgi/', super_required(app_views.uwsgi_restart.as_view()), name="uwsgi_restart"),
    path('restart/server/', super_required(app_views.server_restart.as_view()), name="server_restart"),

    # Mysql
    path('mysql/', super_required(mysql_views.databases.as_view()), name="mysql_databases"),
    path('mysql/new/', super_required(mysql_views.new.as_view()), name="mysql_database_new"),
    path('mysql/<str:serial>/delete/', super_required(mysql_views.delete.as_view()), name="mysql_database_delete"),
    path('mysql/<str:serial>/export/', super_required(mysql_views.export_sql.as_view()), name="mysql_database_export"),
    path('mysql/<str:serial>/import/', super_required(mysql_views.import_sql.as_view()), name="mysql_database_import"),
    path('mysql/<str:serial>/password/change/', super_required(mysql_views.password_change.as_view()), name="mysql_database_password_change"),

    # Settings
    path('settings/', super_required(setting_views.settings.as_view()), name="settings"),
    path('about/', super_required(setting_views.about.as_view()), name="about"),
    path('dpanel/update/', super_required(setting_views.dpanel_update.as_view()), name="dpanel_update"),
]
