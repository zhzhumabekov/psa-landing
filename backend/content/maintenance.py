"""Режим обслуживания: сайт отвечает 503 (templates/503.html), админка работает.

Включается в админке — «Настройки» → «Сайт» → «Режим обслуживания» (SiteConfig),
или командой manage.py maintenance on/off. Пока режим включён, вошедшие в админку
сотрудники (is_staff) видят сайт как обычно — можно проверить изменения до того,
как открыть его посетителям.
"""
from django.conf import settings
from django.db import DatabaseError
from django.http import HttpResponse
from django.template.loader import render_to_string

from .models import SiteConfig

# Адреса, которые работают и в режиме обслуживания.
ALLOWED_PREFIXES = ("/admin/", settings.STATIC_URL, settings.MEDIA_URL)
RETRY_AFTER_SECONDS = 3600


def maintenance_enabled(request=None):
    try:
        return SiteConfig.load(request).maintenance_mode
    except DatabaseError:  # база ещё не создана / миграции не применены
        return False


def maintenance_response(request=None):
    response = HttpResponse(render_to_string("503.html", request=request), status=503)
    response["Retry-After"] = str(RETRY_AFTER_SECONDS)
    return response


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            not request.path.startswith(ALLOWED_PREFIXES)
            and not getattr(request.user, "is_staff", False)
            and maintenance_enabled(request)
        ):
            return maintenance_response(request)
        return self.get_response(request)
