#!/usr/bin/env bash
# Резервная копия данных сайта (база + загруженные файлы) в backups/psa-<дата>.tar.gz.
# Сайт при этом не останавливается: база копируется штатным механизмом SQLite (backup),
# а не простым копированием файла, — копия целостная даже во время записи.
#
#   sudo bash deploy/backup.sh
#
# Восстановление — см. README.md, раздел «Сервер», «Резервные копии».
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")/.."

mkdir -p backups
chmod 700 backups
FILE="backups/psa-$(date +%Y-%m-%d_%H%M).tar.gz"

docker compose exec -T web python -c "
import sqlite3
src = sqlite3.connect('/data/db.sqlite3'); dst = sqlite3.connect('/data/backup.sqlite3')
src.backup(dst); dst.close(); src.close()
"
docker compose exec -T web tar -C /data -czf - backup.sqlite3 media > "$FILE"
docker compose exec -T web rm -f /data/backup.sqlite3
chmod 600 "$FILE"

echo "Готово: $FILE ($(du -h "$FILE" | cut -f1))"
