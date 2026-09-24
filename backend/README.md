# Бэкенд на Django (локальный запуск)

SQLite внутри (файл `db.sqlite3`, создаётся `migrate`), всё поставлено в venv — ничего не устанавливалось глобально.

## Запуск

```bash
cd backend
./venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
```

Это и есть весь сайт — открывайте http://127.0.0.1:8000/, вся страница целиком (шапка, hero, о компании, проекты, партнёры, 4 раздела с контентом из БД, контакты). Отдельного статик-сервера для фронтенда больше нет — `templates/index.html` рендерится через Django-шаблонизатор, `static/styles.css`/`static/script.js` отдаёт `django.contrib.staticfiles`.

## Админка

http://127.0.0.1:8000/admin/

- Логин: `admin`
- Пароль: `PsaLocalDev2026!`

**Сменить пароль перед любым реальным использованием** (в самой админке, раздел «Пользователи», или `manage.py changepassword admin`).

## Как отображается контент 4 разделов

`content.views.home` (главная страница) при каждом запросе читает все 4 модели из БД и передаёт querysets в шаблон `templates/index.html`, который рендерит их через `{% for %}` (Django сам экранирует значения — безопасно от XSS, без ручной работы с DOM, как было в JS-версии). Добавили запись в `/admin/` — она сразу появится на сайте при следующей загрузке страницы, без пересборки и без API-запроса из браузера.

## API (только чтение, публично) — для внешних потребителей, сайту больше не нужен

| Эндпоинт | Модель | Поля |
|---|---|---|
| `GET /api/local-content/` | `LocalContentEntry` | id, title, date, body |
| `GET /api/procurement/` | `ProcurementEntry` | id, title, status, deadline, description, url |
| `GET /api/documents/` | `DocumentEntry` | id, title, category, date, file_url, url |
| `GET /api/news/` | `NewsEntry` | id, title, date, excerpt, body |

Создание/редактирование/удаление — только через `/admin/` (в API это осознанно не выведено, `ReadOnlyModelViewSet`). Сама страница сайта эти эндпоинты больше не вызывает (контент теперь серверный, см. выше) — API оставлен на случай, если данные понадобятся другому потребителю (мобильное приложение, другой сайт и т.п.). Если не понадобится — можно смело удалить `content/serializers.py`, `content/views.py` (класс-вьюсеты), `content/urls.py` и связанный `include` в `psa_backend/urls.py`.

## Структура

```
backend/
├── venv/                — виртуальное окружение (не в git)
├── manage.py
├── requirements.txt      — зафиксированные версии (Django, DRF, django-cors-headers)
├── templates/index.html  — вся разметка сайта (шаблон, не статика)
├── static/
│   ├── styles.css        — стили (без изменений от прежней статик-версии)
│   └── script.js         — мобильное меню, модалки проектов, i18n, форма (fetch-логика удалена — не нужна)
├── psa_backend/          — настройки, TEMPLATES/STATICFILES_DIRS, корневые urls (в т.ч. `path('', home)`)
└── content/              — приложение: модели, вью главной страницы, админка, API
    ├── models.py         — LocalContentEntry, ProcurementEntry, DocumentEntry, NewsEntry
    ├── views.py            — home() — рендер шаблона; + ReadOnlyModelViewSet'ы для /api/
    ├── admin.py           — регистрация моделей в /admin/
    ├── serializers.py      — DRF-сериализаторы (только для /api/)
    └── urls.py             — роуты /api/...
```

`db.sqlite3` и `media/` (загруженные файлы документов) — не в git, это данные, не код (см. `.gitignore`). Схема воссоздаётся миграциями (`content/migrations/`, которые в git) на новой базе через `manage.py migrate`.

## Восстановить с нуля (новая машина / потеряли venv)

```bash
cd backend
python -m venv venv
./venv/Scripts/pip.exe install -r requirements.txt
./venv/Scripts/python.exe manage.py migrate
DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=admin@psa.local DJANGO_SUPERUSER_PASSWORD="НОВЫЙ_ПАРОЛЬ" ./venv/Scripts/python.exe manage.py createsuperuser --noinput
./venv/Scripts/python.exe seed.py   # опционально, тестовые записи для проверки
```
