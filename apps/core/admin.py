from django.contrib import admin

from .models import ReferenceOption

admin.site.site_header = "Wonderland ERP Administration"
admin.site.site_title = "Wonderland ERP"
admin.site.index_title = "Verwaltung"


@admin.register(ReferenceOption)
class ReferenceOptionAdmin(admin.ModelAdmin):
    list_display = ["category", "value", "order"]
    list_filter = ["category"]
    search_fields = ["category", "value"]
    ordering = ["category", "order", "value"]
