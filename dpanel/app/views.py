import os
import pathlib
import shutil
import socket
import subprocess

from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
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


class app_user_new(View):
    def post(self, request, serial):
        app = App.objects.get(serial=serial)
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        superuser = request.POST.get('superuser')
        if superuser == 'on':
            superuser = True
        else:
            superuser = False
        if username and password and email:
            try:
                cmd = f"from django.contrib.auth.models import User; User.objects.create_user('{username}', '{email}', '{password}', is_superuser={superuser})"
                os.system(f'sudo {app.venv_path}/bin/python {app.www_path}/manage.py shell -c "{cmd}"')
                messages.success(request, _('User created successfully for app {}').format(app.name))
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, _('Please enter a username and password and email and try again.'))
        return render(request, 'app/certificate.html', {'app': app})


class app_certificates(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        return render(request, 'app/certificate.html', {'app': app})


class app_certificate_new(View):
    def get(self, request, serial):
        wildcard = request.GET.get('wildcard') or None
        app = App.objects.get(serial=serial)
        try:
            create_domain_ssl(app.domain, wildcard)
            AppCertificate.objects.create(app=app)
            messages.success(request, _('Certificate created successfully'))
            subprocess.run("sudo systemctl reload nginx", shell=True, check=True)
        except Exception as e:
            messages.error(request, _('Certificate created failed'))
            messages.warning(request, str(e))

        return redirect('app_certificates', app.serial)


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
        try:
            pathlib.Path('/var/www-deleted').mkdir(parents=True, exist_ok=True)
            shutil.move(app.www_path, str(app.www_path).replace('/www/', '/www-deleted/') + str(
                timezone.now().strftime("_%Y-%m-%d_time_%H.%M.%S")))
        except Exception as e:
            pass
        try:
            os.remove(f'/etc/nginx/sites-available/{app.domain}.conf')
        except Exception as e:
            pass
        try:
            os.remove(f'/etc/nginx/sites-enabled/{app.domain}.conf')
        except Exception as e:
            pass
        try:
            os.remove(f'/etc/uwsgi/apps-available/{app.domain}.ini')
        except Exception as e:
            pass
        try:
            os.remove(f'/etc/uwsgi/apps-enabled/{app.domain}.ini')
        except Exception as e:
            pass
        try:
            shutil.rmtree(app.venv_path)
        except Exception as e:
            pass
        try:
            os.system(f'sudo certbot delete --cert-name {app.domain}')
        except Exception as e:
            pass
        os.system(f'sudo killall -9 uwsgi')
        os.system(f'sudo systemctl restart nginx')
        os.system(f'sudo systemctl restart uwsgi')
        return redirect('apps')


class app_files(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        path = app.www_path
        files = []
        dirs = []
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                files.append(f)
            else:
                dirs.append(f)
        return render(request, 'app/files.html', {'app': app, 'files': files, 'dirs': dirs, 'path': path,
                                                  'parent': pathlib.Path(path).parent.absolute()})


class app_files_ajax(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        path = request.GET.get('path')
        if not path.startswith(app.www_path):
            path = app.www_path
        files = []
        dirs = []
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                files.append(f)
            else:
                dirs.append(f)
        return render(request, 'app/inc/files-list.html', {'app': app, 'files': files, 'dirs': dirs, 'path': path,
                                                           'parent': pathlib.Path(path).parent.absolute()})


class app_files_ajax_upload(View):
    def post(self, request):
        print(request.POST.get)
        serial = request.POST.get('app')
        app = App.objects.get(serial=serial)
        path = request.POST.get('path')
        print(path, '   *****  ', app.www_path)
        if not path.startswith(app.www_path):
            return JsonResponse({"error": 1, "success": False})
        try:
            file = request.FILES['file']
            if file.name:
                fn = os.path.basename(file.name)
                open(f'{path}/{fn}', 'wb').write(file.read())
            req = {
                "error": 0,
                "success": True
            }
        except Exception as e:
            req = {
                "error": 1,
                "error_message": str(e),
                "success": False
            }

        return JsonResponse(req)


class extract_zip(View):
    def get(self, request):
        path = request.GET.get('path')
        file = request.GET.get('file')
        folder = request.GET.get('folder')
        try:
            if folder == 'true':
                print(file.rsplit('.', 1)[0])
                shutil.unpack_archive(file, file.rsplit('.', 1)[0])
            else:
                shutil.unpack_archive(file, path)
            req = {
                "error": 0,
                "success": True
            }
        except Exception as e:
            req = {
                "error": 1,
                "error_message": str(e),
                "success": False
            }

        return JsonResponse(req)


class file_remove(View):
    def get(self, request):
        file = request.GET.get('file')
        try:
            if os.path.isfile(file):
                os.remove(file)
            elif os.path.isdir(file):
                shutil.rmtree(file)
            req = {
                "error": 0,
                "success": True
            }
        except Exception as e:
            messages.error(request, str(e))
            req = {
                "error": 1,
                "error_message": str(e),
                "success": False
            }

        return JsonResponse(req)


class file_edit(View):
    def get(self, request):
        file = request.GET.get('file')
        if not os.path.isfile(file):
            return redirect('apps')
        filename = os.path.basename(file)
        with open(file, "r") as file:
            text = file.read()

        return render(request, 'app/text.html', {'text': text, 'filename': filename})

    def post(self, request):
        file = request.GET.get('file')
        text = request.POST.get('text')
        with open(file, "w") as file:
            file.write(text)
        messages.success(request, _('File was successfully updated'))
        return self.get(request)


class uwsgi_restart(View):
    def get(self, request):
        try:
            # subprocess.call(['uwsgi', '--reload', '/path/to/uwsgi.ini'])
            os.system(f'sudo systemctl restart nginx')
            os.system(f'sudo systemctl restart uwsgi')
            messages.success(request, _('uwsgi restarted successfully'))
        except subprocess.CalledProcessError as e:
            messages.error(request, _('uwsgi restart failed'))

        return redirect('apps')


class nginx_restart(View):
    def get(self, request):
        try:
            os.system(f'sudo systemctl restart nginx')
            messages.success(request, _('nginx restarted successfully'))
        except subprocess.CalledProcessError as e:
            messages.error(request, _('nginx restart failed'))

        return redirect('apps')
