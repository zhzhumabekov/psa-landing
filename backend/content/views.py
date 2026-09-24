from django.shortcuts import render
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


def procurement_page(request):
    return render(request, "procurement.html", {"procurement_entries": ProcurementEntry.objects.all()})


def documents_page(request):
    return render(request, "documents.html", {"document_entries": DocumentEntry.objects.all()})


def news_page(request):
    return render(request, "news.html", {"news_entries": NewsEntry.objects.all()})


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
