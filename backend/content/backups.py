"""Резервные копии сайта: база SQLite + загруженные файлы (media/) в одном zip.

Общий код для админки («Настройки» → «Резервные копии», content/backup_views.py)
и команд manage.py backup_create / backup_restore (их вызывают deploy/backup.sh и
deploy/restore.sh). Копии лежат в DATA_DIR/backups/ (на сервере — том /data).

Формат копии psa-<дата>.zip:
    backup.json   — когда сделана, есть ли файлы, применённые миграции;
    db.sqlite3    — база (снимок штатным backup API SQLite — целостный даже во
                    время записи, при нескольких процессах gunicorn);
    media/...     — загруженные файлы (если включены).

Восстановление тоже идёт через backup API SQLite (содержимое текущей базы
заменяется на месте, открытые соединения других процессов это переживают), затем
применяются миграции. Перед восстановлением автоматически делается копия текущего
состояния.
"""
import json
import shutil
from contextlib import closing
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.db import connections
from django.db.migrations.loader import MigrationLoader
from django.utils import timezone

FORMAT_VERSION = 1
NAME_PREFIX = "psa-"
# Эти файлы уже сжаты — в zip кладём как есть, так копия с сотнями МБ PDF делается быстро.
STORED_SUFFIXES = {".pdf", ".zip", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".docx", ".xlsx", ".pptx", ".rar", ".7z", ".mp4"}


class BackupError(Exception):
    """Понятное пользователю сообщение: что не так с копией."""


def backup_dir():
    path = Path(settings.DATA_DIR) / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path():
    return Path(settings.DATABASES["default"]["NAME"])


def media_root():
    return Path(settings.MEDIA_ROOT)


def safe_backup_path(name):
    """Путь к копии по имени файла — только внутри папки копий (без ../)."""
    path = (backup_dir() / Path(name).name).resolve()
    if path.parent != backup_dir().resolve() or path.suffix not in (".zip", ".sqlite3") or not path.is_file():
        raise BackupError("Копия не найдена.")
    return path


def _applied_migrations(database):
    with closing(sqlite3.connect(database)) as conn:
        try:
            return sorted(f"{app}.{name}" for app, name in conn.execute("SELECT app, name FROM django_migrations"))
        except sqlite3.DatabaseError as error:
            raise BackupError("В файле нет базы этого сайта (нет таблицы миграций).") from error


