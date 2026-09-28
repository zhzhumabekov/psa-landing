"""Режим обслуживания сайта (страница 503, админка при этом работает).

    manage.py maintenance on      # включить
    manage.py maintenance off     # выключить
    manage.py maintenance status  # показать, включён ли
"""
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Включить/выключить режим обслуживания (посетители видят страницу 503, админка работает)."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["on", "off", "status"])

    def handle(self, *args, action, **options):
        flag = settings.MAINTENANCE_FLAG
        if action == "on":
            flag.touch()
            self.stdout.write(self.style.WARNING("Режим обслуживания включён: посетители видят страницу 503, админка и вошедшие сотрудники — сайт как обычно."))
        elif action == "off":
            flag.unlink(missing_ok=True)
            self.stdout.write(self.style.SUCCESS("Режим обслуживания выключен."))
        else:
            self.stdout.write("Режим обслуживания " + ("включён." if flag.exists() else "выключен."))
