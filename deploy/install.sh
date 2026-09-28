#!/usr/bin/env bash
# Автоматическая установка сайта на сервер Ubuntu / Debian: Docker, сайт в контейнере,
# Caddy с HTTPS-сертификатом Let's Encrypt. Запускать из папки проекта:
#
#   sudo bash deploy/install.sh                        # установить или обновить
#   sudo bash deploy/install.sh --import-procurement   # + перенести «Закупки» с psa.kz (~310 МБ)
#
# Повторный запуск — обновление (после git pull): пересобирает и перезапускает
# контейнеры, данные (база, файлы) и настройки .env не трогает.
#
# Без вопросов (например, из CI) — заранее задать переменные:
#   SITE_DOMAINS="psa.kz, www.psa.kz"      (пусто — сайт по IP без HTTPS)
#   DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD, DJANGO_SUPERUSER_EMAIL
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")/.."

IMPORT_PROCUREMENT=0
for arg in "$@"; do
    case "$arg" in
        --import-procurement) IMPORT_PROCUREMENT=1 ;;
        -h|--help) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "Неизвестный параметр: $arg (см. --help)" >&2; exit 2 ;;
    esac
done

step() { printf '\n\033[36m==> %s\033[0m\n' "$1"; }
fail() { printf '\n\033[31mОшибка: %s\033[0m\n' "$1" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || fail "запустите через sudo: sudo bash deploy/install.sh"
[ -f docker-compose.yml ] || fail "не найден docker-compose.yml — запускайте из папки проекта."

# ---------- 1. Docker ----------
if ! command -v docker >/dev/null 2>&1; then
    step "Устанавливаю Docker (официальный скрипт get.docker.com)"
    command -v curl >/dev/null 2>&1 || { apt-get update -q && apt-get install -y -q curl ca-certificates; }
    curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker >/dev/null 2>&1 || true
docker compose version >/dev/null 2>&1 || fail "нет плагина docker compose — установите пакет docker-compose-plugin."

# ---------- 2. Настройки (.env) ----------
if [ ! -f .env ]; then
    step "Создаю настройки .env"
    if [ -z "${SITE_DOMAINS+x}" ]; then
        echo "Домен сайта, например: psa.kz, www.psa.kz"
        echo "(DNS-запись домена должна уже указывать на этот сервер — иначе сертификат не выпустится)."
        read -r -p "Пусто — открыть сайт по IP без HTTPS: " SITE_DOMAINS
    fi
    DOMAINS="$(echo "$SITE_DOMAINS" | tr -d ' ')"
    SECRET="$(head -c 64 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 60)"

    if [ -n "$DOMAINS" ]; then
        FIRST="${DOMAINS%%,*}"
        SITE_ADDRESS="$(echo "$DOMAINS" | sed 's/,/, /g')"
        ALLOWED="$DOMAINS"
        CSRF="$(echo "$DOMAINS" | sed 's/[^,]*/https:\/\/&/g')"
        HTTPS=1
        BASE_URL="https://$FIRST"
    else
        IPS="$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -v ':' | grep -v '^$' | paste -sd, -)"
        [ -n "$IPS" ] || fail "не удалось определить IP сервера — задайте SITE_DOMAINS или впишите адрес в .env вручную."
        SITE_ADDRESS=":80"
        ALLOWED="$IPS"
        CSRF="$(echo "$IPS" | sed 's/[^,]*/http:\/\/&/g')"
        HTTPS=0
        BASE_URL="http://${IPS%%,*}"
    fi

    umask 077
    cat > .env <<ENV
# Настройки сайта на сервере (создано deploy/install.sh $(date '+%Y-%m-%d %H:%M')).
# Не публиковать и не коммитить: здесь секретный ключ. Образец — .env.example.
SITE_ADDRESS=$SITE_ADDRESS
DJANGO_SECRET_KEY=$SECRET
DJANGO_ALLOWED_HOSTS=$ALLOWED
DJANGO_CSRF_TRUSTED_ORIGINS=$CSRF
DJANGO_HTTPS=$HTTPS
WAGTAILADMIN_BASE_URL=$BASE_URL
GUNICORN_WORKERS=3
ENV
    umask 022
    echo "Сохранено в .env (адрес: $BASE_URL)."
else
    step "Настройки .env уже есть — оставляю как есть"
fi
SITE_URL="$(grep '^WAGTAILADMIN_BASE_URL=' .env | cut -d= -f2-)"

# ---------- 3. Брандмауэр ----------
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
    step "Открываю порты 80 и 443 в брандмауэре (ufw)"
    ufw allow 80/tcp >/dev/null
    ufw allow 443/tcp >/dev/null
    ufw allow 443/udp >/dev/null
fi

# ---------- 4. Сборка и запуск ----------
step "Собираю и запускаю контейнеры (первый раз — несколько минут)"
docker compose up -d --build --remove-orphans

step "Жду, пока сайт запустится (миграции, статика, разделы)"
WEB_ID="$(docker compose ps -q web)"
for _ in $(seq 1 60); do
    STATUS="$(docker inspect --format '{{.State.Health.Status}}' "$WEB_ID" 2>/dev/null || echo starting)"
    [ "$STATUS" = "healthy" ] && break
    [ "$STATUS" = "unhealthy" ] && break
    sleep 5
done
if [ "$STATUS" != "healthy" ]; then
    docker compose logs --tail 60 web
    fail "сайт не запустился (состояние: $STATUS) — последние строки лога выше."
fi
echo "Сайт работает."

# ---------- 5. Администратор ----------
HAS_ADMIN=0
docker compose exec -T web python manage.py shell --no-imports -c \
    "import sys; from django.contrib.auth import get_user_model; sys.exit(0 if get_user_model().objects.filter(is_superuser=True).exists() else 3)" \
    || HAS_ADMIN=$?
if [ "$HAS_ADMIN" -eq 3 ]; then
    step "Создаю администратора для /admin/"
    if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
        docker compose exec -T \
            -e DJANGO_SUPERUSER_USERNAME -e DJANGO_SUPERUSER_PASSWORD -e DJANGO_SUPERUSER_EMAIL="${DJANGO_SUPERUSER_EMAIL:-}" \
            web python manage.py createsuperuser --no-input
    else
        docker compose exec web python manage.py createsuperuser
    fi
elif [ "$HAS_ADMIN" -ne 0 ]; then
    fail "не удалось проверить администратора."
fi

# ---------- 6. Закупки с psa.kz ----------
if [ "$IMPORT_PROCUREMENT" -eq 1 ]; then
    step "Переношу «Закупки» с psa.kz"
    docker compose exec -T web python manage.py import_psa_procurement
fi

printf '\n\033[32mГотово.\033[0m Сайт: %s   Админка: %s/admin/\n' "$SITE_URL" "$SITE_URL"
cat <<'HELP'

Полезные команды (из папки проекта):
  docker compose logs -f web                                   логи сайта
  docker compose exec web python manage.py maintenance on      режим обслуживания (off — выключить)
  sudo bash deploy/backup.sh                                   резервная копия базы и файлов в backups/
  sudo bash deploy/restore.sh backups/<файл>.tar.gz           восстановить из резервной копии
  git pull && sudo bash deploy/install.sh                      обновить сайт
HELP
