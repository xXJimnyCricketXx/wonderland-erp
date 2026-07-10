from django.contrib import admin

from .models import CompanyProfile


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ["company_name", "email", "updated_at"]
