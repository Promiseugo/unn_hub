from django.contrib import admin
from .models import Category, SubCategory, Listing, ListingImage


class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1
    prepopulated_fields = {'slug': ('name',)}


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug', 'icon')
    inlines = [SubCategoryInline]


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'category', 'slug')
    list_filter = ('category',)


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    inlines = [ListingImageInline]
    list_display = ('title', 'seller', 'category', 'subcategory', 'price', 'condition', 'view_count', 'is_active', 'is_sold', 'created_at')
    list_filter = ('is_active', 'is_sold', 'category', 'subcategory', 'condition')
    search_fields = ('title', 'seller__email', 'description')
    list_editable = ('is_active', 'is_sold')
    ordering = ('-created_at',)
