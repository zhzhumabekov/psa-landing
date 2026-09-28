# Контейнер сайта: Django + Wagtail под gunicorn. Запускается через docker-compose.yml
# в корне репозитория (там же Caddy — HTTPS, статика и загруженные файлы).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_DEBUG=0 \
    DJANGO_DATA_DIR=/data \
    DJANGO_STATIC_ROOT=/app/staticfiles

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Непривилегированный пользователь. /data и /app/staticfiles создаются заранее с его
# владельцем — Docker перенесёт владельца в новые тома при первом запуске.
RUN useradd --system --uid 10001 --home-dir /app app \
    && mkdir -p /data/media /data/backups /app/staticfiles \
    && chown -R app:app /data /app/staticfiles \
    && chmod +x docker-entrypoint.sh
USER app

VOLUME ["/data", "/app/staticfiles"]
EXPOSE 8000

# /admin/login/ отвечает и в режиме обслуживания (503 — только для посетителей).
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/admin/login/', timeout=4)"]

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["sh", "-c", "exec gunicorn psa_backend.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3} --timeout 300 --access-logfile - --error-logfile -"]
