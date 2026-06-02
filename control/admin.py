from django.contrib import admin
from .models import AdminLog


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action', 'target_model', 'target_id', 'description', 'ip_address', 'created_at')
    list_filter = ('action', 'target_model', 'created_at')
    search_fields = ('admin__email', 'description', 'target_model')
    readonly_fields = ('admin', 'action', 'target_model', 'target_id', 'description', 'ip_address', 'created_at')
    date_hierarchy = 'created_at'
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
