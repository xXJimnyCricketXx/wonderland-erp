from django.contrib import admin

from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        "id", "sku", "title", "price", "stock_quantity", "minimum_stock_quantity",
        "supplier", "parent_article", "is_active", "is_archived",
    ]
    list_filter = ["is_active", "is_archived", "supplier"]
    search_fields = ["sku", "title"]
