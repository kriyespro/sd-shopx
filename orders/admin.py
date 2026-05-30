from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'price', 'quantity', 'metal_type', 'ring_size')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'first_name', 'last_name', 'email', 'total', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'email', 'first_name', 'last_name')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    list_editable = ('status',)
    inlines = [OrderItemInline]
