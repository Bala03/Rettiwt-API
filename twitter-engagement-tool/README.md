# Twitter Engagement Tool

A powerful tool that integrates twscrape with Rettiwt API for managing multiple Twitter accounts using cookies and performing engagement activities.

## Features

- Bulk import of Twitter accounts with cookies
- Automatic conversion to Rettiwt API format
- Database storage of account credentials
- Support for multiple engagement activities (likes, retweets, follows)
- Rate limit management with automatic account switching

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
python -m twitter_engagement init-db
```

## Usage

### Adding Accounts

Create an `accounts.txt` file with the following format:
```
username1:password1:email1@example.com:emailpass1:cookie_string1
username2:password2:email2@example.com:emailpass2:cookie_string2
```

Then run:
```bash
python -m twitter_engagement add-accounts accounts.txt
```

### Automatic Login Methods

#### Method 1: Android API Login (Recommended)
Uses Twitter's Android API for more reliable authentication:
```bash
# Login specific account
python -m twitter_engagement android-login --username user1

# Login all accounts without cookies
python -m twitter_engagement android-login --all
```

#### Method 2: Web API Login
Uses Twitter's web API (may require email verification):
```bash
# Auto-login accounts without cookies
python -m twitter_engagement auto-login --limit 5
```

### Converting to Rettiwt Format

To convert accounts to Rettiwt API format:
```bash
python -m twitter_engagement convert-rettiwt
```

### Viewing Accounts

To list all accounts:
```bash
python -m twitter_engagement list-accounts
```

## Account File Format

The tool supports multiple formats for the accounts file:

1. **With cookies (recommended)**:
   ```
   username:password:email:email_password:cookies
   ```

2. **Without cookies**:
   ```
   username:password:email:email_password
   ```

3. **Cookie formats supported**:
   - Raw cookie string: `"auth_token=xxx; ct0=yyy"`
   - JSON format: `{"auth_token": "xxx", "ct0": "yyy"}`
   - Base64 encoded cookies

## Rettiwt API Key Format

The tool automatically generates Rettiwt API keys in the following format:
```json
{
  "apiKey": "generated_key",
  "cookies": {
    "auth_token": "xxx",
    "ct0": "yyy"
  },
  "username": "twitter_username"
}
```

## Security Notes

- Store your `accounts.txt` file securely
- Never commit account credentials to version control
- Use environment variables for sensitive configuration
- The database file contains sensitive information - protect it accordingly

## License

MIT