def _sqlite_copy(source, target):
    """Снимок базы source → target штатным механизмом SQLite (с учётом WAL)."""
    src = sqlite3.connect(source)
    dst = sqlite3.connect(target)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def create_backup(include_media=True, reason=""):
    """Создать копию, вернуть путь к zip."""
    stamp = timezone.localtime().strftime("%Y-%m-%d_%H%M%S")
    base = f"{NAME_PREFIX}{stamp}{'' if include_media else '-db'}{'-' + reason if reason else ''}"
    # Две копии в одну секунду не должны затирать друг друга.
    target, n = backup_dir() / f"{base}.zip", 2
    while target.exists() or target.with_suffix(".zip.part").exists():
        target, n = backup_dir() / f"{base}-{n}.zip", n + 1
    partial = target.with_suffix(".zip.part")
    with tempfile.TemporaryDirectory(dir=backup_dir()) as tmp:
        snapshot = Path(tmp) / "db.sqlite3"
        _sqlite_copy(db_path(), snapshot)
        manifest = {
            "format": FORMAT_VERSION,
            "created_at": timezone.localtime().isoformat(timespec="seconds"),
            "includes_media": bool(include_media),
            "migrations": _applied_migrations(snapshot),
        }
        media_count = 0
        with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
            archive.write(snapshot, "db.sqlite3")
            if include_media and media_root().is_dir():
                for file in sorted(media_root().rglob("*")):
                    if file.is_file():
                        compress = zipfile.ZIP_STORED if file.suffix.lower() in STORED_SUFFIXES else zipfile.ZIP_DEFLATED
                        archive.write(file, "media/" + file.relative_to(media_root()).as_posix(), compress_type=compress)
                        media_count += 1
            manifest["media_files"] = media_count
            archive.writestr("backup.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    partial.replace(target)
    return target


def read_backup(path):
    """Проверить копию и вернуть сведения о ней (для списка и перед восстановлением)."""
    path = Path(path)
    if path.suffix == ".sqlite3":  # просто файл базы (например, локальная backend/db.sqlite3)
        _check_database(path)
        return {"format": 0, "created_at": None, "includes_media": False, "media_files": 0, "migrations": _applied_migrations(path)}
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if "backup.json" not in names or "db.sqlite3" not in names:
                raise BackupError("Это не резервная копия сайта: в архиве нет backup.json и db.sqlite3.")
            manifest = json.loads(archive.read("backup.json"))
    except zipfile.BadZipFile as error:
        raise BackupError("Файл повреждён или это не zip-архив.") from error
    if manifest.get("format", 0) > FORMAT_VERSION:
        raise BackupError("Копия сделана более новой версией сайта — сначала обновите сайт.")
    return manifest


def _check_database(path):
    with open(path, "rb") as file:
        if file.read(16) != b"SQLite format 3\x00":
            raise BackupError("Файл базы в копии — не база SQLite.")
    with closing(sqlite3.connect(path)) as conn:
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise BackupError("База в копии повреждена (integrity_check не прошла).")
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {"wagtailcore_page", "django_migrations"} <= tables:
        raise BackupError("В копии база другого сайта (нет таблиц Wagtail).")


def _check_migrations(backup_migrations):
    """Копия не должна быть «новее» кода: неизвестные коду миграции откатить нельзя."""
    known = {f"{app}.{name}" for app, name in MigrationLoader(None, ignore_no_migrations=True).disk_migrations}
    unknown = sorted(set(backup_migrations) - known)
    if unknown:
        raise BackupError("Копия сделана более новой версией сайта (миграции " + ", ".join(unknown[:3])
                          + ("…" if len(unknown) > 3 else "") + ") — сначала обновите сайт.")


def _extract_media(archive, target_dir):
    base = target_dir.resolve()
    for member in archive.infolist():
        if not member.filename.startswith("media/") or member.is_dir():
            continue
        destination = (base / member.filename[len("media/"):]).resolve()
        if base not in destination.parents:  # защита от путей вида media/../../etc
            raise BackupError(f"Недопустимый путь в архиве: {member.filename}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(member) as src, open(destination, "wb") as dst:
            shutil.copyfileobj(src, dst)


def restore_backup(path, restore_media=True, make_safety_copy=True):
    """Восстановить базу (и файлы) из копии. Возвращает путь к копии «до восстановления»."""
    path = Path(path)
    manifest = read_backup(path)
    restore_media = restore_media and manifest.get("includes_media", False)
    with tempfile.TemporaryDirectory(dir=backup_dir()) as tmp:
        tmp = Path(tmp)
        if path.suffix == ".sqlite3":
            database = path
        else:
            database = tmp / "db.sqlite3"
            with zipfile.ZipFile(path) as archive:
                with archive.open("db.sqlite3") as src, open(database, "wb") as dst:
                    shutil.copyfileobj(src, dst)
        _check_database(database)
        _check_migrations(_applied_migrations(database))

        # Файлы распаковываются во временную папку ДО копии «до восстановления» —
        # неподходящий архив отклоняется сразу, ничего не меняя и не создавая.
        new_media = None
        if restore_media:
            new_media = tmp / "media"
            new_media.mkdir()
            with zipfile.ZipFile(path) as archive:
                _extract_media(archive, new_media)

        safety = create_backup(include_media=restore_media, reason="before-restore") if make_safety_copy else None

        # База: содержимое заменяется на месте через backup API — без подмены файла,
        # поэтому соединения других процессов gunicorn остаются рабочими.
        connections.close_all()
        _sqlite_copy(database, db_path())

        if new_media is not None:
            old = media_root().with_name(media_root().name + ".old")
            if old.exists():
                shutil.rmtree(old)
            if media_root().exists():
                media_root().rename(old)
            shutil.move(str(new_media), str(media_root()))
            shutil.rmtree(old, ignore_errors=True)

    call_command("migrate", interactive=False, verbosity=0)
    return safety


def list_backups():
    items = []
    for path in sorted(backup_dir().iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not path.is_file() or path.suffix not in (".zip", ".sqlite3"):
            continue
        info = {"name": path.name, "size": path.stat().st_size,
                "modified": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.get_current_timezone())}
        try:
            manifest = read_backup(path) if path.suffix == ".zip" else {"includes_media": False, "media_files": 0}
            info.update(includes_media=manifest.get("includes_media", False), media_files=manifest.get("media_files", 0),
                        automatic="before-restore" in path.name, error="")
        except BackupError as error:
            info.update(includes_media=False, media_files=0, automatic=False, error=str(error))
        items.append(info)
    return items
