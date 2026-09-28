"""Поле `url` → `external_url` у ProcurementPage и DocumentPage.

Имя `url` перекрывало свойство Wagtail Page.url (адрес самой страницы) —
ломались «Смотреть на сайте» в админке и всё, что строит ссылку на страницу
через page.url. В ревизиях ключ тоже переименовываем, чтобы старые версии
открывались со ссылкой.
"""
from django.db import migrations

MODELS = ["procurementpage", "documentpage"]


def rename_in_revisions(old, new):
    def run(apps, schema_editor):
        ContentType = apps.get_model("contenttypes.ContentType")
        Revision = apps.get_model("wagtailcore.Revision")
        for model_name in MODELS:
            content_type = ContentType.objects.filter(app_label="content", model=model_name).first()
            if content_type is None:
                continue
            for revision in Revision.objects.filter(content_type=content_type):
                if old in revision.content:
                    revision.content[new] = revision.content.pop(old)
                    revision.save(update_fields=["content"])

    return run


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0007_procurement_sections"),
        ("wagtailcore", "0001_initial"),
    ]

    operations = [
        migrations.RenameField("procurementpage", "url", "external_url"),
        migrations.RenameField("documentpage", "url", "external_url"),
        migrations.RunPython(rename_in_revisions("url", "external_url"), rename_in_revisions("external_url", "url")),
    ]
