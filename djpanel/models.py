from django.db import models
from django.utils.translation import gettext_lazy as _


class App(models.Model):
    serial = models.CharField(_('Serial'), max_length=500, unique=True, editable=False)
    name = models.CharField(_('Name'), max_length=500)
    domain = models.CharField(max_length=50, verbose_name=_('Domain'), unique=True)
    port = models.IntegerField(_('Port'), unique=True)
    www_path = models.CharField(max_length=5000, verbose_name=_('Path'))
    uwsgi_path = models.CharField(max_length=5000, verbose_name=_('Startup path'))
    venv_path = models.CharField(max_length=5000, verbose_name=_('Environment Path'))
    nginx_config = models.CharField(max_length=5000, verbose_name=_('Nginx config'))
    uwsgi_config = models.CharField(max_length=5000, verbose_name=_('Uwsgi config'))
    force_https = models.BooleanField(verbose_name=_('Force HTTPS'), default=False)
    activated = models.BooleanField(verbose_name=_('Activated'), default=True)

    def __str__(self):
        return self.domain

    def save(self, *args, **kwargs):
        if not self.pk:
            import uuid
            self.serial = uuid.uuid4()
        if not self.name:
            self.name = self.domain
        super(DjangoApp, self).save(*args, **kwargs)
