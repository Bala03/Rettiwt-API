# How to Get Real Working Rettiwt API Keys

## Option 1: Using the Twitter Engagement Tool

1. **Prepare your accounts file** with real credentials:
   ```
   JamesPham179380|CTrP0ow2WvipQLPRyUYv|pagachhasenohrl76329@outlook.it|5PD6MUN4S1|
   watcher652070|pVGQNMigRdEUQujYDWpR|shrievemazorra3827@outlook.it|QTRPVO9CG3|
   ```

2. **Add accounts to database**:
   ```bash
   python -m twitter_engagement add-accounts accounts.txt --format "username|password|email|email_password|cookies"
   ```

3. **Login using Android API** (this will get real cookies):
   ```bash
   python -m twitter_engagement android-login --all
   ```

4. **Export the credentials**:
   ```bash
   python -m twitter_engagement export-rettiwt
   ```

## Option 2: Using Rettiwt-Auth Tool

1. **Install rettiwt-auth**:
   ```bash
   npm install -g rettiwt-auth
   ```

2. **Generate API key for each account**:
   ```bash
   rettiwt-auth
   # Follow prompts to enter username/password
   # It will return the actual API key
   ```

## Option 3: Manual Browser Method

1. **Login to Twitter** in Chrome/Firefox
2. **Install cookie extension** (EditThisCookie)
3. **Export cookies** for twitter.com
4. **Extract these specific cookies**:
   - auth_token
   - ct0
   - kdt (if available)
   - twid (user ID)

5. **Use the actual cookies** in the tool

## What Real Cookies Look Like

```json
{
  "auth_token": "5d4f3a2b1c9e8d7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f",
  "ct0": "8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d",
  "kdt": "LKnMmOoPpQqRrSsTtUuVvWw",
  "twid": "u%3D1234567890",
  "personalization_id": "v1_aBcDeFgHiJkLmNoPqRsTuVw==",
  "guest_id": "v1%3A172934857629348576"
}
```

## Important Notes

1. **I cannot generate working keys** without actually logging into Twitter
2. **The tool needs to authenticate** with Twitter's servers to get real cookies
3. **Security**: Never share your real cookies or API keys publicly
4. **Expiration**: Cookies expire and need to be refreshed periodically

## The Android Login Process

When you run the android-login command with real credentials:

1. It connects to Twitter's Android API
2. Authenticates with username/password
3. Receives OAuth tokens
4. Generates working Rettiwt API keys
5. Stores everything in the database

Without actual authentication, any key I generate will be invalid.