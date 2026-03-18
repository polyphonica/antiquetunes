from django.contrib import admin
from .models import DownloadToken, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('sheet_music', 'unit_price')


class DownloadTokenInline(admin.TabularInline):
    model = DownloadToken
    extra = 0
    readonly_fields = ('token', 'customer', 'created_at', 'download_count', 'expires_at', 'max_downloads')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_reference', 'email', 'status', 'total', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_reference', 'guest_email', 'customer__email')
    readonly_fields = ('order_reference', 'stripe_session_id', 'stripe_payment_intent_id', 'created_at', 'updated_at')
    inlines = [OrderItemInline]


@admin.register(DownloadToken)
class DownloadTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'order_item', 'customer', 'download_count', 'max_downloads', 'expires_at', 'is_valid')
    list_filter = ('created_at',)
    readonly_fields = ('token', 'created_at')
