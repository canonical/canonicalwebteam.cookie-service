# routes.py
from datetime import datetime, timezone
import flask
from flask import request, jsonify, redirect, Blueprint, current_app

from .helpers import (
    get_client,
    is_safe_return_uri,
    is_secure_context,
    get_serializer,
    extract_user_uuid_from_signed_cookie,
    check_cookie_stale,
)


consent_bp = Blueprint("cookie_consent", __name__)


def _make_set_preferences_response(consent: dict):
    """Build a standard 'set_preferences' response payload."""
    return (
        jsonify(
            {
                "action": "set_preferences",
                "consent": consent,
                "cookies_freshness_ts": datetime.now(timezone.utc).isoformat(),
            }
        ),
        200,
    )


@consent_bp.route("/init")
def init():
    user_uuid = extract_user_uuid_from_signed_cookie()
    service_url = current_app.config["CENTRAL_COOKIE_SERVICE_URL"]
    redirect_url = f"{service_url}/api/v1/cookies/session?return_uri="
    cookies_accepted = request.cookies.get("_cookies_accepted")

    if not get_client().is_service_up():
        return jsonify({"error": "Cookie service not available"}), 503

    # User not authenticated, redirect to central service
    if not user_uuid and not request.cookies.get(
        "_cookies_redirect_attempted"
    ):
        return (
            jsonify({"action": "redirect", "redirect_url": redirect_url}),
            200,
        )
    elif user_uuid:
        # Sync cookies set while offline
        if request.cookies.get("_cookies_set_offline"):
            remote_preferences = get_client().fetch_preferences(user_uuid)
            remote_cookie_ts = remote_preferences["updated_at"]
            local_cookie_ts = request.cookies.get("_cookies_freshness_ts")

            if (
                remote_cookie_ts
                and local_cookie_ts
                and remote_cookie_ts < local_cookie_ts
            ):
                result = get_client().post_preferences(
                    user_uuid, {"preferences": {"consent": cookies_accepted}}
                )

                if result:
                    response = jsonify(
                        {"action": "offline_preferences_synced"}
                    )
                    response.delete_cookie("_cookies_set_offline")
                    return response, 200

                return (
                    jsonify({"error": "Failed to sync offline preferences"}),
                    502,
                )
            else:
                return _make_set_preferences_response(
                    remote_preferences["preferences"]["consent"]
                )

        # Refresh stale cookies
        if check_cookie_stale() or not cookies_accepted:
            preferences = get_client().fetch_preferences(user_uuid)[
                "preferences"
            ]
            return _make_set_preferences_response(preferences["consent"])

    return jsonify({"action": "none"}), 200


@consent_bp.route("/callback")
def callback():
    """
    - Handles the redirect from the central service.
    - Exchanges the code for a user_uuid.
    - Stores the user_uuid in the secure HttpOnly cookie.
    """
    code = request.args.get("code")
    return_uri = request.args.get("return_uri") or "/"
    if not is_safe_return_uri(return_uri):
        return_uri = "/"

    if not code:
        return jsonify({"error": "No code provided"}), 400

    client = get_client()
    data = client.exchange_code_for_uuid(code)

    if data is None:
        return jsonify({"error": "Failed to exchange code"}), 500

    user_uuid = data.get("user_uuid")

    if not user_uuid:
        return jsonify({"error": "No user_uuid in response"}), 500

    serializer = get_serializer()
    signed_cookie = serializer.dumps(user_uuid)

    response = flask.make_response(redirect(return_uri))

    # Set the authentication cookie
    response.set_cookie(
        "_cookies_auth_token",
        signed_cookie,
        httponly=True,
        samesite="Lax",
        secure=is_secure_context(),
        max_age=31536000,
    )

    # Set a flag cookie to avoid redirect loops
    response.set_cookie(
        "_cookies_redirect_attempted",
        "1",
        max_age=300,
        httponly=True,
        samesite="Lax",
    )

    return response


@consent_bp.route("/get-preferences", methods=["GET"])
def get_preferences():
    """
    Retrieves the user's ID from their session cookie
    and fetches their preferences.
    """
    user_uuid = extract_user_uuid_from_signed_cookie()
    if not user_uuid:
        return jsonify({"error": "Not authenticated"}), 401

    preferences = get_client().fetch_preferences(user_uuid)
    return jsonify(preferences), 200


@consent_bp.route("/set-preferences", methods=["POST"])
def set_preferences():
    """
    Retrieves the user's ID from their session cookie
    and sets new preferences.
    It also sets a timestamp cookie to indicate freshness.
    """
    user_uuid = extract_user_uuid_from_signed_cookie()
    if not user_uuid:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.json
    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    result = get_client().post_preferences(user_uuid, data)
    if result is None:
        return jsonify({"error": "Failed to save preferences"}), 500

    cookies_freshness_ts = datetime.now(timezone.utc).isoformat()

    return (
        jsonify(
            {
                "message": "Preferences saved",
                "cookies_freshness_ts": cookies_freshness_ts,
            }
        ),
        200,
    )
