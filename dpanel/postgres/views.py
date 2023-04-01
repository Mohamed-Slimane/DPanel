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
            database.password = str(uuid.uuid4()).replace('-', '')[:15]

            os.system(f'sudo -u postgres psql -c "CREATE DATABASE {database.name};"')
            os.system(
                f'sudo -u postgres psql -c "CREATE USER {database.username} WITH PASSWORD \'{database.password}\';"')
            os.system(
                f'sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE {database.name} TO {database.username};"')

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


class database_download(View):
    def get(self, request, serial):
        database = PostgresDatabase.objects.get(serial=serial)
        Path('/var/dpfiles/backups/psql/').mkdir(parents=True, exist_ok=True)
        database_file = f'/var/dpfiles/backups/psql/{database.name}_{datetime.today().strftime("%d-%m-%Y_%H-%M")}.dump'
        os.system(f'sudo -u postgres pg_dump "postgresql://{database.username}:{database.password}@localhost/{database.name}" > {database_file}')

        if os.path.exists(database_file):
            file_size = os.path.getsize(database_file)
            filename = os.path.basename(database_file)
            response = HttpResponse(FileWrapper(open(database_file, 'rb')), content_type='application/gzip')
            response['Content-Disposition'] = 'attachment; filename=%s' % filename
            response['Content-Length'] = file_size
            return response
        else:
            return HttpResponse("The file does not exist")

        # return redirect('postgres_databases')

# conn = psycopg2.connect(
#     database='postgres',
#     host='127.0.0.1',
#     port='5433',
#     user='dppsql',
#     password=Path('/var/.dppsql').read_text().replace('\n', '')
# )
# conn.autocommit = True
# cur = conn.cursor()
# cur.execute(f"CREATE DATABASE {database.name}")
# cur.execute("CREATE USER {database.username} WITH PASSWORD '{password}'".format(database=database,
#                                                                                 password=(AsIs(
#                                                                                     database.password))))
# cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {database.name} TO {database.username}")
# conn.commit()
# cur.close()
# conn.close()
