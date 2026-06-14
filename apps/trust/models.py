import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TimeStampedModel


class EmailOTP(TimeStampedModel):
    PURPOSE_VERIFY_EMAIL = 'verify_email'
    PURPOSE_CHOICES = [(PURPOSE_VERIFY_EMAIL, 'Verify email')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='email_otps')
    code = models.CharField(max_length=6, blank=True, default='')
    code_hash = models.CharField(max_length=128, blank=True, default='')
    purpose = models.CharField(max_length=32, choices=PURPOSE_CHOICES, default=PURPOSE_VERIFY_EMAIL)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    send_count = models.PositiveSmallIntegerField(default=1)
    last_sent_at = models.DateTimeField(default=timezone.now)
    request_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'purpose', 'consumed_at', '-created_at']),
            models.Index(fields=['expires_at']),
        ]

    @classmethod
    def issue(cls, user, *, request_ip='', ttl_minutes=10):
        cls.objects.filter(user=user, purpose=cls.PURPOSE_VERIFY_EMAIL, consumed_at__isnull=True).update(
            consumed_at=timezone.now(),
        )
        raw_code = f"{secrets.randbelow(1000000):06d}"
        otp = cls.objects.create(
            user=user,
            code='',
            code_hash=make_password(raw_code),
            expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
            request_ip=request_ip or None,
        )
        otp.plain_code = raw_code
        return otp

    @property
    def is_valid(self):
        return self.consumed_at is None and self.expires_at >= timezone.now()

    def check_code(self, raw_code):
        if not self.is_valid:
            return False
        if self.code_hash:
            return check_password(raw_code, self.code_hash)
        return bool(self.code and secrets.compare_digest(self.code, raw_code))


class IdentityVerification(TimeStampedModel):
    TYPE_STUDENT_ID = 'student_id'
    TYPE_GOVERNMENT_ID = 'government_id'
    TYPE_BUSINESS = 'business'
    TYPE_CHOICES = [
        (TYPE_STUDENT_ID, 'Student ID'),
        (TYPE_GOVERNMENT_ID, 'Government ID'),
        (TYPE_BUSINESS, 'Business verification'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_EXPIRED = 'expired'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_EXPIRED, 'Expired'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='identity_verifications')
    verification_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    document = models.ImageField(upload_to='identity-verification/%Y/%m/', blank=True, null=True)
    selfie = models.ImageField(upload_to='identity-selfies/%Y/%m/', blank=True, null=True)
    document_reference = models.CharField(max_length=128, blank=True)
    provider = models.CharField(max_length=64, blank=True, help_text='External KYC provider or manual review.')
    provider_reference = models.CharField(max_length=128, blank=True)
    liveness_passed = models.BooleanField(default=False)
    phone_otp_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    risk_score = models.PositiveSmallIntegerField(default=50)
    retention_until = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_identity_verifications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    consent_acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'risk_score', '-created_at']),
            models.Index(fields=['user', 'verification_type', '-created_at']),
            models.Index(fields=['retention_until']),
        ]

    def __str__(self):
        return f"{self.user} {self.verification_type} verification"


class ExternalSellerApplication(TimeStampedModel):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='external_seller_application')
    business_name = models.CharField(max_length=160, blank=True)
    phone_number = models.CharField(max_length=32)
    public_profile_url = models.URLField(blank=True)
    campus_reason = models.TextField(help_text='Why should this seller be allowed to sell to the campus community?')
    proof_image = models.ImageField(upload_to='external-seller-proof/%Y/%m/', blank=True, null=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_external_seller_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['reviewed_at']),
        ]

    def __str__(self):
        return f"{self.user} external seller application ({self.status})"


class UserSessionSecurityEvent(TimeStampedModel):
    EVENT_LOGIN = 'login'
    EVENT_NEW_DEVICE = 'new_device'
    EVENT_NEW_IP = 'new_ip'
    EVENT_CONCURRENT_LIMIT = 'concurrent_limit'
    EVENT_CHOICES = [
        (EVENT_LOGIN, 'Login'),
        (EVENT_NEW_DEVICE, 'New device'),
        (EVENT_NEW_IP, 'New IP'),
        (EVENT_CONCURRENT_LIMIT, 'Concurrent session limit'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='session_security_events')
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    session_key = models.CharField(max_length=80, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'event_type', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
        ]


class UserRestriction(TimeStampedModel):
    REASON_SCAM = 'scam'
    REASON_HARASSMENT = 'harassment'
    REASON_SPAM = 'spam'
    REASON_UNVERIFIED = 'unverified'
    REASON_POLICY = 'policy'
    REASON_CHOICES = [
        (REASON_SCAM, 'Scam or fraud'),
        (REASON_HARASSMENT, 'Harassment'),
        (REASON_SPAM, 'Spam'),
        (REASON_UNVERIFIED, 'Verification issue'),
        (REASON_POLICY, 'Policy violation'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='restrictions')
    reason = models.CharField(max_length=32, choices=REASON_CHOICES)
    note = models.TextField(blank=True)
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_restrictions',
    )

    class Meta:
        indexes = [models.Index(fields=['user', 'is_active', 'ends_at'])]

    def __str__(self):
        return f"{self.user} restricted for {self.reason}"

    @property
    def is_current(self):
        return self.is_active and (self.ends_at is None or self.ends_at > timezone.now())


class SafetyAcknowledgement(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='safety_ack')
    acknowledged_at = models.DateTimeField(default=timezone.now)
    version = models.CharField(max_length=24, default='2026-05')
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} safety acknowledgement"


