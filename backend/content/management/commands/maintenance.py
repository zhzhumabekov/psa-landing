"""Режим обслуживания сайта (страница 503, админка при этом работает).
То же самое — в админке: «Настройки» → «Сайт» → «Режим обслуживания».

    manage.py maintenance on      # включить
    manage.py maintenance off     # выключить
    manage.py maintenance status  # показать, включён ли
"""
from django.core.management.base import BaseCommand

from content.models import SiteConfig


class Command(BaseCommand):
    help = "Включить/выключить режим обслуживания (посетители видят страницу 503, админка работает)."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["on", "off", "status"])

    def handle(self, *args, action, **options):
        config = SiteConfig.load()
        if action in ("on", "off"):
            config.maintenance_mode = action == "on"
            config.save(update_fields=["maintenance_mode"])
        if config.maintenance_mode:
            self.stdout.write(self.style.WARNING("Режим обслуживания включён: посетители видят страницу 503, админка и вошедшие сотрудники — сайт как обычно."))
        else:
            self.stdout.write(self.style.SUCCESS("Режим обслуживания выключен."))
