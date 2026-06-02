from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Wishlist


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('phone', 'avatar', 'address_line1', 'city', 'state', 'country', 'pincode')


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    list_editable = ('is_active',)
    search_fields = ('email', 'first_name', 'last_name', 'username')
    ordering = ('-date_joined',)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city', 'country', 'created_at')
    list_filter = ('country',)
    search_fields = ('user__email', 'user__first_name', 'phone', 'city')
    readonly_fields = ('user', 'created_at')
    fields = ('user', 'phone', 'avatar', 'address_line1', 'city', 'state', 'country', 'pincode', 'created_at')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__email', 'product__name')
    date_hierarchy = 'added_at'
    list_select_related = ('user', 'product')
