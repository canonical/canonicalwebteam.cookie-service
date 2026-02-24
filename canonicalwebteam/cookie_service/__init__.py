# __init__.py
import os
from .routes import consent_bp
from .client import CookieServiceClient

# Export main class for package-level imports
__all__ = ["CookieConsent"]


class CookieConsent:
    def init_app(
        self,
        app,
        get_cache_func,
        set_cache_func,
        start_health_check=True,
    ):
        """
        Initializes the cookie consent module.

        :param app: The Flask app object.
        :param get_cache_func: A function that retrieves a value
            from the cache given a key. If the key is not found,
            the function should return None.
        :param set_cache_func: A function that sets a value in the cache
            with a key, value and timeout.
            Signiture: `set_cache_func(key, value, timeout)`
        :param start_health_check: Whether to automatically start the
            health check thread (default: True).
        """

        if os.getenv("COOKIE_SERVICE_DISABLED"):
            return

        self.get_cache = get_cache_func
        self.set_cache = set_cache_func
        self.start_health_check = start_health_check

        # Set default configuration values for the package
        app.config["COOKIE_SERVICE_API_KEY"] = os.getenv(
            "COOKIE_SERVICE_API_KEY", ""
        )
        app.config.setdefault(
            "CENTRAL_COOKIE_SERVICE_URL", "https://cookies.canonical.com"
        )
        app.config.setdefault("PREFERENCES_COOKIE_EXPIRY_DAYS", 365)

        self.client = CookieServiceClient(
            app, self.get_cache, self.set_cache, self.start_health_check
        )
        app.extensions["cookie_consent_client"] = self.client

        app.register_blueprint(consent_bp, url_prefix="/cookies")

        # Periodically ping the cookie service to check its health
        if start_health_check:
            self.client.start_health_check_thread()

        return self
