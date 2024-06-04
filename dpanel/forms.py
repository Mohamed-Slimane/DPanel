from dpanel.models import App, MysqlDatabase
from django import forms


class AppForm(forms.ModelForm):
    class Meta:
        model = App
        fields = ['name', 'domain', 'startup_file', 'entry_point']


class AppEditForm(forms.ModelForm):
    class Meta:
        model = App
        fields = ['name', 'startup_file', 'entry_point']


class MysqlDatabaseForm(forms.ModelForm):
    class Meta:
        model = MysqlDatabase
        exclude = ['serial', 'password']
