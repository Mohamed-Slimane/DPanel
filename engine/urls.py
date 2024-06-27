from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.urls import path, include

from engine import settings

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    path('', include('dpanel.urls'))
)
