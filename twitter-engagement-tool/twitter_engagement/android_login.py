"""Android API-based login for Twitter - inspired by Nitter project"""

import asyncio
import httpx
import json
import sys
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import secrets
import hashlib
from .models import TwitterAccount
from .utils import generate_rettiwt_api_key
from .converter import RettwiConverter


# Twitter Android API constants
TW_CONSUMER_KEY = '3nVuSoBZnx6U4vzUxf5w'
TW_CONSUMER_SECRET = 'Bcs59EFbbsdF6Sl9Ng71smgStWEGwXXKSjYvPVt7qys'
TW_ANDROID_USER_AGENT = "TwitterAndroid/10.21.0-release.0 (310210000-r-0) ONEPLUS+A3010/9 (OnePlus;ONEPLUS+A3010;OnePlus;OnePlus3;0;;1;2016)"


@dataclass
class AndroidAuthResult:
    """Result from Android authentication"""
    oauth_token: str
    oauth_token_secret: str
    user_id: Optional[str] = None
    screen_name: Optional[str] = None
    cookies: Optional[Dict[str, str]] = None


class TwitterAndroidAuth:
    """Twitter authentication using Android API endpoints"""
    
    def __init__(self):
        self.session: Optional[httpx.AsyncClient] = None
        self.bearer_token: Optional[str] = None
        self.guest_token: Optional[str] = None
        self.att: Optional[str] = None
    
    async def get_bearer_token(self) -> str:
        """Get bearer token using consumer credentials"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.twitter.com/oauth2/token",
                auth=(TW_CONSUMER_KEY, TW_CONSUMER_SECRET),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data='grant_type=client_credentials'
            )
            response.raise_for_status()
            data = response.json()
            return f"{data['token_type']} {data['access_token']}"
    
    async def get_guest_token(self, bearer_token: str) -> str:
        """Get guest token for unauthenticated requests"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.twitter.com/1.1/guest/activate.json",
                headers={'Authorization': bearer_token}
            )
            response.raise_for_status()
            data = response.json()
            return data['guest_token']
    
    def generate_device_id(self) -> str:
        """Generate a random device ID"""
        return secrets.token_hex(16)
    
    async def create_session(self) -> httpx.AsyncClient:
        """Create authenticated session with proper headers"""
        self.bearer_token = await self.get_bearer_token()
        self.guest_token = await self.get_guest_token(self.bearer_token)
        
        headers = {
            'Authorization': self.bearer_token,
            "Content-Type": "application/json",
            "User-Agent": TW_ANDROID_USER_AGENT,
            "X-Twitter-API-Version": '5',
            "X-Twitter-Client": "TwitterAndroid",
            "X-Twitter-Client-Version": "10.21.0-release.0",
            "OS-Version": "28",
            "System-User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ONEPLUS A3010 Build/PKQ1.181203.001)",
            "X-Twitter-Active-User": "yes",
            "X-Guest-Token": self.guest_token,
            "X-Twitter-Client-DeviceID": self.generate_device_id()
        }
        
        self.session = httpx.AsyncClient(headers=headers)
        return self.session
    
    async def login_flow_start(self) -> Tuple[str, Dict]:
        """Start the login flow and get flow token"""
        payload = {
            "flow_token": None,
            "input_flow_data": {
                "country_code": None,
                "flow_context": {
                    "referrer_context": {
                        "referral_details": "utm_source=google-play&utm_medium=organic",
                        "referrer_url": ""
                    },
                    "start_location": {
                        "location": "deeplink"
                    }
                },
                "requested_variant": None,
                "target_user_id": 0
            }
        }
        
        response = await self.session.post(
            'https://api.twitter.com/1.1/onboarding/task.json',
            params={
                'flow_name': 'login',
                'api_version': '1',
                'known_device_token': '',
                'sim_country_code': 'us'
            },
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        # Update ATT header if present
        if 'att' in response.headers:
            self.att = response.headers['att']
            self.session.headers['att'] = self.att
        
        return data.get('flow_token'), data
    
    async def login_enter_username(self, flow_token: str, username: str) -> Tuple[str, Dict]:
        """Enter username in login flow"""
        payload = {
            "flow_token": flow_token,
            "subtask_inputs": [{
                "enter_text": {
                    "suggestion_id": None,
                    "text": username,
                    "link": "next_link"
                },
                "subtask_id": "LoginEnterUserIdentifier"
            }]
        }
        
        response = await self.session.post(
            'https://api.twitter.com/1.1/onboarding/task.json',
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data.get('flow_token'), data
    
    async def login_enter_password(self, flow_token: str, password: str) -> Tuple[str, Dict]:
        """Enter password in login flow"""
        payload = {
            "flow_token": flow_token,
            "subtask_inputs": [{
                "enter_password": {
                    "password": password,
                    "link": "next_link"
                },
                "subtask_id": "LoginEnterPassword"
            }]
        }
        
        response = await self.session.post(
            'https://api.twitter.com/1.1/onboarding/task.json',
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data.get('flow_token'), data
    
    async def extract_auth_result(self, response_data: Dict) -> Optional[AndroidAuthResult]:
        """Extract authentication result from response"""
        for subtask in response_data.get('subtasks', []):
            if 'open_account' in subtask:
                account_data = subtask['open_account']
                
                # Extract cookies from the session
                cookies = {}
                if self.session and hasattr(self.session, 'cookies'):
                    cookies = dict(self.session.cookies)
                
                return AndroidAuthResult(
                    oauth_token=account_data.get('oauth_token', ''),
                    oauth_token_secret=account_data.get('oauth_token_secret', ''),
                    user_id=account_data.get('user_id'),
                    screen_name=account_data.get('screen_name'),
                    cookies=cookies
                )
        return None
    
    async def authenticate(self, username: str, password: str) -> Optional[AndroidAuthResult]:
        """Perform full authentication flow"""
        try:
            # Create session
            await self.create_session()
            
            # Start login flow
            flow_token, _ = await self.login_flow_start()
            
            # Enter username
            flow_token, _ = await self.login_enter_username(flow_token, username)
            
            # Enter password
            flow_token, response = await self.login_enter_password(flow_token, password)
            
            # Extract result
            result = await self.extract_auth_result(response)
            
            return result
            
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return None
        finally:
            if self.session:
                await self.session.aclose()


async def android_login_and_convert(account: TwitterAccount) -> Optional[Dict[str, Any]]:
    """
    Login using Android API and convert to Rettiwt format
    """
    try:
        print(f"🤖 Attempting Android API login for {account.username}...")
        
        # Create authenticator
        auth = TwitterAndroidAuth()
        
        # Authenticate
        result = await auth.authenticate(account.username, account.password)
        
        if not result:
            raise ValueError("Authentication failed")
        
        print(f"✅ Authentication successful for {account.username}")
        print(f"   OAuth Token: {result.oauth_token[:20]}...")
        print(f"   Screen Name: {result.screen_name}")
        
        # Create synthetic cookies for Rettiwt format
        # Since Android API doesn't return web cookies, we'll create a format
        # that includes the OAuth credentials
        synthetic_cookies = {
            'auth_token': result.oauth_token,
            'oauth_token_secret': result.oauth_token_secret,
            'ct0': hashlib.sha256(f"{result.oauth_token}:{result.oauth_token_secret}".encode()).hexdigest()[:32],
            'user_id': result.user_id or '',
            'screen_name': result.screen_name or account.username,
            'auth_type': 'android_oauth'
        }
        
        # Update account
        account.cookies = synthetic_cookies
        
        # Generate Rettiwt API key
        api_key = generate_rettiwt_api_key(account)
        
        # Create Rettiwt configuration
        rettiwt_config = {
            "username": account.username,
            "apiKey": api_key,
            "cookies": synthetic_cookies,
            "oauth": {
                "token": result.oauth_token,
                "token_secret": result.oauth_token_secret
            },
            "email": account.email,
            "auth_method": "android_api"
        }
        
        return rettiwt_config
        
    except Exception as e:
        print(f"❌ Android auth failed for {account.username}: {str(e)}")
        return None


async def test_android_auth(username: str, password: str):
    """Test Android authentication directly"""
    auth = TwitterAndroidAuth()
    result = await auth.authenticate(username, password)
    
    if result:
        print("✅ Authentication successful!")
        print(f"OAuth Token: {result.oauth_token}")
        print(f"OAuth Token Secret: {result.oauth_token_secret}")
        print(f"User ID: {result.user_id}")
        print(f"Screen Name: {result.screen_name}")
        return result
    else:
        print("❌ Authentication failed!")
        return None