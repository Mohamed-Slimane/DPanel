from django.contrib.auth import views as auth_views
from django.urls import path

from dpanel import views
from dpanel.domain import views as domain
from dpanel.app import python as app
from dpanel.certificate import views as certificate
from dpanel.file import views as file
from dpanel.functions import super_required
from dpanel.mysql import views as mysql_views, manage as mysql_manage, user as mysql_user
from dpanel.setting import views as setting_views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('logout/', super_required(auth_views.LogoutView.as_view()), name="logout"),
    path('password/change/', super_required(auth_views.PasswordChangeView.as_view(
        template_name='account/password-change.html', form_class=auth_views.SetPasswordForm)
    ), name="password_change"),
    path('password/change/done', super_required(auth_views.PasswordChangeDoneView.as_view(
        template_name='account/password-change-done.html')
    ), name="password_change_done"),

    # Dashboard
    path('', super_required(views.dashboard.as_view()), name="dashboard"),

    # Domains
    path('domains/', super_required(domain.domains.as_view()), name="domains"),
    path('domains/new/', super_required(domain.new.as_view()), name="domain_new"),
    path('domains/<str:serial>/edit/', super_required(domain.edit.as_view()), name="domain_edit"),
    path('domains/<str:serial>/delete/', super_required(domain.delete.as_view()), name="domain_delete"),
    path('domains/<str:serial>/config/', super_required(domain.config.as_view()), name="domain_config"),

    # Certificate
    path('domains/<str:serial>/certificates/', super_required(certificate.certificates.as_view()), name="certificates"),
    path('domains/<str:serial>/certificates/new/', super_required(certificate.certificate_new.as_view()), name="certificate_new"),

    # Apps
    path('apps/python/', super_required(app.apps.as_view()), name="apps"),
    path('apps/python/new/', super_required(app.new.as_view()), name="python_app_new"),
    path('apps/python/<str:serial>/edit/', super_required(app.edit.as_view()), name="python_app_edit"),
    path('apps/python/<str:serial>/delete/', super_required(app.delete.as_view()), name="python_app_delete"),
    path('apps/python/<str:serial>/status/', super_required(app.status.as_view()), name="python_app_status"),
    path('apps/python/<str:serial>/restart/', super_required(app.restart.as_view()), name="python_app_restart"),
    path('apps/python/<str:serial>/log/', super_required(app.log.as_view()), name="python_app_log"),
    path('apps/python/package/install/', super_required(app.package_install.as_view()), name="python_app_package_install"),
    path('apps/python/<str:serial>/package/requirements/', super_required(app.requirements_install.as_view()), name="python_app_requirements_install"),

    # Manage
    path('restart/uwsgi/', super_required(views.uwsgi_restart.as_view()), name="uwsgi_restart"),
    path('restart/nginx/', super_required(views.nginx_restart.as_view()), name="nginx_restart"),
    path('restart/mysql/', super_required(views.mysql_restart.as_view()), name="mysql_restart"),
    path('restart/server/', super_required(views.server_restart.as_view()), name="server_restart"),

    # MySQL User
    path('mysql/users/', super_required(mysql_user.users.as_view()), name="mysql_users"),
    path('mysql/user/new/', super_required(mysql_user.new.as_view()), name="mysql_user_new"),
    path('mysql/user/<serial>/edit/', super_required(mysql_user.edit.as_view()), name="mysql_user_edit"),
    path('mysql/user/<serial>/delete/', super_required(mysql_user.delete.as_view()), name="mysql_user_delete"),

    # MySQL Database
    path('mysql/', super_required(mysql_views.databases.as_view()), name="mysql_databases"),
    path('mysql/new/', super_required(mysql_views.new.as_view()), name="mysql_database_new"),
    path('mysql/<str:serial>/', super_required(mysql_views.database.as_view()), name="mysql_database"),
    path('mysql/<str:serial>/edit/', super_required(mysql_views.edit.as_view()), name="mysql_database_edit"),
    path('mysql/<str:serial>/delete/', super_required(mysql_views.delete.as_view()), name="mysql_database_delete"),
    path('mysql/<str:serial>/reset/', super_required(mysql_views.reset.as_view()), name="mysql_database_reset"),

    # MySQL Manage
    path('mysql/<str:serial>/manage/', super_required(mysql_manage.manage.as_view()), name="mysql_database_manage"),
    path('mysql/<str:serial>/manage/table/<name>/', super_required(mysql_manage.table.as_view()), name="mysql_database_manage_table"),

    # MySQL Backup
    path('mysql/<str:serial>/backup/', super_required(mysql_views.backup_create.as_view()), name="mysql_backup_create"),
    path('mysql/backup/<str:serial>/restore/', super_required(mysql_views.backup_restore.as_view()), name="mysql_backup_restore"),
    path('mysql/backup/<str:serial>/import/', super_required(mysql_views.backup_import.as_view()), name="mysql_backup_import"),
    path('mysql/backup/<str:serial>/delete/', super_required(mysql_views.backup_delete.as_view()), name="mysql_backup_delete"),
    path('mysql/backup/<str:serial>/download/', super_required(mysql_views.backup_download.as_view()), name="mysql_backup_download"),


    # Files
    path('apps/files/', super_required(file.files.as_view()), name="files"),
    path('apps/files/ajax/', super_required(file.files_ajax.as_view()), name="files_ajax"),
    path('apps/files/manage/upload/ajax/', super_required(file.files_ajax_upload.as_view()), name="files_ajax_upload"),
    path('apps/files/manage/preview/', super_required(file.file_preview.as_view()), name="file_preview"),
    path('apps/files/manage/edit/', super_required(file.file_edit.as_view()), name="file_edit"),
    path('apps/files/manage/remove/', super_required(file.file_remove.as_view()), name="file_remove"),
    path('apps/files/manage/download/', super_required(file.file_download.as_view()), name="file_download"),
    path('apps/files/manage/zip/extract/ajax/', super_required(file.extract_zip.as_view()), name="zip_extract"),

    # Settings
    path('settings/', super_required(setting_views.settings.as_view()), name="settings"),
    path('more/', super_required(setting_views.more.as_view()), name="more"),
]
