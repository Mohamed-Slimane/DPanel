import subprocess

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views import View

from dpanel.functions import get_option
from dpanel.models import Domain, SSLCertificate
from dpanel.ssl import create_ssl, install_certbot


class certificates(View):
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
        app = Domain.objects.get(serial=serial)
        return render(request, 'app/certificate.html', {'app': app})


class certificate_new(View):
    def get(self, request, serial):
        app = Domain.objects.get(serial=serial)
        try:
            expiration_date = create_ssl(app)
            if expiration_date:
                SSLCertificate.objects.create(app=app, expire_date=expiration_date)
            messages.success(request, _('Certificate created successfully'))
            subprocess.run("systemctl reload nginx", shell=True, check=True)
        except subprocess.CalledProcessError as e:
            messages.error(request, _('Certificate created failed'))
            messages.warning(request, str(e))

        return redirect('certificates', app.serial)