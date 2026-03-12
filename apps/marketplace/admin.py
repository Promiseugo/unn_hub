from django.contrib import admin
from .models import Category, Listing, ListingImage


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug')


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    inlines = [ListingImageInline]
    list_display = ('title', 'seller', 'category', 'price', 'condition', 'is_active', 'is_sold', 'created_at')
    list_filter = ('is_active', 'is_sold', 'category', 'condition')
    search_fields = ('title', 'seller__email', 'description')
    list_editable = ('is_active', 'is_sold')
    ordering = ('-created_at',)
