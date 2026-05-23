class SecurityHeadersMiddleware:
    """
    Adds conservative browser hardening headers that are safe for the current
    template-heavy frontend. CSP is report-only until inline scripts/styles are
    refactored into static assets.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        response.setdefault('X-Permitted-Cross-Domain-Policies', 'none')
        response.setdefault('Cross-Origin-Resource-Policy', 'same-origin')
        response.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
        response.setdefault(
            'Content-Security-Policy-Report-Only',
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://accounts.google.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: https:; "
            "media-src 'self' https:; "
            "connect-src 'self'; "
            "frame-src 'self' https://accounts.google.com; "
            "base-uri 'self'; "
            "form-action 'self' https://accounts.google.com;"
        )
        return response
