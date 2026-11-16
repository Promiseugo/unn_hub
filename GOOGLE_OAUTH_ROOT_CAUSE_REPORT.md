# Google OAuth Root Cause Report — UniTraX

**Date:** 2026-11-16  
**Investigator:** Claude (Sonnet 4.6)  
**Scope:** Investigation only. No code changes made.

---

## 1. Existing Implementation Assessment

### Stack
| Component | Value |
|-----------|-------|
| Django | 5.2.15 |
| django-allauth | 65.16.1 |
| Provider | `allauth.socialaccount.providers.google` |
| AUTH_USER_MODEL | `accounts.User` (custom, inherits AbstractUser) |

### What is correctly configured

- `allauth.socialaccount.providers.google` is in `INSTALLED_APPS` (base.py:80).
- `django.contrib.sites` is in `INSTALLED_APPS` (base.py:58), required by allauth.
- `SITE_ID = 1` is set (base.py:45).
- `allauth.account.auth_backends.AuthenticationBackend` is in `AUTHENTICATION_BACKENDS` (base.py:127).
- `allauth.account.middleware.AccountMiddleware` is in `MIDDLEWARE` (base.py:115).
- allauth URLs are registered: `path('accounts/', include('allauth.urls'))` (config/urls.py:30).
- Expected callback URL path: `/accounts/google/login/callback/`.
- Login template references the Google login form correctly with `{% url 'google_login' %}` (templates/accounts/login.html:351).
- `SECURE_PROXY_SSL_HEADER` is set for production (config/settings/production.py:25), enabling HTTPS detection behind Railway's reverse proxy.

### Configuration method used

Credentials are loaded from environment variables and injected into `SOCIALACCOUNT_PROVIDERS['google']['APP']` **conditionally** (base.py:417–423):

```python
GOOGLE_CLIENT_ID = config('SOCIAL_AUTH_GOOGLE_CLIENT_ID', default='')
GOOGLE_CLIENT_SECRET = config('SOCIAL_AUTH_GOOGLE_CLIENT_SECRET', default='')

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    SOCIALACCOUNT_PROVIDERS['google']['APP'] = {
        'client_id': GOOGLE_CLIENT_ID,
        'secret': GOOGLE_CLIENT_SECRET,
        ...
    }
```

If either env var is absent, the `APP` block is never added.

---

## 2. Confirmed Configuration Defects

### DEFECT 1 — Conditional APP block: missing credentials silently disable OAuth (CRITICAL)

**File:** `config/settings/base.py`, lines 414–423  
**Problem:** The `SOCIALACCOUNT_PROVIDERS['google']['APP']` block is only added when both `SOCIAL_AUTH_GOOGLE_CLIENT_ID` and `SOCIAL_AUTH_GOOGLE_CLIENT_SECRET` are non-empty strings. If either variable is missing or blank in the Railway environment, the APP block is silently omitted.

When allauth receives the `APP` block, it uses those credentials directly. When the APP block is absent, allauth falls back to looking for a `SocialApp` database record. If the production database has no `SocialApp` row for Google (which is the default for a fresh deployment), allauth raises:

```
allauth.socialaccount.models.SocialApp.DoesNotExist: SocialApp matching query does not exist.
```

This shows as a 500 error to the user. The OAuth flow never starts.

**Verification step:** In Railway → Variables, check that `SOCIAL_AUTH_GOOGLE_CLIENT_ID` and `SOCIAL_AUTH_GOOGLE_CLIENT_SECRET` are both set and non-empty.

---

### DEFECT 2 — Redirect URI mismatch in Google Cloud Console (CRITICAL)

**Problem:** Google OAuth enforces exact matching between the `redirect_uri` sent by the application and the Authorized Redirect URIs registered in the Google Cloud Console OAuth credential.

The application sends:
```
https://<railway-domain>/accounts/google/login/callback/
```

If the Google Cloud Console only lists development URIs such as:
```
http://localhost:8000/accounts/google/login/callback/
http://127.0.0.1:8000/accounts/google/login/callback/
```

…every production login attempt returns Google's `redirect_uri_mismatch` error (Error 400) and the user never reaches the callback.

**Required Google Cloud Console URI format:**
```
https://<your-exact-railway-domain>/accounts/google/login/callback/
```
The trailing slash is mandatory. HTTP must not be used for production. The domain must exactly match `ALLOWED_HOSTS` and the actual deployed URL.

---

### DEFECT 3 — No `SocialAccountAdapter` to enforce university email domains

**File:** No adapter configured anywhere in the project.  
**Problem:** `OFFICIAL_UNIVERSITY_EMAIL_DOMAINS = ['unn.edu.ng', 'student.unn.edu.ng']` is defined (base.py:30–34), and the OTP flow enforces university emails for password-based registration. However, there is no `SOCIALACCOUNT_ADAPTER` configured in settings, and no custom adapter class exists in the codebase.

