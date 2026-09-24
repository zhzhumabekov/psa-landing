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


# Главная страница — серверный рендеринг через шаблонизатор (не JS fetch,
# см. templates/index.html): контент 4 разделов приходит прямо из БД.
def home(request):
    context = {
        "local_content_entries": LocalContentEntry.objects.all(),
        "procurement_entries": ProcurementEntry.objects.all(),
        "document_entries": DocumentEntry.objects.all(),
        "news_entries": NewsEntry.objects.all(),
    }
    return render(request, "index.html", context)


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
