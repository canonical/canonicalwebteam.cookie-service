### 2.1.0 [06-03-2026]
**Requires [cookie-policy](https://github.com/canonical/cookie-policy) npm package 3.9.0**
* Updates paths to `/_cookies`

### 2.0.0 [22-12-2025]
**Requires [cookie-policy](https://github.com/canonical/cookie-policy) npm package 3.9.0**
* Add '/cookies/init' to run on each page request and return user preferences or an action to the client.
* The following have been removed and are now handled client side by the [cookie-policy npm package](https://github.com/canonical/cookie-policy)
  - Redirecting
  - Before and after request hooks
  - Setting cookie preferences

### 1.0.5 [17-12-2025]
- Don't cache the redirect responses

### 1.0.4 [16-12-2025]
- Don't raise an error on missing API key

### 1.0.3 [16-12-2025]
- Skip `/_status/check` endpoint
- Only add header `"vary": "cookie"` to html response

### 1.0.2 [12-12-2025]
- Add header "vary": "cookie" to after_request hook to ensure fresh response on redirect

### 1.0.1 [11-12-2025]
- Extend timeout for healthcheck

### 1.0.0 [25-11-2025]
**Initial release**
- Creates a Flask extension for integrating with the Canonical shared cookie consent service. See [README.md](/README.md) for further details.