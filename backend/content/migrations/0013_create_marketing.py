"""Раздел «Маркетинг» (/marketing/) с подразделами «Предстоящие» и «Архив» —
как на psa.kz/marketing/.

Slug'и `future` ↔ `archive` — пара для кнопок «Перенести в архив» /
«Вернуть в предстоящие» (content/archive_transfer.py), их не менять.
"""
from django.db import migrations

SECTIONS = [
    ("Предстоящие", "Алдағы", "Upcoming", "future"),
    ("Архив", "Архив", "Archive", "archive"),
]

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # treebeard (Wagtail), шаг — 4 символа


def next_child_path(Page, parent):
    last = Page.objects.filter(path__startswith=parent.path, depth=parent.depth + 1).order_by("-path").first()
    number = 0
    if last:
        for char in last.path[-4:]:
            number = number * len(ALPHABET) + ALPHABET.index(char)
    number += 1
    step = ""
    for _ in range(4):
        number, rest = divmod(number, len(ALPHABET))
        step = ALPHABET[rest] + step
    return parent.path + step


def create_marketing(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    Page = apps.get_model("wagtailcore.Page")
    HomePage = apps.get_model("content", "HomePage")
    MarketingIndexPage = apps.get_model("content", "MarketingIndexPage")
    MarketingSectionPage = apps.get_model("content", "MarketingSectionPage")

    home = HomePage.objects.filter(depth=2).first()
    if home is None or MarketingIndexPage.objects.exists():
        return

    def create(model, model_name, parent, title, slug, **fields):
        content_type, _ = ContentType.objects.get_or_create(app_label="content", model=model_name)
        page = model.objects.create(
            title=title,
            draft_title=title,
            slug=slug,
            content_type=content_type,
            locale_id=parent.locale_id,
            path=next_child_path(Page, parent),
            depth=parent.depth + 1,
            numchild=0,
            url_path=f"{parent.url_path}{slug}/",
            **fields,
        )
        Page.objects.filter(pk=parent.pk).update(numchild=parent.numchild + 1)
        parent.numchild += 1
        return page

    index = create(MarketingIndexPage, "marketingindexpage", home, "Маркетинг", "marketing")
    for title, title_kz, title_en, slug in SECTIONS:
        create(MarketingSectionPage, "marketingsectionpage", index, title, slug, title_kz=title_kz, title_en=title_en)


def remove_marketing(apps, schema_editor):
    Page = apps.get_model("wagtailcore.Page")
    MarketingIndexPage = apps.get_model("content", "MarketingIndexPage")
    for index in MarketingIndexPage.objects.all():
        parent = Page.objects.get(path=index.path[:-4])
        Page.objects.filter(path__startswith=index.path).delete()
        Page.objects.filter(pk=parent.pk).update(numchild=max(parent.numchild - 1, 0))


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0012_marketing"),
    ]

    operations = [
        migrations.RunPython(create_marketing, remove_marketing),
    ]
