# UniTraX Trust & Safety Architecture

## Implemented controls

- University email registration gate using `OFFICIAL_UNIVERSITY_EMAIL_DOMAINS`.
- OTP email verification and middleware enforcement before posting, messaging, reviews, and interactions.
- Safety acknowledgement before high-risk flows.
- Optional student ID verification with admin review.
- Trust score and badge foundation: Verified Student, Trusted Seller, Top Rated Seller.
- Generic report model for listings, users, chats/messages, scams, harassment, and suspicious behavior.
- Suspicious activity, audit log, moderation log, and active user restriction models.
- Listing approval workflow with automatic risk scoring.
- Prohibited-item keyword detection and contact-info detection in listings.
- In-app message contact redaction, moderation status, and original-message retention for review.
- Admin moderation views for reports, suspicious activity, student ID checks, restrictions, audit logs, and listing approvals.

## Known risks and attack vectors

- Email domain verification does not prove current enrollment. Add registrar/SSO integration when possible.
- OTP delivery depends on mail infrastructure. Use a transactional provider with SPF, DKIM, DMARC, bounce handling, and abuse monitoring.
- Keyword fraud detection is bypassable. Attackers can use misspellings, screenshots, coded language, or image-only listings.
- Phone/email redaction is not a complete off-platform prevention system. Fraudsters can split numbers across messages or use image attachments.
- Trust scores can be gamed with collusive reviews and fake transactions unless transaction completion is verified.
- IP-based controls are weak against VPNs, NATed campus networks, and mobile networks.
- Device fingerprinting must be privacy-aware and disclosed; avoid invasive browser fingerprinting without a legal basis.
- Image moderation currently has hooks only. Production should use background scanning and quarantine before public display.

## Production recommendations

- Move PostgreSQL to managed backups with point-in-time recovery and encrypted storage.
- Add Redis-backed rate limiting for login, OTP, posting, messaging, report submission, and image uploads.
- Add Celery jobs for image moderation, duplicate listing detection, trust score recomputation, and suspicious activity aggregation.
- Add perceptual image hashing to detect duplicate/scam listings.
- Add payment escrow or at least structured "transaction completed" confirmations before increasing seller reputation.
- Add moderator roles/groups and object-level permission checks for moderation actions.
- Add immutable audit logging for sensitive moderation events.
- Add CSP, HSTS, secure cookies, trusted proxy settings, and malware scanning for uploaded media in production.
- Keep personal contact details hidden by default; prefer masked, expiring reveal flows only after both users acknowledge risk.
- Add reviewer/reporter reputation controls to reduce malicious reporting and review brigading.
