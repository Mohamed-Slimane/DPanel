import os

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class App(models.Model):
    serial = models.CharField(_('Serial'), max_length=500, unique=True, editable=False)
    name = models.CharField(_('Name'), max_length=500)
    domain = models.CharField(max_length=50, verbose_name=_('Domain'), unique=True,
                              help_text=_('For example: mayproject.com, app.mayproject.com'))
    port = models.IntegerField(_('Port'), unique=True)
    www_path = models.CharField(max_length=5000, verbose_name=_('Path'))
    startup_file = models.CharField(_('Startup file'), default='startup.py', max_length=5000, help_text=_(
        'The folder that contains the startup file, for example: mayproject/wsgi.py'))
    entry_point = models.CharField(_('entry point'), default='application', max_length=5000, null=True, blank=True,
                                   help_text=_('Entry point in startup file for example: application'))
    venv_path = models.CharField(max_length=5000, verbose_name=_('Environment Path'))
    nginx_config = models.CharField(max_length=5000, verbose_name=_('Nginx config'))
    uwsgi_config = models.CharField(max_length=5000, verbose_name=_('Uwsgi config'))
    force_https = models.BooleanField(verbose_name=_('Force HTTPS'), default=False)
    is_active = models.BooleanField(verbose_name=_('Is active'), default=True)

    def __str__(self):
        return self.name

    def certificates(self):
        return self.certificate_app.order_by('-created_date')

    def save(self, *args, **kwargs):
        # if not self.pk:
        #     import uuid
        #     self.serial = uuid.uuid4()
        if not self.name:
            if 'http' in self.domain or 'https' in self.domain:
                self.domain = self.domain.split('//')[1]
            self.name = self.domain
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
    created_date = models.DateTimeField(auto_now=True)

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


class AppCertificate(models.Model):
    serial = models.CharField(_('Serial'), max_length=500, unique=True, editable=False)
    app = models.ForeignKey(App, verbose_name=_('App'), related_name='certificate_app', on_delete=models.CASCADE)
    domain = models.CharField(max_length=50, verbose_name=_('Domain'))
    created_date = models.DateTimeField(auto_now=True)
    expire_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.app

    def save(self, *args, **kwargs):
        if not self.pk:
            import uuid
            self.serial = uuid.uuid4()
        else:
            self.domain = self.app.domain
        super().save(*args, **kwargs)


class Option(models.Model):
    key = models.CharField(max_length=50, verbose_name=_('Key'), null=True, blank=True, unique=True)
    value = models.CharField(max_length=5000, verbose_name=_('Value'), null=True, blank=True)

    def __str__(self):
        return self.key
