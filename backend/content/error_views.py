"""Просмотр страниц ошибок при DEBUG = True (тогда Django вместо них показывает
отладочные страницы): /_errors/400/, /_errors/403/, /_errors/404/, /_errors/500/, /_errors/503/.
Подключаются в psa_backend/urls.py только в режиме разработки.
"""
from django.http import Http404
from django.shortcuts import render

from .maintenance import maintenance_response

# 400 и 500 Django рендерит без request (контекста шаблона нет) — так и показываем.
WITHOUT_REQUEST = {400, 500}


def error_preview(request, code):
    if code == 503:
        return maintenance_response(request)
    if code not in (400, 403, 404, 500):
        raise Http404
    return render(None if code in WITHOUT_REQUEST else request, f"{code}.html", status=code)
