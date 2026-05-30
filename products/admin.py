from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVariant, Review, Tag


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ('image', 'alt', 'is_primary', 'position')


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 2
    fields = ('metal', 'ring_size', 'price_modifier', 'stock')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'position', 'is_active')
    list_editable = ('position', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_filter = ('parent', 'is_active')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'metal_type', 'diamond_shape', 'is_featured', 'is_new_arrival', 'is_active')
    list_editable = ('is_featured', 'is_new_arrival', 'is_active')
    list_filter = ('category', 'metal_type', 'diamond_shape', 'certification', 'is_featured', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]
    filter_horizontal = ('tags',)
    fieldsets = (
        ('Basic Info', {'fields': ('category', 'name', 'slug', 'description', 'short_description', 'tags')}),
        ('Pricing', {'fields': ('price', 'compare_price')}),
        ('Specifications', {'fields': ('metal_type', 'diamond_shape', 'carat_weight', 'certification', 'stock')}),
        ('Status', {'fields': ('is_featured', 'is_new_arrival', 'is_active')}),
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'is_approved', 'created_at')
    list_editable = ('is_approved',)
    list_filter = ('rating', 'is_approved')
