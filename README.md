# Canonical Cookie Service Integration

A Flask extension for integrating with the Canonical shared cookie consent service. This package handles user consent preferences, session management, and synchronization with a central cookie service.

## Installation

```bash
pip install canonicalwebteam.cookie_service
```

Or add to your `requirements.txt`:
```
canonicalwebteam.cookie-service
```

### Frontend Dependency

This package requires the [cookie-policy](https://github.com/canonical/cookie-policy/) npm package (version 4.8.0 or above) for client-side cookie management:

## Quick Start

```python
from flask import Flask
from canonicalwebteam.cookie_service import CookieConsent

app = Flask(__name__)

# Required: Set up cache functions (see Cache Integration section)
def get_cache(key):
    return your_cache.get(key)

def set_cache(key, value, timeout):
    your_cache.set(key, value, timeout)

# Initialize the cookie consent service
cookie_service = CookieConsent().init_app(
    app,
    get_cache_func=get_cache,
    set_cache_func=set_cache,
    start_health_check=True,  # Optional: default True
)
```

## Configuration

### Required Environment Variables

```bash
export COOKIE_SERVICE_API_KEY="your-api-key-here"
```

### Optional Enviroment Variables

```bash
export COOKIE_SERVICE_START="true"
```

By default the service will start, it is recommended adding this to your `.env` by defualt to prevent this. 

### Optional Configuration

These can be set in your Flask app config and have the following defaults:

```python
# URL of the central cookie service (default: production)
app.config["CENTRAL_COOKIE_SERVICE_URL"] = "https://cookies.canonical.com" # Useful for testing with locally or with https://cookies.staging.canonical.com

# Number of days before preference cookies expire (default: 365)
app.config["PREFERENCES_COOKIE_EXPIRY_DAYS"] = 365
```

## Cache Integration

The package requires integration with a caching system to store the health check status of the cookie service. This prevents excessive API calls and improves performance.

### Cache Function Requirements

You must provide two functions:

#### `get_cache_func(key)`
Retrieves a value from the cache.
- **Parameters:** `key` (str) - The cache key
- **Returns:** The cached value or `None` if not found

#### `set_cache_func(key, value, timeout)`
Stores a value in the cache with a timeout.
- **Parameters:**
  - `key` (str) - The cache key
  - `value` (any) - The value to cache
  - `timeout` (int) - TTL in seconds

#### Using Flask-Caching:
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

def get_cache(key):
    return cache.get(key)

def set_cache(key, value, timeout):
    cache.set(key, value, timeout=timeout)
```

## Initialization Parameters

### `init_app(app, get_cache_func, set_cache_func, start_health_check=True)`

#### Required Parameters:
- **`app`**: Flask application instance
- **`get_cache_func`**: Function to retrieve cached values (see Cache Integration)
- **`set_cache_func`**: Function to store cached values (see Cache Integration)

#### Optional Parameters:
- **`start_health_check`** (bool, default: `True`)
  - Starts a background thread that pings the cookie service every 15 seconds
  - The health status is cached and used to determine whether to redirect users to the service
  - Set to `False` to disable health checks (not recommended for production)
  - Common pattern: `start_health_check=not app.debug` (only run in production)


## Linting

This project uses tox for linting, the config is found in [tox.ini](/tox.ini)

It exposes the following commands that run on files within /canonicalwebteam:

- `tox -e lint`
- `tox -e format`

## How It Works

The system works by creating a session within the central service with an ID. This same ID is used to create an encrypted cookie on each site the user visits, creating an association. This ID can then be used to fetch preferences.

### 1. Autherization Flow

1. User visits your site
2. The client calls `/cookies/init` and checks for a user auth cookie
3. If no cookie exists, user is redirected to the central cookie service
4. The cookie service creates a session (as https://cookies.canonical.com) and redirects back to `/cookies/callback?code=<code>`
5. The callback exchanges the code for a `user_uuid` and stores it in an encrypted cookie for future use
6. User is redirected back to their original destination

## Routes Provided

The package automatically registers the following routes under `/cookies`:

- **`/cookies/init`** - Is called on each pay load, directs the client on what action to take (redirect/fetch prefs/sync prefs/nothing)
- **`/cookies/callback`** - Handles OAuth-style callback from the central service
- **`/cookies/get-preferences`** - API endpoint to fetch current user's preferences
- **`/cookies/set-preferences`** - API endpoint to update current user's preferences (called by cookie-policy package)

## Cookies Set by This Package

| Cookie Name | Purpose | Lifetime | Attributes |
|-------------|---------|----------|------------|
| `_cookies_auth_token` | Encrypted cookie containing `user_uuid` | 365 days | HttpOnly, Secure, SameSite=Lax |
| `_cookies_redirect_attempted` | Prevents redirect loops | Session | Secure, SameSite=Lax |

**Cookies set my the JS module [cookie-policy](https://github.com/canonical/cookie-policy) also include**

| Cookie Name | Purpose | Lifetime | Attributes |
|-------------|---------|----------|------------|
| `_cookies_accepted` | Encrypted cookie containing `user_uuid` | 365 days | HttpOnly, Secure, SameSite=Lax |
| `_cookies_freshness_ts` | Prevents redirect loops | 365 days | Secure, SameSite=Lax |
| `_cookies_set_offline` | Used to sync offline cookies | Session | Secure, SameSite=Lax |

## Support

- Report issues: [GitHub Issues](https://github.com/canonical/canonicalwebteam.cookie-service/issues)
- Reach out to Web Engineering.

