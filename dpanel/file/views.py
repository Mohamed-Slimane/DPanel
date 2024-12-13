import mimetypes
import os
import pathlib
import shutil

from django.contrib import messages
from django.http import FileResponse
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views import View

from engine.settings import WWW_FOLDER


class files(View):
    def get(self, request):
        path = request.GET.get('path') or WWW_FOLDER
        if not path.startswith(WWW_FOLDER):
            path = WWW_FOLDER
        files = []
        dirs = []
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                files.append(f)
            else:
                dirs.append(f)
        context = {
            'files': files,
            'dirs': dirs,
            'path': path,
            'parent': pathlib.Path(path).parent.absolute(),
        }
        return render(request, 'file/files.html', context)


class files_ajax(View):
    def get(self, request):
        path = request.GET.get('path') or WWW_FOLDER
        if not path.startswith(WWW_FOLDER):
            path = WWW_FOLDER
        files = []
        dirs = []
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                files.append(f)
            else:
                dirs.append(f)
        files.sort()
        dirs.sort()
        context = {
            'files': files,
            'dirs': dirs,
            'path': path,
            'parent': pathlib.Path(path).parent.absolute(),
        }
        return render(request, 'file/list.html', context)


class files_ajax_upload(View):
    def post(self, request):
        path = request.POST.get('path')
        if not path:
            return JsonResponse({"error": 1, "success": False, "message": _("Invalid path")})
        try:
            if 'remote_file' in request.POST:
                url = request.POST.get('remote_file')
                import urllib.request
                try:
                    response = urllib.request.urlopen(url)
                    file_content = response.read()
                    filename = os.path.basename(url)
                    filename = filename.split('?')[0]
                    file_path = os.path.join(path, filename)
                    with open(file_path, 'wb') as f:
                        f.write(file_content)
                    return JsonResponse({'error': 0, 'success': True, 'message': 'File uploaded successfully.'})
                except urllib.error.URLError as e:
                    return JsonResponse(
                        {'error': 1, 'success': False, 'message': 'Failed to download the file: ' + str(e)})

            file = request.FILES['file']
            if file.name:
                fn = os.path.basename(file.name)
                open(f'{path}/{fn}', 'wb').write(file.read())
            req = {"error": 0, "success": True}
        except Exception as e:
            req = {"error": 1, "error_message": str(e), "success": False}

        return JsonResponse(req)


class extract_zip(View):
    def get(self, request):
        path = request.GET.get('path') or WWW_FOLDER
        if not path.startswith(WWW_FOLDER):
            path = WWW_FOLDER
        file = request.GET.get('file')
        folder = request.GET.get('folder')
        try:
            if folder == 'true':
                print(file.rsplit('.', 1)[0])
                shutil.unpack_archive(file, file.rsplit('.', 1)[0])
            else:
                shutil.unpack_archive(file, path)
            req = {"error": 0, "success": True}
        except Exception as e:
            req = {"error": 1, "error_message": str(e), "success": False}

        return JsonResponse(req)


class file_remove(View):
    def get(self, request):
        file = request.GET.get('file')
        try:
            if os.path.isfile(file):
                os.remove(file)
            elif os.path.isdir(file):
                shutil.rmtree(file)
            req = {"error": 0, "success": True}
        except Exception as e:
            messages.error(request, str(e))
            req = {"error": 1, "error_message": str(e), "success": False}

        return JsonResponse(req)


class file_preview(View):
    image_extensions = ['.jpg', '.png', '.jpeg', '.svg', '.gif', '.webp', '.ico', '.bmp', '.tiff']
    pdf_extensions = ['.pdf']
    video_audio_extensions = ['.mp4', '.mkv', '.webm', '.mp3', '.m4a', '.ogg', '.avi', '.wmv', '.mov', '.flv', '.3gp']

    def get(self, request):
        file = request.GET.get('file')
        if not os.path.isfile(file):
            return redirect('dashboard')
        filename = os.path.basename(file)
        try:
            file_extension = file.lower()

            if any(file_extension.endswith(ext) for ext in self.image_extensions):
                return HttpResponse(open(file, 'rb'), content_type=mimetypes.guess_type(file)[0])

            if any(file_extension.endswith(ext) for ext in self.pdf_extensions):
                return FileResponse(open(file, 'rb'), content_type=mimetypes.guess_type(file)[0])

            if any(file_extension.endswith(ext) for ext in self.video_audio_extensions):
                return FileResponse(open(file, 'rb'), content_type=mimetypes.guess_type(file)[0])

            with open(file, "r") as f:
                text = f.read()
            return render(request, 'file/preview.html', {'text': text, 'filename': filename})

        except Exception as e:
            return HttpResponse(_('Cannot preview this file: {}'.format(str(e))))


class file_download(View):
    def get(self, request):
        try:
            file = request.GET.get('file')
            if not os.path.isfile(file):
                return redirect('dashboard')
            filename = os.path.basename(file)
            response = FileResponse(open(file, 'rb'), content_type=mimetypes.guess_type(file)[0])
            response['Content-Disposition'] = f'attachment; filename={filename}'
            return response
        except Exception as e:
            messages.error(request, str(e))
            return redirect('dashboard')


class file_edit(View):
    def get(self, request):
        file = request.GET.get('file')
        if not os.path.isfile(file):
            return redirect('dashboard')
        filename = os.path.basename(file)
        with open(file, "r") as file:
            text = file.read()

        return render(request, 'file/edit.html', {'text': text, 'filename': filename})

    def post(self, request):
        file = request.GET.get('file')
        text = request.POST.get('text')
        with open(file, "w") as file:
            file.write(text)
        messages.success(request, _('File was successfully updated'))
        return self.get(request)


