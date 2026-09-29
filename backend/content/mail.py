"""Отправка почты с настройками из админки («Настройки» → «Почта (SMTP)»).

SiteEmailBackend подключён в settings.MAILERS: при каждой отправке читает
EmailSettings и передаёт письма стандартному SMTP-бэкенду Django. Если SMTP-сервер
в админке не указан — письма выводятся в лог сервера (консольный бэкенд), чтобы
их можно было увидеть при отладке.

email_test — страница админки «Отправить тестовое письмо».
"""
import logging
import smtplib
import ssl
from email.utils import formataddr

from django.conf import settings
from django.contrib import messages
from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.core.validators import validate_email
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from .models import EmailSettings

logger = logging.getLogger(__name__)

SMTP_TIMEOUT = 20  # секунд — чтобы недоступный сервер не подвешивал отправку формы


def sender_address(config):
    """«Имя <адрес>» отправителя из настроек, иначе DEFAULT_FROM_EMAIL."""
    address = config.from_email or config.username
    if not address:
        return settings.DEFAULT_FROM_EMAIL
    return formataddr((config.from_name, address)) if config.from_name else address


class InsecureSMTPBackend(SMTPBackend):
    """SMTP с шифрованием, но без проверки сертификата — для самоподписанного
    сертификата внутреннего сервера (Exchange). Включается снятием галочки
    «Проверять сертификат сервера»."""

    @property
    def ssl_context(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context


def explain_error(error):
    """Текст ошибки SMTP + подсказка, что поправить в настройках."""
    text = str(error)
    if isinstance(error, ssl.SSLCertVerificationError):
        hint = ("У сервера самоподписанный или чужой сертификат. Если это сервер вашей организации "
                "(например, Exchange), снимите галочку «Проверять сертификат сервера».")
    elif isinstance(error, ssl.SSLError) and "WRONG_VERSION_NUMBER" in text:
        hint = "Сервер на этом порту не работает по SSL — выберите «STARTTLS» (порт 587) или проверьте порт."
    elif isinstance(error, smtplib.SMTPException) and "No suitable authentication method" in text:
        hint = ("Сервер не предлагает вход по логину и паролю без шифрования — выберите «STARTTLS» "
                "(Exchange до шифрования разрешает только вход Windows — NTLM, его сайт не поддерживает).")
    elif isinstance(error, smtplib.SMTPNotSupportedError):
        hint = "Сервер не поддерживает выбранное шифрование или вход — проверьте «Шифрование» и порт."
    elif isinstance(error, smtplib.SMTPAuthenticationError):
        hint = ("Сервер отклонил логин или пароль. Проверьте пароль; для Exchange попробуйте логин в виде "
                "адреса почты, ДОМЕН\\логин или логин@домен.local. Если не помогает — у администратора "
                "почты: разрешён ли вход по паролю (Basic/LOGIN) для этого ящика и коннектора.")
    elif isinstance(error, (smtplib.SMTPSenderRefused, smtplib.SMTPDataError)) and "5.7.60" in text:
        hint = "Сервер не разрешает отправлять от этого адреса — «Адрес отправителя» должен совпадать с ящиком логина."
    elif isinstance(error, smtplib.SMTPRecipientsRefused) and "5.7.54" in text:
        hint = "Сервер не пересылает письма на внешние адреса без входа — укажите логин и пароль."
    elif isinstance(error, (TimeoutError, ConnectionRefusedError, OSError)) and not isinstance(error, smtplib.SMTPException):
        hint = "Нет соединения с сервером — проверьте адрес и порт и что сервер доступен из сети, где работает сайт."
    else:
        return text
    return f"{text} — {hint}"


class SiteEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        config = EmailSettings.load()
        if config.host:
            backend_class = SMTPBackend if config.verify_certificate else InsecureSMTPBackend
            backend = backend_class(
                alias=self.alias,
                host=config.host,
                port=config.port,
                username=config.username,
                password=config.password,
                use_tls=config.security == "tls",
                use_ssl=config.security == "ssl",
                timeout=SMTP_TIMEOUT,
                fail_silently=self.fail_silently,
            )
            sender = sender_address(config)
            for message in email_messages:
                # Письма без явного отправителя (from_email не задан) — от имени из настроек.
                if message.from_email == settings.DEFAULT_FROM_EMAIL:
                    message.from_email = sender
        else:
            logger.warning("SMTP-сервер не настроен (админка → Настройки → Почта) — письмо только выведено в лог.")
            backend = ConsoleBackend(alias=self.alias, fail_silently=self.fail_silently)
        return backend.send_messages(email_messages)


def email_test(request):
    """Тестовое письмо с текущими настройками — показывает ответ сервера при ошибке."""
    if not request.user.has_perm("content.change_emailsettings"):
        raise PermissionDenied
    config = EmailSettings.load()
    settings_url = reverse("wagtailsettings:edit", args=["content", "emailsettings"])
    to = (request.POST.get("to") or request.user.email or "").strip()

    if request.method == "POST":
        try:
            validate_email(to)
        except ValidationError:
            messages.error(request, "Укажите адрес, на который отправить тестовое письмо.")
        else:
            if not config.host:
                messages.error(request, "SMTP-сервер не указан — письмо не уйдёт. Заполните настройки почты и сохраните их.")
            else:
                try:
                    mail.send_mail(
                        "Тестовое письмо с сайта PSA",
                        "Это тестовое письмо: настройки почты сайта работают.\n\n"
                        f"Сервер: {config.host}:{config.port}, отправитель: {sender_address(config)}.",
                        None,
                        [to],
                    )
                except Exception as error:  # noqa: BLE001 — показываем пользователю любой ответ сервера
                    logger.warning("Тестовое письмо не отправлено: %s", error)
                    messages.error(request, f"Письмо не отправлено: {explain_error(error)}")
                else:
                    messages.success(request, f"Тестовое письмо отправлено на {to}. Проверьте почту (и папку «Спам»).")
                    return redirect(settings_url)

    return TemplateResponse(request, "admin/email_test.html", {
        "config": config,
        "to": to,
        "settings_url": settings_url,
    })
