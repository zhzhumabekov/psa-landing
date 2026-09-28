#!/usr/bin/env bash
# Резервная копия сайта (база + загруженные файлы) — и на сервере (её видно в админке:
# «Настройки» → «Резервные копии»), и в папке backups/ рядом с проектом.
# Сайт при этом не останавливается. То же самое делает кнопка «Создать копию» в админке.
#
#   sudo bash deploy/backup.sh              # база и файлы
#   sudo bash deploy/backup.sh --no-media   # только база
#
# Ежедневно в 3:00 — строка в «sudo crontab -e»:
#   0 3 * * * cd /путь/к/psa-landing && bash deploy/backup.sh
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")/.."

mkdir -p backups
chmod 700 backups

# Последняя строка вывода команды — путь к копии внутри контейнера.
REMOTE="$(docker compose exec -T web python manage.py backup_create "$@" | tail -n 1 | tr -d '\r')"
NAME="$(basename "$REMOTE")"
docker compose cp "web:$REMOTE" "backups/$NAME"
chmod 600 "backups/$NAME"

echo "Готово: backups/$NAME ($(du -h "backups/$NAME" | cut -f1)). Копия есть и в админке — «Настройки» → «Резервные копии»."
