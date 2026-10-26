
from django.contrib import admin
from .models import KnowledgeArticle


@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "created_at", "updated_at")
    search_fields = ("title", "content", "source")
    list_filter = ("created_at",)
