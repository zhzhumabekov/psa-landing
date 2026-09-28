#!/usr/bin/env bash
# Восстановление данных сайта на сервере — из резервной копии deploy/backup.sh или
# из обычного файла базы (например, локальной backend/db.sqlite3):
#
#   sudo bash deploy/restore.sh backups/psa-2026-09-28_0300.tar.gz   # база + загруженные файлы
#   sudo bash deploy/restore.sh db.sqlite3 [папка-media]              # только база (и файлы, если указаны)
#
# Текущие данные на сервере заменяются. Перед восстановлением скрипт сам делает
# резервную копию текущего состояния (deploy/backup.sh).
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")/.."

fail() { printf '\n\033[31mОшибка: %s\033[0m\n' "$1" >&2; exit 1; }

SRC="${1:-}"
MEDIA_SRC="${2:-}"
[ -n "$SRC" ] && [ -f "$SRC" ] || fail "укажите файл: sudo bash deploy/restore.sh backups/psa-<дата>.tar.gz"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/media"

case "$SRC" in
    *.tar.gz|*.tgz)
        tar -xzf "$SRC" -C "$WORK"
        [ -f "$WORK/backup.sqlite3" ] || fail "в архиве нет backup.sqlite3 — это не копия deploy/backup.sh?"
        mv "$WORK/backup.sqlite3" "$WORK/db.sqlite3"
        ;;
    *)
        cp "$SRC" "$WORK/db.sqlite3"
        if [ -n "$MEDIA_SRC" ]; then
            [ -d "$MEDIA_SRC" ] || fail "нет папки $MEDIA_SRC"
            cp -r "$MEDIA_SRC/." "$WORK/media/"
        fi
        ;;
esac
head -c 16 "$WORK/db.sqlite3" | grep -q "SQLite format 3" || fail "$SRC — не база SQLite."

echo "==> Резервная копия текущих данных (на всякий случай)"
bash deploy/backup.sh

echo "==> Останавливаю сайт и заменяю данные"
docker compose stop web
# От root во временном контейнере с теми же томами: старый журнал WAL удаляется ДО
# копирования (иначе SQLite применил бы его к восстановленной базе), владелец файлов —
# пользователь app, от которого работает сайт.
docker compose run --rm --no-deps --user root --entrypoint sh -v "$WORK:/restore:ro" web -c '
    set -e
    rm -f /data/db.sqlite3 /data/db.sqlite3-wal /data/db.sqlite3-shm
    cp /restore/db.sqlite3 /data/db.sqlite3
    cp -r /restore/media/. /data/media/
    chown -R app:app /data
'

echo "==> Запускаю сайт (миграции применятся сами)"
docker compose start web
echo "Готово. Логи: docker compose logs -f web"
