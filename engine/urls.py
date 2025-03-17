from django.conf.urls.static import static
from django.shortcuts import render
from django.urls import path, include
from engine import settings
from engine.settings import DEBUG
from django.utils.translation import gettext_lazy as _

handler404 = lambda request, exception: render(request, "error.html", {"error": {"code": 404, "message": _("Page Not Found")}}, status=404)
handler500 = lambda request: render(request, "error.html", {"error": {"code": 500, "message": _("Internal Server Error")}}, status=500)
handler403 = lambda request, exception: render(request, "error.html", {"error": {"code": 403, "message": _("Forbidden")}}, status=403)
handler400 = lambda request, exception: render(request, "error.html", {"error": {"code": 400, "message": _("Bad Request")}}, status=400)


urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include('dpanel.urls'))
]
if DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

