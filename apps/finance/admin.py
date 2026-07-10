from django.contrib import admin

from .models import AccountMapping, Expense, LedgerEntry, SKR03Account


@admin.register(SKR03Account)
class SKR03AccountAdmin(admin.ModelAdmin):
    list_display = ["number", "name"]
    search_fields = ["number", "name"]


@admin.register(AccountMapping)
class AccountMappingAdmin(admin.ModelAdmin):
    list_display = ["art", "variante", "skr03_account"]
    list_filter = ["art"]
    search_fields = ["art", "variante"]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        "date", "description", "category", "amount", "vat_rate", "supplier",
        "status", "is_cancelled", "is_archived",
    ]
    list_filter = ["category", "status", "is_cancelled", "is_archived", "supplier"]
    search_fields = ["description", "invoice_number", "supplier_order_number"]


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ["date", "entry_type", "title", "amount", "net", "order", "source"]
    list_filter = ["entry_type", "source"]
    search_fields = ["title", "info", "etsy_listing_ref"]
