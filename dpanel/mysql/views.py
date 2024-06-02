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
from dpanel.models import MysqlDatabase


class databases(View):
    def post(self, request):
        mysql_status = get_option('mysql_status')
        if not mysql_status or mysql_status == 'False':
            if request.POST.get('mysql_install'):
                res = install_mysql_server()
            else:
                res = {
                    'success': False,
                    'message': _('Form validation error')
                }
        else:
            res = {
                'success': False,
                'message': _('There is an existing Mysql server installed')
            }
        return JsonResponse(res)

    def get(self, request):
        databases = MysqlDatabase.objects.all()
        databases = paginator(request, databases, int(get_option('paginator', '20')))
        return render(request, 'mysql/databases.html', {'databases': databases})


class new(View):
    def post(self, request):
        form = MysqlDatabaseForm(request.POST)
        if form.is_valid():
            database = form.save(commit=False)
            database.password = str(uuid.uuid4()).replace('-', '')[:15]

            try:
                subprocess.run(['sudo', 'mysql', '-e', f'CREATE DATABASE {database.name};'])
                subprocess.run(['sudo', 'mysql', '-e', f"CREATE USER '{database.username}'@'localhost' IDENTIFIED BY '{database.password}';"])
                subprocess.run(['sudo', 'mysql', '-e', f"GRANT ALL PRIVILEGES ON {database.name}.* TO '{database.username}'@'localhost';"])

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
        os.system(f'sudo mysql -e "DROP DATABASE {database.name};"')
        os.system(f'sudo mysql -e "DROP USER \'{database.username}\'@\'localhost\';"')
        database.delete()
        return redirect('mysql_databases')


class export_sql(View):
    def get(self, request, serial):
        database = MysqlDatabase.objects.get(serial=serial)
        Path('/var/server/dpanel/backups/mysql/').mkdir(parents=True, exist_ok=True)
        database_file = f'/var/server/dpanel/backups/mysql/{database.name}_{datetime.datetime.today().strftime("%d-%m-%Y_%H-%M")}.sql.gz'
        os.system(f'sudo mysqldump {database.name} | gzip > {database_file}')

        if os.path.exists(database_file):
            file_size = os.path.getsize(database_file)
            filename = os.path.basename(database_file)
            response = HttpResponse(FileWrapper(open(database_file, 'rb')), content_type='application/gzip')
            response['Content-Disposition'] = 'attachment; filename=%s' % filename
            response['Content-Length'] = file_size
            return response
        else:
            return HttpResponse("The file does not exist")

        # return serve(request, os.path.basename(database_file), os.path.dirname(database_file))
        # return redirect('mysql_databases')


class import_sql(View):
    def post(self, request, serial):
        database = MysqlDatabase.objects.get(serial=serial)
        try:
            sql_file = request.FILES['sql_file']
        except Exception as e:
            messages.error(request, f"Failed to import SQL file: {e}")
            return redirect('mysql_databases')

        if sql_file.name.endswith('.gz') or sql_file.name.endswith('.sql'):
            try:
                os.system(f'sudo mysql -e "DROP DATABASE {database.name};"')
                subprocess.run(['sudo', 'mysql', '-e', f'CREATE DATABASE {database.name};'])
                subprocess.run(['sudo', 'mysql', '-e', f"CREATE USER '{database.username}'@'localhost' IDENTIFIED BY '{database.password}';"])
                subprocess.run(['sudo', 'mysql', '-e', f"GRANT ALL PRIVILEGES ON {database.name}.* TO '{database.username}'@'localhost';"])
                mysql_command = ['mysql', database.name]
                # Check if the file is a gzipped file
                if sql_file.name.endswith('.gz'):
                    # Read the gzipped content, decompress, and then decode it as text
                    with gzip.open(sql_file, 'rb') as f:
                        sql_content = f.read().decode('utf-8')
                else:
                    # Read the content of a regular SQL file directly
                    sql_content = sql_file.read().decode('utf-8')

                subprocess.run(mysql_command, input=sql_content, text=True, check=True)
                messages.success(request, _("SQL file imported successfully!"))
            except subprocess.CalledProcessError as e:
                messages.error(request, _(f"Failed to import SQL file: {e}"))
            except Exception as e:
                messages.error(request, _(f"Error handling the SQL file: {e}"))
        else:
            messages.error(request, _("File format is not supported!"))
        return redirect('mysql_databases')  # Redirect to the desired URL after handling the file


class password_change(View):
    def get(self, request, serial):
        database = MysqlDatabase.objects.get(serial=serial)
        database.password = str(uuid.uuid4()).replace('-', '')[:15]
        mysql_command = f"ALTER USER '{database.username}'@'localhost' IDENTIFIED BY '{database.password}';"
        try:
            subprocess.run(['sudo', 'mysql', '-e', mysql_command])
            database.save()
            messages.success(request, f"Password for user '{database.username}' changed successfully!")
        except subprocess.CalledProcessError as e:
            messages.error(request, f"Failed to change password: {e}")
        return redirect('mysql_databases')
