import markdown
from bs4 import BeautifulSoup
from django.utils.safestring import mark_safe
from wagtail import blocks
from wagtail.contrib.table_block.blocks import TableBlock

TABLE_OPTIONS = {
    "startRows": 3,
    "startCols": 3,
    "height": 216,
    "mergeCells": True,
    "contextMenu": [
        "row_above",
        "row_below",
        "---------",
        "col_left",
        "col_right",
        "---------",
        "remove_row",
        "remove_col",
        "---------",
        "mergeCells",
        "alignment",
        "---------",
        "undo",
        "redo",
    ],
}


class MarkdownBlock(blocks.TextBlock):
    """Markdown → HTML при выводе на сайт. Таблицы — синтаксисом `| a | b |`.

    Сырой HTML внутри Markdown тоже пропускается (как и у HTMLBlock) —
    писать сюда может только пользователь админки.
    """

    def render_basic(self, value, context=None):
        return mark_safe(markdown.markdown(value or "", extensions=["tables", "fenced_code", "sane_lists"]))

    class Meta:
        icon = "code"
        label = "Markdown"
        rows = 10
        help_text = "Заголовки: ## Заголовок. Жирный: **текст**. Список: - пункт. Таблица: строки вида | Колонка 1 | Колонка 2 |, под шапкой | --- | --- |."


# Блоки основного текста страниц (body/description). Порядок — как в меню
# «+» в редакторе.
class ContentBlocks(blocks.StreamBlock):
    text = blocks.RichTextBlock(label="Текст", icon="pilcrow")
    table = TableBlock(label="Таблица", table_options=TABLE_OPTIONS)
    markdown = MarkdownBlock()
    html = blocks.RawHTMLBlock(
        label="HTML",
        help_text="Вставляется на страницу как есть, без проверки — только для доверенного кода.",
    )

    class Meta:
        # Каждый блок в обёртке .content-block--<тип> (таблицы прокручиваются по горизонтали).
        template = "blocks/content_blocks.html"


# Блоки, из которых берётся короткое превью в списках разделов. Таблицы
# (и отдельные блоки, и внутри Markdown) и сырой HTML в обрезанном виде
# выглядели бы сломанными — их в превью нет.
PREVIEW_BLOCK_TYPES = ("text", "markdown")


def text_preview(stream_value):
    html = "".join(str(block.render()) for block in stream_value if block.block_type in PREVIEW_BLOCK_TYPES)
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        table.decompose()
    return mark_safe(str(soup))


# Телефон в подвале сайта: номер (ссылка tel:) + пояснение на трёх языках.
class PhoneBlock(blocks.StructBlock):
    number = blocks.CharBlock(label="Номер", help_text="Например: +7 7172 79 89 20")
    note = blocks.CharBlock(label="Пояснение", required=False, help_text="Например: Канцелярия")
    note_kz = blocks.CharBlock(label="Пояснение (қазақша)", required=False)
    note_en = blocks.CharBlock(label="Пояснение (English)", required=False)

    class Meta:
        icon = "mobile-alt"
        label = "Телефон"

