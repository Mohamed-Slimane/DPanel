import os
import pathlib
import subprocess
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import gettext_lazy as _
from dpanel.models import Option


def super_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    actual_decorator = user_passes_test(lambda u: u.is_superuser, login_url=login_url,
                                        redirect_field_name=redirect_field_name, )
    if function:
        return actual_decorator(function)
    return function


def create_app_server_block(app):
    try:
        available = '/etc/nginx/sites-available'
        enabled = '/etc/nginx/sites-enabled'
        pathlib.Path(available).mkdir(parents=True, exist_ok=True)
        pathlib.Path(enabled).mkdir(parents=True, exist_ok=True)
        nginx_conf = f'{available}/{app.serial}.conf'
        os.system(f'touch {nginx_conf}')
        conf = '''
upstream wsgi_server {{
    server 0.0.0.0:{app.port};
}}
server {{
    listen 80;
    listen [::]:80;

    server_name {app.domain};    
    root {app.www_path};  
    
    location / {{
        try_files $uri $uri/ =404;
        add_header Access-Control-Allow-Origin *;
        proxy_pass http://wsgi_server;
        include proxy_params;
    }}

    error_page 404 /404.html;

    location ~* \.(jpg|jpeg|gif|css|png|js|ico|html)$ {{
        access_log off;
        expires max;
    }}

    location ~ /\.(ht|py|db|html) {{
        deny  all;
    }}

    location  /. {{
        return 404;
    }}
}}
'''.format(app=app)
        with open(nginx_conf, 'w') as f:
            f.write(conf)
            app.nginx_config = nginx_conf
        os.system(f"ln -s {nginx_conf} {enabled}/{app.serial}.conf")
        return True
    except Exception as e:
        print(str(e))
        return False


def create_uwsgi_config(app):
    try:
        available = '/etc/uwsgi/apps-available'
        enabled = '/etc/uwsgi/apps-enabled'
        pathlib.Path(available).mkdir(parents=True, exist_ok=True)
        pathlib.Path(enabled).mkdir(parents=True, exist_ok=True)
        uwsgi_conf = f'{available}/{app.serial}.ini'
        module = "{}:{}".format(str(app.startup_file).replace('.py', ''), app.entry_point)
        os.system(f'touch {uwsgi_conf}')
        conf = f"""
[uwsgi]
# plugin = http
processname = {app.name}
processes = 1
threads = 2
chdir = {app.www_path}
module = {module}
http = 0.0.0.0:{app.port}
daemonize={app.www_path}/log.log
vacuum = true
master = true
max-requests = 1000
chmod-socket = 666
venv = {app.venv_path}
"""
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
        startup_content = """
HELLO_MESSAGE = '<!doctypehtml><html lang=en><meta charset=UTF-8><meta content="width=device-width,initial-scale=1"name=viewport><title>Startup</title><style>#logo{font-size:35px;font-weight:700}#logo span{background:#1d1e2c;padding:5px 20px;border-radius:5px;color:#fff}</style><body style=text-align:center;margin-top:50px;font-family:sans-serif><div id=logo><span>DPanel</span></div><div dir=rtl><p>مرحبا!<p><p>شكرًا لاستخدامك DPanel لإدارة خدمات الويب الخاصة بك.<p>هذا الملف هو ملف تجريبي تم إنشاؤه تلقائيًا بواسطة DPanel لاختبار الإعدادات والتجربة بها.</div><hr><p>Welcome!<p>Thank you for using DPanel to manage your web services.<p>This file is a demo file automatically created by DPanel for testing and experimenting with your settings'
def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    return [HELLO_MESSAGE.encode()]
        """
        # Write content to the startup.py file
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
                line = f"ALLOWED_HOSTS = ['{app.domain}']\n"
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
        subprocess.run(["sudo", "apt", "update"])
        subprocess.run(["sudo", "apt", "install", "-y", "nginx"])
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
        subprocess.run(["sudo", "apt", "update"])
        subprocess.run(["sudo", "apt", "install", "-y", "uwsgi"])
        subprocess.run(["python3", "-m", "pip", "install", "uwsgi"])
        subprocess.run(["python3", "-m", "pip", "install", "django"])
        file_path = "/etc/systemd/system/uwsgi.service"
        file_content = """
[Unit]
Description=uWSGI Emperor
After=syslog.target

[Service]
ExecStart=/usr/local/bin/uwsgi --emperor /etc/uwsgi/apps-enabled
Restart=always
KillSignal=SIGQUIT
Type=notify
StandardError=syslog
NotifyAccess=all

[Install]
WantedBy=multi-user.target
        """
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
        subprocess.run(["sudo", "apt", "update"])
        subprocess.run(["sudo", "apt", "install", "-y", "mysql-server"])
        subprocess.run(["sudo", "systemctl", "start", "mysql"])
        subprocess.run(["sudo", "systemctl", "enable", "mysql"])
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

