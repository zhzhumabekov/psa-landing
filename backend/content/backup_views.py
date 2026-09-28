"""Админка: «Настройки» → «Резервные копии» (только для суперпользователей).

Создать / загрузить / скачать / удалить / восстановить копию — логика в content/backups.py.
"""
import logging
from functools import wraps
from pathlib import Path

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.http import urlencode
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_POST

from .backups import (
    BackupError, backup_dir, create_backup, db_path, list_backups, media_root, read_backup, restore_backup,
    safe_backup_path,
)

logger = logging.getLogger(__name__)


def superuser_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper


def _folder_size(path):
    return sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file()) if Path(path).is_dir() else 0


@superuser_required
def backups_index(request):
    restored = request.GET.get("restored")
    return TemplateResponse(request, "admin/backups/index.html", {
        "backups": list_backups(),
        "db_size": db_path().stat().st_size if db_path().exists() else 0,
        "media_size": _folder_size(media_root()),
        "backup_dir": backup_dir(),
        "restored": restored,
        "safety": request.GET.get("safety"),
    })


@superuser_required
@require_POST
def backup_create(request):
    try:
        path = create_backup(include_media=bool(request.POST.get("include_media")))
    except Exception as error:  # noqa: BLE001 — показываем причину в админке
        logger.exception("Резервная копия не создана")
        messages.error(request, f"Копия не создана: {error}")
    else:
        messages.success(request, f"Копия создана: {path.name}.")
    return redirect("backups_index")


@superuser_required
@require_POST
def backup_upload(request):
    upload = request.FILES.get("file")
    suffix = Path(upload.name).suffix.lower() if upload else ""
    if not upload or suffix not in (".zip", ".sqlite3"):
        messages.error(request, "Выберите файл копии: .zip (копия сайта) или .sqlite3 (файл базы).")
        return redirect("backups_index")
    stem = get_valid_filename(Path(upload.name).stem)[:60] or "backup"
    target = backup_dir() / f"psa-uploaded-{timezone.localtime():%Y-%m-%d_%H%M%S}-{stem}{suffix}"
    with open(target, "wb") as file:
        for chunk in upload.chunks():
            file.write(chunk)
    try:
        read_backup(target)
    except BackupError as error:
        target.unlink(missing_ok=True)
        messages.error(request, f"Файл не принят: {error}")
    else:
        messages.success(request, f"Копия загружена: {target.name}. Чтобы применить её — «Восстановить».")
    return redirect("backups_index")


@superuser_required
def backup_download(request, name):
    try:
        path = safe_backup_path(name)
    except BackupError as error:
        messages.error(request, str(error))
        return redirect("backups_index")
    return FileResponse(open(path, "rb"), as_attachment=True, filename=path.name)


@superuser_required
@require_POST
def backup_delete(request, name):
    try:
        path = safe_backup_path(name)
    except BackupError as error:
        messages.error(request, str(error))
    else:
        path.unlink()
        messages.success(request, f"Копия удалена: {name}.")
    return redirect("backups_index")


@superuser_required
def backup_restore(request, name):
    try:
        path = safe_backup_path(name)
        manifest = read_backup(path)
    except BackupError as error:
        messages.error(request, str(error))
        return redirect("backups_index")

    if request.method == "POST":
        if not request.POST.get("confirm"):
            messages.error(request, "Отметьте, что понимаете: текущие данные будут заменены.")
        else:
            restore_media = bool(request.POST.get("restore_media"))
            try:
                safety = restore_backup(path, restore_media=restore_media)
            except BackupError as error:
                messages.error(request, f"Не восстановлено: {error}")
            except Exception as error:  # noqa: BLE001
                logger.exception("Восстановление из %s не удалось", name)
                messages.error(request, f"Не восстановлено: {error}")
            else:
                # После восстановления сессия может оказаться из копии — сообщение
                # передаём в адресе, а не через messages (они живут в сессии).
                query = {"restored": name}
                if safety:
                    query["safety"] = safety.name
                return redirect(reverse("backups_index") + "?" + urlencode(query))

    return TemplateResponse(request, "admin/backups/restore_confirm.html", {
        "name": name,
        "manifest": manifest,
        "created": parse_datetime(manifest["created_at"]) if manifest.get("created_at") else None,
        "size": path.stat().st_size,
    })
