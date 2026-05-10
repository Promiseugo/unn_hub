from django.contrib import admin
from .models import ServiceCategory, ServiceSubCategory, ServiceOffer


class ServiceSubCategoryInline(admin.TabularInline):
    model = ServiceSubCategory
    extra = 1
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug', 'icon')
    inlines = [ServiceSubCategoryInline]


@admin.register(ServiceSubCategory)
class ServiceSubCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'category', 'slug')
    list_filter = ('category',)


@admin.register(ServiceOffer)
class ServiceOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'category', 'subcategory', 'price', 'view_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'subcategory', 'delivery_mode')
    search_fields = ('title', 'provider__email', 'description')
    ordering = ('-created_at',)
