from django.http import JsonResponse
from django.shortcuts import render
from django.views import View


class terminal(View):
    def post(self, request):
        return JsonResponse({})

    def get(self, request):
        return render(request, 'terminal/terminal.html')
