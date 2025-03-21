from django.db.models import Q

from dpanel.models import Domain, MysqlDatabase, PythonApp, MysqlUser
from django import forms
from django.utils.translation import gettext_lazy as _
class DomainForm(forms.ModelForm):
    class Meta:
        model = Domain
        fields = ['name', 'www_path']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'domain-validator'})

class PythonAppForm(forms.ModelForm):
    class Meta:
        model = PythonApp
        fields = ['name', 'www_path', 'domain', 'startup_file', 'entry_point']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'domain-validator'})
        # self.fields['domain'].widget.attrs.update({'required': True})


class PythonAppEditForm(forms.ModelForm):
    class Meta:
        model = PythonApp
        fields = ['name', 'www_path', 'domain', 'startup_file', 'entry_point', 'processes', 'threads', 'max_requests', 'chmod_socket', 'plugin', 'vacuum', 'master']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["domain"].queryset = Domain.objects.filter(Q(domain_app__isnull=True) | Q(domain_app=self.instance))

class MysqlUserForm(forms.ModelForm):
    class Meta:
        model = MysqlUser
        exclude = ['serial']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'domain-validator'})

class MysqlDatabaseForm(forms.ModelForm):
    class Meta:
        model = MysqlDatabase
        exclude = ['serial']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'domain-validator'})
        self.fields['users'].widget.attrs.update({'class': 'select2_field'})

