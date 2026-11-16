# UniTraX — Redeployment Decision Document

**Date:** 2026-11-16  
**Investigator:** Claude (Sonnet 4.6)  
**Scope:** Combined decision document. No code changes, no deployments, no credential changes made.

---

## 1. Can Google OAuth Be Fixed Without Changing Hosting?

**Yes. The OAuth failure is a configuration problem, not a hosting problem.**

Three independent causes were found, all fixable on Railway without touching the codebase or migrating:

| Cause | Fix location |
|-------|-------------|
| Missing Railway env vars (`SOCIAL_AUTH_GOOGLE_CLIENT_ID`, `SOCIAL_AUTH_GOOGLE_CLIENT_SECRET`) | Railway dashboard → Variables |
| Production redirect URI missing from Google Cloud Console | Google Cloud Console → Credentials → OAuth client |
| `SocialApp` database record possibly empty or in conflict | Django Admin → Social Applications |

None of these require changing the host.

---

## 2. Is Migration Actually Necessary?

**No.** The decision to explore migration appears to have been triggered by the perception that "Railway isn't working." The OAuth failure has nothing to do with Railway. The app's production settings show Railway-awareness was considered carefully (`railway.json` already present, Resend chosen explicitly because Railway blocks outbound SMTP, `SECURE_PROXY_SSL_HEADER` configured).

The only scenario where migration becomes justified is if Railway's billing grows beyond ~$10–15/month as the platform scales and other platforms offer equivalent reliability at lower cost. That is not an emergency decision.

---

## 3. Best Cost-to-Reliability Hosting Provider

**Railway Hobby (~$5/month)** for the current stage.

| Tier | Platform | Monthly cost | Reliability | Effort to migrate |
|------|----------|-------------|-------------|------------------|
| Current | Railway Hobby | ~$5 | Good | 0 (already deployed) |
| Budget alternative | Koyeb Eco | ~$2.69 | Fair | Low |
| Comparable managed | Render Starter | ~$7 | Good | Low |
| Growth path | Hetzner CX22 VPS | ~€3.79 | Manual | Very high |
| Serverless | Google Cloud Run | ~$0–10 | Excellent | High |

Railway Hobby is the right choice now. The team should not migrate during a debugging phase.

---

## 4. What Must Be Completed Before Redeployment

Complete all of these in the order listed before attempting another deployment.

### Step 1 — Fix OAuth configuration (external systems)

**A. Railway Variables** — set both:
```
SOCIAL_AUTH_GOOGLE_CLIENT_ID=<client-id>.apps.googleusercontent.com
SOCIAL_AUTH_GOOGLE_CLIENT_SECRET=<client-secret>
```
Do not leave either blank. These are read-only by the app; they are not logged.

**B. Google Cloud Console** — open your OAuth 2.0 client and add this exact URI to Authorized redirect URIs:
```
https://<your-railway-domain>/accounts/google/login/callback/
```
Include the trailing slash. Keep the development URIs already there.

**C. OAuth consent screen** — if the screen is in "Testing" mode, either publish it to production or add your Google accounts as approved test users.

### Step 2 — Fix database Site record

In Django Admin → Sites → Edit the single record (pk=1):
- **Domain name:** `<your-railway-domain>` (no protocol, no path)
- **Display name:** `UniTraX`

### Step 3 — Add settings to prevent double email verification

Add these two lines to `config/settings/base.py` inside `SOCIALACCOUNT_PROVIDERS['google']` block, or as top-level settings:

```python
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_EMAIL_REQUIRED = False
```

This prevents allauth from triggering its own email confirmation redirect after Google login. UniTraX's own OTP flow handles university email verification separately.

### Step 4 — Write a custom SocialAccountAdapter (required for trust safety)

Without this, any Google account (gmail.com, yahoo.com, etc.) can register on UniTraX and bypass university email domain checks. The adapter must:

1. Check the Google-provided email domain against `OFFICIAL_UNIVERSITY_EMAIL_DOMAINS`.
2. If the domain does not match, reject the signup with a clear error message.
3. If the domain matches, allow signup and trigger the OTP verification flow.

```python
# apps/accounts/adapters.py (new file)
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.core.exceptions import ValidationError


class UniversityEmailSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.account.extra_data.get('email', '')
        domain = email.split('@')[-1].lower() if '@' in email else ''
        allowed_domains = getattr(settings, 'OFFICIAL_UNIVERSITY_EMAIL_DOMAINS', [])
        if allowed_domains and domain not in allowed_domains:
            raise ValidationError(
                f"UniTraX is restricted to {', '.join(allowed_domains)} email addresses. "
                f"Your Google account uses @{domain}."
            )
        super().pre_social_login(request, sociallogin)
```

