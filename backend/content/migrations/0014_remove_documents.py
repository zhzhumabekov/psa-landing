"""Удаление раздела «Документы» (/documents/): страницы раздела и модели
DocumentsIndexPage / DocumentPage.

Библиотеку файлов Wagtail («Документы» в меню админки — wagtail.documents,
файлы «Закупок») это не затрагивает.

Сначала удаляем сами страницы: иначе в дереве Wagtail остались бы страницы
несуществующего типа и админка падала бы. Откат миграции вернёт пустые
таблицы, но не страницы — раздел можно создать заново в админке.
"""
from django.db import migrations

MODELS = ("documentsindexpage", "documentpage")


def delete_documents_pages(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Page = apps.get_model("wagtailcore", "Page")
    Revision = apps.get_model("wagtailcore", "Revision")
    ReferenceIndex = apps.get_model("wagtailcore", "ReferenceIndex")

    types = ContentType.objects.filter(app_label="content", model__in=MODELS)
    page_type = ContentType.objects.filter(app_label="wagtailcore", model="page").first()

    # Верхние страницы раздела (обычно одна — /documents/) вместе со всем, что внутри.
    tops = [p for p in Page.objects.filter(content_type__in=types).order_by("path")]
    tops = [p for p in tops if not any(p.path.startswith(t.path) and p.path != t.path for t in tops)]
    for top in tops:
        subtree = Page.objects.filter(path__startswith=top.path)
        ids = [str(pk) for pk in subtree.values_list("pk", flat=True)]
        if page_type:
            Revision.objects.filter(base_content_type=page_type, object_id__in=ids).delete()
            ReferenceIndex.objects.filter(base_content_type=page_type, object_id__in=ids).delete()
        subtree.delete()
        parent = Page.objects.filter(path=top.path[:-4]).first()
        if parent:
            Page.objects.filter(pk=parent.pk).update(numchild=max(parent.numchild - 1, 0))


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0013_create_marketing'),
        ('wagtailcore', '0098_apitoken'),
    ]

    operations = [
        migrations.RunPython(delete_documents_pages, migrations.RunPython.noop),
        migrations.DeleteModel(
            name='DocumentPage',
        ),
        migrations.DeleteModel(
            name='DocumentsIndexPage',
        ),
    ]
