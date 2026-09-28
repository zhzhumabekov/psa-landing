from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

urlpatterns = [
    path('admin/', include(wagtailadmin_urls)),
    # Раздача файлов из библиотеки документов Wagtail. Не 'documents/' —
    # этот адрес занят страницей раздела «Документы».
    path('files/', include(wagtaildocs_urls)),
]

if settings.DEBUG:
    from content.error_views import error_preview

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Просмотр страниц ошибок (при DEBUG Django показывает вместо них отладочные).
    urlpatterns += [path('_errors/<int:code>/', error_preview)]

# Всё остальное — дерево страниц Wagtail (главная и разделы). Должно быть
# последним: ловит любые адреса.
urlpatterns += [
    path('', include(wagtail_urls)),
]
