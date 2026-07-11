from django.contrib import admin

from .models import Customer, Supplier, SupplierDiscountTier


class SupplierDiscountTierInline(admin.TabularInline):
    model = SupplierDiscountTier
    extra = 1


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["id", "last_name", "first_name", "email", "status", "is_returning_customer", "is_archived"]
    list_filter = ["status", "is_returning_customer", "is_archived"]
    search_fields = ["first_name", "last_name", "email", "etsy_buyer_user_id"]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["id", "last_name", "first_name", "company_name", "platform", "status", "is_archived"]
    list_filter = ["status", "is_archived"]
    search_fields = ["first_name", "last_name", "company_name", "account_number"]
    inlines = [SupplierDiscountTierInline]
