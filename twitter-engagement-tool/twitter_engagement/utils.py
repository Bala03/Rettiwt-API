"""Utility functions"""

import json
import base64
import hashlib
import secrets
from typing import Dict, Union
from datetime import datetime


def parse_cookies(cookie_value: str) -> Dict[str, str]:
    """Parse cookies from various formats"""
    if not cookie_value:
        return {}
    
    # Try to decode base64
    try:
        decoded = base64.b64decode(cookie_value).decode('utf-8')
        cookie_value = decoded
    except Exception:
        pass
    
    # Try to parse as JSON
    try:
        data = json.loads(cookie_value)
        
        # Handle different JSON formats
        if isinstance(data, dict):
            if 'cookies' in data:
                # Nested cookies object
                cookies_data = data['cookies']
                if isinstance(cookies_data, list):
                    # Array of cookie objects
                    return {c['name']: c['value'] for c in cookies_data if 'name' in c and 'value' in c}
                elif isinstance(cookies_data, dict):
                    return cookies_data
            else:
                # Direct cookie dictionary
                return data
        elif isinstance(data, list):
            # Array of cookie objects
            return {c['name']: c['value'] for c in data if 'name' in c and 'value' in c}
    except json.JSONDecodeError:
        pass
    
    # Try to parse as cookie string (key=value; key2=value2)
    try:
        cookies = {}
        for pair in cookie_value.split(';'):
            pair = pair.strip()
            if '=' in pair:
                key, value = pair.split('=', 1)
                cookies[key.strip()] = value.strip()
        
        if cookies:
            return cookies
    except Exception:
        pass
    
    raise ValueError(f"Unable to parse cookies from: {cookie_value[:50]}...")


def generate_rettiwt_api_key(account: 'TwitterAccount') -> str:
    """Generate a Rettiwt API key from account credentials"""
    # Rettiwt API key generation logic
    # This is a simplified version - you may need to adjust based on actual Rettiwt requirements
    
    # Extract essential cookies
    essential_cookies = {
        'auth_token': account.cookies.get('auth_token', ''),
        'ct0': account.cookies.get('ct0', ''),
        'kdt': account.cookies.get('kdt', ''),
        'twid': account.cookies.get('twid', ''),
        'guest_id': account.cookies.get('guest_id', '')
    }
    
    # Remove empty values
    essential_cookies = {k: v for k, v in essential_cookies.items() if v}
    
    # Generate a unique key based on username and cookies
    key_data = f"{account.username}:{json.dumps(essential_cookies, sort_keys=True)}"
    api_key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    # Create a formatted API key
    api_key = f"rwt_{api_key_hash}_{secrets.token_hex(8)}"
    
    return api_key


def validate_twitter_cookies(cookies: Dict[str, str]) -> bool:
    """Validate that required Twitter cookies are present"""
    # Twitter requires at least ct0 (CSRF token) and auth_token for authenticated requests
    required_cookies = {'ct0', 'auth_token'}
    return all(cookie in cookies and cookies[cookie] for cookie in required_cookies)


def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    if not dt:
        return "Never"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate_string(s: str, max_length: int = 50) -> str:
    """Truncate string with ellipsis if too long"""
    if len(s) <= max_length:
        return s
    return s[:max_length-3] + "..."