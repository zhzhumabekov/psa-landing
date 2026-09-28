"""Перенос записи «Закупок» между подразделами «Объявления» ↔ «Архив».

Кнопки в админке — content/wagtail_hooks.py; сам перенос — штатное
перемещение страницы Wagtail (MovePageAction: права, журнал действий,
обновление адресов), без копирования.
"""
import re

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from wagtail.actions.move_page import MovePageAction
from wagtail.models import Page

from .models import ProcurementPage, ProcurementSectionPage

# slug подраздела-источника → (slug подраздела-назначения, текст кнопки)
TRANSFERS = {
    "announcements": ("archive", "Перенести в архив"),
    "archive": ("announcements", "Вернуть в объявления"),
}


def get_transfer(page, user=None):
    """(подраздел-назначение, текст кнопки) или None, если перенос для этой
    страницы не предусмотрен или у пользователя нет прав на перемещение."""
    if not issubclass(page.specific_class or Page, ProcurementPage):
        return None
    parent = page.get_parent()
    if parent is None or parent.slug not in TRANSFERS:
        return None
    target_slug, label = TRANSFERS[parent.slug]
    target = ProcurementSectionPage.objects.sibling_of(parent, inclusive=False).filter(slug=target_slug).first()
    if target is None:
        return None
    if user is not None and not page.permissions_for_user(user).can_move_to(target):
        return None
    return target, label


def transfer_url(page, next_url=None):
    url = reverse("procurement_transfer", args=[page.pk])
    if next_url:
        url += "?" + urlencode({"next": next_url})
    return url


def free_slug(page, target):
    """Slug, свободный среди записей подраздела-назначения. Числовой суффикс
    (-2, -3…), добавленный из-за совпадений, сначала снимается — так при
    переносе туда и обратно запись возвращается к прежнему адресу."""
    taken = set(target.get_children().exclude(pk=page.pk).values_list("slug", flat=True))
    base = re.sub(r"-\d+$", "", page.slug) or page.slug
    slug, n = base, 2
    while slug in taken:
        slug, n = f"{base}-{n}", n + 1
    return slug


def procurement_transfer(request, page_id):
    page = get_object_or_404(Page, pk=page_id).specific
    transfer = get_transfer(page)
    if transfer is None:
        raise Http404("Перенос для этой страницы не предусмотрен.")
    target, label = transfer
    if not page.permissions_for_user(request.user).can_move_to(target):
        raise PermissionDenied

    next_url = request.GET.get("next") or request.POST.get("next") or ""
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = ""

    if request.method == "POST":
        new_slug = free_slug(page, target)
        if new_slug != page.slug:
            # В назначении уже есть запись с таким адресом — меняем slug и у
            # опубликованной версии, и у последней ревизии (черновика).
            page.slug = new_slug
            page.set_url_path(page.get_parent())
            page.save(update_fields=["slug", "url_path"], clean=False)
            if page.latest_revision and "slug" in page.latest_revision.content:
                page.latest_revision.content["slug"] = new_slug
                page.latest_revision.save(update_fields=["content"])
        MovePageAction(page, target, pos="last-child", user=request.user).execute()
        messages.success(request, f"«{page.get_admin_display_title()}» — перенесено в «{target.title}».")
        return redirect(next_url or reverse("wagtailadmin_explore", args=[target.pk]))

    return TemplateResponse(request, "admin/procurement_transfer_confirm.html", {
        "page": page,
        "source": page.get_parent(),
        "target": target,
        "label": label,
        "next_url": next_url,
    })
