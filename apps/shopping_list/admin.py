from django.contrib import admin

from .models import ShoppingListItem


@admin.register(ShoppingListItem)
class ShoppingListItemAdmin(admin.ModelAdmin):
    list_display = ["title", "article_number", "supplier", "quantity", "price_total", "is_archived"]
    list_filter = ["supplier", "is_archived"]
    search_fields = ["title", "article_number"]
