from django.contrib import admin
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
    list_display = ('title', 'seller', 'category', 'subcategory', 'price', 'condition', 'view_count', 'is_active', 'is_sold', 'created_at', 'expires_at')
    list_filter = ('is_active', 'is_sold', 'category', 'subcategory', 'condition')
    search_fields = ('title', 'seller__email', 'description')
    list_editable = ('is_active', 'is_sold')
    ordering = ('-created_at',)
