from django.contrib import admin
from .models import ServiceCategory, ServiceSubCategory, ServiceOffer


class ServiceSubCategoryInline(admin.TabularInline):
    model = ServiceSubCategory
    extra = 1
    prepopulated_fields = {'slug': ('name',)}
    fields = (
        'name', 'slug', 'icon', 'banner_image',
        'is_featured', 'sort_order', 'seo_title', 'seo_description',
    )


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('sort_order', 'name', 'slug', 'icon', 'is_featured')
    list_display_links = ('name',)
    list_editable = ('sort_order', 'is_featured')
    search_fields = ('name', 'slug', 'seo_title', 'seo_description')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'icon', 'banner_image'),
        }),
        ('Display', {
            'fields': ('is_featured', 'sort_order'),
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description'),
        }),
    )
    inlines = [ServiceSubCategoryInline]


@admin.register(ServiceSubCategory)
class ServiceSubCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('sort_order', 'name', 'category', 'slug', 'icon', 'is_featured')
    list_display_links = ('name',)
    list_editable = ('sort_order', 'is_featured')
    list_filter = ('category', 'is_featured')
    search_fields = ('name', 'slug', 'seo_title', 'seo_description')
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'slug', 'icon', 'banner_image'),
        }),
        ('Display', {
            'fields': ('is_featured', 'sort_order'),
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description'),
        }),
    )


@admin.register(ServiceOffer)
class ServiceOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'category', 'subcategory', 'price', 'view_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'subcategory', 'delivery_mode')
    search_fields = ('title', 'provider__email', 'description')
    ordering = ('-created_at',)
