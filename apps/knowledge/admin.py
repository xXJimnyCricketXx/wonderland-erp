from django.contrib import admin

from .models import (
    CustomsTariffCode, MaterialCategory, PackagingLicenseDocument, PackagingLicenseSubmission,
    PackagingType, PackagingTypeMaterial, ShippingOption,
)


class PackagingTypeMaterialInline(admin.TabularInline):
    model = PackagingTypeMaterial
    extra = 0


@admin.register(PackagingType)
class PackagingTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "dimensions", "valid_from"]
    search_fields = ["name"]
    inlines = [PackagingTypeMaterialInline]


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "price_per_kg"]
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


@admin.register(PackagingLicenseDocument)
class PackagingLicenseDocumentAdmin(admin.ModelAdmin):
    list_display = ["year", "doc_type", "uploaded_at"]
    list_filter = ["doc_type", "year"]


@admin.register(PackagingLicenseSubmission)
class PackagingLicenseSubmissionAdmin(admin.ModelAdmin):
    list_display = ["submission_type", "year", "due_date", "submitted"]
    list_filter = ["submission_type", "submitted"]


