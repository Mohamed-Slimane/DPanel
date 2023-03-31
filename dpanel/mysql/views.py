import os
import random
import string
import uuid
from pathlib import Path

from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from dpanel.forms import MysqlDatabaseForm
from dpanel.models import MysqlDatabase
import mysql.connector


class databases(View):
    def get(self, request):
        databases = MysqlDatabase.objects.all()
        return render(request, 'mysql/databases.html', {'databases': databases})


class database_new(View):
    def post(self, request):
        form = MysqlDatabaseForm(request.POST, request.FILES)
        if form.is_valid():
            database = form.save(commit=False)
            database.password = str(uuid.uuid4()).replace('-', '')[:10]

            os.system(f'sudo mysql -e "CREATE DATABASE {database.name};"')
            os.system("sudo mysql -e \"CREATE USER '{database.username}'@'localhost' IDENTIFIED BY '{database.password}'\"".format(database=database))
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