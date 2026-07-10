from django.contrib import admin

from .models import CustomsTariffCode, KnowledgeEntry, PackagingType, ShippingOption


@admin.register(KnowledgeEntry)
class KnowledgeEntryAdmin(admin.ModelAdmin):
    list_display = ["title", "updated_at"]
    search_fields = ["title", "content", "tags"]


@admin.register(PackagingType)
class PackagingTypeAdmin(admin.ModelAdmin):
    list_display = [
        "name", "paper_kg_per_unit", "plastic_kg_per_unit", "glass_kg_per_unit", "valid_from",
    ]
    search_fields = ["name"]


@admin.register(ShippingOption)
class ShippingOptionAdmin(admin.ModelAdmin):
    list_display = [
        "carrier", "description", "price_note", "requires_tracking_number",
        "is_international", "valid_from",
    ]
    list_filter = ["carrier", "is_international", "requires_tracking_number"]
    search_fields = ["carrier", "description", "use_case"]


@admin.register(CustomsTariffCode)
class CustomsTariffCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "definition", "description"]
    search_fields = ["code", "definition"]
