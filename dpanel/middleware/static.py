import os
from django.http import FileResponse, Http404
from django.utils.deprecation import MiddlewareMixin
from engine import settings

class StaticFilesMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith(settings.STATIC_URL):
            static_file_path = os.path.join(settings.STATIC_ROOT, request.path[len(settings.STATIC_URL):].lstrip('/'))
            if os.path.exists(static_file_path):
                return FileResponse(open(static_file_path, 'rb'))
            raise Http404("Static file not found")
