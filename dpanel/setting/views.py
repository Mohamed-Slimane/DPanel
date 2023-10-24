from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect
from django.views import View

from dpanel.functions import save_option


class settings(View):
    def post(self, request):
        try:
            items = [{'key': key, 'value': request.POST.get(key)} for key in
                     ['company_name', 'company_email', 'paginator',]]
            for item in items:
                save_option(item['key'], item['value'])
            messages.success(request, _('Settings saved'))
            return redirect('settings')
        except:
            messages.error(request, _('An error occurred while saving settings'))
            return self.get(request)

    def get(self, request):
        return render(request, 'settings/settings.html')


class about(View):

    def get(self, request):
        return render(request, 'settings/about.html')
