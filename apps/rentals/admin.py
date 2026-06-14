from django.contrib import admin
from django.utils import timezone
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
        'approval_status', 'risk_score', 'is_active', 'is_taken', 'created_at',
    )
    list_filter = ('approval_status', 'is_active', 'is_taken', 'rental_type', 'gender_preference', 'rental_period')
    search_fields = ('title', 'landlord__email', 'address', 'area')
    list_editable = ('approval_status', 'is_active', 'is_taken')
    ordering = ('-created_at',)
    readonly_fields = ('risk_reasons', 'risk_score', 'created_at', 'updated_at')
    actions = ('approve_rentals', 'reject_rentals')

    @admin.action(description='Approve selected rentals')
    def approve_rentals(self, request, queryset):
        queryset.update(
            approval_status=RentalListing.APPROVAL_APPROVED,
            is_active=True,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )

    @admin.action(description='Reject selected rentals')
    def reject_rentals(self, request, queryset):
        queryset.update(
            approval_status=RentalListing.APPROVAL_REJECTED,
            is_active=False,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )


@admin.register(RentalInquiry)
class RentalInquiryAdmin(admin.ModelAdmin):
    list_display = ('inquirer', 'rental', 'is_read', 'created_at')
    list_filter = ('is_read',)
    list_editable = ('is_read',)
    search_fields = ('inquirer__email', 'rental__title')
