import os
import pathlib

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test


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
            app.uwsgi_config = uwsgi_conf
        os.system(f"sudo ln -s {uwsgi_conf} {enabled}/{app.domain}.ini")
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
        sudo {app.venv_path}/bin/python manage.py migrate   
        '''.format(app=app))
    except Exception as e:
        print(str(e))
