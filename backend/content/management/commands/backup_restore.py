"""Восстановление сайта из резервной копии (zip из backup_create или файл базы .sqlite3).
То же — в админке: «Настройки» → «Резервные копии» → «Восстановить».

    manage.py backup_restore backups/psa-2026-09-28_030000.zip
    manage.py backup_restore path/to/db.sqlite3 --yes   # без вопроса

Текущие данные заменяются; перед этим автоматически делается копия текущего состояния.
"""
from django.core.management.base import BaseCommand, CommandError

from content.backups import BackupError, read_backup, restore_backup


class Command(BaseCommand):
    help = "Восстановить базу и загруженные файлы из резервной копии."

    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument("--no-media", action="store_true", help="Восстановить только базу, файлы не трогать.")
        parser.add_argument("--yes", action="store_true", help="Не спрашивать подтверждение.")

    def handle(self, *args, path, no_media=False, yes=False, **options):
        try:
            manifest = read_backup(path)
        except (BackupError, OSError) as error:
            raise CommandError(str(error)) from error
        media = manifest.get("includes_media") and not no_media
        self.stdout.write(f"Копия: {path}, создана {manifest.get('created_at') or '—'}, "
                          f"файлы: {'да (' + str(manifest.get('media_files', 0)) + ')' if media else 'нет'}.")
        if not yes and input("Текущие данные будут заменены. Продолжить? [y/N] ").strip().lower() not in ("y", "yes", "д", "да"):
            raise CommandError("Отменено.")
        try:
            safety = restore_backup(path, restore_media=media)
        except BackupError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS("Восстановлено."))
        if safety:
            self.stdout.write(f"Копия состояния до восстановления: {safety}")
