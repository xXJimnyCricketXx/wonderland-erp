from django.contrib import admin

from .models import Gemstone


@admin.register(Gemstone)
class GemstoneAdmin(admin.ModelAdmin):
    list_display = ["name", "mineral_class", "mohs_hardness", "origin"]
    search_fields = ["name", "alternative_names", "application", "origin"]
