# routes.py
import flask
from flask import request, jsonify, redirect, Blueprint, current_app
from urllib.parse import urlencode
from .helpers import (
    set_cookies_accepted_with_ts,
    get_client,
    is_safe_return_uri,
    is_secure_context,
    get_serializer,
    delete_cookie_auth_tokens,
    extract_user_uuid_from_signed_cookie
)
from .exceptions import UserNotFoundException


consent_bp = Blueprint("cookie_consent", __name__)


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
        "_cookie_auth_token",
        signed_cookie,
        httponly=True,
        samesite="Lax",
        secure=is_secure_context(),
        max_age=31536000,
    )

    # Set authentication flag (for client-side checks)
    response.set_cookie(
        "_cookie_authenticated",
        "true",
        httponly=False,
        samesite="Lax",
        secure=is_secure_context(),
        max_age=31536000
    )

    try:
        preferences = client.fetch_preferences(user_uuid)
        if preferences and preferences.get("preferences"):
            consent = preferences["preferences"].get("consent")
            if consent:
                set_cookies_accepted_with_ts(response, consent)
    except UserNotFoundException:
        # The user creation failed, clear associated cookies
        delete_cookie_auth_tokens(response)
        return response

    return response


@consent_bp.route("/get-preferences", methods=["GET"])
def get_preferences():
    """
    Retrieves the user's ID from their session and fetches their preferences.
    """
    user_uuid = extract_user_uuid_from_signed_cookie()
    if not user_uuid:
        return jsonify({"error": "Not authenticated"}), 401

    preferences = get_client().fetch_preferences(user_uuid)
    return jsonify(preferences), 200


@consent_bp.route("/set-preferences", methods=["POST"])
def set_preferences():
    """
    Retrieves the user's ID from their session and sets new preferences.
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

    return jsonify({"message": "Preferences saved"}), 200
