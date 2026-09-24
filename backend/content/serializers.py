from rest_framework import serializers

from .models import DocumentEntry, LocalContentEntry, NewsEntry, ProcurementEntry


class LocalContentEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalContentEntry
        fields = ["id", "title", "date", "body"]


class ProcurementEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcurementEntry
        fields = ["id", "title", "status", "deadline", "description", "url"]


class DocumentEntrySerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = DocumentEntry
        fields = ["id", "title", "category", "date", "file_url", "url"]

    def get_file_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url


class NewsEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsEntry
        fields = ["id", "title", "date", "excerpt", "body"]
