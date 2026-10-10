from django.contrib import admin
from .models import Product, Variant, Address, Coupon, Order, OrderItem, Review, NewsletterSubscriber, Category
from django.utils.html import format_html

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'image_preview']
    readonly_fields = ['image_preview']
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" alt="Category image" style="width:160px;height:100px;object-fit:cover;border-radius:6px">', obj.image.url)
        return 'Using default collection photograph'

class VariantInline(admin.TabularInline):
    model = Variant
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'active']
    list_filter = ['category', 'active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ['name']}
    inlines = [VariantInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ['product', 'product_name', 'variant_name', 'quantity', 'unit_price']
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['reference', 'customer_name', 'status', 'total', 'created_at']
    list_filter = ['status']
    search_fields = ['email', 'customer_name', 'reference']
    readonly_fields = ['reference', 'user', 'customer_name', 'email', 'address', 'note', 'subtotal', 'discount', 'total', 'coupon_code', 'checkout_key', 'created_at']
    inlines = [OrderItemInline]
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'approved']
    list_filter = ['approved']
    readonly_fields = ['user', 'product', 'rating', 'text', 'created_at']

admin.site.register([Address, Coupon, NewsletterSubscriber])
admin.site.site_header = 'Kedarmart administration'
