#!/usr/bin/env python3
"""Test script for Twitter Engagement Tool integration"""

import asyncio
import json
from pathlib import Path
from twitter_engagement.database import AccountDatabase
from twitter_engagement.parser import AccountParser
from twitter_engagement.converter import RettwiConverter
from twitter_engagement.utils import parse_cookies


async def test_integration():
    """Test the complete integration flow"""
    print("🚀 Testing Twitter Engagement Tool Integration\n")
    
    # Test 1: Parse cookies
    print("1️⃣ Testing cookie parsing...")
    test_cookies = [
        'auth_token=abc123; ct0=xyz789',
        '{"auth_token": "def456", "ct0": "uvw012"}',
        'eyJhdXRoX3Rva2VuIjogImdoaTc4OSIsICJjdDAiOiAicnN0MzQ1In0='  # base64
    ]
    
    for i, cookie_str in enumerate(test_cookies, 1):
        try:
            cookies = parse_cookies(cookie_str)
            print(f"   ✅ Test {i}: Parsed {len(cookies)} cookies")
        except Exception as e:
            print(f"   ❌ Test {i}: Failed - {e}")
    
    # Test 2: Parse accounts file
    print("\n2️⃣ Testing account file parsing...")
    try:
        accounts = AccountParser.parse_file(
            'accounts_example.txt',
            'username:password:email:email_password:cookies'
        )
        print(f"   ✅ Parsed {len(accounts)} accounts from file")
        for acc in accounts:
            has_cookies = "✓" if acc.cookies else "✗"
            print(f"      - {acc.username}: cookies {has_cookies}")
    except Exception as e:
        print(f"   ❌ Failed to parse accounts: {e}")
        return
    
    # Test 3: Database operations
    print("\n3️⃣ Testing database operations...")
    db = AccountDatabase("test_twitter_accounts.db")
    
    try:
        await db.init_db()
        print("   ✅ Database initialized")
        
        # Add accounts
        for account in accounts:
            await db.add_account(account)
        print(f"   ✅ Added {len(accounts)} accounts to database")
        
        # Get stats
        stats = await db.get_stats()
        print(f"   📊 Database stats:")
        for key, value in stats.items():
            print(f"      - {key}: {value}")
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return
    
    # Test 4: Rettiwt conversion
    print("\n4️⃣ Testing Rettiwt API conversion...")
    accounts_with_cookies = [acc for acc in accounts if acc.cookies]
    
    if accounts_with_cookies:
        results = RettwiConverter.batch_convert(accounts_with_cookies)
        success_count = sum(1 for r in results.values() if r['status'] == 'success')
        print(f"   ✅ Converted {success_count}/{len(accounts_with_cookies)} accounts")
        
        # Show sample config
        for username, result in results.items():
            if result['status'] == 'success':
                config = result['config']
                print(f"\n   📋 Sample Rettiwt config for {username}:")
                print(f"      API Key: {config['apiKey']}")
                print(f"      Cookies: {len(config['cookies'])} cookies")
                break
    else:
        print("   ⚠️  No accounts with cookies to convert")
    
    # Test 5: Generate and store Rettiwt keys
    print("\n5️⃣ Testing Rettiwt key generation and storage...")
    try:
        results = await db.generate_rettiwt_keys()
        print(f"   ✅ Generated {len(results)} Rettiwt API keys")
        
        # Export credentials
        credentials = await db.get_rettiwt_credentials()
        if credentials:
            with open('test_rettiwt_credentials.json', 'w') as f:
                json.dump(credentials, f, indent=2)
            print(f"   ✅ Exported {len(credentials)} credentials to test_rettiwt_credentials.json")
    except Exception as e:
        print(f"   ❌ Rettiwt generation error: {e}")
    
    # Cleanup
    print("\n🧹 Cleaning up test files...")
    Path("test_twitter_accounts.db").unlink(missing_ok=True)
    Path("test_rettiwt_credentials.json").unlink(missing_ok=True)
    print("   ✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_integration())