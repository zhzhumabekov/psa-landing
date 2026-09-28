"""Стартовое дерево страниц: Главная и 4 раздела под ней.

Slug'и разделов совпадают с прежними адресами (/local-content/ и т.д.),
на них же завязано меню в templates/base.html ({% slugurl %}).
"""
from django.db import migrations

SECTIONS = [
    ("localcontentindexpage", "Местное содержание", "local-content"),
    ("procurementindexpage", "Закупки", "procurement"),
    ("documentsindexpage", "Документы", "documents"),
    ("newsindexpage", "Новости", "news"),
]


def create_site_tree(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    Locale = apps.get_model("wagtailcore.Locale")
    Page = apps.get_model("wagtailcore.Page")
    Site = apps.get_model("wagtailcore.Site")

    # Стандартная приветственная страница из wagtailcore.0002_initial_data
    # (вместе с ней каскадом удаляется и Site, который на неё указывал).
    Page.objects.filter(
        content_type__app_label="wagtailcore", content_type__model="page", depth=2
    ).delete()

    locale = Locale.objects.first()

    def create(model_name, title, slug, path, depth, url_path, numchild=0):
        model = apps.get_model("content", model_name)
        content_type, _ = ContentType.objects.get_or_create(app_label="content", model=model_name)
        return model.objects.create(
            title=title,
            draft_title=title,
            slug=slug,
            content_type=content_type,
            locale=locale,
            path=path,
            depth=depth,
            numchild=numchild,
            url_path=url_path,
        )

    home = create("homepage", "Главная", "home", "00010001", 2, "/home/", numchild=len(SECTIONS))
    for i, (model_name, title, slug) in enumerate(SECTIONS, start=1):
        create(model_name, title, slug, f"{home.path}{i:04d}", 3, f"/home/{slug}/")

    Site.objects.create(hostname="localhost", port=80, root_page=home, is_default_site=True, site_name="ТОО «PSA»")


def remove_site_tree(apps, schema_editor):
    HomePage = apps.get_model("content", "HomePage")
    Page = apps.get_model("wagtailcore.Page")
    home = HomePage.objects.filter(depth=2).first()
    if home:
        Page.objects.filter(path__startswith=home.path).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_site_tree, remove_site_tree),
    ]
