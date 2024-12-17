import subprocess

from django.shortcuts import render
from django.views import View

from dpanel.models import MysqlDatabase


def mysql_tables(user, password, host, database):
    try:
        command = ['mysql', '-u', user, f'-p{password}', '-h', host, '-e', f"USE {database}; SHOW TABLE STATUS;"]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        status_lines = result.stdout.strip().split('\n')[1:]

        tables = []
        for line in status_lines:
            columns = line.split('\t')
            tables.append({
                "name": columns[0],
                "type": columns[1],
                "rows": columns[4],
                "size": columns[6],
                "collation": columns[14],
            })
        return tables


    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return []

def mysql_table_rows(user, password, host, database, table):
    try:
        # استعلام لاستخراج أسماء الأعمدة
        describe_command = ['mysql', '-u', user, f'-p{password}', '-h', host, '-e',
                            f'USE {database}; DESCRIBE {table};']
        describe_result = subprocess.run(describe_command, capture_output=True, text=True, check=True)

        # استخراج أسماء الأعمدة
        columns = describe_result.stdout.strip().split('\n')[1:]  # نتجاهل السطر الأول
        column_names = [col.split('\t')[0] for col in columns]  # استخراج أسماء الأعمدة

        # استعلام لاستخراج جميع البيانات من الجدول
        select_command = ['mysql', '-u', user, f'-p{password}', '-h', host, '-e',
                          f'USE {database}; SELECT * FROM {table};']
        select_result = subprocess.run(select_command, capture_output=True, text=True, check=True)

        # تقسيم النتائج إلى صفوف وقيم
        rows = select_result.stdout.strip().split('\n')[1:]  # نتجاهل السطر الأول الذي يحتوي على أسماء الأعمدة
        data = []

        for row in rows:
            # TODO: يتم تجاهل القيم التي لا توجد بها قيمة ويسبب ذلك خطأ ويجب ان يصلح
            values = row.split('\t')  # القيم في الصف
            row_dict = dict(zip(column_names, values))  # دمج الأعمدة مع القيم
            data.append(row_dict)  # إضافة الصف إلى القائمة

        return column_names, data  # إرجاع أسماء الأعمدة وقيم البيانات

    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return [], []


class manage(View):
    def get(self, request, serial):
        database = MysqlDatabase.objects.get(serial=serial)
        tables = mysql_tables(database.username, database.password, 'localhost', database.name)
        return render(request, 'mysql/manage.html', {'database': database, 'tables': tables})


class table(View):
    def get(self, request, serial, name):
        database = MysqlDatabase.objects.get(serial=serial)
        column_names, table_data = mysql_table_rows(database.username, database.password, 'localhost', database.name, name)
        return render(request, 'mysql/table.html', {'database': database, 'column_names': column_names, 'table_data': table_data})

