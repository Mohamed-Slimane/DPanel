import os
import uuid
from pathlib import Path
from wsgiref.util import FileWrapper

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.datetime_safe import datetime
from django.utils.translation import gettext_lazy as _
from django.views import View

from dpanel.forms import MysqlDatabaseForm
from dpanel.models import MysqlDatabase


class databases(View):
    def get(self, request):
        databases = MysqlDatabase.objects.all()
        return render(request, 'mysql/databases.html', {'databases': databases})


class database_new(View):
    def post(self, request):
        form = MysqlDatabaseForm(request.POST, request.FILES)
        if form.is_valid():
            database = form.save(commit=False)
            database.password = str(uuid.uuid4()).replace('-', '')[:15]

            os.system(f'sudo mysql -e "set global validate_password.policy = LOW;"')
            os.system(f'sudo mysql -e "CREATE DATABASE {database.name};"')
            os.system(f"sudo mysql -e \"CREATE USER '{database.username}'@'localhost' IDENTIFIED BY '{database.password}'\"".format(database=database))
            # os.system(f"sudo mysql -e \"SET PASSWORD FOR '{database.username}'@'hostname' = PASSWORD('{database.password}');\"")
            os.system(f'sudo mysql -e "GRANT ALL PRIVILEGES ON {database.name}.* TO \'{database.username}\'@\'localhost\';"')

            database.save()
            messages.add_message(request, messages.SUCCESS, _('Database successfully created'))
            return redirect('mysql_databases')
        else:
            messages.add_message(request, messages.ERROR, _('Form validation error'))
            return render(request, 'mysql/new.html', {'form': form})

    def get(self, request):
        form = MysqlDatabaseForm(request.POST or None)
        return render(request, 'mysql/new.html', {'form': form})


class database_delete(View):
    def get(self, request, serial):
        database = MysqlDatabase.objects.get(serial=serial)
        os.system(f'sudo mysql -e "DROP DATABASE {database.name};"')
        os.system(f'sudo mysql -e "DROP USER \'{database.username}\'@\'localhost\';"')
        database.delete()
        return redirect('mysql_databases')


class database_download(View):
    def get(self, request, serial):
        database = MysqlDatabase.objects.get(serial=serial)
        Path('/var/dpfiles/backups/mysql/').mkdir(parents=True, exist_ok=True)
        database_file = f'/var/dpfiles/backups/mysql/{database.name}_{datetime.today().strftime("%d-%m-%Y_%H-%M")}.sql.gz'
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

# cnx = mysql.connector.connect(
#     user='dpmysql',
#     password=Path('/var/.dpmysql').read_text().replace('\n', ''),
#     host='localhost'
# )
#
# # Create a new database
# cursor = cnx.cursor()
# cursor.execute("CREATE DATABASE {}".format(database.name))
#
# # Create a new user and grant privileges on the new database
# cursor.execute("CREATE USER '{}'@'localhost' IDENTIFIED BY '{}'".format(database.username, database.password))
# cursor.execute("GRANT ALL PRIVILEGES ON {}.* TO '{}'@'localhost'".format(database.name, database.username))
# cursor.execute("FLUSH PRIVILEGES")
#
# # Close the cursor and connection
# cursor.close()
# cnx.close()
