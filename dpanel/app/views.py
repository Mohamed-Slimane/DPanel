import mimetypes
import os
import pathlib
import shutil
import socket
import subprocess
import uuid

from django.contrib import messages
from django.http import FileResponse
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View

from dpanel.forms import AppForm, AppEditForm
from dpanel.functions import create_app_server_block, create_venv, create_uwsgi_config, get_option, \
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
            app.www_path = f'{WWW_FOLDER}{app.domain}'
            app.venv_path = f'{VENV_FOLDER}{app.serial}'

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
            os.system(f'systemctl restart nginx')
            os.system(f'systemctl restart uwsgi.service')
            messages.add_message(request, messages.SUCCESS, _('App successfully created'))
            return redirect('apps')
        else:
            messages.add_message(request, messages.ERROR, _('Form validation error'))
            return render(request, 'app/new.html', {'form': form})

    def get(self, request):
        form = AppForm(request.POST or None)
        return render(request, 'app/new.html', {'form': form})


class app_edit(View):
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


class app_log(View):
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


class app_restart(View):
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


class app_status(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        try:
            if app.is_active:
                subprocess.call(['service', 'uwsgi', 'stop', f'/etc/uwsgi/apps-enabled/{app.serial}.ini'])
                messages.success(request, f'Successfully stopped app <b>{app.name}</b>.')
            else:
                subprocess.call(['service', 'uwsgi', 'start', f'/etc/uwsgi/apps-enabled/{app.serial}.ini'])
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
            subprocess.run("systemctl reload nginx", shell=True, check=True)
        except subprocess.CalledProcessError as e:
            messages.error(request, _('Certificate created failed'))
            messages.warning(request, str(e))

        return redirect('app_certificates', app.serial)


class app_config(View):
    def post(self, request, serial):
        config_code = request.POST.get('config_code')
        app = App.objects.get(serial=serial)
        try:
            with open(app.nginx_config, 'w') as f:
                f.write(config_code)
            with open(str(app.nginx_config).replace('sites-enabled/', 'sites-available/'), 'w') as f:
                f.write(config_code)
            os.system(f'systemctl restart nginx')
            messages.success(request, _('App configuration updated successfully'))
        except Exception as e:
            messages.error(request, _('Error in updating app configuration') + str(e))
        return self.get(request, serial)

    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        try:
            config_code = pathlib.Path(app.nginx_config).read_text()
        except Exception as e:
            config_code = ''
        return render(request, 'file/config.html', {'app': app, 'config_code': config_code})


class app_delete(View):
    def get(self, request, serial):
        app = App.objects.get(serial=serial)
        app.delete()
        subprocess.call(['service', 'uwsgi', 'stop', f'/etc/uwsgi/apps-enabled/{app.serial}.ini'])
        try:
            pathlib.Path('/var/www-deleted').mkdir(parents=True, exist_ok=True)
            shutil.move(app.www_path, str(app.www_path).replace('/www/', '/www-deleted/') + str(
                timezone.now().strftime("_%Y-%m-%d_time_%H.%M.%S")))
        except Exception as e:
            pass
        try:
            subprocess.call(['rm', f'/etc/nginx/sites-available/{app.serial}.conf'])
        except Exception as e:
            pass
        try:
            subprocess.call(['rm', f'/etc/nginx/sites-enabled/{app.serial}.conf'])
        except Exception as e:
            pass
        try:
            subprocess.call(['rm', f'/etc/uwsgi/apps-available/{app.serial}.ini'])
        except Exception as e:
            pass
        try:
            subprocess.call(['rm', f'/etc/uwsgi/apps-enabled/{app.serial}.ini'])
        except Exception as e:
            pass
        try:
            shutil.rmtree(app.venv_path)
        except Exception as e:
            pass
        try:
            os.system(f'certbot delete --cert-name {app.domain}')
        except Exception as e:
            pass
        os.system(f'systemctl restart nginx')
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
        return render(request, 'file/files.html', {'app': app, 'files': files, 'dirs': dirs, 'path': path,
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
        return render(request, 'file/list.html', {'app': app, 'files': files, 'dirs': dirs, 'path': path,
                                                  'parent': pathlib.Path(path).parent.absolute()})


class app_files_ajax_upload(View):
    def post(self, request):
        serial = request.POST.get('app')
        app = App.objects.get(serial=serial)
        path = request.POST.get('path')
        if not path.startswith(app.www_path):
            return JsonResponse({"error": 1, "success": False})
        try:
            if 'remote_file' in request.POST:
                url = request.POST.get('remote_file')
                import urllib.request
                try:
                    response = urllib.request.urlopen(url)
                    file_content = response.read()
                    filename = os.path.basename(url)
                    filename = filename.split('?')[0]
                    file_path = os.path.join(path, filename)
                    with open(file_path, 'wb') as f:
                        f.write(file_content)
                    return JsonResponse({'error': 0, 'success': True, 'message': 'File uploaded successfully.'})
                except urllib.error.URLError as e:
                    return JsonResponse(
                        {'error': 1, 'success': False, 'message': 'Failed to download the file: ' + str(e)})

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


class file_preview(View):
    image_extensions = ['.jpg', '.png', '.jpeg', '.svg', '.gif', '.webp', '.ico', '.bmp', '.tiff']
    pdf_extensions = ['.pdf']
    video_audio_extensions = ['.mp4', '.mkv', '.webm', '.mp3', '.m4a', '.ogg', '.avi', '.wmv', '.mov', '.flv', '.3gp']

    def get(self, request):
        file = request.GET.get('file')
        if not os.path.isfile(file):
            return redirect('apps')
        filename = os.path.basename(file)
        try:
            file_extension = file.lower()

            if any(file_extension.endswith(ext) for ext in self.image_extensions):
                return HttpResponse(open(file, 'rb'), content_type=mimetypes.guess_type(file)[0])

            if any(file_extension.endswith(ext) for ext in self.pdf_extensions):
                return FileResponse(open(file, 'rb'), content_type=mimetypes.guess_type(file)[0])

            if any(file_extension.endswith(ext) for ext in self.video_audio_extensions):
                return FileResponse(open(file, 'rb'), content_type=mimetypes.guess_type(file)[0])

            with open(file, "r") as f:
                text = f.read()
            return render(request, 'file/preview.html', {'text': text, 'filename': filename})

        except Exception as e:
            return HttpResponse(_('Cannot preview this file: {}'.format(str(e))))


class file_download(View):
    def get(self, request):
        try:
            file = request.GET.get('file')
            if not os.path.isfile(file):
                return redirect('apps')
            filename = os.path.basename(file)
            response = FileResponse(open(file, 'rb'), content_type=mimetypes.guess_type(file)[0])
            response['Content-Disposition'] = f'attachment; filename={filename}'
            return response
        except Exception as e:
            messages.error(request, str(e))
            return redirect('apps')


class file_edit(View):
    def get(self, request):
        file = request.GET.get('file')
        if not os.path.isfile(file):
            return redirect('apps')
        filename = os.path.basename(file)
        with open(file, "r") as file:
            text = file.read()

        return render(request, 'file/edit.html', {'text': text, 'filename': filename})

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
            os.system(f'systemctl restart nginx')
            os.system(f'systemctl restart uwsgi')
            messages.success(request, _('uwsgi restarted successfully'))
        except subprocess.CalledProcessError as e:
            messages.error(request, _('uwsgi restart failed'))

        return redirect('apps')


class nginx_restart(View):
    def get(self, request):
        try:
            os.system(f'systemctl restart nginx')
            messages.success(request, _('nginx restarted successfully'))
        except subprocess.CalledProcessError as e:
            messages.error(request, _('nginx restart failed'))

        return redirect('apps')


class mysql_restart(View):
    def get(self, request):
        try:
            os.system(f'systemctl restart mysql')
            messages.success(request, _('mysql restarted successfully'))
        except subprocess.CalledProcessError as e:
            messages.error(request, _('mysql restart failed'))

        return redirect('apps')


class server_restart(View):
    def get(self, request):
        try:
            subprocess.run(['reboot'])
            messages.success(request, _('Server restarted successfully, please wait the server rebooting'))
        except subprocess.CalledProcessError as e:
            messages.error(request, _('Server restart failed'))
        return redirect('apps')
