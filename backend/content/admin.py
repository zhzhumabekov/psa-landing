from django.contrib import admin
from django.db import models

from .models import DocumentEntry, LocalContentEntry, NewsEntry, ProcurementEntry
from .widgets import QuillWidget

# Поля с форматированным текстом (жирный/ссылки/списки — через Quill,
# см. widgets.py). Рендерятся на сайте через `|safe` (см. templates/) —
# источник доверенный: только аутентифицированный админ пишет сюда HTML.
RICH_TEXT_OVERRIDES = {
    models.TextField: {"widget": QuillWidget},
}


@admin.register(LocalContentEntry)
class LocalContentEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "date")
    ordering = ("-date",)
    formfield_overrides = RICH_TEXT_OVERRIDES


@admin.register(ProcurementEntry)
class ProcurementEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "deadline")
    list_filter = ("status",)
    ordering = ("-deadline",)
    formfield_overrides = RICH_TEXT_OVERRIDES


@admin.register(DocumentEntry)
class DocumentEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "date")
    ordering = ("-date",)


@admin.register(NewsEntry)
class NewsEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "date")
    ordering = ("-date",)
    formfield_overrides = RICH_TEXT_OVERRIDES
