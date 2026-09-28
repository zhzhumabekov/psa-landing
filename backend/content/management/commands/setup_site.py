"""Создаёт недостающие разделы и подразделы сайта с нужными адресами.

    manage.py setup_site            # создать недостающее, исправить адреса
    manage.py setup_site --dry-run  # только показать, что будет сделано

Структура — content/site_tree.py. Безопасно запускать повторно: ничего не
удаляет и не трогает записи. Раздел/подраздел ищется по slug; если такого нет,
но есть страница того же типа с тем же заголовком (например, подраздел создан
в админке заново и получил адрес «arxiv» вместо «archive»), ей возвращается
нужный slug — вместе с адресами всех записей внутри.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from content.models import HomePage
from content.site_tree import SITE_TREE


class DryRun(Exception):
    pass


class Command(BaseCommand):
    help = "Создать недостающие разделы и подразделы сайта (content/site_tree.py) с нужными адресами."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Ничего не менять, только показать.")

    def handle(self, *args, dry_run=False, **options):
        home = HomePage.objects.filter(depth=2).first()
        if home is None:
            raise CommandError("Нет «Главной» (HomePage) — сначала manage.py migrate.")
        self.changes = 0
        try:
            with transaction.atomic():
                for index_model, slug, title, section_model, sections in SITE_TREE:
                    index = self.ensure(home, index_model, slug, title)
                    for section_slug, section_title, title_kz, title_en in sections:
                        self.ensure(index, section_model, section_slug, section_title, title_kz=title_kz, title_en=title_en)
                if dry_run:
                    raise DryRun
        except DryRun:
            self.stdout.write(self.style.WARNING("--dry-run: изменения не сохранены."))
        if not self.changes:
            self.stdout.write(self.style.SUCCESS("Структура сайта в порядке, изменений нет."))
        elif not dry_run:
            self.stdout.write(self.style.SUCCESS(f"Готово, изменений: {self.changes}."))

    def ensure(self, parent, model, slug, title, **translations):
        """Страница model с этим slug под parent — найти, исправить адрес или создать."""
        existing = model.objects.child_of(parent)
        page = existing.filter(slug=slug).first()
        if page:
            return page

        page = existing.filter(title=title).first()
        if page:
            old_url = page.url_path
            page.slug = slug
            page.save_revision().publish()  # Wagtail сам обновит url_path у вложенных записей
            page.refresh_from_db()
            self.report(f"адрес исправлен: {old_url} → {page.url_path}")
            return page

        if model.objects.exists() and model.max_count == 1:
            other = model.objects.first()
            raise CommandError(f"«{title}» уже есть в другом месте дерева ({other.url_path}) — перенесите её под «{parent.title}» в админке.")

        page = model(title=title, slug=slug, **translations)
        parent.add_child(instance=page)
        page.save_revision().publish()
        self.report(f"создано: {page.url_path} ({title})")
        return page

    def report(self, message):
        self.changes += 1
        self.stdout.write(f"  {message}")
