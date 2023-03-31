import os
import random
import string
import uuid
from pathlib import Path

import psycopg2
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from psycopg2._psycopg import AsIs

from dpanel.forms import PostgresDatabaseForm
from dpanel.models import PostgresDatabase


class databases(View):
    def get(self, request):
        databases = PostgresDatabase.objects.all()
        return render(request, 'postgres/databases.html', {'databases': databases})


class database_new(View):
    def post(self, request):
        form = PostgresDatabaseForm(request.POST, request.FILES)
        if form.is_valid():
            database = form.save(commit=False)
            database.password = ''.join(random.choice(string.ascii_letters) for i in range(10))
            conn = psycopg2.connect(
                database='postgres',
                host='127.0.0.1',
                port='5433',
                user='dppsql',
                password=Path('/var/.dppsql').read_text().replace('\n', '')
            )
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute(f"CREATE DATABASE {database.name}")
            cur.execute("CREATE USER {database.username} WITH PASSWORD '{password}'".format(database=database,
                                                                                            password=(AsIs(
                                                                                                database.password))))
            cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {database.name} TO {database.username}")
            conn.commit()
            cur.close()
            conn.close()

            database.save()
            messages.add_message(request, messages.SUCCESS, _('Database successfully created'))
            return redirect('postgres_databases')
        else:
            messages.add_message(request, messages.ERROR, _('Form validation error'))
            return render(request, 'postgres/new.html', {'form': form})

    def get(self, request):
        form = PostgresDatabaseForm(request.POST or None)
        return render(request, 'postgres/new.html', {'form': form})


class database_delete(View):
    def get(self, request, serial):
        database = PostgresDatabase.objects.get(serial=serial)
        os.system(f'sudo -u postgres dropdb {database.name}')
        os.system(f'sudo -u postgres dropuser {database.username} -e')
        database.delete()
        return redirect('postgres_databases')
