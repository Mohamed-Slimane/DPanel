import os
import pathlib
import subprocess

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string

from dpanel.models import Option


def super_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return function

def get_option(key, default=''):
    option = default
    try:
        op = Option.objects.filter(key=key).first()
        if op and op.value != '':
            option = op.value
    except:
        pass
    return option


def save_option(key, value):
    option = Option.objects.filter(key=key)
    if option:
        option.update(key=key, value=value)
    else:
        Option(key=key, value=value).save()


def paginator(request, obj, number=None, page=1):
    paginator = Paginator(obj, get_option('paginator', '20') if not number else number)
    request_page = request.GET.get('page', page)
    try:
        objects = paginator.page(request_page)
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        objects = paginator.page(1)
    return objects


def create_domain_server_block(domain):
    try:
        from engine.settings import NGINX_FOLDER
        available_dir = os.path.join(NGINX_FOLDER, 'sites-available')
        domain.nginx_config = f'{available_dir}/{domain.serial}.conf'
        enabled_conf = domain.nginx_config.replace('available', 'enabled')
        conf = render_to_string('templates/nginx_config.conf', {'domain': domain})
        with open(domain.nginx_config, 'w') as f:
            f.write(conf)
        if os.path.exists(enabled_conf):
            os.system(f"unlink {enabled_conf}")
        os.system(f"ln -s {domain.nginx_config} {enabled_conf}")
        os.system(f'systemctl reload nginx')
        domain.save()
        return True
    except Exception as e:
        print(e)
        return False


def create_index_file(domain):
    pathlib.Path(domain.full_www_path()).mkdir(parents=True, exist_ok=True)
    index_path = domain.full_www_path() + '/index.html'
    if not os.path.exists(index_path):
        content = render_to_string('templates/index.html')
        with open(index_path, 'w') as f:
            f.write(content)


def create_uwsgi_config(app):
    try:
        from engine.settings import UWSGI_FOLDER
        available_dir = os.path.join(UWSGI_FOLDER, 'apps-available')
        app.uwsgi_config = f'{available_dir}/{app.serial}.ini'
        enabled_conf = app.uwsgi_config.replace('available', 'enabled')
        app.module = "{}:{}".format(str(app.startup_file).replace('.py', '').replace('/', '.'), app.entry_point)
        conf = render_to_string('templates/uwsgi_config.ini', {'app': app})
        with open(app.uwsgi_config, 'w') as f:
            f.write(conf)
        if os.path.exists(enabled_conf):
            subprocess.call(['unlink', enabled_conf])
        subprocess.call(['ln', '-s', {app.uwsgi_config}, {enabled_conf}])
        subprocess.call(['touch', f'{app.full_www_path()}/reload.trigger'])
        app.save()
        return True
    except Exception as e:
        return False


def create_venv(path):
    try:
        os.system(f'python3 -m venv {path}')
        return True
    except Exception as e:
        return False


def create_startup_file(app):
    try:
        if not str(app.startup_file).endswith('.py'):
            app.startup_file = f'{app.startup_file}.py'
        startup_file_path = f'{app.full_www_path()}/{app.startup_file}'
        startup_content = render_to_string('templates/startup.py')
        with open(startup_file_path, 'w') as f:
            f.write(startup_content)
        return True
    except Exception as e:
        return False


def create_django_app(app):
    try:
        os.system('''
        cd {app.venv_path}
        chmod 755 -R {app.venv_path}
        chmod 755 -R {app.full_www_path()}
        {app.venv_path}/bin/pip install django
        {app.venv_path}/bin/pip install uwsgi        
        cd {app.full_www_path()}
        django-admin startproject {app.uwsgi_path} .   
        {app.venv_path}/bin/python manage.py collectstatic --noinput   
        {app.venv_path}/bin/python manage.py migrate   
        '''.format(app=app))

        import fileinput
        for line in fileinput.input(f'{app.full_www_path()}/{app.uwsgi_path}/settings.py', inplace=True):
            if line.startswith('ALLOWED_HOSTS = '):
                line = f"ALLOWED_HOSTS = ['{app.domain.name}']\n"
            print(line, end='')
        return True
    except Exception as e:
        return False


def check_db_installed(db_command):
    try:
        import subprocess
        subprocess.check_output([db_command, "--version"])
        return True
    except FileNotFoundError:
        return False


def get_cpu_usage():
    with open('/proc/stat') as file:
        line = file.readline()
        fields = line.split()
        idle = float(fields[4])
        total = sum(float(field) for field in fields[1:])
        cpu_percent = 100.0 - (idle / total * 100.0)
    return cpu_percent


def get_memory_usage():
    with open('/proc/meminfo') as file:
        total_mem = int(file.readline().split()[1])
        free_mem = int(file.readline().split()[1])
    used_mem = total_mem - free_mem
    mem_percent = (used_mem / total_mem) * 100.0
    return mem_percent


def get_dir_usage(directory='/var/www'):
    result = subprocess.run(['df', '-h', directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise Exception(f"Error getting filesystem info: {result.stderr}")
    lines = result.stdout.strip().split('\n')
    fs_info = lines[-1].split()
    total_space = fs_info[1]
    used_space = fs_info[2]
    percent_used = fs_info[4]
    return {'total': total_space, 'used': used_space, 'percent': percent_used}


def get_number_of_threads():
    with open('/proc/stat') as file:
        for line in file:
            if line.startswith('processes'):
                return int(line.split()[1])


def get_number_of_processes():
    with open('/proc/stat') as file:
        for line in file:
            if line.startswith('processes'):
                return int(line.split()[1])

