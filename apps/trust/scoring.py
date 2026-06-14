from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from .utils import report_count_for_user
from .models import TrustScoreEvent, TrustTransaction, UserRestriction
from .utils import models_q_current_restriction


def _score_inputs(user, profile=None):
    from apps.trust.utils import is_campus_email
    profile = profile or user.profile
    age_days = max((timezone.now() - user.date_joined).days, 0)
    successful_transactions = TrustTransaction.objects.filter(
        seller=user,
        status=TrustTransaction.STATUS_COMPLETED,
    ).count()
    actionable_reports = report_count_for_user(user)
    active_restrictions = UserRestriction.objects.filter(
        user=user,
        is_active=True,
    ).filter(models_q_current_restriction()).count()
    return {
        'email_verified': bool(user.is_verified),
        'campus_email': is_campus_email(getattr(user, 'email', '')),
        'has_matric_number': bool(getattr(user, 'matric_number', '')),
        'student_id_verified': bool(profile.student_id_verified),
        'successful_transactions': successful_transactions,
        'avg_rating': float(profile.avg_rating or 0),
        'total_reviews': profile.total_reviews,
        'account_age_days': age_days,
        'response_rate': profile.response_rate,
        'actionable_reports': actionable_reports,
        'active_restrictions': active_restrictions,
        'is_suspended': bool(getattr(user, 'is_suspended', False)),
    }


def calculate_trust_score(user, *, profile=None, inputs=None):
    profile = profile or user.profile
    inputs = inputs or _score_inputs(user, profile)
    score = 20

    if inputs['email_verified']:
        score += 25
    if inputs['campus_email']:
        score += 10   # bonus for a .unn.edu.ng address
    if inputs['has_matric_number']:
        score += 5    # submitted matric, pending manual check
    if inputs['student_id_verified']:
        score += 15
    score += min(inputs['successful_transactions'] * 4, 20)
    score += min(int(profile.avg_rating or 0) * 4, 20)
    score += min(inputs['account_age_days'] // 30, 10)
    score += min(profile.response_rate // 10, 10)
    score -= min(inputs['actionable_reports'] * 12, 45)
    if inputs['active_restrictions']:
        score = min(score, 40)

    if inputs['is_suspended']:
        score = min(score, 10)

    return max(0, min(score, 100))


def update_trust_score(user, *, reason='trust_score_recomputed', actor=None, source=None):
    with transaction.atomic():
        profile = type(user.profile).objects.select_for_update().get(pk=user.profile.pk)
        old_score = profile.trust_score
        inputs = _score_inputs(user, profile)
        profile.successful_transactions = inputs['successful_transactions']
        profile.trust_score = calculate_trust_score(user, profile=profile, inputs=inputs)
        profile.trusted_seller = profile.trust_score >= 70 and profile.successful_transactions >= 3
        profile.top_rated_seller = (
            profile.trust_score >= 85
            and profile.total_reviews >= 5
            and profile.avg_rating >= 4.50
            and profile.successful_transactions >= 5
        )
        profile.save(update_fields=[
            'successful_transactions',
            'trust_score',
            'trusted_seller',
            'top_rated_seller',
            'updated_at',
        ])

        source_content_type = None
        source_object_id = ''
        if source is not None:
            source_content_type = ContentType.objects.get_for_model(source)
            source_object_id = str(source.pk)

        if old_score != profile.trust_score:
            TrustScoreEvent.objects.create(
                user=user,
                old_score=old_score,
                new_score=profile.trust_score,
                reason=reason,
                actor=actor,
                source_content_type=source_content_type,
                source_object_id=source_object_id,
                inputs=inputs,
            )
        return profile.trust_score


def recompute_trust_score(user, *, reason='trust_score_recomputed', actor=None, source=None):
    return update_trust_score(user, reason=reason, actor=actor, source=source)
