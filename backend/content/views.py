from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import DocumentEntry, LocalContentEntry, NewsEntry, ProcurementEntry
from .serializers import (
    DocumentEntrySerializer,
    LocalContentEntrySerializer,
    NewsEntrySerializer,
    ProcurementEntrySerializer,
)


# Главная страница: Hero/О компании/Проекты/Партнёры/Контакты — статичный
# контент, без обращений к БД.
def home(request):
    return render(request, "index.html")


# Местное содержание/Закупки/Документы/Новости — отдельные страницы,
# каждая рендерит свою модель через шаблонизатор (не JS fetch).
def local_content_page(request):
    return render(request, "local_content.html", {"local_content_entries": LocalContentEntry.objects.all()})


# Отдельная страница на каждую запись «Местное содержание».
def local_content_detail(request, pk):
    entry = get_object_or_404(LocalContentEntry, pk=pk)
    return render(request, "local_content_detail.html", {"entry": entry})


def procurement_page(request):
    return render(request, "procurement.html", {"procurement_entries": ProcurementEntry.objects.all()})


def documents_page(request):
    return render(request, "documents.html", {"document_entries": DocumentEntry.objects.all()})


def news_page(request):
    return render(request, "news.html", {"news_entries": NewsEntry.objects.all()})


MAX_UPLOAD_IMAGE_SIZE = 8 * 1024 * 1024  # 8MB


# Загрузка картинок из редактора Quill (content/widgets.py). Доступно
# только сотрудникам (staff_member_required — та же проверка, что и у
# /admin/), не публичный эндпоинт: без этого кто угодно мог бы заливать
# произвольные файлы на сервер.
@staff_member_required
@require_POST
def quill_image_upload(request):
    file = request.FILES.get("image")
    if not file:
        return JsonResponse({"error": "Файл не передан."}, status=400)
    if not (file.content_type or "").startswith("image/"):
        return JsonResponse({"error": "Разрешены только изображения."}, status=400)
    if file.size > MAX_UPLOAD_IMAGE_SIZE:
        return JsonResponse({"error": "Файл слишком большой (максимум 8МБ)."}, status=400)

    path = default_storage.save(f"quill_uploads/{file.name}", file)
    return JsonResponse({"url": default_storage.url(path)})


# Публичное чтение для всех, запись — только через /admin/ (сюда никакого
# create/update/delete не выведено вообще, ReadOnlyModelViewSet).
class LocalContentViewSet(ReadOnlyModelViewSet):
    queryset = LocalContentEntry.objects.all()
    serializer_class = LocalContentEntrySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ProcurementViewSet(ReadOnlyModelViewSet):
    queryset = ProcurementEntry.objects.all()
    serializer_class = ProcurementEntrySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class DocumentViewSet(ReadOnlyModelViewSet):
    queryset = DocumentEntry.objects.all()
    serializer_class = DocumentEntrySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class NewsViewSet(ReadOnlyModelViewSet):
    queryset = NewsEntry.objects.all()
    serializer_class = NewsEntrySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
