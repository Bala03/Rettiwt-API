# Authentication Methods

This tool supports multiple authentication methods to obtain Twitter session credentials and convert them to Rettiwt API format.

## Overview

The tool implements two primary authentication methods:

1. **Android API Authentication** - Uses Twitter's Android app API endpoints
2. **Web API Authentication** - Uses Twitter's web login flow

## Android API Authentication (Recommended)

Based on the Nitter project's approach, this method uses Twitter's Android API endpoints which are generally more stable and less likely to require email verification.

### How it Works

1. **OAuth2 Bearer Token**: Obtains a bearer token using Twitter's consumer key/secret
2. **Guest Token**: Gets a guest token for unauthenticated requests
3. **Login Flow**: Performs the Android app login flow:
   - Submit username
   - Submit password
   - Receive OAuth tokens

### Advantages
- More reliable than web login
- Less likely to trigger security checks
- Returns OAuth tokens directly
- No cookie parsing required

### Usage
```bash
# Login specific account
python -m twitter_engagement android-login --username account1

# Login all accounts without cookies
python -m twitter_engagement android-login --all
```

### Output Format
The Android authentication returns:
```json
{
  "username": "account1",
  "apiKey": "rwt_generated_api_key",
  "cookies": {
    "auth_token": "oauth_token",
    "oauth_token_secret": "oauth_secret",
    "ct0": "generated_csrf_token",
    "auth_type": "android_oauth"
  },
  "oauth": {
    "token": "actual_oauth_token",
    "token_secret": "actual_oauth_token_secret"
  },
  "auth_method": "android_api"
}
```

## Web API Authentication

This method mimics the browser login flow and attempts to obtain web session cookies.

### How it Works

1. **Guest Token**: Obtains initial guest token
2. **Login Initiation**: Starts the login flow
3. **Credential Submission**: Submits username and password
4. **Challenge Handling**: May require email verification
5. **Cookie Extraction**: Extracts session cookies

### Limitations
- May require email verification
- More likely to trigger security checks
- May fail with "suspicious activity" errors

### Usage
```bash
# Auto-login up to 5 accounts
python -m twitter_engagement auto-login --limit 5

# Login specific account
python -m twitter_engagement auto-login --username account1
```

## Manual Cookie Import

If automated login fails, you can manually obtain cookies from a browser session:

### Steps
1. Login to Twitter in a web browser
2. Open Developer Tools (F12)
3. Go to Application → Cookies → twitter.com
4. Copy the following cookies:
   - `auth_token`
   - `ct0`
   - `kdt` (optional)
   - `twid` (optional)

### Format
```
username:password:email:email_pass:auth_token=xxx; ct0=yyy; kdt=zzz
```

## Rettiwt API Key Generation

Once authenticated, the tool generates a Rettiwt API key using:

1. **Essential Cookies**: Extracts auth_token, ct0, and other required cookies
2. **Key Generation**: Creates a unique API key based on username and cookies
3. **Storage**: Saves both cookies and API key in the database

## Security Considerations

1. **Credentials Storage**: All credentials are stored locally in SQLite database
2. **No External Transmission**: Credentials are never sent to external services
3. **Local Processing**: All authentication happens locally
4. **Secure Storage**: Use file permissions to protect the database file

## Troubleshooting

### Android Login Fails
- Verify credentials are correct
- Account may have 2FA enabled (not supported yet)
- Account may be suspended or locked

### Web Login Fails
- Account may require email verification
- Too many login attempts may trigger security
- Try using Android login instead

### Invalid Cookies
- Cookies may have expired
- Ensure you copy all required cookies
- Try re-logging in the browser

## Rate Limits

Twitter enforces rate limits on login attempts:
- Maximum 5-10 login attempts per IP per hour
- Use proxies for bulk operations
- Space out login attempts

## Best Practices

1. **Use Android Login**: More reliable for bulk operations
2. **Save Credentials**: Export successful logins immediately
3. **Monitor Success Rate**: Check which accounts fail repeatedly
4. **Use Proxies**: For large-scale operations
5. **Regular Updates**: Re-authenticate accounts periodically