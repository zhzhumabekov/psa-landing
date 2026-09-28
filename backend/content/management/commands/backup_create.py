"""Резервная копия сайта (база + загруженные файлы) в DATA_DIR/backups/.
То же — в админке: «Настройки» → «Резервные копии».

    manage.py backup_create             # база и файлы
    manage.py backup_create --no-media  # только база
"""
from django.core.management.base import BaseCommand

from content.backups import create_backup


class Command(BaseCommand):
    help = "Создать резервную копию сайта (база + загруженные файлы) в папке backups/."

    def add_arguments(self, parser):
        parser.add_argument("--no-media", action="store_true", help="Без загруженных файлов — только база.")

    def handle(self, *args, no_media=False, **options):
        path = create_backup(include_media=not no_media)
        self.stdout.write(self.style.SUCCESS(f"Готово: {path} ({path.stat().st_size / 1024 / 1024:.1f} МБ)"))
        # Последней строкой — только путь: его читает deploy/backup.sh.
        self.stdout.write(str(path))
