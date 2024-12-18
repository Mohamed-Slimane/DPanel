import os
from django.db import models
from django.utils.translation import gettext_lazy as _


class Domain(models.Model):
    serial = models.CharField(_('Serial'), max_length=500, unique=True, editable=False)
    name = models.CharField(max_length=50, verbose_name=_('Name'), unique=True, help_text=_('For example: mayproject.com, dpanel.top'))
    www_path = models.CharField(max_length=5000, verbose_name=_('Path'))
    nginx_config = models.CharField(max_length=5000, verbose_name=_('Nginx config'))
    force_https = models.BooleanField(verbose_name=_('Force HTTPS'), default=False)
    is_active = models.BooleanField(_('Active'), default=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Domain')
        verbose_name_plural = _('Domains')

    def certificates(self):
        return self.ssl_certificates.order_by('-created')

    def active_certificate(self):
        return self.ssl_certificates.filter(is_active=True).first()

    def save(self, *args, **kwargs):
        if not self.serial:
            import uuid
            self.serial = uuid.uuid4()
        if 'http' in self.name or 'https' in self.name:
            self.name = str(self.name).split('//')[1]
        super().save(*args, **kwargs)

class App(models.Model):
    serial = models.CharField(_('Serial'), max_length=500, unique=True, editable=False)
    name = models.CharField(_('Name'), max_length=500)
    domain = models.OneToOneField(Domain, verbose_name=_('Domain'), related_name='domain_app', on_delete=models.SET_NULL, null=True, blank=True, unique=True)
    port = models.IntegerField(_('Port'), unique=True)
    www_path = models.CharField(max_length=5000, verbose_name=_('Path'))
    startup_file = models.CharField(_('Startup file'), default='startup.py', max_length=500, help_text=_(
        'The folder that contains the startup file, for example: mayproject/wsgi.py'))
    entry_point = models.CharField(_('entry point'), default='application', max_length=500,
                                   help_text=_('Entry point in startup file for example: application'))
    venv_path = models.CharField(max_length=5000, verbose_name=_('Environment Path'))
    uwsgi_config = models.CharField(max_length=5000, verbose_name=_('Uwsgi config'))
    processes = models.IntegerField(_('Processes'), default=1)
    threads = models.IntegerField(_('Threads'), default=1)
    max_requests = models.IntegerField(_('Max requests'), default=1000)
    chmod_socket = models.IntegerField(_('Chmod socket'), default=666)
    plugin = models.CharField(_('Plugin'), default='python3', max_length=500, null=True, blank=True, choices=[('', 'None'), ('python3', 'python3')])
    vacuum = models.BooleanField(_('Vacuum'), default=True)
    master = models.BooleanField(_('Master'), default=True)
    is_active = models.BooleanField(verbose_name=_('Is active'), default=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.serial:
            import uuid
            self.serial = uuid.uuid4()
        super().save(*args, **kwargs)


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
        super().save(*args, **kwargs)


class MysqlDatabaseBackup(models.Model):
    serial = models.CharField(_('Serial'), max_length=500, unique=True, editable=False)
    database = models.ForeignKey(MysqlDatabase, verbose_name=_('Database'), related_name='backup_database',
                                 on_delete=models.SET_NULL, null=True, blank=True)
    path = models.CharField(_('Path'), max_length=5000)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.database

    def filename(self):
        try:
            return os.path.basename(str(self.path).split('?')[0])
        except Exception as e:
            return self.serial

    def save(self, *args, **kwargs):
        if not self.pk:
            import uuid
            self.serial = uuid.uuid4()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        try:
            import os
            os.remove(str(self.path))
        except Exception as e:
            print(e)
        super().delete(*args, **kwargs)


class SSLCertificate(models.Model):
    serial = models.CharField(_('Serial'), max_length=500, unique=True, editable=False)
    domain = models.ForeignKey(Domain, verbose_name=_('Domain'), related_name='ssl_certificates', on_delete=models.CASCADE)
    certificate_path  = models.CharField(_('Certificate (CRT)'), max_length=500)
    private_key_path = models.CharField(_('Private key (KEY)'), max_length=500)
    is_wildcard = models.BooleanField(_('Wildcard'), default=False)
    start_date = models.DateTimeField(null=True, blank=True)
    expire_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.domain.name

    def save(self, *args, **kwargs):
        if not self.pk:
            import uuid
            self.serial = uuid.uuid4()
        super().save(*args, **kwargs)


class Option(models.Model):
    key = models.CharField(max_length=50, verbose_name=_('Key'), null=True, blank=True, unique=True)
    value = models.CharField(max_length=5000, verbose_name=_('Value'), null=True, blank=True)

    def __str__(self):
        return self.key
