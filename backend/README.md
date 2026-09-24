# Бэкенд на Django (локальный запуск)

SQLite внутри (файл `db.sqlite3`, создаётся `migrate`), всё поставлено в venv — ничего не устанавливалось глобально.

## Запуск

```bash
cd backend
./venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
```

Это и есть весь сайт — 5 страниц, все на http://127.0.0.1:8000/:

| URL | Шаблон | Содержимое |
|---|---|---|
| `/` | `index.html` | Header, Hero, О компании, Проекты, Партнёры, Контакты |
| `/local-content/` | `local_content.html` | Местное содержание — контент из БД |
| `/procurement/` | `procurement.html` | Закупки — контент из БД |
| `/documents/` | `documents.html` | Документы — контент из БД |
| `/news/` | `news.html` | Новости — контент из БД |

Все 5 расширяют `templates/base.html` (общая шапка/меню/подвал/модалка проектов) — правки шапки теперь в одном месте, а не в каждом файле. Отдельного статик-сервера для фронтенда нет — шаблоны рендерит Django, `static/styles.css`/`static/script.js` отдаёт `django.contrib.staticfiles`.

## Админка

http://127.0.0.1:8000/admin/

- Логин: `admin`
- Пароль: `PsaLocalDev2026!`

**Сменить пароль перед любым реальным использованием** (в самой админке, раздел «Пользователи», или `manage.py changepassword admin`).

## Как отображается контент 4 разделов

У каждого раздела своя вьюха (`content.views.local_content_page` и т.п.) и свой URL — читает модель из БД, передаёт queryset в свой шаблон, который рендерит его через `{% for %}` (Django сам экранирует значения — безопасно от XSS, без ручной работы с DOM, как было в JS-версии). Добавили запись в `/admin/` — она сразу появится на сайте при следующей загрузке соответствующей страницы, без пересборки и без API-запроса из браузера. Главная страница (`home`) сама по себе к БД не обращается — там только статичный контент.

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
├── templates/
│   ├── base.html          — общая шапка/меню/подвал/модалка проектов
│   ├── index.html         — главная (extends base)
│   ├── local_content.html, procurement.html, documents.html, news.html — extends base
├── static/
│   ├── styles.css        — стили (без изменений от прежней статик-версии)
│   └── script.js         — мобильное меню, модалки проектов, i18n, форма, path-aware плавный скролл
├── psa_backend/          — настройки, TEMPLATES/STATICFILES_DIRS, корневые urls (5 путей на 5 вьюх)
└── content/              — приложение: модели, вьюхи страниц, админка, API
    ├── models.py         — LocalContentEntry, ProcurementEntry, DocumentEntry, NewsEntry
    ├── views.py            — home() + 4 вьюхи разделов (рендер шаблонов); + ReadOnlyModelViewSet'ы для /api/
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
