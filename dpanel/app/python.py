import os
import os
import pathlib
import shutil
import socket
import subprocess

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views import View

from dpanel.forms import PythonAppForm, PythonAppEditForm
from dpanel.functions import create_venv, create_uwsgi_config, get_option, paginator, create_startup_file, \
    create_domain_server_block
from dpanel.models import PythonApp, Domain


class apps(View):
    def get(self, request):
        apps = PythonApp.objects.all().order_by('-created')
        apps = paginator(request, apps, int(get_option('paginator', '20')))
        return render(request, 'app/python/apps.html', {'apps': apps})


class new(View):
    def post(self, request):
        form = PythonAppForm(request.POST)
        if form.is_valid():
            from engine.settings import VENV_FOLDER
            app = form.save(commit=False)
            if not app.www_path.startswith('/'):
                app.www_path = f'/{app.www_path}'
            sock = socket.socket()
            sock.bind(('', 0))
            app.port = sock.getsockname()[1]
            app.save()
            app.venv_path = f'{VENV_FOLDER}/{app.serial}'
            app.save()

            pathlib.Path(app.full_www_path()).mkdir(parents=True, exist_ok=True)
            pathlib.Path(app.venv_path).mkdir(parents=True, exist_ok=True)

            create_venv(app.venv_path)
            create_uwsgi_config(app)
            if not app.startup_file or app.startup_file == "startup.py":
                create_startup_file(app)
            if app.domain:
                create_domain_server_block(app.domain)
            messages.add_message(request, messages.SUCCESS, _('App successfully created'))
            return redirect('apps')
        else:
            messages.add_message(request, messages.ERROR, _('Form validation error'))
            return render(request, 'app/python/new.html', {'form': form})

    def get(self, request):
        form = PythonAppForm(request.POST or None)
        return render(request, 'app/python/new.html', {'form': form})


class edit(View):
    def post(self, request, serial):
        app = PythonApp.objects.get(serial=serial)
        old_domain = app.domain
        form = PythonAppEditForm(request.POST, instance=app)
        if form.is_valid():
            app = form.save(commit=False)
            app.save()
            create_uwsgi_config(app)
            if old_domain != app.domain:
                if old_domain:
                    create_domain_server_block(Domain.objects.get(serial=old_domain.serial))
                if app.domain:
                    create_domain_server_block(app.domain)

            messages.success(request, _('App successfully updated'))
            return redirect('apps')
        messages.error(request, _('Form validation error'))
        return self.get(request, serial)

    def get(self, request, serial):
        app = PythonApp.objects.get(serial=serial)
        form = PythonAppEditForm(request.POST or None, instance=app)
        return render(request, 'app/python/edit.html', {'app': app, 'form': form})


class delete(View):
    def get(self, request, serial):
        app = PythonApp.objects.get(serial=serial)
        try:
            subprocess.call(['unlink', app.uwsgi_config.replace('available', 'enabled')])
        except Exception as e: pass
        try:
            subprocess.call(['rm', app.uwsgi_config])
        except Exception as e: pass
        try:
            shutil.rmtree(app.venv_path)
        except Exception as e: pass
        app.delete()
        if app.domain:
            create_domain_server_block(Domain.objects.get(serial=app.domain.serial))
        messages.success(request, _('App deleted successfully'))
        return redirect('apps')


class restart(View):
    def get(self, request, serial):
        app = PythonApp.objects.get(serial=serial)
        if not app.is_active:
            return redirect('app_status', serial)
        try:
            subprocess.call(['touch', f'{app.full_www_path()}/reload.trigger'])
            messages.success(request, f'Successfully restarted app <b>{app.name}</b>.')
        except subprocess.CalledProcessError as e:
            messages.error(request, f'Error restarting app: {e.stderr}')
        return redirect('apps')


class status(View):
    def get(self, request, serial):
        app = PythonApp.objects.get(serial=serial)
        try:
            if app.is_active:
                subprocess.call(['unlink', app.uwsgi_config.replace('available', 'enabled')])
                messages.success(request, f'Successfully stopped app <b>{app.name}</b>.')
            else:
                subprocess.call(['ln', '-s', app.uwsgi_config, app.uwsgi_config.replace('available', 'enabled')])
                messages.success(request, f'Successfully started app <b>{app.name}</b>.')
            app.is_active = not app.is_active
            app.save()
            subprocess.call(['touch', f'{app.full_www_path()}/reload.trigger'])
            create_domain_server_block(app.domain)
        except subprocess.CalledProcessError as e:
            messages.error(request, f'Error stopping app: {e.stderr}')
        return redirect('apps')



class log(View):
    def get(self, request, serial):
        app = PythonApp.objects.get(serial=serial)
        file = app.full_www_path() + '/log.log'
        if not os.path.isfile(file):
            messages.error(request, _('File not found'))
            return redirect('apps')
        filename = os.path.basename(file)
        with open(file, "r") as file:
            text = file.read()
        return render(request, 'file/preview.html', {'text': text, 'filename': filename})


class requirements_install(View):
    def get(self, request, serial):
        app = PythonApp.objects.get(serial=serial)
        requirements_file = app.full_www_path() + '/requirements.txt'
        try:
            with open(requirements_file, 'r', encoding='utf8') as f:
                pass
            if os.path.isfile(requirements_file):
                subprocess.call([app.venv_path+'/bin/pip', 'install', '-r', requirements_file])
                messages.success(request, _('Successfully installed requirements for app <b>{}</b>.').format(app.name))
            else:
                messages.error(request, _('File <b>requirements.txt</b> not found.'))
        except subprocess.CalledProcessError as e:
            messages.error(request, _('Error installing requirements: {}').format(e.stderr))
        except Exception as e:
            messages.error(request, str(e))
        return redirect('apps')


class package_install(View):
    def get(self, request):
        serial = request.GET.get('app')
        app = PythonApp.objects.get(serial=serial)
        packages = request.GET.getlist('packages')
        try:
            command = f"{app.venv_path}/bin/pip install " + " ".join(packages)
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            return JsonResponse(
                {'success': True, 'message': _('Successfully installed libraries: {}').format(", ".join(packages))})
        except subprocess.CalledProcessError as e:
            return JsonResponse({'success': False, 'message': _('Error installing libraries: {}').format(e.stderr)})
        except Exception as e:
            return JsonResponse({'success': False, 'message': _('Unexpected error: {}').format(str(e))})
