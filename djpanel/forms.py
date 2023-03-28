from djpanel.models import App
from django import forms


class AppForm(forms.ModelForm):
    class Meta:
        model = App
        fields = ['name', 'domain', 'uwsgi_path']
