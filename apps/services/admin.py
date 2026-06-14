from django.contrib import admin
from django.utils import timezone
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
    list_display = ('title', 'provider', 'category', 'subcategory', 'price', 'approval_status', 'risk_score', 'view_count', 'is_active', 'created_at')
    list_filter = ('approval_status', 'is_active', 'category', 'subcategory', 'delivery_mode')
    search_fields = ('title', 'provider__email', 'description')
    list_editable = ('approval_status', 'is_active')
    ordering = ('-created_at',)
    readonly_fields = ('risk_reasons', 'risk_score', 'created_at', 'updated_at')
    actions = ('approve_services', 'reject_services')

    @admin.action(description='Approve selected services')
    def approve_services(self, request, queryset):
        queryset.update(
            approval_status=ServiceOffer.APPROVAL_APPROVED,
            is_active=True,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )

    @admin.action(description='Reject selected services')
    def reject_services(self, request, queryset):
        queryset.update(
            approval_status=ServiceOffer.APPROVAL_REJECTED,
            is_active=False,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
