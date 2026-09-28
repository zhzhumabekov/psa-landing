"""Обязательная структура сайта: разделы под «Главной» и подразделы с
фиксированными адресами (slug). На адреса завязаны меню в templates/base.html
({% slugurl %}) и кнопки «Перенести в архив» (content/archive_transfer.py).

Создаёт/чинит структуру команда manage.py setup_site; подразделы «Закупок»
по этому же списку заполняет manage.py import_psa_procurement.
"""
from .models import (
    DocumentsIndexPage,
    LocalContentIndexPage,
    MarketingIndexPage,
    MarketingSectionPage,
    NewsIndexPage,
    ProcurementIndexPage,
    ProcurementSectionPage,
    ProjectsIndexPage,
)

# (slug, заголовок, заголовок қазақша, заголовок English) — порядок как на psa.kz.
PROCUREMENT_SECTIONS = [
    ("contacts", "Контактные лица", "Байланыс тұлғалары", "Contact persons"),
    ("archive", "Архив", "Архив", "Archive"),
    ("announcements", "Объявления", "Хабарландырулар", "Announcements"),
    ("special-procedure", "Особый порядок осуществления закупок", "Сатып алуды жүзеге асырудың ерекше тәртібі", "Special procurement procedure"),
]

MARKETING_SECTIONS = [
    ("future", "Предстоящие", "Алдағы", "Upcoming"),
    ("archive", "Архив", "Архив", "Archive"),
]

# (модель раздела, slug, заголовок, модель подраздела, подразделы) — порядок как в меню.
SITE_TREE = [
    (ProjectsIndexPage, "projects", "Проекты", None, []),
    (LocalContentIndexPage, "local-content", "Местное содержание", None, []),
    (ProcurementIndexPage, "procurement", "Закупки", ProcurementSectionPage, PROCUREMENT_SECTIONS),
    (MarketingIndexPage, "marketing", "Маркетинг", MarketingSectionPage, MARKETING_SECTIONS),
    (DocumentsIndexPage, "documents", "Документы", None, []),
    (NewsIndexPage, "news", "Новости", None, []),
]
