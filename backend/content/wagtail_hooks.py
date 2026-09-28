from django.templatetags.static import static
from django.urls import path
from django.utils.html import format_html
from wagtail import hooks
from wagtail.admin.action_menu import ActionMenuItem
from wagtail.admin.ui.menus.pages import PageMenuItem

from .archive_transfer import archive_transfer, get_transfer, transfer_url


@hooks.register("register_admin_urls")
def register_archive_transfer_url():
    return [
        path("archive-transfer/<int:page_id>/", archive_transfer, name="archive_transfer"),
    ]


class ArchiveTransferMenuItem(PageMenuItem):
    """«Перенести в архив» / «Вернуть в объявления» («… в предстоящие» —
    в «Маркетинге») — в меню «…» страницы (список страниц и заголовок редактора)."""

    icon_name = "arrow-right-full"
    priority = 11  # сразу после штатного «Переместить»

    def __init__(self, *, page, next_url=None, user=None):
        super().__init__(page=page, next_url=next_url)
        self.transfer = get_transfer(page, user)
        if self.transfer:
            self.label = self.transfer[1]

    def is_shown(self, user):
        return self.transfer is not None

    @property
    def url(self):
        return transfer_url(self.page, self.next_url)


@hooks.register("register_page_listing_more_buttons")
def archive_transfer_listing_button(page, user, next_url=None):
    yield ArchiveTransferMenuItem(page=page, next_url=next_url, user=user)


@hooks.register("register_page_header_buttons")
def archive_transfer_header_button(page, user, view_name, next_url=None):
    yield ArchiveTransferMenuItem(page=page, next_url=next_url, user=user)


class ArchiveTransferActionMenuItem(ActionMenuItem):
    """Тот же пункт в меню публикации внизу редактора записи."""

    order = 45
    icon_name = "arrow-right-full"
    name = "action-archive-transfer"

    def _transfer(self, context):
        if context.get("view") != "edit":
            return None
        return get_transfer(context["page"], context["request"].user)

    def is_shown(self, context):
        return super().is_shown(context) and self._transfer(context) is not None

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["label"] = self._transfer(parent_context)[1]
        return context

    def get_url(self, parent_context):
        page = parent_context["page"]
        return transfer_url(page, parent_context["request"].get_full_path())


@hooks.register("register_page_action_menu_item")
def register_archive_transfer_action():
    return ArchiveTransferActionMenuItem()


# Оформление админки в стиле сайта: шрифты PT (как на сайте) и static/psa-admin.css.
@hooks.register("insert_global_admin_css")
def psa_admin_css():
    return format_html(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=PT+Serif:wght@400;700&family=PT+Sans:wght@400;700&family=PT+Mono&display=swap">'
        '<link rel="stylesheet" href="{}">',
        static("psa-admin.css"),
    )
