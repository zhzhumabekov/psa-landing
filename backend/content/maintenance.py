"""Режим обслуживания: сайт отвечает 503 (templates/503.html), админка работает.

Включается файлом-флагом settings.MAINTENANCE_FLAG — manage.py maintenance on/off.
Файл, а не настройка: переключается без перезапуска сервера. Пока режим
включён, вошедшие в админку сотрудники (is_staff) видят сайт как обычно —
можно проверить изменения до того, как открыть его посетителям.
"""
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse

# Адреса, которые работают и в режиме обслуживания.
ALLOWED_PREFIXES = ("/admin/", settings.STATIC_URL, settings.MEDIA_URL)
RETRY_AFTER_SECONDS = 3600


def maintenance_enabled():
    return settings.MAINTENANCE_FLAG.exists()


def maintenance_response(request=None):
    response = HttpResponse(render_to_string("503.html", request=request), status=503)
    response["Retry-After"] = str(RETRY_AFTER_SECONDS)
    return response


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            maintenance_enabled()
            and not request.path.startswith(ALLOWED_PREFIXES)
            and not getattr(request.user, "is_staff", False)
        ):
            return maintenance_response(request)
        return self.get_response(request)
