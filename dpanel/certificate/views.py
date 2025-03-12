import subprocess
import uuid
from datetime import timedelta
from pathlib import Path

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View

from dpanel.functions import get_option, create_domain_server_block
from dpanel.models import Domain, SSLCertificate
from engine.settings import SSL_FOLDER


class certificates(View):
    def get(self, request, serial):
        domain = Domain.objects.get(serial=serial)
        return render(request, 'certificate/certificates.html', {'domain': domain})


class certificate_new(View):
    def get(self, request, serial):
        cr_type = request.GET.get('cr_type')
        domain = Domain.objects.get(serial=serial)
        random_serial = str(uuid.uuid4()).replace('-', '')
        path = f'{SSL_FOLDER}/{random_serial}'
        Path(path).mkdir(parents=True, exist_ok=True)
        try:
            if cr_type == 'self_signed':
                commend = f'openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout {path}/private.key -out {path}/certificate.crt -subj "/C=US/ST=California/L=San Francisco/O=MyOrg/OU=Dev/CN=localhost"'
            else:
                commend = [
                    'certbot', 'certonly',
                    '--webroot', '-w', path,
                    '-d', domain.name,
                    '--agree-tos',
                    '--email', f'admin@{domain.name}',
                    '--non-interactive'
                ]
            result = subprocess.run(commend, shell=True, check=True)
            if result.returncode != 0:
                messages.error(request, _('Certificate created failed'))
                messages.warning(request, result.stderr)
                return redirect('certificates', domain.serial)

            start_date = timezone.now()
            expiration_date = timezone.now() + timedelta(days=90)

            ssl = domain.ssl_certificates.create(
                start_date=start_date,
                expire_date=expiration_date,
                certificate_path=f'{path}/certificate.crt',
                private_key_path=f'{path}/private.key'
            )
            domain.ssl_certificates.update(is_active=False)
            ssl.is_active = True
            ssl.save()
            create_domain_server_block(domain)
            messages.success(request, _('Certificate created successfully'))
            subprocess.run("systemctl reload nginx", shell=True, check=True)
        except subprocess.CalledProcessError as e:
            messages.error(request, _('Certificate created failed'))
            messages.warning(request, str(e))

        return redirect('certificates', domain.serial)