When a user signs in with any Google account (e.g., a Gmail address), allauth creates a new account without any domain check. A `gmail.com` account receives `is_verified = False` and `trust_tier = 'unverified'`, but it is still a valid account on the platform. The university email eligibility requirement is entirely bypassed.

**Impact:** Identified as a trust and safety defect (see Part B). Does not cause OAuth to fail, but constitutes a broken verification gate.

---

### DEFECT 4 — `SITE_ID` database entry domain mismatch (MEDIUM)

**Problem:** `SITE_ID = 1` is set, but the `django.contrib.sites.models.Site` record in the production database was created by the initial `migrate` command with the default domain `example.com`. Allauth uses the Sites framework for some URL generation (e.g., email confirmation links). If the site domain is wrong, generated URLs in emails will be incorrect.

This does not directly cause OAuth login failure, but allauth's email-based flows (which may be triggered during social signup if `ACCOUNT_EMAIL_VERIFICATION` is not 'none') will generate links pointing at `example.com`.

**Verification step:** In Django Admin → Sites → check that the single Site entry has the correct production domain (e.g., `unitrax-production.up.railway.app`).

---

### DEFECT 5 — `ACCOUNT_EMAIL_VERIFICATION = 'optional'` without `SOCIALACCOUNT_EMAIL_VERIFICATION`

**File:** `config/settings/base.py`, line 399  
**Problem:** `ACCOUNT_EMAIL_VERIFICATION = 'optional'` is set, but `SOCIALACCOUNT_EMAIL_VERIFICATION` is not explicitly set. By default, allauth inherits the `ACCOUNT_EMAIL_VERIFICATION` value for social accounts. With `'optional'`, allauth may still prompt users to verify their email after a social signup, creating an unexpected redirect to allauth's email confirmation page instead of proceeding to the site.

If users hit `/accounts/confirm-email/` unexpectedly after a Google login, it appears to be a broken OAuth flow but is actually allauth's verification step.

