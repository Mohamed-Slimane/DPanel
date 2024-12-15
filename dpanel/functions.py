import os
import pathlib
import subprocess
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
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


def create_domain_server_block(domain, port=None, is_python_app=False):
    try:
        from engine.settings import NGINX_FOLDER
        available = os.path.join(NGINX_FOLDER, 'sites-available')
        enabled = os.path.join(NGINX_FOLDER, 'sites-enabled')
        pathlib.Path(available).mkdir(parents=True, exist_ok=True)
        pathlib.Path(enabled).mkdir(parents=True, exist_ok=True)
        nginx_conf = f'{available}/{domain.serial}.conf'
        os.system(f'touch {nginx_conf}')
        conf = render_to_string('templates/nginx_config.conf', {'server_name': domain.name, 'root': domain.www_path, 'port': port, 'is_python_app': is_python_app})
        with open(nginx_conf, 'w') as f:
            f.write(conf)
            domain.nginx_config = nginx_conf
        os.system(f"ln -s {nginx_conf} {enabled}/{domain.serial}.conf")
        return True
    except Exception as e:
        print(e)
        return False

def create_index_file(domain):
    pathlib.Path(domain.www_path).mkdir(parents=True, exist_ok=True)
    index_path = domain.www_path + '/index.html'
    if not os.path.exists(index_path):
        pathlib.Path(index_path).touch()
        content = render_to_string('templates/index.html')
        with open(domain.www_path + '/index.html', 'w') as f:
            f.write(content)

def create_uwsgi_config(app):
    try:
        from engine.settings import UWSGI_FOLDER
        available = os.path.join(UWSGI_FOLDER, 'apps-available')
        enabled = os.path.join(UWSGI_FOLDER, 'apps-enabled')
        pathlib.Path(available).mkdir(parents=True, exist_ok=True)
        pathlib.Path(enabled).mkdir(parents=True, exist_ok=True)
        uwsgi_conf = f'{available}/{app.serial}.ini'
        app.module = "{}:{}".format(str(app.startup_file).replace('.py', '').replace('/', '.'), app.entry_point)
        os.system(f'touch {uwsgi_conf}')
        conf = render_to_string('templates/uwsgi_config.ini', {'app': app})

        with open(uwsgi_conf, 'w') as f:
            f.write(conf)
        os.system(f"ln -s {uwsgi_conf} {enabled}/{app.serial}.ini")
        app.uwsgi_config = f'{enabled}/{app.serial}.ini'
        return True
    except Exception as e:
        print(str(e))
        return False

def create_venv(path):
    try:
        os.system(f'python3 -m venv {path}')
        return True
    except Exception as e:
        print(str(e))
        return False

def create_startup_file(app):
    try:
        if not str(app.startup_file).endswith('.py'):
            app.startup_file = f'{app.startup_file}.py'
        startup_file_path = f'{app.www_path}/{app.startup_file}'
        os.system(f'touch {startup_file_path}')
        startup_content = render_to_string('templates/startup.py')
        with open(startup_file_path, 'w') as f:
            f.write(startup_content)
        return True
    except Exception as e:
        print(str(e))
        return False


def create_app(app):
    try:
        os.system('''
        cd {app.venv_path}
        chmod 755 -R {app.venv_path}
        chmod 755 -R {app.www_path}
        {app.venv_path}/bin/pip install django
        {app.venv_path}/bin/pip install uwsgi        
        cd {app.www_path}
        django-admin startproject {app.uwsgi_path} .   
        {app.venv_path}/bin/python manage.py collectstatic --noinput   
        {app.venv_path}/bin/python manage.py migrate   
        '''.format(app=app))

        import fileinput
        for line in fileinput.input(f'{app.www_path}/{app.uwsgi_path}/settings.py', inplace=True):
            if line.startswith('ALLOWED_HOSTS = '):
                line = f"ALLOWED_HOSTS = ['{app.domain.name}']\n"
            print(line, end='')
        return True
    except Exception as e:
        print(str(e))
        return False


def check_db_installed(db_command):
    try:
        import subprocess
        subprocess.check_output([db_command, "--version"])
        return True
    except FileNotFoundError:
        return False


def install_nginx_server():
    try:
        subprocess.run(["apt", "update"])
        subprocess.run(["apt", "install", "-y", "nginx"])
        subprocess.run(['ufw', 'allow', '80'])
        subprocess.run(['ufw', 'allow', 'http'])
        subprocess.run(['ufw', 'allow', 'Nginx Full'])
        subprocess.run(['ufw', 'allow', '8080'])
        subprocess.run(['systemctl', 'start', 'nginx'])
        subprocess.run(['systemctl', 'enable', 'nginx'])

        success = True
        message = _("Nginx Server has been successfully installed")

        save_option('nginx_status', True)
    except Exception as e:
        success = False
        message = _("An error occurred while installing Nginx: {}").format(e)

    return {'success': success, 'message': message}


def install_uwsgi_server():
    try:
        subprocess.run(["apt", "update"])
        subprocess.run(["apt", "install", "-y", "uwsgi"])
        subprocess.run(["apt", "install", "-y", "uwsgi-plugin-python3"])
        # subprocess.run(["python3", "-m", "pip", "install", "uwsgi"])
        subprocess.run(["python3", "-m", "pip", "install", "django"])
        file_path = "/etc/systemd/system/uwsgi.service"
        file_content = render_to_string('templates/uwsgi_service.ini')
        with open(file_path, "w") as file:
            file.write(file_content)

        subprocess.run(['systemctl', 'start', 'uwsgi'])
        subprocess.run(['systemctl', 'enable', 'uwsgi'])
        success = True
        message = _("uwsgi Server has been successfully installed")
        save_option('uwsgi_status', True)
    except Exception as e:
        success = False
        message = _("An error occurred while installing uwsgi: {}").format(e)

    return {'success': success, 'message': message}


def install_mysql_server():
    try:
        subprocess.run(["apt", "update"])
        subprocess.run(["apt", "install", "-y", "mysql-server"])
        subprocess.run(["systemctl", "start", "mysql"])
        subprocess.run(["systemctl", "enable", "mysql"])
        success = True
        message = _("MySQL Server has been successfully installed")

        save_option('mysql_status', True)

    except Exception as e:
        success = False
        message = _("An error occurred while installing MySQL: {}").format(e)

    return {'success': success, 'message': message}


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