class StudentIDVerification(TimeStampedModel):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_id_verification')
    student_id_number = models.CharField(max_length=64, blank=True)
    document = models.ImageField(upload_to='student-id-verification/%Y/%m/', blank=True, null=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_student_ids')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=['status', '-created_at'])]

    def __str__(self):
        return f"{self.user} student ID verification"


class Report(TimeStampedModel):
    REASON_SCAM = 'scam'
    REASON_FAKE = 'fake_listing'
    REASON_HARASSMENT = 'harassment'
    REASON_SUSPICIOUS = 'suspicious'
    REASON_PROHIBITED = 'prohibited'
    REASON_OTHER = 'other'
    REASON_CHOICES = [
        (REASON_SCAM, 'Scam or fraud'),
        (REASON_FAKE, 'Fake listing'),
        (REASON_HARASSMENT, 'Harassment'),
        (REASON_SUSPICIOUS, 'Suspicious behavior'),
        (REASON_PROHIBITED, 'Prohibited item'),
        (REASON_OTHER, 'Other'),
    ]
    STATUS_OPEN = 'open'
    STATUS_REVIEWING = 'reviewing'
    STATUS_RESOLVED = 'resolved'
    STATUS_DISMISSED = 'dismissed'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_REVIEWING, 'Reviewing'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_DISMISSED, 'Dismissed'),
    ]

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reports_made')
    reported_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_received')
    reason = models.CharField(max_length=32, choices=REASON_CHOICES)
    details = models.TextField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True)
    is_actionable = models.BooleanField(
        default=False,
        help_text='Only moderator-confirmed actionable reports affect trust scores.',
    )

    class Meta:
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['reported_user', 'status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['reporter', 'content_type', 'object_id'],
                condition=Q(status__in=['open', 'reviewing']),
                name='unique_open_report_per_reporter_target',
            ),
        ]

    def __str__(self):
        return f"{self.get_reason_display()} report #{self.pk}"


class SuspiciousActivity(TimeStampedModel):
    SEVERITY_LOW = 'low'
    SEVERITY_MEDIUM = 'medium'
    SEVERITY_HIGH = 'high'
    SEVERITY_CRITICAL = 'critical'
    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='suspicious_events')
    activity_type = models.CharField(max_length=64)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default=SEVERITY_LOW)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Suspicious activities'
        indexes = [
            models.Index(fields=['activity_type', '-created_at']),
            models.Index(fields=['severity', 'is_resolved', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.severity}: {self.activity_type}"


class TrustTransaction(TimeStampedModel):
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_DISPUTED = 'disputed'
    STATUS_REVERSED = 'reversed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_DISPUTED, 'Disputed'),
        (STATUS_REVERSED, 'Reversed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trust_purchases')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trust_sales')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    buyer_confirmed_at = models.DateTimeField(null=True, blank=True)
    seller_confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_trust_transactions',
    )
    disputed_at = models.DateTimeField(null=True, blank=True)
    disputed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='disputed_trust_transactions',
    )
    note = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['seller', 'status', '-completed_at']),
            models.Index(fields=['buyer', 'seller', 'status']),
            models.Index(fields=['content_type', 'object_id', 'status']),
        ]
        constraints = [
            models.CheckConstraint(check=~Q(buyer=models.F('seller')), name='trust_transaction_not_self'),
            models.UniqueConstraint(
                fields=['buyer', 'seller', 'content_type', 'object_id'],
                condition=Q(status='pending'),
                name='unique_pending_trust_transaction',
            ),
        ]

    def __str__(self):
        return f"{self.buyer} -> {self.seller} ({self.status})"

    def confirm_for(self, user):
        if user == self.buyer and self.buyer_confirmed_at is None:
            self.buyer_confirmed_at = timezone.now()
        elif user == self.seller and self.seller_confirmed_at is None:
            self.seller_confirmed_at = timezone.now()
        else:
            return False

        if self.buyer_confirmed_at and self.seller_confirmed_at:
            self.status = self.STATUS_COMPLETED
            if self.completed_at is None:
                self.completed_at = timezone.now()
            if self.confirmed_by_id is None:
                self.confirmed_by = user
        return True

    def dispute(self, user):
        if user not in (self.buyer, self.seller) or self.status == self.STATUS_REVERSED:
            return False
        self.status = self.STATUS_DISPUTED
        self.disputed_at = timezone.now()
        self.disputed_by = user
        return True

    @classmethod
    def completed_for_review(cls, *, reviewer, owner, content_type, object_id):
        qs = cls.objects.filter(
            buyer=reviewer,
            seller=owner,
            status=cls.STATUS_COMPLETED,
        )
        if content_type and object_id:
            targeted = qs.filter(content_type=content_type, object_id=str(object_id))
            if targeted.exists():
                return True
        return qs.filter(content_type__isnull=True, object_id='').exists()


class TrustScoreEvent(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trust_score_events')
    old_score = models.PositiveSmallIntegerField()
    new_score = models.PositiveSmallIntegerField()
    reason = models.CharField(max_length=80)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='initiated_trust_score_events',
    )
    source_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    source_object_id = models.CharField(max_length=64, blank=True)
    inputs = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['reason', '-created_at']),
            models.Index(fields=['source_content_type', 'source_object_id']),
        ]

    def __str__(self):
        return f"{self.user}: {self.old_score} -> {self.new_score} ({self.reason})"


class AuditLog(TimeStampedModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_events')
    action = models.CharField(max_length=80)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['actor', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.action} by {self.actor or 'system'}"


class ModerationLog(TimeStampedModel):
    moderator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderation_actions')
    action = models.CharField(max_length=80)
    note = models.TextField(blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        indexes = [
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.action} on {self.content_type}:{self.object_id}"
