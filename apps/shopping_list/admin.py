from django.contrib import admin

from .models import ShoppingListItem


@admin.register(ShoppingListItem)
class ShoppingListItemAdmin(admin.ModelAdmin):
    list_display = ["title", "article_number", "supplier_name", "quantity", "price_total", "is_archived"]
    list_filter = ["supplier_name", "is_archived"]
    search_fields = ["title", "article_number", "supplier_name"]
