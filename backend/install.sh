#!/usr/bin/env bash
# Установка сайта с нуля (или «догнать» после git pull) — Ubuntu / Debian.
#
#   bash install.sh                        # venv, пакеты, база, разделы, администратор
#   bash install.sh --import-procurement   # + перенести «Закупки» с psa.kz (~310 МБ)
#
# Безопасно запускать повторно: venv и администратор создаются, только если их
# ещё нет; manage.py setup_site ничего не удаляет, только создаёт недостающие
# разделы/подразделы и исправляет их адреса (структура — content/site_tree.py).
# Администратора без вопросов: заранее задать DJANGO_SUPERUSER_USERNAME,
# DJANGO_SUPERUSER_PASSWORD (и при желании DJANGO_SUPERUSER_EMAIL).
# Windows-вариант этого скрипта — install.ps1.
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8

IMPORT_PROCUREMENT=0
for arg in "$@"; do
    case "$arg" in
        --import-procurement) IMPORT_PROCUREMENT=1 ;;
        -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "Неизвестный параметр: $arg (см. bash install.sh --help)" >&2; exit 2 ;;
    esac
done

PYTHON="venv/bin/python"

step() { printf '\n\033[36m==> %s\033[0m\n' "$1"; }
fail() { printf '\n\033[31mОшибка: %s\033[0m\n' "$1" >&2; exit 1; }

find_python() {
    local candidate
    for candidate in python3.14 python3.13 python3.12 python3; do
        if command -v "$candidate" >/dev/null 2>&1 &&
            "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

create_venv() {
    local base version
    base="$(find_python)" || fail "нужен Python 3.12 или новее. Ubuntu 24.04+: sudo apt install python3 python3-venv;
  Ubuntu 22.04: sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.12 python3.12-venv"
    version="$("$base" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"

    if "$base" -c 'import ensurepip' 2>/dev/null; then
        "$base" -m venv venv
        return
    fi

    # В Ubuntu модуль venv без pip — отдельный пакет python3.X-venv.
    if [ -t 0 ] && command -v apt-get >/dev/null 2>&1; then
        echo "Для виртуального окружения нужен пакет python${version}-venv."
        read -r -p "Установить его сейчас (sudo apt install python${version}-venv)? [Y/n] " answer
        if [[ ! "$answer" =~ ^[NnНн] ]]; then
            sudo apt-get update
            sudo apt-get install -y "python${version}-venv"
            "$base" -m venv venv
            return
        fi
    fi

    # Без sudo: venv без pip, pip ставится официальным get-pip.py.
    echo "Пакета python${version}-venv нет — создаю venv без pip и ставлю pip через get-pip.py."
    "$base" -m venv --without-pip venv || fail "не удалось создать venv. Установите пакет: sudo apt install python${version}-venv"
    "$PYTHON" -c 'import urllib.request; urllib.request.urlretrieve("https://bootstrap.pypa.io/get-pip.py", "venv/get-pip.py")' \
        || fail "не удалось скачать get-pip.py. Установите пакет: sudo apt install python${version}-venv"
    "$PYTHON" venv/get-pip.py --quiet
    rm -f venv/get-pip.py
}

if [ ! -x "$PYTHON" ]; then
    step "Создаю виртуальное окружение venv"
    create_venv
fi

step "Устанавливаю пакеты (requirements.txt)"
"$PYTHON" -m pip install --disable-pip-version-check -q -r requirements.txt || fail "не удалось установить пакеты."

step "Применяю миграции базы (db.sqlite3)"
"$PYTHON" manage.py migrate --no-input || fail "миграции не применились."

step "Проверяю разделы и подразделы сайта"
"$PYTHON" manage.py setup_site || fail "не удалось создать разделы сайта."

has_admin=0
"$PYTHON" manage.py shell --no-imports -c "import sys; from django.contrib.auth import get_user_model; sys.exit(0 if get_user_model().objects.filter(is_superuser=True).exists() else 3)" || has_admin=$?
if [ "$has_admin" -eq 3 ]; then
    step "Создаю администратора для /admin/"
    if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
        "$PYTHON" manage.py createsuperuser --no-input --email "${DJANGO_SUPERUSER_EMAIL:-}" || fail "администратор не создан."
    else
        "$PYTHON" manage.py createsuperuser || fail "администратор не создан."
    fi
elif [ "$has_admin" -ne 0 ]; then
    fail "не удалось проверить администратора."
fi

if [ "$IMPORT_PROCUREMENT" -eq 1 ]; then
    step "Переношу «Закупки» с psa.kz"
    "$PYTHON" manage.py import_psa_procurement || fail "импорт «Закупок» не удался."
fi

printf '\n\033[32mГотово. Запуск сайта:\033[0m\n'
echo "  venv/bin/python manage.py runserver 127.0.0.1:8000"
echo "  сайт — http://127.0.0.1:8000/, админка — http://127.0.0.1:8000/admin/"
