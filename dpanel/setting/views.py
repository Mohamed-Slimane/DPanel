import subprocess

from django.contrib import messages
from django.http import JsonResponse
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


class dpanel_update(View):

    def post(self, request):
        command = "wget -O - https://dpanel.de-ver.com/api/update/update.sh | bash"
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            return JsonResponse({
                'success': False,
                'message': _("Command failed with return code {e.returncode}: {e.stderr}").format(e=e)
            })
        except FileNotFoundError:
            return JsonResponse({
                'success': False,
                'message': _("Command not found. Please make sure 'wget' and 'bash' are installed on your system")
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': _("An error occurred: {e}").format(e=e)
            })

        try:
            subprocess.run(['systemctl', 'restart', 'dpanel'])
            return JsonResponse({
                'success': True,
                'message': _("Updated successfully")
            })
        except:
            pass
        return JsonResponse({
            'success': True,
            'message': _("Updated completed successfully")
        })
