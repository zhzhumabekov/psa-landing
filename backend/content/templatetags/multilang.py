"""Вывод переводимых полей страниц: все заполненные языковые варианты сразу.

Разметка группы:
    <span data-ml>
      <span data-ml-lang="ru">…</span>
      <span data-ml-lang="kz" hidden>…</span>
    </span>
Какой вариант показать, решает переключатель языка на клиенте
(applyContentLanguage в static/script.js); незаполненные переводы в группу
не попадают — тогда показывается русский.
"""
from django import template
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

from content.blocks import text_preview
from content.models import BASE_LANG, LANGUAGES

register = template.Library()

LANG_CODES = [code for code, _ in LANGUAGES]

MONTHS = {
    "ru": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"],
    "kz": ["қаңтар", "ақпан", "наурыз", "сәуір", "мамыр", "маусым", "шілде", "тамыз", "қыркүйек", "қазан", "қараша", "желтоқсан"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
}
DATE_FORMATS = {
    "ru": "{d} {m} {y} г.",
    "kz": "{d} {m} {y} ж.",
    "en": "{d} {m} {y}",
}
# Приставки к дате: {% ml_date value "<вид>" %}. Сейчас не используются
# (срок подачи у закупок убран), механизм оставлен.
DATE_PREFIXES = {}


def _group(tag, values):
    """values: [(lang, html)] — пустые варианты (кроме русского) пропускаются,
    если пусто всё — пустая строка (шаблон сам решает, выводить ли обёртку)."""
    if not any(html for _, html in values):
        return ""
    items = [(lang, html) for lang, html in values if lang == BASE_LANG or html]
    return format_html(
        "<{} data-ml>{}</{}>",
        tag,
        format_html_join(
            "",
            "<" + tag + ' data-ml-lang="{}"{}>{}</' + tag + ">",
            ((lang, "" if lang == BASE_LANG else " hidden", html) for lang, html in items),
        ),
        tag,
    )


@register.simple_tag
def ml(page, field):
    """Строковое поле (заголовок, категория…) — inline."""
    return _group("span", [(lang, page.get_translated(field, lang)) for lang in LANG_CODES])


@register.simple_tag(takes_context=True)
def ml_blocks(context, page, field):
    """StreamField (основной текст) — блочные варианты."""
    values = []
    for lang in LANG_CODES:
        stream = page.get_translated(field, lang)
        values.append((lang, stream.render_as_block(context=context.flatten()) if stream else ""))
    return _group("div", values)


@register.simple_tag
def ml_preview(page, words=25, only_lang=None):
    """Превью для списков: краткое описание (если есть у модели и заполнено)
    или начало основного текста без таблиц. only_lang — один язык без
    обёртки (для <meta description>)."""
    values = []
    for lang in [only_lang] if only_lang else LANG_CODES:
        excerpt = page.get_translated("excerpt", lang) if "excerpt" in page.translated_fields else ""
        if excerpt:
            html = format_html("<p>{}</p>", excerpt)
        else:
            preview = text_preview(page.get_translated(page.preview_source, lang))
            html = mark_safe(Truncator(preview).words(words, html=True))
        values.append((lang, html))
    if only_lang:
        return values[0][1]
    return _group("div", values)


@register.simple_tag
def ml_date(value, kind=""):
    if not value:
        return ""
    values = []
    for lang in LANG_CODES:
        text = DATE_FORMATS[lang].format(d=f"{value.day:02d}", m=MONTHS[lang][value.month - 1], y=value.year)
        if kind:
            text = DATE_PREFIXES[kind][lang].format(text)
        values.append((lang, text))
    return _group("span", values)
