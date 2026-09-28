from django import template

from content.models import ProjectPage

register = template.Library()


# Пункты выпадающего меню «Проекты» в base.html — опубликованные страницы
# раздела «Проекты», в порядке дерева страниц.
@register.simple_tag
def menu_projects():
    return ProjectPage.objects.live().order_by("path")