Then add to settings:
```python
SOCIALACCOUNT_ADAPTER = 'apps.accounts.adapters.UniversityEmailSocialAccountAdapter'
```

**This step is critical for maintaining platform trust safety. Do not deploy Google OAuth without it.**

### Step 5 — Add allauth paths to TrustSafetyMiddleware EXEMPT_PREFIXES

In `apps/trust/middleware.py`, add these to `EXEMPT_PREFIXES`:
```python
'/accounts/google/',
'/accounts/social/',
'/accounts/confirm-email/',
'/accounts/email/',
```

This is a defensive measure — the current middleware does not block OAuth for unauthenticated users, but the exemptions make the intent explicit and prevent future regressions.

### Step 6 — Decide OTP flow for Google-authenticated university emails

Google already verifies email ownership. For university email users who sign in via Google:

**Option A (Recommended for MVP):** Skip the OTP step if the Google-verified email matches a university domain. Set `is_verified = True` immediately in `pre_social_login` or via a post-social-login signal.

**Option B:** Require OTP anyway for all users. This is redundant for Google-authenticated users since Google has already verified they own the email.

Option A reduces friction for legitimate users. Option B is marginally more secure against Google account compromise. Choose based on your trust posture.

---

## 5. Safest Order of Implementation

```
Phase 1 — External systems (no code, no deploy)
─────────────────────────────────────────────
 1. Set SOCIAL_AUTH_GOOGLE_CLIENT_ID in Railway Variables
 2. Set SOCIAL_AUTH_GOOGLE_CLIENT_SECRET in Railway Variables
 3. Add production redirect URI to Google Cloud Console
 4. Verify OAuth consent screen is published (or test users added)
 5. Update Site record in Django Admin (dev database first)

Phase 2 — Code changes (local, then commit)
─────────────────────────────────────────────
 6. Add SOCIALACCOUNT_EMAIL_VERIFICATION = 'none' to base.py
 7. Add SOCIALACCOUNT_EMAIL_REQUIRED = False to base.py
 8. Write apps/accounts/adapters.py (university domain enforcement)
 9. Add SOCIALACCOUNT_ADAPTER to base.py
10. Add allauth paths to TrustSafetyMiddleware EXEMPT_PREFIXES
11. Decide and implement OTP skip for Google-verified university emails

Phase 3 — Local verification
─────────────────────────────────────────────
12. Run dev server locally with SOCIAL_AUTH_GOOGLE_CLIENT_ID set
13. Test full Google OAuth flow: login → callback → account creation
14. Verify non-university Google email is rejected by adapter
15. Verify university Google email proceeds to correct state

Phase 4 — Deploy
─────────────────────────────────────────────
16. Commit code changes (Phases 2 and 3 complete)
17. Push to main (Railway auto-deploys)
18. Verify OAuth callback URI is accessible (visit /accounts/google/login/ in production)
19. Test with a university Google account end-to-end
20. Update Site record in production database via Django Admin
```

---

## 6. What This Investigation Did Not Change

- No code was modified.
- No Railway environment variables were set or changed.
- No Google Cloud Console settings were modified.
- No database records were created or deleted.
- No deployment was made.
- No credentials were exposed.

---

## Appendix: Key Files Referenced

| File | Relevance |
|------|-----------|
| [`config/settings/base.py`](config/settings/base.py) | SOCIALACCOUNT_PROVIDERS, SITE_ID, OFFICIAL_UNIVERSITY_EMAIL_DOMAINS |
| [`config/settings/production.py`](config/settings/production.py) | HTTPS settings, DATABASE_URL, Resend config |
| [`config/urls.py`](config/urls.py) | allauth URL registration path |
| [`apps/accounts/models.py`](apps/accounts/models.py) | Custom User model, username field requirement |
| [`apps/accounts/views.py`](apps/accounts/views.py) | register_view OTP trigger, login_view |
| [`apps/trust/middleware.py`](apps/trust/middleware.py) | TrustSafetyMiddleware EXEMPT_PREFIXES gap |
| [`apps/trust/views.py`](apps/trust/views.py) | OTP verification flow |
| [`templates/accounts/login.html`](templates/accounts/login.html) | Google login button (line 351) |
| [`railway.json`](railway.json) | Railway deploy/build commands |
| [`requirements/base.txt`](requirements/base.txt) | django-allauth version |
| [`GOOGLE_OAUTH_ROOT_CAUSE_REPORT.md`](GOOGLE_OAUTH_ROOT_CAUSE_REPORT.md) | Full OAuth defect analysis |
| [`HOSTING_MIGRATION_ASSESSMENT.md`](HOSTING_MIGRATION_ASSESSMENT.md) | Platform comparison detail |
