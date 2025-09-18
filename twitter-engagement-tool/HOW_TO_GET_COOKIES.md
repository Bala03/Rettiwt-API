# How to Get Twitter Cookies for Rettiwt API

## Method 1: Browser Developer Tools

1. **Login to Twitter** in your browser
2. Open Developer Tools (F12)
3. Go to **Application/Storage** tab
4. Click on **Cookies** → **https://twitter.com**
5. Look for these cookies:
   - `auth_token`
   - `ct0`
   - `kdt`
   - `twid`
   - `personalization_id`

## Method 2: Browser Extension

1. Install a cookie manager extension:
   - **EditThisCookie** (Chrome)
   - **Cookie-Editor** (Firefox/Chrome)
   
2. Login to Twitter
3. Click the extension icon
4. Export cookies for twitter.com
5. Copy the cookie values

## Method 3: Network Inspector

1. Login to Twitter
2. Open Developer Tools → Network tab
3. Make any request on Twitter
4. Look for request headers
5. Copy the `Cookie:` header value

## Example Cookie Format

```
auth_token=1234567890abcdef1234567890abcdef; ct0=abcdef1234567890abcdef1234567890; kdt=aAbBcCdDeEfFgGhHiIjJkKlLmMnN; twid=u%3D1234567890; personalization_id=v1_aBcDeFgHiJkLmNoPqRsTuVw==
```

## Using with the Tool

Once you have the cookies, create your accounts file:

```
username1|password1|email1@example.com|emailpass1|auth_token=xxx; ct0=yyy; kdt=zzz; twid=u%3D123
username2|password2|email2@example.com|emailpass2|auth_token=aaa; ct0=bbb; kdt=ccc; twid=u%3D456
```

## Security Notes

⚠️ **IMPORTANT**: 
- Keep your cookies secure - they provide full access to your account
- Cookies expire after some time (usually days to weeks)
- If you logout from browser, cookies become invalid
- Never share your cookies publicly

## Verification

To verify your cookies are working:

1. Check that you have at least `auth_token` and `ct0`
2. Cookies should be recent (not expired)
3. Test with a simple API call first