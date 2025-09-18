# Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

## Basic Usage

### 1. Initialize Database

```bash
python -m twitter_engagement init-db
```

### 2. Prepare Your Accounts File

Create `accounts.txt` with your Twitter accounts:

```text
user1:password1:email1@example.com:emailpass1:auth_token=xxx; ct0=yyy
user2:password2:email2@example.com:emailpass2:{"auth_token": "aaa", "ct0": "bbb"}
```

### 3. Add Accounts

```bash
python -m twitter_engagement add-accounts accounts.txt
```

### 4. Generate Rettiwt API Keys

```bash
python -m twitter_engagement convert-rettiwt
```

### 5. View Your Accounts

```bash
python -m twitter_engagement list-accounts
```

### 6. Export Rettiwt Credentials

```bash
python -m twitter_engagement export-rettiwt
```

## Cookie Formats Supported

1. **String format**: `auth_token=xxx; ct0=yyy; kdt=zzz`
2. **JSON format**: `{"auth_token": "xxx", "ct0": "yyy"}`
3. **Base64 encoded**: Any of the above formats encoded in base64
4. **Browser export**: Cookie export from browser extensions

## Required Cookies

At minimum, you need:
- `auth_token`: Authentication token
- `ct0`: CSRF token

Optional but recommended:
- `kdt`: Additional security token
- `twid`: Twitter user ID
- `personalization_id`: Personalization tracking

## Using with twscrape

The tool integrates seamlessly with twscrape:

```python
import asyncio
from twscrape import API
from twitter_engagement.database import AccountDatabase

async def use_with_twscrape():
    # Get accounts from our database
    db = AccountDatabase()
    accounts = await db.get_active_accounts()
    
    # Initialize twscrape
    api = API()
    
    # Add accounts to twscrape
    for account in accounts:
        if account.cookies:
            cookie_str = "; ".join([f"{k}={v}" for k, v in account.cookies.items()])
            await api.pool.add_account(
                username=account.username,
                password=account.password,
                email=account.email,
                email_password=account.email_password,
                cookies=cookie_str
            )
    
    # Use twscrape normally
    async for tweet in api.search("python", limit=10):
        print(f"@{tweet.user.username}: {tweet.rawContent}")
```

## Troubleshooting

### Invalid Cookies
- Ensure cookies are fresh (not expired)
- Check that `auth_token` and `ct0` are present
- Try different cookie export methods

### Database Issues
- Run `init-db` command first
- Check file permissions
- Use absolute paths if needed

### Account Not Working
- Check account status: `python -m twitter_engagement list-accounts`
- Update status if needed: `python -m twitter_engagement update-status USERNAME --deactivate`
- Re-add account with fresh cookies