# helpers.py
from flask import request, current_app
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def get_serializer():
    secret_key = current_app.config["SECRET_KEY"]
    return URLSafeTimedSerializer(secret_key, salt="cookie-consent-signer")


def extract_user_uuid_from_signed_cookie():
    signed_cookie = request.cookies.get("_cookies_auth_token")
    if not signed_cookie:
        return None
    serializer = get_serializer()
    try:
        user_uuid = serializer.loads(signed_cookie, max_age=31536000)
        return user_uuid
    except (BadSignature, SignatureExpired):
        return None


def get_client():
    return current_app.extensions["cookie_consent_client"]


def is_secure_context():
    """
    Determine if we are in development (not secure)
    or production (secure).
    """
    return not bool(current_app.debug)


def check_cookie_stale() -> bool:
    """Check if cookie is older than 1 day."""
    timestamp_cookie = request.cookies.get("_cookies_freshness_ts")
    if not timestamp_cookie:
        return True

    try:
        timestamp = datetime.fromisoformat(timestamp_cookie)
        return datetime.now(timezone.utc) - timestamp > timedelta(days=1)
    except Exception:
        return True


def is_safe_return_uri(uri):
    p = urlparse(uri)
    return not p.scheme and not p.netloc
