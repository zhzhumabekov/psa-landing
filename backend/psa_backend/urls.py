"""
URL configuration for psa_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from content.views import (
    documents_page,
    home,
    local_content_detail,
    local_content_page,
    news_page,
    procurement_page,
    quill_image_upload,
)

urlpatterns = [
    path('', home, name='home'),
    path('local-content/', local_content_page, name='local_content_page'),
    path('local-content/<int:pk>/', local_content_detail, name='local_content_detail'),
    path('procurement/', procurement_page, name='procurement_page'),
    path('documents/', documents_page, name='documents_page'),
    path('news/', news_page, name='news_page'),
    path('admin/quill-upload/', quill_image_upload, name='quill_image_upload'),
    path('admin/', admin.site.urls),
    path('api/', include('content.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
