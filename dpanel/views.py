import os
import subprocess
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views import View

from dpanel.functions import get_memory_usage, get_cpu_usage, get_dir_usage
from dpanel.models import Domain, MysqlDatabase


class dashboard(View):
    def post(self, request):
        cpu_percent = get_cpu_usage()
        cpu_percent = int(cpu_percent)
        ram_percent = get_memory_usage()
        ram_percent = int(ram_percent)

        data = {'cpu_percent': cpu_percent, 'ram_percent': ram_percent}
        return JsonResponse(data)

    def get(self, request):
        cpu_percent = get_cpu_usage()
        cpu_percent = int(cpu_percent)
        ram_percent = get_memory_usage()
        ram_percent = int(ram_percent)
        apps = Domain.objects.all()
        databases = MysqlDatabase.objects.all()
        www_status = get_dir_usage()
        data = {'cpu_percent': cpu_percent, 'ram_percent': ram_percent, 'apps': apps, 'databases': databases, 'www_status': www_status}

        return render(request, 'dashboard.html', data)


class uwsgi_restart(View):
    def get(self, request):
        try:
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
        return redirect(request.META['HTTP_REFERER'])


class mysql_restart(View):
    def get(self, request):
        try:
            os.system(f'systemctl restart mysql')
            messages.success(request, _('mysql restarted successfully'))
        except subprocess.CalledProcessError as e:
            messages.error(request, _('mysql restart failed'))

        return redirect(request.META['HTTP_REFERER'])


class server_restart(View):
    def get(self, request):
        try:
            subprocess.run(['reboot'])
            messages.success(request, _('Server restarted successfully, please wait the server rebooting'))
        except subprocess.CalledProcessError as e:
            messages.error(request, _('Server restart failed'))
        return redirect(request.META['HTTP_REFERER'])
