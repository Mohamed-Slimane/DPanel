import os
import pathlib
import subprocess
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.utils.translation import gettext_lazy as _
from dpanel.models import Option


def super_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return function


def create_app_server_block(app):
    try:
        available = '/etc/nginx/sites-available'
        enabled = '/etc/nginx/sites-enabled'
        pathlib.Path(available).mkdir(parents=True, exist_ok=True)
        pathlib.Path(enabled).mkdir(parents=True, exist_ok=True)
        nginx_conf = f'{available}/{app.domain}.conf'
        os.system(f'sudo touch {nginx_conf}')
        conf = '''server
{{
    listen 80;
    listen [::]:80;

    server_name {app.domain};    
    root {app.www_path};  
    
    location / {{
        include proxy_params;
        proxy_pass http://0.0.0.0:{app.port};
    }}

    error_page 404 /404.html;


    location ~* \.(jpg|jpeg|gif|css|png|js|ico|html)$ {{
        access_log off;
        expires max;
    }}

    location ~* \.(eot|otf|ttf|woff|woff2|svg)$ {{
		add_header Access-Control-Allow-Origin *;
  	}}

    location ~ /\.(ht|py|txt|db|html) {{
        deny  all;
    }}

    location  /. {{ ## Disable .htaccess and other hidden files
        return 404;
    }}
}}
'''.format(app=app)
        with open(nginx_conf, 'w') as f:
            f.write(conf)
            app.nginx_config = nginx_conf
        os.system(f"sudo ln -s {nginx_conf} {enabled}/{app.domain}.conf")
    except Exception as e:
        print(str(e))


def create_uwsgi_config(app):
    try:
        available = '/etc/uwsgi/apps-available'
        enabled = '/etc/uwsgi/apps-enabled'
        pathlib.Path(available).mkdir(parents=True, exist_ok=True)
        pathlib.Path(enabled).mkdir(parents=True, exist_ok=True)
        uwsgi_conf = f'{available}/{app.domain}.ini'
        os.system(f'sudo touch {uwsgi_conf}')
        conf = '''
[uwsgi]
# plugin = http
processname = {app.name}
processes = 1
threads = 2
chdir = {app.www_path}
module = {app.uwsgi_path}.wsgi:application
http = 0.0.0.0:{app.port}
daemonize={app.www_path}/log.log
vacuum = true
master = true
max-requests = 1000
chmod-socket = 666
venv = {app.venv_path}
'''.format(app=app)
        with open(uwsgi_conf, 'w') as f:
            f.write(conf)
        os.system(f"sudo ln -s {uwsgi_conf} {enabled}/{app.domain}.ini")
        app.uwsgi_config = f'{enabled}/{app.domain}.ini'
    except Exception as e:
        print(str(e))


def create_venv(path):
    try:
        os.system(f'sudo python3 -m venv {path}')
    except Exception as e:
        print(str(e))


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
        sudo {app.venv_path}/bin/python manage.py collectstatic --noinput   
        sudo {app.venv_path}/bin/python manage.py migrate   
        '''.format(app=app))

        import fileinput
        for line in fileinput.input(f'{app.www_path}/{app.uwsgi_path}/settings.py', inplace=True):
            if line.startswith('ALLOWED_HOSTS = '):
                line = f"ALLOWED_HOSTS = ['{app.domain}']\n"
            print(line, end='')

    except Exception as e:
        print(str(e))


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
        subprocess.run(['sudo', 'ufw', 'allow', '80'])
        subprocess.run(['sudo', 'ufw', 'allow', 'http'])
        subprocess.run(['sudo', 'ufw', 'allow', 'https'])
        subprocess.run(['sudo', 'ufw', 'allow', 'Nginx Full'])
        subprocess.run(['sudo', 'ufw', 'allow', '8080'])
        subprocess.run(['sudo', 'systemctl', 'start', 'nginx'])
        subprocess.run(['sudo', 'systemctl', 'enable', 'nginx'])

        success = True
        message = _("Nginx Server has been successfully installed")

        save_option('nginx_status', True)

    except Exception as e:
        success = False
        message = _("An error occurred while installing Nginx: {}").format(e)

    return {
        'success': success,
        'message': message
    }


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

        subprocess.run(['sudo', 'systemctl', 'start', 'uwsgi'])
        subprocess.run(['sudo', 'systemctl', 'enable', 'uwsgi'])
        success = True
        message = _("uwsgi Server has been successfully installed")
        save_option('uwsgi_status', True)
    except Exception as e:
        success = False
        message = _("An error occurred while installing uwsgi: {}").format(e)

    return {
        'success': success,
        'message': message
    }


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

    return {
        'success': success,
        'message': message
    }


def install_psql_server():
    try:
        subprocess.run(["sudo", "apt", "update"])
        subprocess.run(["sudo", "apt", "install", "-y", "postgresql"])
        subprocess.run(["sudo", "systemctl", "start", "postgresql.service"])
        subprocess.run(["sudo", "systemctl", "enable", "postgresql.service"])
        success = True
        message = _("PostgreSQL Server has been successfully installed")

        save_option('psql_status', True)

    except Exception as e:
        success = False
        message = _("An error occurred while installing PostgreSQL: {}").format(e)

    return {
        'success': success,
        'message': message
    }


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
        option.update(
            key=key,
            value=value
        )
    else:
        Option(
            key=key,
            value=value
        ).save()
