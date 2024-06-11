from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from dpanel.functions import get_memory_usage, get_cpu_usage, get_dir_usage
from dpanel.models import App, MysqlDatabase


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
        apps = App.objects.all()
        databases = MysqlDatabase.objects.all()
        www_status = get_dir_usage()
        data = {'cpu_percent': cpu_percent, 'ram_percent': ram_percent, 'apps': apps, 'databases': databases, 'www_status': www_status}

        return render(request, 'dashboard.html', data)
