from django.db import models


class LocalContentEntry(models.Model):
    title = models.CharField("Заголовок", max_length=200)
    date = models.DateField("Дата")
    body = models.TextField("Текст")

    class Meta:
        verbose_name = "Материал: местное содержание"
        verbose_name_plural = "Местное содержание — материалы"
        ordering = ["-date"]

    def __str__(self):
        return self.title


class ProcurementEntry(models.Model):
    STATUS_OPEN = "Открыт"
    STATUS_CLOSED = "Завершён"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Открыт"),
        (STATUS_CLOSED, "Завершён"),
    ]

    title = models.CharField("Название закупки", max_length=200)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    deadline = models.DateField("Срок подачи", null=True, blank=True)
    description = models.TextField("Описание", blank=True)
    url = models.URLField("Ссылка (тендерная площадка/файл)", blank=True)

    class Meta:
        verbose_name = "Закупка"
        verbose_name_plural = "Закупки"
        ordering = ["-deadline"]

    def __str__(self):
        return self.title


class DocumentEntry(models.Model):
    title = models.CharField("Название документа", max_length=200)
    category = models.CharField("Категория", max_length=100, blank=True)
    date = models.DateField("Дата", null=True, blank=True)
    file = models.FileField("Файл", upload_to="documents/", blank=True)
    url = models.URLField("Ссылка (если файл не загружен)", blank=True)

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        ordering = ["-date"]

    def __str__(self):
        return self.title


class NewsEntry(models.Model):
    title = models.CharField("Заголовок", max_length=200)
    date = models.DateField("Дата")
    excerpt = models.CharField("Краткое описание", max_length=400, blank=True)
    body = models.TextField("Текст новости", blank=True)

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ["-date"]

    def __str__(self):
        return self.title
