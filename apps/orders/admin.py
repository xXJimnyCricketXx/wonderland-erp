from django.contrib import admin

from .models import Order, OrderItem, Review


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_id", "customer", "sale_date", "date_shipped", "order_total",
        "status", "is_archived",
    ]
    list_filter = ["status", "order_type", "is_archived"]
    search_fields = ["order_id", "customer__first_name", "customer__last_name", "buyer_username", "tracking_number"]
    inlines = [OrderItemInline, ReviewInline]
