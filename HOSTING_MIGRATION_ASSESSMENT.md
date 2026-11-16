# Hosting Migration Assessment — UniTraX

**Date:** 2026-11-16  
**Investigator:** Claude (Sonnet 4.6)  
**Scope:** Investigation only. No deployment changes made.

---

## 1. Current Infrastructure

| Layer | Current setup |
|-------|--------------|
| Hosting | Railway (plan unknown) |
| WSGI server | Gunicorn, 2 workers + 2 threads, gthread class |
| Framework | Django 5.2.15 |
| Database | Neon (PostgreSQL, external, via `DATABASE_URL`) |
| Media storage | Cloudinary (optional) or S3 (optional) or local disk |
| Static files | WhiteNoise (served from Django process) |
| Email | Resend via django-anymail (HTTP, not SMTP) |
| Background tasks | None identified (no Celery, no Django-Q) |
| Cache | Redis (optional, falls back to local-memory) |

**Key architectural decisions already made:**
- Neon is used as an external database — not collocated with the host.
- Cloudinary/S3 for media — not tied to the host's filesystem.
- Resend for email — HTTP-based, works on all platforms.
- WhiteNoise for static files — no CDN or separate static host needed.
- No persistent local disk required (logs go to stdout in production).

These decisions mean the app is **highly portable**. Migration is a matter of re-deploying a single container or Procfile-based app, not re-architecting storage.

---

## 2. Platform Compatibility Assessment

### 2a. Railway Hobby ($5/month)

| Criterion | Assessment |
|-----------|-----------|
| Deployment | Nixpacks auto-detects Python/Django from requirements.txt. `railway.json` already present. |
| Docker | Not required (Nixpacks). Dockerfile optional. |
| Env vars | Full support. All secrets in Railway Variables. |
| Database | Neon stays external. `DATABASE_URL` env var supported. |
| Static files | WhiteNoise serves from Django process. No separate step needed. |
| Media | Cloudinary or S3 (env-based). Not stored on Railway. |
| Background tasks | Not present. If added: needs a separate Railway service or cron. |
| Logging | Stdout captured. No persistent log files needed. |
| HTTPS | Railway provides automatic TLS on `*.up.railway.app` and custom domains. |
| Custom domain | Supported on Hobby. |
| OAuth callback | Full HTTPS support. Add `https://your-domain/accounts/google/login/callback/` to Google Console. |
| SMTP | **Blocked** on Hobby (ports 25/465/587). App already uses Resend (HTTP). No impact. |
| Monthly cost | ~$5/month (resource-based billing). ~512MB RAM included. |
| Resource limits | 512MB RAM. Enough for 2 Gunicorn workers at typical Django memory (~80MB/worker). |
| Persistent storage | Not available on Hobby. Irrelevant since all storage is external. |
| Reliability | Shared infrastructure. Single-instance. No HA. |
| Migration effort | **Minimal** — `railway.json` and Procfile already in repo. |

**Verdict:** Lowest migration effort. Already configured. Best choice if current billing is the issue.

---

### 2b. Google Cloud Run (pay-per-request)

| Criterion | Assessment |
|-----------|-----------|
| Deployment | Requires Dockerfile. Django needs `gunicorn` on PORT env var. `railway.json` not applicable. |
| Docker | **Required**. Must write Dockerfile or use Cloud Buildpacks. |
| Env vars | Google Secret Manager or Cloud Run env vars. More complex than Railway. |
| Database | Neon stays external. Cloud SQL Proxy not needed (Neon is already cloud). |
| Static files | WhiteNoise works. Cloud Run serves HTTPS. |
| Media | Cloudinary or S3. No change needed. |
| Background tasks | Not supported natively. Would need Cloud Tasks or Cloud Scheduler. |
| Logging | Stdout captured by Cloud Logging. |
| HTTPS | Automatic TLS on `*.run.app` and custom domains. |
| Custom domain | Supported via Cloud Run domain mapping or Load Balancer. |
| OAuth callback | Full HTTPS. |
| SMTP | Not blocked (not relevant — using Resend). |
| Monthly cost | ~$0–$10/month at low traffic (scales to zero between requests). CPU charged per request. |
| Resource limits | Min 128MB RAM (256MB recommended for Django). Max configurable. |
| Cold starts | Django apps have ~2–5s cold starts on Cloud Run at zero instances. Can set min-instances=1 to avoid. |
| Migration effort | **High** — Dockerfile needed, GCP IAM setup, project creation, service account, etc. |

