import subprocess
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from dpanel.models import MysqlDatabase


def list_tables_mysql(user, password, host, database):
    try:
        command = ['mysql', '-u', user, f'-p{password}', '-h', host, '-e', f'USE {database}; SHOW TABLES;']

        result = subprocess.run(command, capture_output=True, text=True, check=True)
        table_list = result.stdout.strip().split('\n')[1:]
        tables = []
        for table in table_list:
            status_command = ['mysql', '-u', user, f'-p{password}', '-h', host, '-e',
                              f'USE {database}; SHOW TABLE STATUS LIKE \'{table}\';']
            status_result = subprocess.run(status_command, capture_output=True, text=True, check=True)
            if status_result.returncode != 0:
                print(f"Error: {status_result.stderr}")
                continue
            status_lines = status_result.stdout.strip().split('\n')[1:]
            status_columns = [line.split('\t') for line in status_lines]
            table_rows = status_columns[0][4]
            table_type = status_columns[0][1]
            table_collation = status_columns[0][14]
            table_size = status_columns[0][6]
            tables.append({"name": table, "rows": table_rows, "type": table_type, "collation": table_collation,
                           "size": table_size})

        return {'success': True, 'tables': tables}

    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return {'success': False}


class manage(View):
    def get(self, request, serial):
        database = MysqlDatabase.objects.get(serial=serial)
        return render(request, 'mysql/manage.html', {'database': database})


class tables(View):
    def get(self, request, serial):
        database = MysqlDatabase.objects.get(serial=serial)
        tables = list_tables_mysql(database.username, database.password, 'localhost', database.name)
        return JsonResponse(tables)

