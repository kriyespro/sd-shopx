from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'product_name', 'metal_type', 'ring_size', 'price', 'quantity', 'line_total')
    readonly_fields = ('line_total',)
    can_delete = False

    @admin.display(description='Total')
    def line_total(self, obj):
        if not obj or obj.pk is None and obj.price is None:
            return '—'
        return obj.total_price


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'email', 'total', 'status', 'status_badge', 'created_at')
    list_filter = ('status', 'country', 'created_at')
    search_fields = ('order_number', 'email', 'first_name', 'last_name', 'phone')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    list_editable = ('status',)
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    save_on_top = True
    list_per_page = 25
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'status', 'notes', 'created_at', 'updated_at')
        }),
        ('Customer', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Shipping Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'country', 'pincode')
        }),
        ('Financials', {
            'fields': ('subtotal', 'shipping_cost', 'total')
        }),
    )

    def customer_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    customer_name.short_description = 'Customer'

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'confirmed': '#3b82f6',
            'processing': '#8b5cf6',
            'shipped': '#06b6d4',
            'delivered': '#10b981',
            'cancelled': '#ef4444',
            'refunded': '#6b7280',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:12px;font-size:11px">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
