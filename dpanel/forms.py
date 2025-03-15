from dpanel.models import Domain, MysqlDatabase, App, MysqlUser
from django import forms
from django.utils.translation import gettext_lazy as _
class DomainForm(forms.ModelForm):
    class Meta:
        model = Domain
        fields = ['name', 'www_path']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'domain-validator'})

class AppForm(forms.ModelForm):
    class Meta:
        model = App
        fields = ['name', 'www_path', 'domain', 'startup_file', 'entry_point']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'domain-validator'})
        # self.fields['domain'].widget.attrs.update({'required': True})


class AppEditForm(forms.ModelForm):
    class Meta:
        model = App
        fields = ['name', 'www_path', 'startup_file', 'entry_point', 'processes', 'threads', 'max_requests', 'chmod_socket', 'plugin', 'vacuum', 'master']

class MysqlUserForm(forms.ModelForm):
    class Meta:
        model = MysqlUser
        exclude = ['serial']

class MysqlDatabaseForm(forms.ModelForm):
    class Meta:
        model = MysqlDatabase
        exclude = ['serial']
