from django.contrib import admin
from django.utils import timezone

from .models import (
    AuditLog, EmailOTP, ModerationLog, Report, SafetyAcknowledgement,
    StudentIDVerification, SuspiciousActivity, TrustScoreEvent,
    TrustTransaction, UserRestriction, IdentityVerification,
    ExternalSellerApplication,
    UserSessionSecurityEvent,
)
from .scoring import update_trust_score


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'purpose', 'expires_at', 'consumed_at', 'request_ip', 'created_at')
    list_filter = ('purpose', 'consumed_at')
    search_fields = ('user__email', 'request_ip')
    readonly_fields = ('created_at', 'updated_at')
    exclude = ('code', 'code_hash')


@admin.register(StudentIDVerification)
class StudentIDVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'student_id_number', 'reviewer', 'reviewed_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__email', 'user__username', 'student_id_number')
    actions = ('approve', 'reject')

    @admin.action(description='Approve selected student ID verifications')
    def approve(self, request, queryset):
        queryset.update(status=StudentIDVerification.STATUS_APPROVED, reviewer=request.user, reviewed_at=timezone.now())
        for verification in queryset.select_related('user__profile'):
            verification.user.profile.student_id_verified = True
            verification.user.profile.save(update_fields=['student_id_verified'])
            update_trust_score(
                verification.user,
                reason='student_id_approved',
                actor=request.user,
                source=verification,
            )

    @admin.action(description='Reject selected student ID verifications')
    def reject(self, request, queryset):
        queryset.update(status=StudentIDVerification.STATUS_REJECTED, reviewer=request.user, reviewed_at=timezone.now())
        for verification in queryset.select_related('user__profile'):
            verification.user.profile.student_id_verified = False
            verification.user.profile.save(update_fields=['student_id_verified'])
            update_trust_score(
                verification.user,
                reason='student_id_rejected',
                actor=request.user,
                source=verification,
            )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reason', 'status', 'is_actionable', 'reporter', 'reported_user', 'content_type', 'object_id', 'created_at')
    list_filter = ('status', 'is_actionable', 'reason', 'content_type')
    search_fields = ('details', 'reporter__email', 'reported_user__email', 'object_id')
    list_editable = ('status', 'is_actionable')
    readonly_fields = ('created_at', 'updated_at')
    actions = ('mark_actionable_resolved', 'dismiss')

    def save_model(self, request, obj, form, change):
        if change and ('status' in form.changed_data or 'is_actionable' in form.changed_data):
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
        if obj.reported_user and (not change or 'status' in form.changed_data or 'is_actionable' in form.changed_data):
            update_trust_score(
                obj.reported_user,
                reason='report_moderation_changed',
                actor=request.user,
                source=obj,
            )

    @admin.action(description='Mark selected reports actionable and resolved')
    def mark_actionable_resolved(self, request, queryset):
        queryset.update(
            status=Report.STATUS_RESOLVED,
            is_actionable=True,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        for report in queryset.select_related('reported_user'):
            if report.reported_user:
                update_trust_score(
                    report.reported_user,
                    reason='report_actionable_resolved',
                    actor=request.user,
                    source=report,
                )

    @admin.action(description='Dismiss selected reports')
    def dismiss(self, request, queryset):
        queryset.update(
            status=Report.STATUS_DISMISSED,
            is_actionable=False,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        for report in queryset.select_related('reported_user'):
            if report.reported_user:
                update_trust_score(
                    report.reported_user,
                    reason='report_dismissed',
                    actor=request.user,
                    source=report,
                )


@admin.register(UserRestriction)
class UserRestrictionAdmin(admin.ModelAdmin):
    list_display = ('user', 'reason', 'is_active', 'starts_at', 'ends_at', 'created_by')
    list_filter = ('is_active', 'reason')
    search_fields = ('user__email', 'note')

    def save_model(self, request, obj, form, change):
        if obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        update_trust_score(
            obj.user,
            reason='user_restriction_changed',
            actor=request.user,
            source=obj,
        )


@admin.register(SuspiciousActivity)
class SuspiciousActivityAdmin(admin.ModelAdmin):
    list_display = ('activity_type', 'severity', 'user', 'ip_address', 'is_resolved', 'created_at')
    list_filter = ('severity', 'activity_type', 'is_resolved')
    search_fields = ('description', 'user__email', 'ip_address')
    list_editable = ('is_resolved',)


@admin.register(TrustTransaction)
class TrustTransactionAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'seller', 'status', 'content_type', 'object_id', 'completed_at', 'confirmed_by', 'created_at')
    list_filter = ('status', 'content_type')
    search_fields = ('buyer__email', 'buyer__username', 'seller__email', 'seller__username', 'object_id', 'note')
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if obj.status == TrustTransaction.STATUS_COMPLETED and obj.completed_at is None:
            obj.completed_at = timezone.now()
        if obj.status == TrustTransaction.STATUS_COMPLETED and obj.buyer_confirmed_at is None:
            obj.buyer_confirmed_at = timezone.now()
        if obj.status == TrustTransaction.STATUS_COMPLETED and obj.seller_confirmed_at is None:
            obj.seller_confirmed_at = timezone.now()
        if obj.confirmed_by_id is None and obj.status == TrustTransaction.STATUS_COMPLETED:
            obj.confirmed_by = request.user
        old_seller = None
        if change:
            old_seller = TrustTransaction.objects.filter(pk=obj.pk).values_list('seller', flat=True).first()
        super().save_model(request, obj, form, change)
        update_trust_score(
            obj.seller,
            reason='trust_transaction_changed',
            actor=request.user,
            source=obj,
        )
        if old_seller and old_seller != obj.seller_id:
            from django.contrib.auth import get_user_model
            previous_seller = get_user_model().objects.filter(pk=old_seller).first()
            if previous_seller:
                update_trust_score(
                    previous_seller,
                    reason='trust_transaction_changed',
                    actor=request.user,
                    source=obj,
                )


@admin.register(TrustScoreEvent)
class TrustScoreEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'old_score', 'new_score', 'reason', 'actor', 'created_at')
    list_filter = ('reason',)
    search_fields = ('user__email', 'user__username', 'actor__email', 'source_object_id')
    readonly_fields = (
        'user', 'old_score', 'new_score', 'reason', 'actor',
        'source_content_type', 'source_object_id', 'inputs',
        'created_at', 'updated_at',
    )

    def has_add_permission(self, request):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor', 'content_type', 'object_id', 'ip_address', 'created_at')
    list_filter = ('action', 'content_type')
    search_fields = ('actor__email', 'object_id', 'ip_address')
    readonly_fields = ('actor', 'action', 'ip_address', 'user_agent', 'content_type', 'object_id', 'metadata', 'created_at', 'updated_at')


