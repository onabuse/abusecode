import hmac
import secrets
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, RedirectResponse

from . import config

SESSION_SECRET = config.SESSION_SECRET or secrets.token_hex(32)

# Paths that never require dashboard auth.
PUBLIC_PATHS = {"/login", "/api/login", "/api/health", "/favicon.ico"}


def auth_enabled():
    return bool(config.ADMIN_TOKEN)


def proxy_authorized(request):
    if not config.PROXY_TOKEN:
        return True
    token = request.headers.get("x-proxy-token", "")
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:]
    return bool(token) and hmac.compare_digest(token, config.PROXY_TOKEN)


def check_admin_token(token):
    if not auth_enabled():
        return True
    return bool(token) and hmac.compare_digest(token, config.ADMIN_TOKEN)


def is_same_origin(request):
    """True for browser requests originating from this dashboard itself.

    The built-in playground calls /v1 from the same origin. When a proxy token
    is configured we still allow those dashboard calls through, while external
    clients must present the token.
    """
    if request.headers.get("sec-fetch-site") == "same-origin":
        return True
    host = request.headers.get("host", "")
    for header in ("origin", "referer"):
        value = request.headers.get(header) or ""
        if value and urlparse(value).netloc == host:
            return True
    return False


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path

        if request.method == "OPTIONS":
            return await call_next(request)
        if path.startswith("/static") or path in PUBLIC_PATHS:
            return await call_next(request)

        # Proxy has its own optional token and must stay API-friendly.
        if path.startswith("/v1/"):
            if proxy_authorized(request) or is_same_origin(request):
                return await call_next(request)
            return JSONResponse(
                {
                    "error": {
                        "type": "unauthorized",
                        "message": "Invalid or missing proxy token.",
                    }
                },
                status_code=401,
            )

        if not auth_enabled() or request.session.get("auth") is True:
            return await call_next(request)

        if path.startswith("/api/"):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return RedirectResponse("/login", status_code=303)
