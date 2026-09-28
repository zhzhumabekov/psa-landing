"""Подвал сайта: контакты с подвала psa.kz (ru / kz / en, на 2026-09-28).

Телефон закупок — 79 89 75, как в русской и казахской версиях psa.kz
(в английской там указан 79 89 25 — похоже на устаревший).
"""
import uuid

from django.db import migrations


def phone(number, note, note_kz, note_en):
    return {
        "type": "phone",
        "id": str(uuid.uuid4()),
        "value": {"number": number, "note": note, "note_kz": note_kz, "note_en": note_en},
    }


def fill_footer(apps, schema_editor):
    Site = apps.get_model("wagtailcore", "Site")
    FooterSettings = apps.get_model("content", "FooterSettings")
    for site in Site.objects.all():
        if FooterSettings.objects.filter(site=site).exists():
            continue
        FooterSettings.objects.create(
            site=site,
            org_name="ТОО «PSA»",
            org_name_kz="«PSA» ЖШС",
            org_name_en="PSA LLP",
            tagline="Полномочный орган Правительства Республики Казахстан по соглашениям о разделе продукции",
            tagline_kz="Өнімді бөлу туралы келісімдер бойынша Қазақстан Республикасы Үкіметінің өкілетті органы",
            tagline_en="Authorized body of the Government of the Republic of Kazakhstan for production sharing agreements",
            address="Республика Казахстан, 010000,\nгород Астана, ул. Сыганак, 17/10",
            address_kz="Қазақстан Республикасы, 010000,\nАстана қаласы, Сығанақ көшесі, 17/10 үйі",
            address_en="010000, Astana, Republic of Kazakhstan,\nSyganaq street, 17/10",
            phones=[
                phone("+7 7172 79 89 20", "Канцелярия", "Кеңсе", "Office"),
                phone("+7 7172 79 89 21", "Канцелярия", "Кеңсе", "Office"),
                phone("+7 7172 79 89 75", "Закупки", "Сатып алу", "Procurement"),
            ],
            email="info@psa.kz",
            mail_url="https://mail.psa.kz/owa",
        )


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0010_footer_settings"),
    ]

    operations = [
        migrations.RunPython(fill_footer, migrations.RunPython.noop),
    ]
