from django.contrib import admin
from .models import RentalListing, RentalImage, RentalInquiry


class RentalImageInline(admin.TabularInline):
    model = RentalImage
    extra = 1


class RentalInquiryInline(admin.TabularInline):
    model = RentalInquiry
    extra = 0
    readonly_fields = ('inquirer', 'message', 'created_at', 'is_read')
    can_delete = False


@admin.register(RentalListing)
class RentalListingAdmin(admin.ModelAdmin):
    inlines = [RentalImageInline, RentalInquiryInline]
    list_display = (
        'title', 'landlord', 'rental_type', 'price',
        'rental_period', 'area', 'gender_preference',
        'is_active', 'is_taken', 'created_at',
    )
    list_filter = ('is_active', 'is_taken', 'rental_type', 'gender_preference', 'rental_period')
    search_fields = ('title', 'landlord__email', 'address', 'area')
    list_editable = ('is_active', 'is_taken')
    ordering = ('-created_at',)


@admin.register(RentalInquiry)
class RentalInquiryAdmin(admin.ModelAdmin):
    list_display = ('inquirer', 'rental', 'is_read', 'created_at')
    list_filter = ('is_read',)
    list_editable = ('is_read',)
    search_fields = ('inquirer__email', 'rental__title')
