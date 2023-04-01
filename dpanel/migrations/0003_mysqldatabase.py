# Generated by Django 4.1.7 on 2023-03-31 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dpanel', '0002_postgresdatabase_alter_app_uwsgi_path'),
    ]

    operations = [
        migrations.CreateModel(
            name='MysqlDatabase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serial', models.CharField(editable=False, max_length=500, unique=True, verbose_name='Serial')),
                ('name', models.CharField(max_length=500, unique=True, verbose_name='Name')),
                ('username', models.CharField(max_length=500, unique=True, verbose_name='Username')),
                ('password', models.CharField(max_length=500, verbose_name='Password')),
            ],
        ),
    ]