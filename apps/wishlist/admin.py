from django.contrib import admin

from .models import WishlistItem, WishlistItemImage


class WishlistItemImageInline(admin.TabularInline):
    model = WishlistItemImage
    extra = 1
    max_num = 5


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "estimated_price", "source_url", "created_at"]
    list_filter = ["status", "tags"]
    search_fields = ["title", "notes"]
    inlines = [WishlistItemImageInline]
