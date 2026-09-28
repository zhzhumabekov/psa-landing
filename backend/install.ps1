# Установка сайта с нуля (или «догнать» после git pull) — Windows PowerShell.
#
#   powershell -ExecutionPolicy Bypass -File install.ps1                      # venv, пакеты, база, разделы, администратор
#   powershell -ExecutionPolicy Bypass -File install.ps1 -ImportProcurement   # + перенести «Закупки» с psa.kz (~310 МБ)
#
# Безопасно запускать повторно: venv и администратор создаются, только если их
# ещё нет; manage.py setup_site ничего не удаляет, только создаёт недостающие
# разделы/подразделы и исправляет их адреса (структура — content/site_tree.py).
# Администратора без вопросов: заранее задать $env:DJANGO_SUPERUSER_USERNAME,
# $env:DJANGO_SUPERUSER_PASSWORD (и при желании $env:DJANGO_SUPERUSER_EMAIL).
param(
    [switch]$ImportProcurement
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$python = Join-Path $PSScriptRoot "venv\Scripts\python.exe"

function Step($text) { Write-Host ""; Write-Host "==> $text" -ForegroundColor Cyan }

function Run {
    & $python @args
    if ($LASTEXITCODE -ne 0) { throw "Команда завершилась с ошибкой: python $args" }
}

if (-not (Test-Path $python)) {
    Step "Создаю виртуальное окружение venv"
    $base = $null
    $candidates = @(
        @{ Exe = "py"; Args = @("-3") },
        @{ Exe = "python"; Args = @() }
    )
    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Exe -ErrorAction SilentlyContinue)) { continue }
        $ver = & $candidate.Exe @($candidate.Args) -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($LASTEXITCODE -eq 0 -and $ver -and [version]"$ver" -ge [version]"3.12") { $base = $candidate; break }
    }
    if ($null -eq $base) { throw "Нужен Python 3.12 или новее: https://www.python.org/downloads/ (при установке отметьте «Add python.exe to PATH»)." }
    & $base.Exe @($base.Args) -m venv venv
    if ($LASTEXITCODE -ne 0) { throw "Не удалось создать venv." }
}

Step "Устанавливаю пакеты (requirements.txt)"
Run -m pip install --disable-pip-version-check -q -r requirements.txt

Step "Применяю миграции базы (db.sqlite3)"
Run manage.py migrate --no-input

Step "Проверяю разделы и подразделы сайта"
Run manage.py setup_site

& $python manage.py shell --no-imports -c "import sys; from django.contrib.auth import get_user_model; sys.exit(0 if get_user_model().objects.filter(is_superuser=True).exists() else 3)"
if ($LASTEXITCODE -eq 3) {
    Step "Создаю администратора для /admin/"
    if ($env:DJANGO_SUPERUSER_USERNAME -and $env:DJANGO_SUPERUSER_PASSWORD) {
        Run manage.py createsuperuser --no-input --email "$env:DJANGO_SUPERUSER_EMAIL"
    } else {
        Run manage.py createsuperuser
    }
} elseif ($LASTEXITCODE -ne 0) {
    throw "Не удалось проверить администратора."
}

if ($ImportProcurement) {
    Step "Переношу «Закупки» с psa.kz"
    Run manage.py import_psa_procurement
}

Write-Host ""
Write-Host "Готово. Запуск сайта:" -ForegroundColor Green
Write-Host "  .\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000"
Write-Host "  сайт — http://127.0.0.1:8000/, админка — http://127.0.0.1:8000/admin/"
