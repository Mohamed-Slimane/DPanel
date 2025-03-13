import subprocess

from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View

from dpanel.forms import MysqlUserForm
from dpanel.functions import get_option, paginator
from dpanel.models import MysqlUser

# subprocess.run(['mysql', '-e', f"GRANT ALL PRIVILEGES ON {database.name}.* TO '{database.username}'@'localhost';"])

class users(View):
    def get(self, request):
        users = MysqlUser.objects.all()
        users = paginator(request, users, int(get_option('paginator', '20')))
        return render(request, 'mysql/user/users.html', {'users': users})

class new(View):
    def post(self, request):
        form = MysqlUserForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                subprocess.run(['mysql', '-e', f"CREATE USER '{user.name}'@'localhost' IDENTIFIED BY '{user.password}';"])
                user.save()
                messages.add_message(request, messages.SUCCESS, _('Database successfully created'))
            except Exception as e:
                messages.add_message(request, messages.ERROR, str(e))
                return self.get(request)
            return redirect('mysql_users')
        else:
            messages.add_message(request, messages.ERROR, _('Form validation error'))
            return self.get(request)

    def get(self, request):
        form = MysqlUserForm(request.POST or None)
        return render(request, 'mysql/new.html', {'form': form})

class edit(View):
    def post(self, request, serial):
        user = MysqlUser.objects.get(serial=serial)
        form = MysqlUserForm(request.POST, instance=user)
        form.initial['name'].disabled = True
        if form.is_valid():
            try:
                user = form.save(commit=False)
                mysql_command = f"ALTER USER '{user.name}'@'localhost' IDENTIFIED BY '{user.password}';"
                subprocess.run(['mysql', '-e', mysql_command])
                user.save()
                messages.add_message(request, messages.SUCCESS, _('User successfully updated'))
            except Exception as e:
                messages.add_message(request, messages.ERROR, str(e))
                return self.get(request)
            return redirect('mysql_users')
        else:
            messages.add_message(request, messages.ERROR, _('Form validation error'))
            return self.get(request)

    def get(self, request):
        form = MysqlUserForm(request.POST or None)
        form.initial['name'].disabled = True
        return render(request, 'mysql/new.html', {'form': form})


class delete(View):
    def get(self, request, serial):
        user = MysqlUser.objects.get(serial=serial)
        subprocess.run(['mysql', '-e', f"DROP USER \'{user.name}\'@\'localhost\';"])
        user.delete()
        messages.warning(request, _('Database successfully deleted'))
        return redirect('mysql_users')
