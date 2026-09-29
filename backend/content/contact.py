"""Форма «Контакты» на главной: POST /contact/.

Обращение всегда сохраняется в базе (админка → «Обращения»), затем уходит письмо на
адреса из «Настройки» → «Форма «Контакты»» (через SMTP из «Настройки» → «Почта»).
Если письмо не ушло, обращение всё равно сохранено, а ошибка записана в него —
посетителю показывается «Отправлено», сотрудники увидят обращение в админке.

Защита от спама: скрытое поле-ловушка (боты его заполняют) и не больше
RATE_LIMIT обращений с одного IP за RATE_WINDOW.
Ответ — JSON для скрипта на странице (static/script.js); без JavaScript форма
отправляется обычным POST и возвращает на главную.
"""
import logging
from datetime import timedelta

from django import forms
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .mail import explain_error
from .models import BASE_LANG, LANGUAGES, ContactFormSettings, ContactMessage

logger = logging.getLogger(__name__)

RATE_LIMIT = 5
RATE_WINDOW = timedelta(minutes=10)
HONEYPOT_FIELD = "website"


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]

    def clean(self):
        cleaned = super().clean()
        for field in ("name", "message"):
            if field in cleaned and not cleaned[field].strip():
                self.add_error(field, "Обязательное поле.")
        return cleaned


def client_ip(request):
    # За Caddy адрес посетителя — в X-Forwarded-For (Caddy заменяет присланное клиентом).
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded.split(",")[0].strip() or request.META.get("REMOTE_ADDR") or None


def notify(entry):
    """Письмо о новом обращении. Ошибку не пробрасываем — запоминаем в обращении."""
    config = ContactFormSettings.load()
    recipients = config.recipient_list
    if not recipients:
        entry.email_error = "Адреса получателей не указаны (Настройки → Форма «Контакты»)."
        return
    admin_url = settings.WAGTAILADMIN_BASE_URL.rstrip("/") + reverse("contact_messages:edit", args=[entry.pk])
    language = dict(LANGUAGES).get(entry.language, entry.language or "—")
    body = (
        "Новое обращение с сайта (форма «Контакты»).\n\n"
        f"Имя: {entry.name}\n"
        f"E-mail: {entry.email}\n"
        f"Язык сайта: {language}\n"
        f"Получено: {timezone.localtime(entry.created_at):%d.%m.%Y %H:%M}\n\n"
        f"Сообщение:\n{entry.message}\n\n"
        f"Обращение в админке: {admin_url}\n"
        "Чтобы ответить, нажмите «Ответить» — письмо уйдёт отправителю обращения."
    )
    try:
        EmailMessage(config.subject, body, to=recipients, reply_to=[entry.email]).send()
    except Exception as error:  # noqa: BLE001 — любая ошибка SMTP не должна терять обращение
        logger.exception("Письмо об обращении #%s не отправлено", entry.pk)
        entry.email_error = explain_error(error)
    else:
        entry.email_sent = True
        entry.email_error = ""


@require_POST
def contact_submit(request):
    wants_json = request.headers.get("X-Requested-With") == "fetch"

    def reply(status, **data):
        if wants_json:
            return JsonResponse({"ok": status == 200, **data}, status=status)
        return redirect("/?contact=" + ("sent" if status == 200 else "error") + "#contacts")

    # Бот заполнил скрытое поле — делаем вид, что всё хорошо, ничего не сохраняем.
    if request.POST.get(HONEYPOT_FIELD):
        return reply(200)

    ip = client_ip(request)
    if ip and ContactMessage.objects.filter(ip_address=ip, created_at__gte=timezone.now() - RATE_WINDOW).count() >= RATE_LIMIT:
        return reply(429, error="too_many")

    form = ContactForm(request.POST)
    if not form.is_valid():
        return reply(400, error="invalid", fields=sorted(form.errors))

    entry = form.save(commit=False)
    entry.ip_address = ip
    lang = request.POST.get("language", "")
    entry.language = lang if lang in dict(LANGUAGES) else BASE_LANG
    entry.save()
    notify(entry)
    entry.save(update_fields=["email_sent", "email_error"])
    return reply(200)
