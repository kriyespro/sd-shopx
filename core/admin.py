from django.contrib import admin
from django.shortcuts import redirect

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Brand', {'fields': ('site_name', 'logo')}),
        ('Contact', {'fields': ('email', 'phone', 'whatsapp_number', 'business_hours')}),
        ('Address', {'fields': (
            'address_line1', 'address_line2', 'city', 'state', 'country', 'pincode',
        )}),
        ('Social', {'fields': ('instagram_url', 'facebook_url', 'twitter_url')}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _ = SiteSettings.objects.get_or_create(pk=1)
        return redirect('admin:core_sitesettings_change', obj.pk)