**Recommended fix:** Add `SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'` to `SOCIALACCOUNT_PROVIDERS['google']` to prevent allauth from triggering a secondary email confirmation after social login (the platform's own OTP flow handles this).

---

### DEFECT 6 — `TrustSafetyMiddleware` does not exempt allauth social login paths

**File:** `apps/trust/middleware.py`, lines 15–27  
**Problem:** The middleware EXEMPT_PREFIXES list includes `/accounts/login/` and `/accounts/register/` but does NOT include `/accounts/google/` or `/accounts/social/`. Allauth's social login initiation path is `/accounts/google/login/`, which does not start with `/accounts/login/`.

**Practical impact (low for most users):** The OAuth initiation request is made by an unauthenticated user, so `user.is_authenticated` is False and the middleware takes no action. However, if a logged-in user tries to link a Google account, the middleware runs but only blocks PROTECTED_PREFIXES actions. The OAuth path is not a PROTECTED_PREFIX, so this works correctly. The risk is subtle: if middleware logic is tightened in future, this exemption gap could cause OAuth to be intercepted.

---

## 3. Expected vs Actual Authentication Flow

### Expected flow (working)
```
User clicks "Sign in with Google"
  → POST /accounts/google/login/?process=login
  → allauth reads APP credentials from SOCIALACCOUNT_PROVIDERS
  → allauth builds authorization URL with client_id and redirect_uri
  → 302 redirect → Google authorization page
  → User grants permission
  → Google 302 → /accounts/google/login/callback/?code=...&state=...
  → allauth verifies state token (anti-CSRF)
  → allauth exchanges code for access token with Google
  → allauth fetches user profile (email, name) from Google
  → allauth matches email → existing User or creates new User
  → allauth creates SocialAccount record
  → allauth calls login() to establish Django session
  → 302 redirect → LOGIN_REDIRECT_URL (/)
```

### Actual flow (failing)

**Failure mode A (most likely):** No APP credentials in Railway environment  
```
User clicks "Sign in with Google"
  → POST /accounts/google/login/?process=login
  → allauth looks for SOCIALACCOUNT_PROVIDERS['google']['APP'] → not present
  → allauth queries SocialApp.objects.get(provider='google', sites__id=SITE_ID)
  → SocialApp.DoesNotExist raised
  → Django 500 error (no Google app configured)
```

**Failure mode B:** Redirect URI mismatch  
```
User clicks "Sign in with Google"
  → allauth builds authorization URL with correct client_id
  → 302 redirect → Google authorization page  ← this succeeds
  → User grants permission
  → Google rejects callback: redirect_uri does not match registered URIs
  → Google returns: Error 400: redirect_uri_mismatch
  → User sees Google's error page, never returns to UniTraX
```

---

## 4. Potential Causes Requiring External Verification

| Cause | Where to verify |
|-------|----------------|
| `SOCIAL_AUTH_GOOGLE_CLIENT_ID` empty or missing | Railway dashboard → Variables |
| `SOCIAL_AUTH_GOOGLE_CLIENT_SECRET` empty or missing | Railway dashboard → Variables |
| Production redirect URI not in Google Cloud Console | Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client ID → Authorized redirect URIs |
| OAuth consent screen in "Testing" mode (only test users allowed) | Google Cloud Console → APIs & Services → OAuth consent screen → Publishing status |
| Wrong SITE_ID domain in database | Django Admin → Sites |
| SocialApp database record conflicts with settings APP block | Django Admin → Social Applications |

---

## 5. Required Google Cloud Console Settings

Navigate to: **Google Cloud Console → APIs & Services → Credentials → [your OAuth 2.0 Client ID]**

Under **Authorized redirect URIs**, add all of the following:
```
http://localhost:8000/accounts/google/login/callback/
http://127.0.0.1:8000/accounts/google/login/callback/
https://<your-railway-production-domain>/accounts/google/login/callback/
```

Replace `<your-railway-production-domain>` with the exact domain shown in the Railway service (e.g., `unitrax.up.railway.app`). Include the trailing slash.

Under **OAuth consent screen**:
- Publishing status must be **In production** (not "Testing") unless you will only test with approved test users.
- Scopes: `openid`, `email`, `profile` are sufficient.

---

## 6. Required Django Configuration

### Environment variables (Railway)
```
SOCIAL_AUTH_GOOGLE_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
SOCIAL_AUTH_GOOGLE_CLIENT_SECRET=<your-client-secret>
SITE_ID=1
```

### Django database (one-time)
1. In Django Admin → Sites → change the single entry:
   - **Domain name:** `<your-railway-domain>` (no protocol, no trailing slash)
   - **Display name:** `UniTraX`

2. If you are NOT using the env-var APP approach (not recommended for this codebase), create a SocialApp in Django Admin → Social Applications:
   - Provider: Google
   - Client id: `<your-client-id>`
   - Secret key: `<your-secret>`
   - Sites: add Site #1

   **Do not** create a SocialApp in the database if you are using the env-var APP approach — having both causes duplicate lookup confusion in some allauth versions.

### Recommended settings additions (to config/settings/base.py)
```python
# Prevent allauth from triggering its own email verification after social login.
# UniTraX uses its own OTP flow for this.
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_EMAIL_REQUIRED = False

# Explicitly set for clarity (already implied by ACCOUNT_SIGNUP_FIELDS)
ACCOUNT_USERNAME_REQUIRED = False
```

---

## 7. Safe Verification Steps

1. **Confirm Railway env vars exist** (do not reveal values): open Railway → Service → Variables → check `SOCIAL_AUTH_GOOGLE_CLIENT_ID` and `SOCIAL_AUTH_GOOGLE_CLIENT_SECRET` are present and non-empty.

2. **Confirm Google Cloud Console redirect URI**: open Google Cloud Console → Credentials → OAuth client → verify the production domain is in Authorized redirect URIs.

3. **Confirm OAuth consent screen is published**: check Publishing status is "In production" (or add your Google account as a test user if staying in Testing mode).

4. **In development**: navigate to `/accounts/google/login/` while `DEBUG=True`. If you see a 500 error referencing `SocialApp.DoesNotExist`, the APP block is missing. If you see Google's error page, it's a redirect URI mismatch.

5. **Check Site record**: in Django Admin (dev or prod) → Sites → confirm pk=1 has the correct domain.

---

## 8. Recommended Correction (Priority Order)

1. **Set Railway env vars** `SOCIAL_AUTH_GOOGLE_CLIENT_ID` and `SOCIAL_AUTH_GOOGLE_CLIENT_SECRET` with valid credentials from Google Cloud Console.

2. **Add production redirect URI** to Google Cloud Console's Authorized redirect URIs.

3. **Update the Site record** in the database to the correct production domain.

4. **Add `SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'`** to settings to prevent double email verification prompts.

5. **Write a custom `SocialAccountAdapter`** (see Part B) to enforce university email domain restrictions on social signup.

6. **Add allauth OAuth paths to `TrustSafetyMiddleware` EXEMPT_PREFIXES** as defensive measure:
   ```python
   '/accounts/google/',
   '/accounts/social/',
   '/accounts/confirm-email/',
   ```

---

*This report is an investigation only. No changes have been made to the codebase, database, Google Cloud Console, or Railway configuration.*
