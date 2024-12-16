import os
import os
import pathlib
import shutil
import socket
import subprocess
import uuid

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views import View

from dpanel.forms import AppForm, AppEditForm
from dpanel.functions import create_venv, create_uwsgi_config, get_option, \
    install_uwsgi_server, install_nginx_server, paginator, create_startup_file, create_domain_server_block
from dpanel.models import App


class apps(View):
    def post(self, request):
        uwsgi_status = get_option('uwsgi_status')
        nginx_status = get_option('nginx_status')
        if not uwsgi_status or uwsgi_status == 'False' or not nginx_status or nginx_status == 'False':
            if request.POST.get('uwsgi_install'):
                res = install_uwsgi_server()
            elif request.POST.get('nginx_install'):
                res = install_nginx_server()
            else:
                res = {'success': False, 'message': _('Form validation error')}
        else:
            res = {'success': False, 'message': _('There is an existing uwsgi or nginx server installed')}
        return JsonResponse(res)

    def get(self, request):
        apps = App.objects.all().order_by('-created')
        apps = paginator(request, apps, int(get_option('paginator', '20')))
        return render(request, 'app/apps.html', {'apps': apps})


class app_new(View):
    def post(self, request):
        form = AppForm(request.POST)
        if form.is_valid():
            from engine.settings import WWW_FOLDER
            from engine.settings import VENV_FOLDER

            app = form.save(commit=False)
            app.serial = uuid.uuid4()
            app.www_path = os.path.join(WWW_FOLDER, str(app.domain))
            app.venv_path = os.path.join(VENV_FOLDER, str(app.serial))

            pathlib.Path(app.www_path).mkdir(parents=True, exist_ok=True)
            pathlib.Path(app.venv_path).mkdir(parents=True, exist_ok=True)

            sock = socket.socket()
            sock.bind(('', 0))
            app.port = sock.getsockname()[1]

            the_venv = create_venv(app.venv_path)
            if not the_venv:
                messages.add_message(request, messages.ERROR, _('Failed to create venv'))
                return self.get(request)
            the_wsgi = create_uwsgi_config(app)
            if not the_wsgi:
                messages.add_message(request, messages.ERROR, _('Failed to create uwsgi config'))
                return self.get(request)
            if not app.startup_file or app.startup_file == "startup.py":
                the_startup = create_startup_file(app)
                if not the_startup:
                    messages.add_message(request, messages.ERROR, _('Failed to create startup.py'))
            the_block = create_domain_server_block(app.domain)
            if not the_block:
                messages.add_message(request, messages.ERROR, _('Failed to create domain server block'))
                return self.get(request)
            app.save()
            os.system(f'systemctl reload nginx')
            os.system(f'systemctl restart uwsgi')
            messages.add_message(request, messages.SUCCESS, _('App successfully created'))
            return redirect('apps')
        else:
            messages.add_message(request, messages.ERROR, _('Form validation error'))
            return render(request, 'app/new.html', {'form': form})

    def get(self, request):
        form = AppForm(request.POST or None)
        return render(request, 'app/new.html', {'form': form})


class edit(View):
    def post(self, request, serial):
        app = App.objects.get(serial=serial)
        form = AppEditForm(request.POST, instance=app)
        if form.is_valid():
            form.save()
            the_wsgi = create_uwsgi_config(app)
            if not the_wsgi:
                messages.add_message(request, messages.ERROR, _('Failed to update uwsgi config'))
            messages.success(request, _('App updated successfully'))
            if app.is_active:
                subprocess.call(['service', 'uwsgi', 'restart', f'/etc/uwsgi/apps-enabled/{app.serial}.ini'])
            return redirect('apps')
        messages.error(request, _('Form validation error'))
        return self.get(request, serial)

    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        form = AppEditForm(request.POST or None, instance=app)
        return render(request, 'app/edit.html', {'app': app, 'form': form})


class delete(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        app.delete()
        create_domain_server_block(app.domain)
        try:
            subprocess.call(['rm', app.uwsgi_config])
        except Exception as e:
            pass
        try:
            subprocess.call(['rm', str(app.uwsgi_config).replace('enabled', 'available')])
        except Exception as e:
            pass
        try:
            shutil.rmtree(app.venv_path)
        except Exception as e:
            pass
        os.system(f'systemctl restart uwsgi')
        os.system(f'systemctl reload nginx')
        messages.success(request, _('App deleted successfully'))
        return redirect('apps')


class restart(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        try:
            subprocess.call(['service', 'uwsgi', 'restart', f'/etc/uwsgi/apps-enabled/{app.serial}.ini'])
            if not app.is_active:
                app.is_active = True
                app.save()
            messages.success(request, f'Successfully restarted app <b>{app.name}</b>.')
        except subprocess.CalledProcessError as e:
            messages.error(request, f'Error restarting app: {e.stderr}')

        return redirect('apps')


class status(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        try:
            if app.is_active:
                subprocess.call(['rm', app.uwsgi_config])
                messages.success(request, f'Successfully stopped app <b>{app.name}</b>.')
            else:
                create_uwsgi_config(app)
                messages.success(request, f'Successfully started app <b>{app.name}</b>.')
            app.is_active = not app.is_active
            app.save()
            create_domain_server_block(app.domain)
            os.system(f'systemctl reload uwsgi')
        except subprocess.CalledProcessError as e:
            messages.error(request, f'Error stopping app: {e.stderr}')
        return redirect('apps')



class log(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        file = app.www_path + '/log.log'
        if not os.path.isfile(file):
            messages.error(request, _('File not found'))
            return redirect('apps')
        filename = os.path.basename(file)
        with open(file, "r") as file:
            text = file.read()
        return render(request, 'file/preview.html', {'text': text, 'filename': filename})


class requirements_install(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        requirements_file = app.www_path + '/requirements.txt'
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
        app = App.objects.get(serial=serial)
        package = request.GET.get('package')
        try:
            subprocess.call([app.venv_path + '/bin/pip', 'install', package])
            return JsonResponse({'success': True, 'message': _('Successfully installed library <b>{}</b> to app <b>{}</b>.').format(package, app.name)})
        except subprocess.CalledProcessError as e:
            return JsonResponse({'success': False, 'message': _('Error installing library: {}').format(e.stderr)})