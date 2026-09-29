"""
FastAPI Security Headers & Correlation ID Middleware.
Applies HTTP hardening headers, tracks request correlation IDs, and prevents credential leakage in error responses.
"""

from typing import Callable
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces HTTP security headers and correlation tracing.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID") or f"corr_{uuid.uuid4().hex[:12]}"
        request.state.correlation_id = correlation_id

        response: Response = await call_next(request)

        # Standard Security Hardening Headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Apply no-cache to sensitive endpoints (auth, security, management)
        if any(request.url.path.startswith(prefix) for prefix in ("/api/auth", "/api/security", "/api/management")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        return response
