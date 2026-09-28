from django.db import models
from wagtail.admin.panels import FieldPanel, ObjectList, TabbedInterface
from wagtail.fields import StreamField
from wagtail.models import Page

from .blocks import ContentBlocks

# Языки контента. Русский — основной (штатные поля Wagtail: title и т.д.),
# для kz/en у переводимых полей есть копии с суффиксом: title_kz, body_en...
# Пустой перевод на сайте подменяется русским (см. templatetags/multilang.py).
BASE_LANG = "ru"
LANGUAGES = [("ru", "Русский"), ("kz", "Қазақша"), ("en", "English")]
TRANSLATION_LANGS = [code for code, _ in LANGUAGES if code != BASE_LANG]


class TranslatedPage(Page):
    """Страница с переводами: в админке вкладки «Русский / Қазақша / English».

    Наследник задаёт translated_fields — имена полей, у которых есть копии
    <поле>_kz и <поле>_en (сами поля объявляются в модели явно).
    """

    translated_fields = ()

    class Meta:
        abstract = True

    def get_translated(self, field, lang):
        if lang == BASE_LANG:
            return getattr(self, field)
        return getattr(self, f"{field}_{lang}")

    @classmethod
    def build_edit_handler(cls):
        tabs = [ObjectList(cls.content_panels, heading="Русский")]
        for code, name in LANGUAGES:
            if code != BASE_LANG:
                tabs.append(ObjectList([FieldPanel(f"{f}_{code}") for f in cls.translated_fields], heading=name))
        tabs.append(ObjectList(cls.promote_panels, heading="Продвижение"))
        if cls.settings_panels:
            tabs.append(ObjectList(cls.settings_panels, heading="Настройки"))
        return TabbedInterface(tabs)


def title_translation(lang_name):
    return models.CharField(f"Заголовок ({lang_name})", max_length=255, blank=True)


def body_translation(verbose_name, lang_name):
    return StreamField(ContentBlocks(), verbose_name=f"{verbose_name} ({lang_name})", blank=True)


# Главная: Hero/О компании/Проекты/Партнёры/Контакты — статичный контент
# в шаблоне (переводы на kz/ru/en — в static/script.js), в БД только сама
# страница как корень дерева.
class HomePage(Page):
    template = "index.html"
    max_count = 1
    subpage_types = [
        "content.LocalContentIndexPage",
        "content.ProcurementIndexPage",
        "content.DocumentsIndexPage",
        "content.NewsIndexPage",
    ]

    class Meta:
        verbose_name = "Главная страница"


# Разделы: у каждого страница-список (индекс) и страницы-записи под ней.
# Заголовки/подводки списков — в шаблонах (data-i18n), не в БД.
class SectionIndexPage(Page):
    max_count = 1
    parent_page_types = ["content.HomePage"]
    entry_model = None
    entry_ordering = ()

    class Meta:
        abstract = True

    def get_entries(self):
        return self.entry_model.objects.child_of(self).live().order_by(*self.entry_ordering)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["entries"] = self.get_entries()
        return context


class LocalContentPage(TranslatedPage):
    date = models.DateField("Дата")
    body = StreamField(ContentBlocks(), verbose_name="Текст")

    title_kz = title_translation("қазақша")
    body_kz = body_translation("Текст", "қазақша")
    title_en = title_translation("English")
    body_en = body_translation("Текст", "English")
    translated_fields = ("title", "body")

    template = "local_content_detail.html"
    parent_page_types = ["content.LocalContentIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = "Материал: местное содержание"
        verbose_name_plural = "Местное содержание — материалы"

    preview_source = "body"


class LocalContentIndexPage(SectionIndexPage):
    template = "local_content.html"
    subpage_types = ["content.LocalContentPage"]
    entry_model = LocalContentPage
    entry_ordering = ("-date",)

    class Meta:
        verbose_name = "Раздел «Местное содержание»"


class ProcurementPage(TranslatedPage):
    STATUS_OPEN = "Открыт"
    STATUS_CLOSED = "Завершён"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Открыт"),
        (STATUS_CLOSED, "Завершён"),
    ]

    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    deadline = models.DateField("Срок подачи", null=True, blank=True)
    description = StreamField(ContentBlocks(), verbose_name="Описание", blank=True)
    url = models.URLField("Ссылка (тендерная площадка/файл)", blank=True)

    title_kz = title_translation("қазақша")
    description_kz = body_translation("Описание", "қазақша")
    title_en = title_translation("English")
    description_en = body_translation("Описание", "English")
    translated_fields = ("title", "description")

    template = "procurement_detail.html"
    parent_page_types = ["content.ProcurementIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel("status"),
        FieldPanel("deadline"),
        FieldPanel("description"),
        FieldPanel("url"),
    ]

    class Meta:
        verbose_name = "Закупка"
        verbose_name_plural = "Закупки"

    preview_source = "description"

    @property
    def is_closed(self):
        return self.status == self.STATUS_CLOSED


class ProcurementIndexPage(SectionIndexPage):
    template = "procurement.html"
    subpage_types = ["content.ProcurementPage"]
    entry_model = ProcurementPage
    entry_ordering = ("-deadline",)

    class Meta:
        verbose_name = "Раздел «Закупки»"


class DocumentPage(TranslatedPage):
    category = models.CharField("Категория", max_length=100, blank=True)
    date = models.DateField("Дата", null=True, blank=True)
    document = models.ForeignKey(
        "wagtaildocs.Document",
        verbose_name="Файл",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    url = models.URLField("Ссылка (если файл не загружен)", blank=True)

    title_kz = title_translation("қазақша")
    category_kz = models.CharField("Категория (қазақша)", max_length=100, blank=True)
    title_en = title_translation("English")
    category_en = models.CharField("Категория (English)", max_length=100, blank=True)
    translated_fields = ("title", "category")

    template = "document_detail.html"
    parent_page_types = ["content.DocumentsIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel("category"),
        FieldPanel("date"),
        FieldPanel("document"),
        FieldPanel("url"),
    ]

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"

    @property
    def file_url(self):
        if self.document:
            return self.document.url
        return self.url


class DocumentsIndexPage(SectionIndexPage):
    template = "documents.html"
    subpage_types = ["content.DocumentPage"]
    entry_model = DocumentPage
    entry_ordering = ("-date",)

    class Meta:
        verbose_name = "Раздел «Документы»"


class NewsPage(TranslatedPage):
    date = models.DateField("Дата")
    excerpt = models.CharField("Краткое описание", max_length=400, blank=True)
    body = StreamField(ContentBlocks(), verbose_name="Текст новости", blank=True)

    title_kz = title_translation("қазақша")
    excerpt_kz = models.CharField("Краткое описание (қазақша)", max_length=400, blank=True)
    body_kz = body_translation("Текст новости", "қазақша")
    title_en = title_translation("English")
    excerpt_en = models.CharField("Краткое описание (English)", max_length=400, blank=True)
    body_en = body_translation("Текст новости", "English")
    translated_fields = ("title", "excerpt", "body")

    template = "news_detail.html"
    parent_page_types = ["content.NewsIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("excerpt"),
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"

    preview_source = "body"


class NewsIndexPage(SectionIndexPage):
    template = "news.html"
    subpage_types = ["content.NewsPage"]
    entry_model = NewsPage
    entry_ordering = ("-date",)

    class Meta:
        verbose_name = "Раздел «Новости»"


for _model in (LocalContentPage, ProcurementPage, DocumentPage, NewsPage):
    _model.edit_handler = _model.build_edit_handler()
