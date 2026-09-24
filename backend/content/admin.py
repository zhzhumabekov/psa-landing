from django.contrib import admin

from .models import DocumentEntry, LocalContentEntry, NewsEntry, ProcurementEntry


@admin.register(LocalContentEntry)
class LocalContentEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "date")
    ordering = ("-date",)


@admin.register(ProcurementEntry)
class ProcurementEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "deadline")
    list_filter = ("status",)
    ordering = ("-deadline",)


@admin.register(DocumentEntry)
class DocumentEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "date")
    ordering = ("-date",)


@admin.register(NewsEntry)
class NewsEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "date")
    ordering = ("-date",)