**Verdict:** Cost-efficient for irregular traffic. Overkill for a campus marketplace. High setup complexity.

---

### 2c. Render (free tier deprecated; Starter ~$7/month)

| Criterion | Assessment |
|-----------|-----------|
| Deployment | Auto-detects Python. `gunicorn` start command set in Dashboard or `render.yaml`. |
| Docker | Optional. Can use Render's Python buildpack. |
| Env vars | Render Environment Variables. Secret Files for `.env`. |
| Database | Neon stays external. `DATABASE_URL` env var supported. |
| Static files | WhiteNoise. Render's CDN optional. |
| Media | Cloudinary or S3. No change. |
| Background tasks | Render Background Workers (separate service). |
| Logging | Stdout + Render log stream. |
| HTTPS | Automatic on `*.onrender.com` and custom domains. |
| Custom domain | Supported on paid plans. |
| OAuth callback | Full HTTPS. |
| SMTP | Not blocked. |
| Monthly cost | ~$7/month (Starter). Free tier spins down after 15 minutes (not suitable for production). |
| Resource limits | 512MB RAM on Starter. Similar to Railway Hobby. |
| Reliability | Auto-restart. Sleep-free on paid tier. |
| Migration effort | **Low** — `Procfile` usable, minor dashboard configuration. |

**Verdict:** Comparable to Railway. Slightly more expensive. Render's free tier is not suitable for production.

---

### 2d. Koyeb (free-tier with limitations; Eco ~$2.69/month)

| Criterion | Assessment |
|-----------|-----------|
| Deployment | Docker or Git-based. Auto-detect Python. `gunicorn` start command. |
| Docker | Optional. Koyeb supports `Procfile`-based deployments. |
| Env vars | Koyeb Secrets and Service env vars. |
| Database | Neon stays external. Standard `DATABASE_URL`. |
| Static files | WhiteNoise. |
| Media | Cloudinary or S3. |
| Background tasks | Not natively supported as a separate process. |
| Logging | Stdout captured. |
| HTTPS | Automatic on `*.koyeb.app` and custom domains. |
| Custom domain | Supported. |
| OAuth callback | Full HTTPS. |
| SMTP | Not blocked. |
| Monthly cost | ~$2.69/month (Eco plan, 512MB RAM). Free tier available but has cold starts and sleep. |
| Resource limits | 512MB RAM on Eco. 0.1 vCPU (shared). May be tight under load. |
| Migration effort | **Low-medium** — Koyeb dashboard is straightforward but less mature than Railway/Render. |

**Verdict:** Cheapest paid option. Limited CPU on Eco plan may cause slow responses under load. Good for low-traffic MVP.

---

### 2e. Hetzner Cloud VPS (CX22: €3.79/month)

| Criterion | Assessment |
|-----------|-----------|
| Deployment | Full Linux VPS. Manual: nginx, supervisor/systemd, gunicorn. Or Docker Compose. |
| Docker | Optional but strongly recommended for maintainability. |
| Env vars | `.env` file on server or Docker secrets. Must secure access. |
| Database | Neon stays external. Standard `DATABASE_URL`. |
| Static files | nginx serves `/staticfiles/` directly (better than WhiteNoise alone). |
| Media | Cloudinary or S3 recommended (avoid local disk for media on a VPS without a volume). |
| Background tasks | Celery with Redis, or systemd timers. Full control. |
| Logging | Configured via nginx + journald. |
| HTTPS | Let's Encrypt via certbot or Caddy. |
| Custom domain | Full control. |
| OAuth callback | Full HTTPS once TLS is set up. |
| SMTP | Not blocked. |
| Monthly cost | €3.79/month (CX22: 2 vCPU, 4GB RAM). Significantly more resources for less money. |
| Resource limits | 4GB RAM, 2 vCPU. Easily handles Django + multiple workers. |
| Operational complexity | **Very high** — OS updates, security patches, backups, TLS renewal, monitoring all manual. |
| Migration effort | **High** — Server provisioning, nginx config, gunicorn systemd unit, TLS, firewall. |
| Reliability | Single-instance VPS. No automatic HA. Manual failover. |

