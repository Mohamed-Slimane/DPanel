import datetime
import gzip
import os
import subprocess
import uuid
from pathlib import Path
from wsgiref.util import FileWrapper

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View

from dpanel.forms import MysqlDatabaseForm
from dpanel.functions import get_option, install_mysql_server, paginator
from dpanel.models import MysqlDatabase, MysqlDatabaseBackup


class databases(View):
    def post(self, request):
        mysql_status = get_option('mysql_status')
        if not mysql_status or mysql_status == 'False':
            if request.POST.get('mysql_install'):
                res = install_mysql_server()
            else:
                res = {'success': False, 'message': _('Form validation error')}
        else:
            res = {'success': False, 'message': _('There is an existing MySQL server installed')}
        return JsonResponse(res)

    def get(self, request):
        databases = MysqlDatabase.objects.all()
        databases = paginator(request, databases, int(get_option('paginator', '20')))
        return render(request, 'mysql/databases.html', {'databases': databases})


class database(View):
    def get(self, request, serial):
        database = MysqlDatabase.objects.get(serial=serial)
        return render(request, 'mysql/database.html', {'database': database})


class new(View):
    def post(self, request):
        form = MysqlDatabaseForm(request.POST)
        if form.is_valid():
            database = form.save(commit=False)
            database.password = str(uuid.uuid4()).replace('-', '')[:15]
            try:
                subprocess.run(['mysql', '-e', f'CREATE DATABASE {database.name};'])
                subprocess.run(['mysql', '-e',
                                f"CREATE USER '{database.username}'@'localhost' IDENTIFIED BY '{database.password}';"])
                subprocess.run(
                    ['mysql', '-e', f"GRANT ALL PRIVILEGES ON {database.name}.* TO '{database.username}'@'localhost';"])

                database.save()
                messages.add_message(request, messages.SUCCESS, _('Database successfully created'))
            except Exception as e:
                messages.add_message(request, messages.ERROR, str(e))
                return self.get(request)

            return redirect('mysql_databases')
        else:
            messages.add_message(request, messages.ERROR, _('Form validation error'))
            return self.get(request)

    def get(self, request):
        form = MysqlDatabaseForm(request.POST or None)
        return render(request, 'mysql/new.html', {'form': form})


class delete(View):
    def get(self, request, serial):
        database = MysqlDatabase.objects.get(serial=serial)
        os.system(f'mysql -e "DROP DATABASE {database.name};"')
        os.system(f'mysql -e "DROP USER \'{database.username}\'@\'localhost\';"')
        database.delete()
        messages.warning(request, _('Database successfully deleted'))
        return redirect('mysql_databases')


class reset(View):
    def get(self, request, serial):
        database = MysqlDatabase.objects.get(serial=serial)
        os.system(f'mysql -e "DROP DATABASE IF EXISTS {database.name};"')
        subprocess.run(['mysql', '-e', f'CREATE DATABASE {database.name};'])
        subprocess.run(
            ['mysql', '-e', f"GRANT ALL PRIVILEGES ON {database.name}.* TO '{database.username}'@'localhost';"])
        messages.warning(request, _('Database successfully reset'))
        return redirect('mysql_database', serial)


class backup_create(View):
    def get(self, request, serial):
        database = MysqlDatabase.objects.get(serial=serial)
        folder = '/var/server/dpanel/backups/mysql/'
        Path(folder).mkdir(parents=True, exist_ok=True)
        database_file = f'{folder}{database.name}_{datetime.datetime.today().strftime("%d-%m-%Y_%H-%M-%S")}.sql.gz'
        os.system(f'mysqldump {database.name} | gzip > {database_file}')
        backup = MysqlDatabaseBackup(database=database, path=database_file)
        backup.save()
        messages.success(request, _('Backup created successfully for {}').format(database.name))
        return redirect('mysql_database', database.serial)


class backup_restore(View):
    def get(self, request, serial):
        backup = MysqlDatabaseBackup.objects.get(serial=serial)
        subprocess.run(['mysql', '-e', f'DROP DATABASE IF EXISTS {backup.database.name};'])
        subprocess.run(['mysql', '-e', f'CREATE DATABASE {backup.database.name};'])
        subprocess.run(['mysql', '-e',
                        f"GRANT ALL PRIVILEGES ON {backup.database.name}.* TO '{backup.database.username}'@'localhost';"])
        if backup.path.endswith('.gz'):
            with gzip.open(backup.path, 'rb') as f:
                sql_content = f.read().decode('utf-8')
        else:
            sql_content = backup.path.read().decode('utf-8')
        subprocess.run(['mysql', backup.database.name], input=sql_content, text=True)
        messages.success(request, _('Backup restored successfully for {}').format(backup.database.name))
        return redirect('mysql_database', backup.database.serial)


class backup_import(View):
    def post(self, request, serial):
        database = MysqlDatabase.objects.get(serial=serial)
        try:
            sql_file = request.FILES['sql_file']
        except Exception as e:
            messages.error(request, f"Failed to import SQL file: {e}")
            return redirect('mysql_databases')

        if sql_file.name.endswith('.gz') or sql_file.name.endswith('.sql'):
            try:
                os.system(f'mysql -e "DROP DATABASE IF EXISTS {database.name};"')
                subprocess.run(['mysql', '-e', f'CREATE DATABASE {database.name};'])
                subprocess.run(
                    ['mysql', '-e', f"GRANT ALL PRIVILEGES ON {database.name}.* TO '{database.username}'@'localhost';"])
                if sql_file.name.endswith('.gz'):
                    with gzip.open(sql_file, 'rb') as f:
                        sql_content = f.read().decode('utf-8')
                else:
                    sql_content = sql_file.read().decode('utf-8')
                subprocess.run(['mysql', database.name], input=sql_content, text=True)
                messages.success(request, _("SQL file imported successfully!"))
            except subprocess.CalledProcessError as e:
                messages.error(request, _(f"Failed to import SQL file: {e}"))
            except Exception as e:
                messages.error(request, _(f"Error handling the SQL file: {e}"))
        else:
            messages.error(request, _("File format is not supported!"))
        return redirect('mysql_database', database.serial)


class backup_delete(View):
    def get(self, request, serial):
        backup = MysqlDatabaseBackup.objects.get(serial=serial)
        backup.delete()
        messages.warning(request, _('Backup deleted successfully {}').format(backup.filename()))
        if backup.database:
            return redirect('mysql_database', backup.database.serial)
        else:
            return redirect('mysql_databases')


class backup_download(View):
    def get(self, request, serial):
        backup = MysqlDatabaseBackup.objects.get(serial=serial)
        if os.path.exists(backup.path):
            file_size = os.path.getsize(backup.path)
            filename = os.path.basename(backup.path)
            response = HttpResponse(FileWrapper(open(backup.path, 'rb')), content_type='application/gzip')
            response['Content-Disposition'] = 'attachment; filename=%s' % filename
            response['Content-Length'] = file_size
            return response
        else:
            messages.error(request, _('Backup file not found'))
            return redirect('mysql_database', backup.database.serial)


class password_change(View):
    def get(self, request, serial):
        database = MysqlDatabase.objects.get(serial=serial)
        database.password = str(uuid.uuid4()).replace('-', '')[:15]
        mysql_command = f"ALTER USER '{database.username}'@'localhost' IDENTIFIED BY '{database.password}';"
        try:
            subprocess.run(['mysql', '-e', mysql_command])
            database.save()
            messages.success(request, f"Password for user '{database.username}' changed successfully!")
        except subprocess.CalledProcessError as e:
            messages.error(request, f"Failed to change password: {e}")
        return redirect('mysql_database', database.serial)
