import os
import pathlib
import shutil
import socket
import subprocess
from datetime import datetime

from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from dpanel.forms import AppForm
from dpanel.functions import create_app_server_block, create_venv, create_app, create_uwsgi_config, get_option, \
    install_uwsgi_server, install_nginx_server, paginator, create_startup_file
from dpanel.models import App, AppCertificate
from dpanel.ssl import create_app_ssl, install_certbot


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
        apps = App.objects.all()
        apps = paginator(request, apps, int(get_option('paginator', '20')))
        return render(request, 'app/apps.html', {'apps': apps})


class app_user_new(View):
    def post(self, request, serial):
        app = App.objects.get(serial=serial)
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        superuser = request.POST.get('superuser')
        if superuser == 'on':
            is_superuser = True
        else:
            is_superuser = False
        if username and password and email:
            try:
                from django.contrib.auth.models import User
                cmd = f"from django.contrib.auth.models import User; User.objects.create_user(username='{username}', email='{email}', password='{password}', is_superuser={is_superuser})"
                full_command = f"sudo {app.venv_path}/bin/python {app.www_path}/manage.py shell -c \"{cmd}\""
                # Execute the command using os.system()
                os.system(full_command)

                messages.success(request, full_command)
                messages.success(request, _('User created successfully for app {}').format(app.name))
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, _('Please enter a username and password and email and try again.'))
        return render(request, 'app/certificate.html', {'app': app})


class app_restart(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        try:
            subprocess.call(['sudo', 'service', 'uwsgi', 'restart', f'/etc/uwsgi/apps-enabled/{app.serial}.ini'])
            app.is_active = True
            app.save()
            messages.success(request, f'Successfully restarted app <b>{app.name}</b>.')
        except subprocess.CalledProcessError as e:
            messages.error(request, f'Error restarting app: {e.stderr}')

        return redirect('apps')


class app_status(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        try:
            if app.is_active:
                subprocess.call(['sudo', 'service', 'uwsgi', 'stop', f'/etc/uwsgi/apps-enabled/{app.serial}.ini'])
                messages.success(request, f'Successfully stopped app <b>{app.name}</b>.')
            else:
                subprocess.call(['sudo', 'service', 'uwsgi', 'start', f'/etc/uwsgi/apps-enabled/{app.serial}.ini'])
                messages.success(request, f'Successfully started app <b>{app.name}</b>.')
            app.is_active = not app.is_active
            app.save()
        except subprocess.CalledProcessError as e:
            messages.error(request, f'Error stopping app: {e.stderr}')

        return redirect('apps')


class app_certificates(View):
    def post(self, request, serial):
        certbot_status = get_option('certbot_status')
        if not certbot_status or certbot_status == 'False':
            if request.POST.get('certbot_install'):
                res = install_certbot()
            else:
                res = {'success': False, 'message': _('Form validation error')}
        else:
            res = {'success': False, 'message': _('Certbot is already installed')}
        return JsonResponse(res)

    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        return render(request, 'app/certificate.html', {'app': app})


class app_certificate_new(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        try:
            expiration_date = create_app_ssl(app)
            if expiration_date:
                AppCertificate.objects.create(app=app, expire_date=expiration_date)
            messages.success(request, _('Certificate created successfully'))
            subprocess.run("sudo systemctl reload nginx", shell=True, check=True)
        except subprocess.CalledProcessError as e:
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

            the_block = create_app_server_block(app)
            if not the_block:
                messages.add_message(request, messages.ERROR, _('Failed to create app server block'))
                return self.get(request)
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
                    messages.add_message(request, messages.ERROR,
                                         _('Failed to create startup.py'))  # return self.get(request)
            else:
                pass
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
            shutil.copy(app.nginx_config, f'/etc/nginx/sites-enabled/{app.serial}.conf')
            os.system(f'sudo systemctl restart nginx')
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
        subprocess.call(['sudo', 'service', 'uwsgi', 'stop', f'/etc/uwsgi/apps-enabled/{app.serial}.ini'])
        try:
            pathlib.Path('/var/www-deleted').mkdir(parents=True, exist_ok=True)
            shutil.move(app.www_path, str(app.www_path).replace('/www/', '/www-deleted/') + str(
                timezone.now().strftime("_%Y-%m-%d_time_%H.%M.%S")))
        except Exception as e:
            pass
        try:
            subprocess.call(['sudo', 'rm', f'/etc/nginx/sites-available/{app.serial}.conf'])
        except Exception as e:
            pass
        try:
            subprocess.call(['sudo', 'rm', f'/etc/nginx/sites-enabled/{app.serial}.conf'])
        except Exception as e:
            pass
        try:
            subprocess.call(['sudo', 'rm', f'/etc/uwsgi/apps-available/{app.serial}.ini'])
        except Exception as e:
            pass
        try:
            subprocess.call(['sudo', 'rm', f'/etc/uwsgi/apps-enabled/{app.serial}.ini'])
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
        os.system(f'sudo systemctl restart nginx')
        messages.success(request, _('App deleted successfully'))
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
        files.sort()
        dirs.sort()
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
            req = {"error": 0, "success": True}
        except Exception as e:
            req = {"error": 1, "error_message": str(e), "success": False}

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
            req = {"error": 0, "success": True}
        except Exception as e:
            req = {"error": 1, "error_message": str(e), "success": False}

        return JsonResponse(req)


class file_remove(View):
    def get(self, request):
        file = request.GET.get('file')
        try:
            if os.path.isfile(file):
                os.remove(file)
            elif os.path.isdir(file):
                shutil.rmtree(file)
            req = {"error": 0, "success": True}
        except Exception as e:
            messages.error(request, str(e))
            req = {"error": 1, "error_message": str(e), "success": False}

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


class server_restart(View):
    def get(self, request):
        try:
            subprocess.run(['reboot'])
            messages.success(request, _('Server restarted successfully'))
        except subprocess.CalledProcessError as e:
            messages.error(request, _('Server restart failed'))
        return redirect('apps')