**Verdict:** Best raw value for money. Unsuitable for a solo/small team unless someone has Linux server administration experience. Failure risk higher than managed platforms.

---

## 3. Comparison Table

| Platform | Monthly cost (est.) | RAM | Setup effort | Reliability | OAuth | SMTP | Static | PaaS managed |
|----------|-------------------|-----|-------------|-------------|-------|------|--------|-------------|
| **Railway Hobby** | ~$5 | 512MB | **Minimal** (already set up) | Good | ✓ | ✗ (Resend OK) | WhiteNoise | ✓ |
| Render Starter | ~$7 | 512MB | Low | Good | ✓ | ✓ | WhiteNoise | ✓ |
| Koyeb Eco | ~$2.69 | 512MB | Low-medium | Fair | ✓ | ✓ | WhiteNoise | ✓ |
| Cloud Run | ~$0–10 | Configurable | High | Excellent | ✓ | ✓ | WhiteNoise | ✓ |
| Hetzner CX22 | ~€3.79 | 4GB | Very high | Manual | ✓ | ✓ | nginx | ✗ |

---

## 4. Database: Neon

Neon is already external to Railway and all other platforms. No migration is needed regardless of which host is chosen. The existing pooled/direct URL split (`DATABASE_URL` for app, `DATABASE_MIGRATE_URL` for migrate) works identically on all platforms.

**Recommendation:** Keep Neon as-is.

---

## 5. Media Storage

If `USE_CLOUDINARY=True` or `USE_S3=True` in env vars, media is already external. If neither is set, media is stored on the host's local filesystem — which is ephemeral on all PaaS platforms. For production, one of Cloudinary or S3 must be enabled.

**Recommendation:** Set `USE_CLOUDINARY=True` with valid Cloudinary credentials in the deployment environment. This is already implemented in `production.py`.

---

## 6. Railway Affordability Assessment

Railway Hobby plan pricing is resource-based. A Django app with 2 Gunicorn workers at typical idle RAM of ~150–180MB total, running 24/7, falls within ~$5/month. If the current plan is Railway's older "Starter" or a trial, switching to Hobby resolves billing.

**The OAuth failure is unrelated to hosting affordability.** Google OAuth was failing due to missing/incorrect configuration (see `GOOGLE_OAUTH_ROOT_CAUSE_REPORT.md`), not due to Railway's platform limitations.

---

## 7. Recommendation

**Stay on Railway Hobby** and fix the Google OAuth configuration.

**Reasoning:**
1. The `railway.json`, `Procfile`, and production settings are already Railway-specific. Zero additional infrastructure work needed.
2. The OAuth failure is a configuration problem, not a hosting problem. It will occur on any platform with the same misconfiguration.
3. Neon, Cloudinary/S3, and Resend remain unchanged regardless of host choice.
4. Railway Hobby at ~$5/month is appropriate for a live campus MVP. It is not a "free tier" — it is a paid, managed platform with TLS and auto-deploy from Git.
5. Migrating to another platform now would add work and risk without fixing the root cause.

**If cost escalates** (Railway bills spike due to traffic), the next migration path in order of effort is:
1. **Render** (Procfile reuse, ~$7/month)
2. **Koyeb Eco** (~$2.69/month, lowest cost managed option)
3. **Hetzner VPS** (only if the team has server administration capacity)

Do not migrate to Cloud Run unless the team has GCP experience and expects pay-per-request billing to be cheaper than flat-rate plans.

---

*This report is an investigation only. No deployment changes have been made.*
