#!/usr/bin/env bash
# Восстановление сайта на сервере из резервной копии — то же, что «Восстановить»
# в админке («Настройки» → «Резервные копии»), но из файла на сервере:
#
#   sudo bash deploy/restore.sh backups/psa-2026-09-28_030000.zip   # копия (база + файлы)
#   sudo bash deploy/restore.sh db.sqlite3                           # только файл базы
#
# Перенести контент с локального компьютера: там — «manage.py backup_create»
# (появится backend/backups/psa-….zip), скопировать zip на сервер и выполнить эту
# команду с ним (или загрузить zip в админке кнопкой «Загрузить копию»).
#
# Текущие данные заменяются; перед этим сайт сам делает копию текущего состояния.
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")/.."

fail() { printf '\n\033[31mОшибка: %s\033[0m\n' "$1" >&2; exit 1; }

SRC="${1:-}"
[ -n "$SRC" ] && [ -f "$SRC" ] || fail "укажите файл: sudo bash deploy/restore.sh backups/psa-<дата>.zip"
case "$SRC" in
    *.zip|*.sqlite3) ;;
    *) fail "нужен файл .zip (резервная копия сайта) или .sqlite3 (файл базы)." ;;
esac

read -r -p "Текущие данные сайта будут заменены данными из $SRC. Продолжить? [y/N] " answer
[[ "$answer" =~ ^[YyДд] ]] || fail "отменено."

NAME="psa-uploaded-$(date +%Y-%m-%d_%H%M%S)-$(basename "$SRC")"
docker compose exec -T web mkdir -p /data/backups
docker compose cp "$SRC" "web:/data/backups/$NAME"
docker compose exec -T --user root web chown app:app "/data/backups/$NAME"
docker compose exec -T web python manage.py backup_restore "/data/backups/$NAME" --yes

echo "Готово. Файл копии остался в админке: «Настройки» → «Резервные копии»."
