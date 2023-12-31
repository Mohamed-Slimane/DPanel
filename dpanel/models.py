from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class App(models.Model):
    serial = models.CharField(_('Serial'), max_length=500, unique=True, editable=False)
    framework = models.CharField(_('Framework'), max_length=500, choices=[('django', 'Django'), ('flask', 'Flask'), ('bottle', 'Bottle'),], default='django')
    name = models.CharField(_('Name'), max_length=500)
    domain = models.CharField(max_length=50, verbose_name=_('Domain'), unique=True)
    port = models.IntegerField(_('Port'), unique=True)
    www_path = models.CharField(max_length=5000, verbose_name=_('Path'))
    uwsgi_path = models.CharField(max_length=5000, verbose_name=_('Uwsgi path'),
                                  help_text=_('The folder that contains the wsgi.py file, for example: (mayproject)'))
    venv_path = models.CharField(max_length=5000, verbose_name=_('Environment Path'))
    nginx_config = models.CharField(max_length=5000, verbose_name=_('Nginx config'))
    uwsgi_config = models.CharField(max_length=5000, verbose_name=_('Uwsgi config'))
    force_https = models.BooleanField(verbose_name=_('Force HTTPS'), default=False)
    activated = models.BooleanField(verbose_name=_('Activated'), default=True)

    def __str__(self):
        return self.name

    def certificates(self):
        return self.certificate_app.order_by('-created_date')

    def save(self, *args, **kwargs):
        if not self.pk:
            import uuid
            self.serial = uuid.uuid4()
        if not self.name:
            if 'http' in self.domain or 'https' in self.domain:
                self.domain = self.domain.split('//')[1]
            self.name = self.domain
        super(App, self).save(*args, **kwargs)


class PostgresDatabase(models.Model):
    serial = models.CharField(_('Serial'), max_length=500, unique=True, editable=False)
    name = models.CharField(_('Name'), unique=True, max_length=500)
    username = models.CharField(_('Username'), unique=True, max_length=500)
    password = models.CharField(_('Password'), max_length=500)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk:
            import uuid
            self.serial = uuid.uuid4()
        super(PostgresDatabase, self).save(*args, **kwargs)


class MysqlDatabase(models.Model):
    serial = models.CharField(_('Serial'), max_length=500, unique=True, editable=False)
    name = models.CharField(_('Name'), unique=True, max_length=500)
    username = models.CharField(_('Username'), unique=True, max_length=500)
    password = models.CharField(_('Password'), max_length=500)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk:
            import uuid
            self.serial = uuid.uuid4()
        super(MysqlDatabase, self).save(*args, **kwargs)


class AppCertificate(models.Model):
    serial = models.CharField(_('Serial'), max_length=500, unique=True, editable=False)
    app = models.ForeignKey(App, verbose_name=_('App'), related_name='certificate_app', on_delete=models.CASCADE)
    domain = models.CharField(max_length=50, verbose_name=_('Domain'))
    created_date = models.DateTimeField(auto_now=True)
    expire_date = models.DateTimeField()

    def __str__(self):
        return self.app


    def save(self, *args, **kwargs):
        if not self.pk:
            import uuid
            self.serial = uuid.uuid4()
        else:
            self.domain = self.app.domain
        super(AppCertificate, self).save(*args, **kwargs)


class Option(models.Model):
    key = models.CharField(max_length=50, verbose_name=_('Key'), null=True, blank=True, unique=True)
    value = models.CharField(max_length=5000, verbose_name=_('Value'), null=True, blank=True)

    def __str__(self):
        return self.key