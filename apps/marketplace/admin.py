from django.contrib import admin
from django.utils import timezone
from .models import Category, SubCategory, Listing, ListingImage


class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1
    prepopulated_fields = {'slug': ('name',)}
    fields = (
        'name', 'slug', 'icon', 'banner_image',
        'is_featured', 'sort_order', 'seo_title', 'seo_description',
    )


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
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
    inlines = [SubCategoryInline]


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
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


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    inlines = [ListingImageInline]
    list_display = ('title', 'seller', 'category', 'subcategory', 'price', 'condition', 'approval_status', 'risk_score', 'view_count', 'is_active', 'is_sold', 'created_at', 'expires_at')
    list_filter = ('approval_status', 'is_active', 'is_sold', 'category', 'subcategory', 'condition')
    search_fields = ('title', 'seller__email', 'description')
    list_editable = ('approval_status', 'is_active', 'is_sold')
    ordering = ('-created_at',)
    readonly_fields = ('risk_reasons', 'risk_score', 'created_at', 'updated_at')
    actions = ('approve_listings', 'reject_listings')

    @admin.action(description='Approve selected listings')
    def approve_listings(self, request, queryset):
        queryset.update(
            approval_status=Listing.APPROVAL_APPROVED,
            is_active=True,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )

    @admin.action(description='Reject selected listings')
    def reject_listings(self, request, queryset):
        queryset.update(
            approval_status=Listing.APPROVAL_REJECTED,
            is_active=False,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
