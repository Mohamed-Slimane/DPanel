import os
import pathlib
import subprocess

from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render
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
            domain = form.save(commit=False)
            if not domain.www_path.startswith('/'):
                domain.www_path = f'/{domain.www_path}'
            domain.save()
            pathlib.Path(domain.full_www_path()).mkdir(parents=True, exist_ok=True)
            create_domain_server_block(domain)
            if request.POST.get('create_index') == 'on':
                create_index_file(domain)
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
            subprocess.call(['unlink', domain.nginx_config.replace('available', 'enabled')])
        except Exception as e: print(e)
        try:
            subprocess.call(['rm', domain.nginx_config])
        except Exception as e: print(e)
        domain.delete()
        subprocess.call(['systemctl', 'reload', 'nginx'])
        messages.success(request, _('Domain deleted successfully'))
        return redirect('domains')


class config(View):
    def post(self, request, serial):
        config_code = request.POST.get('config_code')
        domain = Domain.objects.get(serial=serial)
        try:
            with open(domain.nginx_config, 'w') as f:
                f.write(config_code)
            os.system(f'systemctl reload nginx')
            messages.success(request, _('Domain configuration updated successfully'))
        except Exception as e:
            messages.error(request, _('Error in updating domain configuration') + str(e))
        return self.get(request, serial)

    def get(self, request, serial):
        domain = Domain.objects.get(serial=serial)
        try:
            config_code = pathlib.Path(domain.nginx_config).read_text()
        except Exception as e:
            messages.error(request, _('Error in reading domain configuration') + str(e))
            config_code = ''
        return render(request, 'file/config.html', {'name': domain.name, 'config_code': config_code})


