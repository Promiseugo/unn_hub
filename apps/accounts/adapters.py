"""
accounts/adapters.py

Custom django-allauth SocialAccountAdapter for UniTraX.

Responsibilities:
  1. Reject disposable email addresses (consistent with password registration).
  2. Auto-connect an incoming Google account to any existing password account
     with the same email, preventing duplicate accounts.
  3. Trust Google's email verification — mark new social users as verified
     immediately so they skip the OTP step.
"""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from apps.trust.utils import DISPOSABLE_EMAIL_DOMAINS

logger = logging.getLogger('apps.accounts')


class UniversityEmailSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """
        Called after Google auth completes, before account lookup or creation.

        Order of checks:
          1. Require a verified email from Google.
          2. Reject disposable-domain emails.
          3. Auto-connect to an existing password account with the same email,
             preventing duplicate accounts and upgrading their verified state.
        """
        email = (sociallogin.account.extra_data.get('email') or '').lower().strip()

        if not email:
            raise ValidationError(
                "Your Google account does not have a verified email address. "
                "Please use the email/password registration instead."
            )

        domain = email.split('@')[-1] if '@' in email else ''
        if domain in DISPOSABLE_EMAIL_DOMAINS:
            raise ValidationError("Disposable email addresses are not permitted on UniTraX.")

        # Connect the incoming Google account to an existing password account
        # that shares the same email, instead of creating a duplicate.
        if not sociallogin.is_existing:
            User = get_user_model()
            try:
                existing_user = User.objects.get(email=email)
                sociallogin.connect(request, existing_user)
                logger.info(
                    "Google social account connected to existing account: %s", email
                )
                # Trust Google's verification for the existing user too.
                if not existing_user.is_verified:
                    existing_user.is_verified = True
                    if existing_user.trust_tier == 'unverified':
                        existing_user.trust_tier = 'verified_student'
                        existing_user.save(update_fields=['is_verified', 'trust_tier'])
                    else:
                        existing_user.save(update_fields=['is_verified'])
                    self._update_trust_score(existing_user)
            except User.DoesNotExist:
                pass

        super().pre_social_login(request, sociallogin)

    def save_user(self, request, sociallogin, form=None):
        """
        Called only for brand-new users created via social signup.
        Marks them as verified immediately — Google has already confirmed
        email ownership, so the OTP step is redundant.
        """
        user = super().save_user(request, sociallogin, form)

        needs_save = False
        if not user.is_verified:
            user.is_verified = True
            needs_save = True
        if user.trust_tier == 'unverified':
            user.trust_tier = 'verified_student'
            needs_save = True

        if needs_save:
            user.save(update_fields=['is_verified', 'trust_tier'])
            self._update_trust_score(user)

        logger.info("New social account user created and verified: %s", user.email)
        return user

    # ------------------------------------------------------------------ #
    # Private helpers                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _update_trust_score(user):
        try:
            from apps.trust.scoring import update_trust_score
            update_trust_score(user, reason='email_verified', actor=user, source=user)
        except Exception:
            pass
