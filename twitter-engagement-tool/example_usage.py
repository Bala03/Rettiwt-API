#!/usr/bin/env python3
"""Example usage of Twitter Engagement Tool with twscrape integration"""

import asyncio
from twscrape import API as TwscrapeAPI
from twitter_engagement.database import AccountDatabase
from twitter_engagement.converter import RettwiConverter


async def example_engagement_activities():
    """Example of using the tool for engagement activities"""
    
    # Initialize database
    db = AccountDatabase()
    
    # Get all active accounts with Rettiwt keys
    accounts = await db.get_active_accounts()
    rettiwt_accounts = [acc for acc in accounts if acc.rettiwt_api_key]
    
    print(f"Found {len(rettiwt_accounts)} accounts with Rettiwt API keys")
    
    # Initialize twscrape API
    twscrape_api = TwscrapeAPI("twscrape_accounts.db")
    
    # Add accounts to twscrape
    for account in rettiwt_accounts:
        if account.cookies:
            # Convert cookies to string format for twscrape
            cookie_str = "; ".join([f"{k}={v}" for k, v in account.cookies.items()])
            
            await twscrape_api.pool.add_account(
                username=account.username,
                password=account.password,
                email=account.email,
                email_password=account.email_password,
                cookies=cookie_str,
                proxy=account.proxy
            )
    
    print(f"Added {len(rettiwt_accounts)} accounts to twscrape")
    
    # Example: Search and like tweets
    async def like_tweets_about(topic: str, limit: int = 10):
        """Example function to like tweets about a topic"""
        print(f"\n🔍 Searching for tweets about '{topic}'...")
        
        tweets = []
        async for tweet in twscrape_api.search(topic, limit=limit):
            tweets.append(tweet)
            print(f"   Found: {tweet.user.username}: {tweet.rawContent[:100]}...")
        
        print(f"\n👍 Would like {len(tweets)} tweets (actual liking not implemented)")
        # Note: Actual liking would require implementing Twitter's like endpoint
        # This is just a demonstration of the search functionality
        
        return tweets
    
    # Example: Follow users who tweet about a topic
    async def follow_users_interested_in(topic: str, limit: int = 5):
        """Example function to follow users interested in a topic"""
        print(f"\n🔍 Finding users interested in '{topic}'...")
        
        users = set()
        async for tweet in twscrape_api.search(topic, limit=limit*2):
            users.add((tweet.user.id, tweet.user.username))
            if len(users) >= limit:
                break
        
        print(f"\n👥 Would follow {len(users)} users (actual following not implemented)")
        for user_id, username in users:
            print(f"   - @{username} (ID: {user_id})")
        
        return list(users)
    
    # Example: Get user engagement stats
    async def get_user_stats(username: str):
        """Get statistics for a user"""
        print(f"\n📊 Getting stats for @{username}...")
        
        try:
            user = await twscrape_api.user_by_login(username)
            print(f"   Followers: {user.followersCount:,}")
            print(f"   Following: {user.friendsCount:,}")
            print(f"   Tweets: {user.statusesCount:,}")
            print(f"   Likes: {user.favouritesCount:,}")
            
            # Get recent tweets
            print(f"\n   Recent tweets:")
            tweet_count = 0
            async for tweet in twscrape_api.user_tweets(user.id, limit=5):
                print(f"      - {tweet.rawContent[:80]}...")
                print(f"        💬 {tweet.replyCount} | 🔁 {tweet.retweetCount} | ❤️  {tweet.likeCount}")
                tweet_count += 1
            
            return user
        except Exception as e:
            print(f"   Error: {e}")
            return None
    
    # Run examples
    if rettiwt_accounts:
        # Search and "like" tweets
        await like_tweets_about("Python programming", limit=5)
        
        # "Follow" users
        await follow_users_interested_in("machine learning", limit=3)
        
        # Get user stats
        await get_user_stats("elonmusk")
    else:
        print("No accounts with Rettiwt API keys found. Please run:")
        print("  python -m twitter_engagement add-accounts accounts.txt")
        print("  python -m twitter_engagement convert-rettiwt")


async def show_rettiwt_format():
    """Show how to use Rettiwt API format"""
    db = AccountDatabase()
    credentials = await db.get_rettiwt_credentials()
    
    if credentials:
        print("\n📄 Rettiwt API Format Example:")
        print("=" * 50)
        
        # Show first credential as example
        cred = credentials[0]
        print(f"Username: {cred['username']}")
        print(f"API Key: {cred['api_key']}")
        print(f"Cookies: {len(cred['cookies'])} cookies")
        print(f"Generated: {cred['generated_at']}")
        
        print("\n🔧 Usage with Rettiwt API:")
        print("```javascript")
        print("const rettiwt = new Rettiwt({")
        print(f'  apiKey: "{cred["api_key"]}",')
        print("  // Additional configuration")
        print("});")
        print("```")
        
        print("\n📦 Full credential object:")
        import json
        print(json.dumps({
            'apiKey': cred['api_key'],
            'cookies': cred['cookies'],
            'username': cred['username']
        }, indent=2))


if __name__ == "__main__":
    print("🐦 Twitter Engagement Tool - Example Usage\n")
    
    # Run the examples
    asyncio.run(example_engagement_activities())
    
    # Show Rettiwt format
    asyncio.run(show_rettiwt_format())