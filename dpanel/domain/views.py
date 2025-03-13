import os
import pathlib
import shutil
import subprocess
import uuid

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View

from dpanel.forms import DomainForm
from dpanel.functions import create_domain_server_block, get_option, paginator, create_index_file
from dpanel.models import Domain


class domains(View):
    def get(self, request):
        domains = Domain.objects.all().order_by('-created')
        domains = paginator(request, domains, int(get_option('paginator', '20')))
        return render(request, 'domain/domains.html', {'domains': domains})


class new(View):
    def post(self, request):
        form = DomainForm(request.POST)
        if form.is_valid():
            from engine.settings import WWW_FOLDER
            domain = form.save(commit=False)
            domain.www_path = f'{WWW_FOLDER}{domain.name}'
            domain.save()
            pathlib.Path(domain.www_path).mkdir(parents=True, exist_ok=True)
            the_block = create_domain_server_block(domain)
            if not the_block:
                messages.add_message(request, messages.ERROR, _('Failed to create domain server block'))
                return self.get(request)
            create_index_file(domain)
            domain.save()
            os.system(f'systemctl reload nginx')
            messages.add_message(request, messages.SUCCESS, _('Domain successfully created'))
            return redirect('domains')
        else:
            messages.add_message(request, messages.ERROR, _('Form validation error'))
            return render(request, 'domain/new.html', {'form': form})

    def get(self, request):
        form = DomainForm(request.POST or None)
        return render(request, 'domain/new.html', {'form': form})



class delete(View):
    def get(self, request, serial):
        domain = Domain.objects.get(serial=serial)
        try:
            os.system(f"unlink {domain.nginx_config}")
        except Exception as e:
            print(e)
        try:
            pathlib.Path('/var/www-deleted').mkdir(parents=True, exist_ok=True)
            shutil.move(domain.www_path, str(domain.www_path).replace('/www/', '/www-deleted/') + str(
                timezone.now().strftime("_%Y-%m-%d_time_%H.%M.%S")))
        except Exception as e:
            print(e)
        try:
            subprocess.call(['rm', f'/etc/nginx/sites-available/{domain.serial}.conf'])
        except Exception as e:
            print(e)
        try:
            subprocess.call(['rm', f'/etc/nginx/sites-enabled/{domain.serial}.conf'])
        except Exception as e:
            print(e)
        domain.delete()
        os.system(f'systemctl reload nginx')
        messages.success(request, _('Domain deleted successfully'))
        return redirect('domains')


class config(View):
    def post(self, request, serial):
        config_code = request.POST.get('config_code')
        domain = Domain.objects.get(serial=serial)
        try:
            with open(domain.nginx_config, 'w') as f:
                f.write(config_code)
            with open(str(domain.nginx_config).replace('sites-enabled/', 'sites-available/'), 'w') as f:
                f.write(config_code)
            os.system(f'systemctl reload nginx')
            messages.success(request, _('Domain configuration updated successfully'))
        except Exception as e:
            messages.error(request, _('Error in updating app configuration') + str(e))
        return self.get(request, serial)

    def get(self, request, serial):
        domain = Domain.objects.get(serial=serial)
        print(domain.nginx_config)
        try:
            config_code = pathlib.Path(domain.nginx_config).read_text()
        except Exception as e:
            config_code = ''
        return render(request, 'file/config.html', {'name': domain.name, 'config_code': config_code})


