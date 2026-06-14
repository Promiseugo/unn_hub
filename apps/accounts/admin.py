from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    readonly_fields = (
        'student_id_verified', 'successful_transactions', 'response_rate',
        'trust_score', 'trusted_seller', 'top_rated_seller',
        'avg_rating', 'total_reviews',
    )
    fieldsets = (
        (None, {'fields': ('avatar', 'bio', 'department', 'level')}),
        ('Trust & verification', {
            'fields': (
                'student_id_verified', 'successful_transactions',
                'response_rate', 'trust_score', 'trusted_seller',
                'top_rated_seller', 'avg_rating', 'total_reviews',
            )
        }),
    )


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('email', 'username', 'first_name', 'last_name', 'trust_tier', 'is_verified', 'external_seller_approved', 'is_suspended', 'is_staff')
    list_filter = ('trust_tier', 'is_verified', 'external_seller_approved', 'is_suspended', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'matric_number')
    ordering = ('-date_joined',)
    fieldsets = UserAdmin.fieldsets + (
        ('UNN Hub', {'fields': ('phone', 'phone_verified', 'matric_number', 'trust_tier', 'external_seller_approved', 'identity_risk_score', 'is_verified', 'is_suspended', 'suspension_reason')}),
    )
    list_display = ('email', 'username', 'first_name', 'last_name', 'matric_number', 'trust_tier', 'is_verified', 'external_seller_approved', 'is_suspended', 'is_staff')
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change and {'is_verified', 'is_suspended'} & set(form.changed_data):
            from apps.trust.scoring import update_trust_score
            update_trust_score(
                obj,
                reason='account_trust_fields_changed',
                actor=request.user,
                source=obj,
            )
