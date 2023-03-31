from dpanel.models import App, PostgresDatabase, MysqlDatabase
from django import forms


class AppForm(forms.ModelForm):
    class Meta:
        model = App
        fields = ['name', 'domain', 'uwsgi_path']


class PostgresDatabaseForm(forms.ModelForm):
    class Meta:
        model = PostgresDatabase
        exclude = ['serial', 'password']


class MysqlDatabaseForm(forms.ModelForm):
    class Meta:
        model = MysqlDatabase
        exclude = ['serial', 'password']
