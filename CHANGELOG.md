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