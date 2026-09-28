from django.templatetags.static import static
from django.urls import path, reverse
from django.utils.html import format_html
from wagtail import hooks
from wagtail.admin.action_menu import ActionMenuItem
from wagtail.admin.menu import MenuItem
from wagtail.admin.panels import FieldPanel
from wagtail.admin.ui.menus.pages import PageMenuItem
from wagtail.admin.ui.tables import BooleanColumn, Column, DateColumn
from wagtail.admin.views import generic
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.permissions import register_permission_policy

from . import backup_views
from .archive_transfer import archive_transfer, get_transfer, transfer_url
from .mail import email_test
from .models import ContactMessage


@hooks.register("register_admin_urls")
def register_archive_transfer_url():
    return [
        path("archive-transfer/<int:page_id>/", archive_transfer, name="archive_transfer"),
        path("email-test/", email_test, name="email_test"),
        path("backups/", backup_views.backups_index, name="backups_index"),
        path("backups/create/", backup_views.backup_create, name="backups_create"),
        path("backups/upload/", backup_views.backup_upload, name="backups_upload"),
        path("backups/<str:name>/download/", backup_views.backup_download, name="backups_download"),
        path("backups/<str:name>/restore/", backup_views.backup_restore, name="backups_restore"),
        path("backups/<str:name>/delete/", backup_views.backup_delete, name="backups_delete"),
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


# ---------- «Обращения» — записи формы «Контакты» (content/contact.py) ----------

class ContactMessagePermissionPolicy(ModelPermissionPolicy):
    """Обращения приходят только с сайта — вручную их не создают (нет кнопки «Добавить»)."""

    def user_has_permission(self, user, action):
        return action != "add" and super().user_has_permission(user, action)

    def users_with_any_permission(self, actions):
        return super().users_with_any_permission([a for a in actions if a != "add"])


register_permission_policy(ContactMessage, ContactMessagePermissionPolicy(ContactMessage))


class ContactMessageEditView(generic.EditView):
    """Открыли обращение — оно считается прочитанным (галочку можно снять)."""

    def get_object(self, queryset=None):
        entry = super().get_object(queryset)
        if self.request.method == "GET" and not entry.is_read:
            ContactMessage.objects.filter(pk=entry.pk).update(is_read=True)
            entry.is_read = True
        return entry


class ContactMessageViewSet(ModelViewSet):
    model = ContactMessage
    name = "contact_messages"
    url_prefix = "contact-messages"
    icon = "mail"
    menu_label = "Обращения"
    menu_order = 150
    add_to_admin_menu = True
    copy_view_enabled = False
    edit_view_class = ContactMessageEditView
    list_display = [
        "name",
        Column("email", label="E-mail"),
        DateColumn("created_at", label="Получено"),
        BooleanColumn("is_read", label="Прочитано"),
        BooleanColumn("email_sent", label="Письмо отправлено"),
    ]
    list_filter = ["is_read", "email_sent", "created_at"]
    search_fields = ["name", "email", "message"]
    panels = [
        FieldPanel("name", read_only=True),
        FieldPanel("email", read_only=True),
        FieldPanel("message", read_only=True),
        FieldPanel("created_at", read_only=True),
        FieldPanel("language", read_only=True),
        FieldPanel("ip_address", read_only=True),
        FieldPanel("email_sent", read_only=True),
        FieldPanel("email_error", read_only=True),
        FieldPanel("is_read"),
    ]


@hooks.register("register_admin_viewset")
def register_contact_messages():
    return ContactMessageViewSet()


# ---------- «Настройки» → «Резервные копии» (content/backup_views.py) ----------

class SuperuserMenuItem(MenuItem):
    def is_shown(self, request):
        return request.user.is_superuser


@hooks.register("register_settings_menu_item")
def register_backups_menu_item():
    return SuperuserMenuItem("Резервные копии", reverse("backups_index"), icon_name="download", order=900)
