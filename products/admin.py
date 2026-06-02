from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVariant, Review, Tag


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2
    fields = ('image', 'alt', 'is_primary', 'position')


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('metal', 'ring_size', 'price_modifier', 'stock')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'position', 'is_active', 'product_count')
    list_editable = ('position', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    list_filter = ('parent', 'is_active')
    fields = ('name', 'slug', 'parent', 'description', 'image', 'position', 'is_active')

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'compare_price', 'metal_type', 'diamond_shape',
                    'certification', 'stock', 'is_featured', 'is_new_arrival', 'is_active', 'created_at')
    list_editable = ('price', 'stock', 'is_featured', 'is_new_arrival', 'is_active')
    list_filter = ('category', 'metal_type', 'diamond_shape', 'certification', 'is_featured', 'is_new_arrival', 'is_active')
    search_fields = ('name', 'description', 'short_description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]
    filter_horizontal = ('tags',)
    date_hierarchy = 'created_at'
    list_per_page = 30
    save_on_top = True
    fieldsets = (
        ('Basic Info', {
            'fields': ('category', 'name', 'slug', 'short_description', 'description', 'tags')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_price')
        }),
        ('Specifications', {
            'fields': ('metal_type', 'diamond_shape', 'carat_weight', 'certification', 'stock')
        }),
        ('Visibility', {
            'fields': ('is_featured', 'is_new_arrival', 'is_active')
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt', 'is_primary', 'position')
    list_editable = ('is_primary', 'position')
    list_filter = ('is_primary',)
    search_fields = ('product__name', 'alt')
    list_select_related = ('product',)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'metal', 'ring_size', 'price_modifier', 'stock', 'final_price')
    list_editable = ('price_modifier', 'stock')
    list_filter = ('metal',)
    search_fields = ('product__name',)
    list_select_related = ('product',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'title', 'is_approved', 'created_at')
    list_editable = ('is_approved',)
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('user__email', 'product__name', 'title', 'body')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
