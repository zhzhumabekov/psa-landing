"""Разовый скрипт: по одной примерной опубликованной странице в каждый раздел.
Запуск: venv/Scripts/python.exe seed.py
Безопасно перезапускать — страница с таким slug в разделе не создаётся повторно.
«Закупки» не заполняет — их контент переносится с psa.kz: manage.py import_psa_procurement.
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "psa_backend.settings")
django.setup()

from content.models import (  # noqa: E402
    DocumentPage,
    DocumentsIndexPage,
    LocalContentIndexPage,
    LocalContentPage,
    NewsIndexPage,
    NewsPage,
)


def seed(index_model, page):
    index = index_model.objects.get()
    if not index.get_children().filter(slug=page.slug).exists():
        index.add_child(instance=page)
        page.save_revision().publish()
    return index.get_children().count()


print(
    "seeded:",
    seed(LocalContentIndexPage, LocalContentPage(
        title="Пример записи — отредактируйте в /admin/",
        slug="primer",
        date="2026-01-01",
        body="<p>Тестовая запись раздела «Местное содержание».</p>",
    )),
    seed(DocumentsIndexPage, DocumentPage(
        title="Пример документа — отредактируйте в /admin/",
        slug="primer",
        category="Пример категории",
        date="2026-01-01",
        external_url="https://example.com/document.pdf",
    )),
    seed(NewsIndexPage, NewsPage(
        title="Пример новости — отредактируйте в /admin/",
        slug="primer",
        date="2026-01-01",
        excerpt="Тестовая запись.",
        body="<p>Полный текст тестовой новости.</p>",
    )),
)
