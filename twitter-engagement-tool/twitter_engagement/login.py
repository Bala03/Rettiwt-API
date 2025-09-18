"""Login functionality to get Twitter cookies automatically"""

import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
import httpx
from httpx import AsyncClient
import time
import os
from .models import TwitterAccount
from .utils import generate_rettiwt_api_key


LOGIN_URL = "https://api.x.com/1.1/onboarding/task.json"
TOKEN = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"


@dataclass
class LoginContext:
    client: AsyncClient
    account: TwitterAccount
    flow_token: Optional[str] = None
    guest_token: Optional[str] = None


class TwitterLogin:
    """Handle Twitter login process to obtain cookies"""
    
    @staticmethod
    async def get_guest_token(client: AsyncClient) -> str:
        """Get guest token for authentication"""
        rep = await client.post("https://api.x.com/1.1/guest/activate.json")
        rep.raise_for_status()
        return rep.json()["guest_token"]
    
    @staticmethod
    async def login_initiate(client: AsyncClient) -> httpx.Response:
        """Initiate login flow"""
        payload = {
            "input_flow_data": {
                "flow_context": {
                    "debug_overrides": {},
                    "start_location": {"location": "unknown"}
                }
            },
            "subtask_versions": {},
        }
        
        rep = await client.post(LOGIN_URL, params={"flow_name": "login"}, json=payload)
        rep.raise_for_status()
        return rep
    
    @staticmethod
    async def login_enter_username(ctx: LoginContext, flow_token: str) -> httpx.Response:
        """Enter username step"""
        payload = {
            "flow_token": flow_token,
            "subtask_inputs": [
                {
                    "subtask_id": "LoginEnterUserIdentifierSSO",
                    "settings_list": {
                        "setting_responses": [
                            {
                                "key": "user_identifier",
                                "response_data": {"text_data": {"result": ctx.account.username}},
                            }
                        ],
                        "link": "next_link",
                    },
                }
            ],
        }
        
        rep = await ctx.client.post(LOGIN_URL, json=payload)
        rep.raise_for_status()
        return rep
    
    @staticmethod
    async def login_enter_password(ctx: LoginContext, flow_token: str) -> httpx.Response:
        """Enter password step"""
        payload = {
            "flow_token": flow_token,
            "subtask_inputs": [
                {
                    "subtask_id": "LoginEnterPassword",
                    "enter_password": {"password": ctx.account.password, "link": "next_link"},
                }
            ],
        }
        
        rep = await ctx.client.post(LOGIN_URL, json=payload)
        rep.raise_for_status()
        return rep
    
    @staticmethod
    async def login_confirm_email(ctx: LoginContext, flow_token: str) -> httpx.Response:
        """Confirm email step"""
        payload = {
            "flow_token": flow_token,
            "subtask_inputs": [
                {
                    "subtask_id": "LoginAcid",
                    "enter_text": {"text": ctx.account.email, "link": "next_link"},
                }
            ],
        }
        
        rep = await ctx.client.post(LOGIN_URL, json=payload)
        rep.raise_for_status()
        return rep
    
    @staticmethod
    async def login_success(ctx: LoginContext, flow_token: str) -> httpx.Response:
        """Complete login flow"""
        payload = {
            "flow_token": flow_token,
            "subtask_inputs": [],
        }
        
        rep = await ctx.client.post(LOGIN_URL, json=payload)
        rep.raise_for_status()
        return rep
    
    @staticmethod
    async def login_instrumentation(ctx: LoginContext, flow_token: str) -> httpx.Response:
        """JS instrumentation step"""
        payload = {
            "flow_token": flow_token,
            "subtask_inputs": [
                {
                    "subtask_id": "LoginJsInstrumentationSubtask",
                    "js_instrumentation": {"response": "{}", "link": "next_link"},
                }
            ],
        }
        
        rep = await ctx.client.post(LOGIN_URL, json=payload)
        rep.raise_for_status()
        return rep
    
    @staticmethod
    async def login_duplication_check(ctx: LoginContext, flow_token: str) -> httpx.Response:
        """Account duplication check"""
        payload = {
            "flow_token": flow_token,
            "subtask_inputs": [
                {
                    "subtask_id": "AccountDuplicationCheck",
                    "check_logged_in_account": {"link": "AccountDuplicationCheck_false"},
                }
            ],
        }
        
        rep = await ctx.client.post(LOGIN_URL, json=payload)
        rep.raise_for_status()
        return rep
    
    @staticmethod
    async def process_login_flow(ctx: LoginContext, response: httpx.Response) -> Optional[httpx.Response]:
        """Process login flow based on current step"""
        data = response.json()
        
        # Update CSRF token if available
        ct0 = ctx.client.cookies.get("ct0", None)
        if ct0:
            ctx.client.headers["x-csrf-token"] = ct0
            ctx.client.headers["x-twitter-auth-type"] = "OAuth2Session"
        
        flow_token = data.get("flow_token")
        if not flow_token:
            raise ValueError(f"No flow_token in response: {data}")
        
        # Process subtasks
        for subtask in data.get("subtasks", []):
            task_id = subtask["subtask_id"]
            
            if task_id == "LoginSuccessSubtask":
                return await TwitterLogin.login_success(ctx, flow_token)
            elif task_id == "LoginEnterUserIdentifierSSO":
                return await TwitterLogin.login_enter_username(ctx, flow_token)
            elif task_id == "LoginEnterPassword":
                return await TwitterLogin.login_enter_password(ctx, flow_token)
            elif task_id == "LoginAcid":
                # Check if it's asking for email or code
                hint = subtask.get("enter_text", {}).get("hint_text", "").lower()
                if "email" in hint:
                    return await TwitterLogin.login_confirm_email(ctx, flow_token)
                else:
                    # Would need email code here - for now, we'll skip
                    print(f"⚠️  Email verification required for {ctx.account.username}")
                    raise ValueError("Email verification not implemented")
            elif task_id == "LoginJsInstrumentationSubtask":
                return await TwitterLogin.login_instrumentation(ctx, flow_token)
            elif task_id == "AccountDuplicationCheck":
                return await TwitterLogin.login_duplication_check(ctx, flow_token)
            else:
                print(f"Unknown task: {task_id}")
        
        return None
    
    @staticmethod
    async def login(account: TwitterAccount) -> Dict[str, str]:
        """
        Attempt to login and get cookies
        Returns dict of cookies on success
        """
        # Create HTTP client
        transport = httpx.AsyncHTTPTransport(retries=3)
        async with AsyncClient(follow_redirects=True, transport=transport) as client:
            # Set headers
            client.headers["user-agent"] = account.user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            client.headers["content-type"] = "application/json"
            client.headers["authorization"] = TOKEN
            client.headers["x-twitter-active-user"] = "yes"
            client.headers["x-twitter-client-language"] = "en"
            
            # Create context
            ctx = LoginContext(client=client, account=account)
            
            try:
                # Get guest token
                guest_token = await TwitterLogin.get_guest_token(client)
                client.headers["x-guest-token"] = guest_token
                
                # Initiate login
                response = await TwitterLogin.login_initiate(client)
                
                # Process login flow
                while response:
                    response = await TwitterLogin.process_login_flow(ctx, response)
                
                # Extract cookies
                cookies = dict(client.cookies)
                
                # Verify we have essential cookies
                if "ct0" not in cookies or "auth_token" not in cookies:
                    raise ValueError("Login failed - missing essential cookies")
                
                return cookies
                
            except Exception as e:
                print(f"❌ Login failed for {account.username}: {str(e)}")
                raise


async def auto_login_and_convert(account: TwitterAccount) -> Optional[Dict[str, Any]]:
    """
    Automatically login and convert to Rettiwt format
    """
    try:
        print(f"🔐 Attempting login for {account.username}...")
        
        # Try to login
        cookies = await TwitterLogin.login(account)
        
        # Update account with cookies
        account.cookies = cookies
        
        # Generate Rettiwt API key
        api_key = generate_rettiwt_api_key(account)
        
        # Create Rettiwt configuration
        rettiwt_config = {
            "username": account.username,
            "apiKey": api_key,
            "cookies": cookies,
            "email": account.email,
            "generatedAt": time.time()
        }
        
        print(f"✅ Successfully logged in and generated Rettiwt API key for {account.username}")
        return rettiwt_config
        
    except Exception as e:
        print(f"❌ Failed to process {account.username}: {str(e)}")
        return None