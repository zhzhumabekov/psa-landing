"""Разовый скрипт: по одной примерной записи в каждую модель.
Запуск: venv/Scripts/python.exe seed.py
Безопасно перезапускать — использует get_or_create по заголовку.
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "psa_backend.settings")
django.setup()

from content.models import DocumentEntry, LocalContentEntry, NewsEntry, ProcurementEntry  # noqa: E402

LocalContentEntry.objects.get_or_create(
    title="Пример записи — отредактируйте в /admin/",
    defaults=dict(date="2026-01-01", body="Тестовая запись раздела «Местное содержание»."),
)

ProcurementEntry.objects.get_or_create(
    title="Пример закупки — отредактируйте в /admin/",
    defaults=dict(status=ProcurementEntry.STATUS_OPEN, deadline="2026-02-01", description="Тестовая запись.", url="https://example.com/tender"),
)

DocumentEntry.objects.get_or_create(
    title="Пример документа — отредактируйте в /admin/",
    defaults=dict(category="Пример категории", date="2026-01-01", url="https://example.com/document.pdf"),
)

NewsEntry.objects.get_or_create(
    title="Пример новости — отредактируйте в /admin/",
    defaults=dict(date="2026-01-01", excerpt="Тестовая запись.", body="Полный текст тестовой новости."),
)

print(
    "seeded:",
    LocalContentEntry.objects.count(),
    ProcurementEntry.objects.count(),
    DocumentEntry.objects.count(),
    NewsEntry.objects.count(),
)
