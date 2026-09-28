from django.core.paginator import Paginator
from django.db import models
from wagtail.admin.panels import FieldPanel, ObjectList, TabbedInterface
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.fields import StreamField
from wagtail.models import Page

from wagtail.contrib.settings.models import BaseSiteSetting, register_setting

from .blocks import ContentBlocks, PhoneBlock

# Языки контента. Русский — основной (штатные поля Wagtail: title и т.д.),
# для kz/en у переводимых полей есть копии с суффиксом: title_kz, body_en...
# Пустой перевод на сайте подменяется русским (см. templatetags/multilang.py).
BASE_LANG = "ru"
LANGUAGES = [("ru", "Русский"), ("kz", "Қазақша"), ("en", "English")]
TRANSLATION_LANGS = [code for code, _ in LANGUAGES if code != BASE_LANG]


class TranslatedFieldsMixin:
    """Значение поля на языке: <поле> — русский, <поле>_kz / <поле>_en — переводы."""

    translated_fields = ()

    def get_translated(self, field, lang):
        if lang == BASE_LANG:
            return getattr(self, field)
        return getattr(self, f"{field}_{lang}")


class TranslatedPage(TranslatedFieldsMixin, Page):
    """Страница с переводами: в админке вкладки «Русский / Қазақша / English».

    Наследник задаёт translated_fields — имена полей, у которых есть копии
    <поле>_kz и <поле>_en (сами поля объявляются в модели явно).
    """

    class Meta:
        abstract = True

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
# страница как корень дерева. Блок «Проекты» на главной (карточки + модалки)
# тоже статичный — отдельно от раздела «Проекты» (ProjectsIndexPage).
class HomePage(Page):
    template = "index.html"
    max_count = 1
    subpage_types = [
        "content.ProjectsIndexPage",
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


class ProjectPage(TranslatedPage):
    region = models.CharField("Регион", max_length=100, blank=True)
    teaser = models.CharField("Кратко (для карточки)", max_length=300, blank=True)
    body = StreamField(ContentBlocks(), verbose_name="Описание проекта", blank=True)

    title_kz = title_translation("қазақша")
    region_kz = models.CharField("Регион (қазақша)", max_length=100, blank=True)
    teaser_kz = models.CharField("Кратко (қазақша)", max_length=300, blank=True)
    body_kz = body_translation("Описание проекта", "қазақша")
    title_en = title_translation("English")
    region_en = models.CharField("Регион (English)", max_length=100, blank=True)
    teaser_en = models.CharField("Кратко (English)", max_length=300, blank=True)
    body_en = body_translation("Описание проекта", "English")
    translated_fields = ("title", "region", "teaser", "body")

    template = "project_detail.html"
    parent_page_types = ["content.ProjectsIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel("region"),
        FieldPanel("teaser"),
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"

    preview_source = "body"


# Порядок проектов — как в дереве страниц (перетаскиванием в админке),
# а не по дате: дат у проектов нет.
class ProjectsIndexPage(SectionIndexPage):
    template = "projects.html"
    subpage_types = ["content.ProjectPage"]
    entry_model = ProjectPage
    entry_ordering = ("path",)

    class Meta:
        verbose_name = "Раздел «Проекты»"


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
    """Запись раздела «Закупки»: объявление, контактное лицо, план закупок…"""

    date = models.DateField("Дата", null=True, blank=True)
    description = StreamField(ContentBlocks(), verbose_name="Текст", blank=True)
    # Файлы общие для всех языков — во вкладках переводов их нет.
    attachments = StreamField(
        [("file", DocumentChooserBlock(label="Файл"))],
        verbose_name="Файлы",
        blank=True,
        help_text="Документы для скачивания (PDF, XLSX…) — из библиотеки «Документы» или загрузить новые.",
    )

    title_kz = title_translation("қазақша")
    description_kz = body_translation("Текст", "қазақша")
    title_en = title_translation("English")
    description_en = body_translation("Текст", "English")
    translated_fields = ("title", "description")

    template = "procurement_detail.html"
    parent_page_types = ["content.ProcurementSectionPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("description"),
        FieldPanel("attachments"),
    ]

    class Meta:
        verbose_name = "Закупки: запись"
        verbose_name_plural = "Закупки: записи"

    preview_source = "description"

    @property
    def files(self):
        return [block.value for block in self.attachments if block.value]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        section = self.get_parent().specific
        context.update(section.subnav_context())
        return context


# Подраздел «Закупок» (Объявления, Архив, Контактные лица, Особый порядок) —
# список записей с пагинацией, как на psa.kz/zakupki/.
class ProcurementSectionPage(TranslatedPage):
    PER_PAGE = 20

    translated_fields = ("title",)
    title_kz = title_translation("қазақша")
    title_en = title_translation("English")

    template = "procurement_section.html"
    parent_page_types = ["content.ProcurementIndexPage"]
    subpage_types = ["content.ProcurementPage"]

    class Meta:
        verbose_name = "Закупки: подраздел"
        verbose_name_plural = "Закупки: подразделы"

    def get_entries(self):
        # Сначала новые; записи без даты — в конце, в порядке дерева страниц.
        return (
            ProcurementPage.objects.child_of(self)
            .live()
            .order_by(models.F("date").desc(nulls_last=True), "path")
        )

    def subnav_context(self):
        # Вкладки-подразделы (как боковое меню на psa.kz/zakupki/).
        return {
            "procurement_sections": self.get_parent().specific.get_entries(),
            "current_section": self,
        }

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        paginator = Paginator(self.get_entries(), self.PER_PAGE)
        context["entries"] = paginator.get_page(request.GET.get("page"))
        context.update(self.subnav_context())
        return context


# «Закупки» — карточки подразделов (порядок — как в дереве страниц).
class ProcurementIndexPage(SectionIndexPage):
    template = "procurement.html"
    subpage_types = ["content.ProcurementSectionPage"]
    entry_model = ProcurementSectionPage
    entry_ordering = ("path",)

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
    external_url = models.URLField("Ссылка (если файл не загружен)", blank=True)

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
        FieldPanel("external_url"),
    ]

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"

    @property
    def file_url(self):
        if self.document:
            return self.document.url
        return self.external_url


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


for _model in (ProjectPage, LocalContentPage, ProcurementSectionPage, ProcurementPage, DocumentPage, NewsPage):
    _model.edit_handler = _model.build_edit_handler()


# Подвал сайта (templates/base.html) — «Настройки» → «Подвал сайта» в админке.
# Ссылки на разделы в подвале — те же, что в меню шапки, из шаблона.
@register_setting(icon="list-ul")
class FooterSettings(TranslatedFieldsMixin, BaseSiteSetting):
    org_name = models.CharField("Название организации", max_length=100, default="ТОО «PSA»")
    tagline = models.CharField("Подпись под названием", max_length=255, blank=True)
    address = models.TextField("Адрес", blank=True, help_text="Каждая строка — с новой строки.")
    phones = StreamField([("phone", PhoneBlock())], verbose_name="Телефоны", blank=True)
    email = models.EmailField("E-mail", blank=True)
    mail_url = models.URLField("Ссылка «Почта» (корпоративная почта)", blank=True)

    org_name_kz = models.CharField("Название организации (қазақша)", max_length=100, blank=True)
    tagline_kz = models.CharField("Подпись под названием (қазақша)", max_length=255, blank=True)
    address_kz = models.TextField("Адрес (қазақша)", blank=True)
    org_name_en = models.CharField("Название организации (English)", max_length=100, blank=True)
    tagline_en = models.CharField("Подпись под названием (English)", max_length=255, blank=True)
    address_en = models.TextField("Адрес (English)", blank=True)

    translated_fields = ("org_name", "tagline", "address")

    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel("org_name"),
            FieldPanel("tagline"),
            FieldPanel("address"),
            FieldPanel("phones", help_text="Пояснения к телефонам на казахском и английском — внутри каждого телефона."),
            FieldPanel("email"),
            FieldPanel("mail_url"),
        ], heading="Русский"),
        ObjectList([FieldPanel("org_name_kz"), FieldPanel("tagline_kz"), FieldPanel("address_kz")], heading="Қазақша"),
        ObjectList([FieldPanel("org_name_en"), FieldPanel("tagline_en"), FieldPanel("address_en")], heading="English"),
    ])

    class Meta:
        verbose_name = "Подвал сайта"

