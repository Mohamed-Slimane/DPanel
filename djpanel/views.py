import os
import pathlib

from django.shortcuts import render
from django.views import View
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from djpanel.forms import AppForm
from djpanel.functions import create_app_server_block, create_venv, create_app, create_uwsgi_config
from djpanel.models import App
from engine.settings import WWW_FOLDER, VENV_FOLDER


class apps(View):
    def get(self, request):
        apps = App.objects.all()
        return render(request, 'app/apps.html', {'apps': apps})


class app_new(View):
    def post(self, request):
        form = AppForm(request.POST)
        if form.is_valid():
            app = form.save(commit=False)
            app.path = f'{WWW_FOLDER}{app.domain}'
            app.venv_path = f'{VENV_FOLDER}{app.domain}'

            pathlib.Path(app.path).mkdir(parents=True, exist_ok=True)
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
            messages.add_message(request, messages.SUCCESS, _('DjangoApp successfully created'))
            return redirect('app', app.serial)
        else:
            messages.add_message(request, messages.ERROR, _('Form validation error'))
            return render(request, 'app/new.html', {'form': form})

    def get(self, request):
        form = AppForm(request.POST or None)
        return render(request, 'app/new.html', {'form': form})