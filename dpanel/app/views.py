import os
import pathlib
import shutil

from django.shortcuts import render
from django.views import View
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from dpanel.forms import AppForm
from dpanel.functions import create_app_server_block, create_venv, create_app, create_uwsgi_config
from dpanel.models import App, AppCertificate
from dpanel.ssl import create_domain_ssl


class apps(View):
    def get(self, request):
        apps = App.objects.all()
        return render(request, 'app/apps.html', {'apps': apps})


class app_ssl_new(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        try:
            create_domain_ssl(app.domain)
            AppCertificate.objects.create(app=app)
            messages.success(request, _('Certificate created successfully'))
        except Exception as e:
            messages.error(request, _('Certificate created failed'))
            messages.error(request, str(e))

        return redirect('apps')


class app_new(View):
    def post(self, request):
        form = AppForm(request.POST)
        if form.is_valid():
            app = form.save(commit=False)
            from engine.settings import WWW_FOLDER
            app.www_path = f'{WWW_FOLDER}{app.domain}'
            from engine.settings import VENV_FOLDER
            app.venv_path = f'{VENV_FOLDER}{app.domain}'

            pathlib.Path(app.www_path).mkdir(parents=True, exist_ok=True)
            pathlib.Path(app.venv_path).mkdir(parents=True, exist_ok=True)

            import socket
            sock = socket.socket()
            sock.bind(('', 0))
            app.port = sock.getsockname()[1]

            create_app_server_block(app)
            create_venv(app.venv_path)
            create_app(app)
            create_uwsgi_config(app)

            app.save()
            os.system(f'sudo systemctl restart nginx')
            os.system(f'sudo systemctl restart uwsgi.service')
            messages.add_message(request, messages.SUCCESS, _('App successfully created'))
            return redirect('apps')
        else:
            messages.add_message(request, messages.ERROR, _('Form validation error'))
            return render(request, 'app/new.html', {'form': form})

    def get(self, request):
        form = AppForm(request.POST or None)
        return render(request, 'app/new.html', {'form': form})


class app_config(View):
    def post(self, request, serial):
        config_code = request.POST.get('config_code')
        app = App.objects.get(serial=serial)
        try:
            with open(app.nginx_config, 'w') as f:
                f.write(config_code)
            os.system(f'sudo systemctl restart nginx')
            os.system(f'sudo systemctl restart uwsgi')
            messages.success(request, _('App configuration updated successfully'))
        except:
            messages.error(request, _('Error in updating django_app configuration'))
        return self.get(request, serial)

    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        try:
            config_code = pathlib.Path(app.nginx_config).read_text()
        except:
            config_code = None
        return render(request, 'app/config.html', {'app': app, 'config_code': config_code})


class app_delete(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        app.delete()
        os.rename(app.www_path, f'{app.www_path}-deleted')
        os.remove(f'/etc/nginx/sites-available/{app.domain}.conf')
        os.remove(f'/etc/nginx/sites-enabled/{app.domain}.conf')
        os.remove(f'/etc/uwsgi/apps-available/{app.domain}.ini')
        os.remove(f'/etc/uwsgi/apps-enabled/{app.domain}.ini')
        shutil.rmtree(app.venv_path)
        os.system(f'sudo systemctl restart nginx')
        os.system(f'sudo systemctl restart uwsgi')
        return redirect('apps')
