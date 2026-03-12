from django.contrib import admin
from .models import ServiceCategory, ServiceOffer


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ServiceOffer)
class ServiceOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'category', 'price', 'delivery_mode', 'is_active')
    list_filter = ('is_active', 'delivery_mode', 'category')
    search_fields = ('title', 'provider__email')
    list_editable = ('is_active',)
