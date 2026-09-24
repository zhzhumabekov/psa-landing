from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet, LocalContentViewSet, NewsViewSet, ProcurementViewSet

router = DefaultRouter()
router.register("local-content", LocalContentViewSet, basename="local-content")
router.register("procurement", ProcurementViewSet, basename="procurement")
router.register("documents", DocumentViewSet, basename="documents")
router.register("news", NewsViewSet, basename="news")

urlpatterns = router.urls