@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'moderator', 'content_type', 'object_id', 'created_at')
    list_filter = ('action', 'content_type')
    search_fields = ('note', 'moderator__email', 'object_id')


@admin.register(SafetyAcknowledgement)
class SafetyAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ('user', 'version', 'ip_address', 'acknowledged_at')
    search_fields = ('user__email', 'ip_address')


@admin.register(IdentityVerification)
class IdentityVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'verification_type', 'status', 'risk_score', 'liveness_passed', 'phone_otp_verified', 'reviewer', 'created_at')
    list_filter = ('status', 'verification_type', 'liveness_passed', 'phone_otp_verified')
    search_fields = ('user__email', 'document_reference', 'provider_reference')
    readonly_fields = ('created_at', 'updated_at')
    actions = ('approve', 'reject')

    @admin.action(description='Approve selected identity verifications')
    def approve(self, request, queryset):
        queryset.update(status=IdentityVerification.STATUS_APPROVED, reviewer=request.user, reviewed_at=timezone.now())

    @admin.action(description='Reject selected identity verifications')
    def reject(self, request, queryset):
        queryset.update(status=IdentityVerification.STATUS_REJECTED, reviewer=request.user, reviewed_at=timezone.now())


@admin.register(ExternalSellerApplication)
class ExternalSellerApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'business_name', 'phone_number', 'status', 'reviewer', 'reviewed_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__email', 'user__username', 'business_name', 'phone_number', 'campus_reason')
    readonly_fields = ('created_at', 'updated_at')
    actions = ('approve_external_sellers', 'reject_external_sellers')

    @admin.action(description='Approve selected external seller applications')
    def approve_external_sellers(self, request, queryset):
        for application in queryset.select_related('user'):
            application.status = ExternalSellerApplication.STATUS_APPROVED
            application.reviewer = request.user
            application.reviewed_at = timezone.now()
            application.save(update_fields=['status', 'reviewer', 'reviewed_at', 'updated_at'])
            application.user.trust_tier = 'verified_external'
            application.user.external_seller_approved = True
            application.user.phone = application.phone_number
            application.user.phone_verified = True
            application.user.save(update_fields=[
                'trust_tier', 'external_seller_approved', 'phone',
                'phone_verified',
            ])

    @admin.action(description='Reject selected external seller applications')
    def reject_external_sellers(self, request, queryset):
        for application in queryset.select_related('user'):
            application.status = ExternalSellerApplication.STATUS_REJECTED
            application.reviewer = request.user
            application.reviewed_at = timezone.now()
            application.save(update_fields=['status', 'reviewer', 'reviewed_at', 'updated_at'])
            application.user.external_seller_approved = False
            application.user.save(update_fields=['external_seller_approved'])


@admin.register(UserSessionSecurityEvent)
class UserSessionSecurityEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'ip_address', 'session_key', 'created_at')
    list_filter = ('event_type',)
    search_fields = ('user__email', 'ip_address', 'session_key', 'user_agent')
    readonly_fields = ('user', 'event_type', 'session_key', 'ip_address', 'user_agent', 'metadata', 'created_at', 'updated_at')
