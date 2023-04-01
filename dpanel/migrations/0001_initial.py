# Generated by Django 4.1.7 on 2023-03-28 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='App',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serial', models.CharField(editable=False, max_length=500, unique=True, verbose_name='Serial')),
                ('name', models.CharField(max_length=500, verbose_name='Name')),
                ('domain', models.CharField(max_length=50, unique=True, verbose_name='Domain')),
                ('port', models.IntegerField(unique=True, verbose_name='Port')),
                ('www_path', models.CharField(max_length=5000, verbose_name='Path')),
                ('uwsgi_path', models.CharField(max_length=5000, verbose_name='Startup path')),
                ('venv_path', models.CharField(max_length=5000, verbose_name='Environment Path')),
                ('nginx_config', models.CharField(max_length=5000, verbose_name='Nginx config')),
                ('uwsgi_config', models.CharField(max_length=5000, verbose_name='Uwsgi config')),
                ('force_https', models.BooleanField(default=False, verbose_name='Force HTTPS')),
                ('activated', models.BooleanField(default=True, verbose_name='Activated')),
            ],
        ),
    ]