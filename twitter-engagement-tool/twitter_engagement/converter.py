"""Convert Twitter accounts to Rettiwt API format"""

import json
import hashlib
import base64
from typing import Dict, List, Optional
from datetime import datetime
from .models import TwitterAccount, RettiwtCredentials


class RettwiConverter:
    """Convert Twitter accounts to Rettiwt API format"""
    
    @staticmethod
    def extract_essential_cookies(cookies: Dict[str, str]) -> Dict[str, str]:
        """Extract essential cookies required by Twitter API"""
        essential_keys = [
            'auth_token',
            'ct0',
            'kdt',
            'twid',
            'guest_id',
            'personalization_id',
            'guest_id_marketing',
            'guest_id_ads',
            'lang',
            '_twitter_sess'
        ]
        
        return {k: v for k, v in cookies.items() if k in essential_keys and v}
    
    @staticmethod
    def generate_api_key(account: TwitterAccount) -> str:
        """Generate a unique API key for Rettiwt"""
        # Extract essential cookies
        essential = RettwiConverter.extract_essential_cookies(account.cookies)
        
        # Create a deterministic key based on username and cookies
        key_source = f"{account.username}:{json.dumps(essential, sort_keys=True)}"
        key_hash = hashlib.sha256(key_source.encode()).hexdigest()
        
        # Format as Rettiwt API key
        # Pattern: rwt_<hash_prefix>_<timestamp_suffix>
        timestamp = int(datetime.now().timestamp())
        api_key = f"rwt_{key_hash[:24]}_{timestamp}"
        
        return api_key
    
    @staticmethod
    def create_rettiwt_config(account: TwitterAccount) -> Dict[str, any]:
        """Create Rettiwt configuration object"""
        if not account.cookies:
            raise ValueError(f"Account {account.username} has no cookies")
        
        # Validate required cookies
        required = {'auth_token', 'ct0'}
        if not all(key in account.cookies for key in required):
            missing = required - set(account.cookies.keys())
            raise ValueError(f"Missing required cookies: {missing}")
        
        # Generate API key
        api_key = RettwiConverter.generate_api_key(account)
        
        # Create configuration
        config = {
            'apiKey': api_key,
            'username': account.username,
            'cookies': RettwiConverter.extract_essential_cookies(account.cookies),
            'userAgent': account.user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'proxy': account.proxy,
            'metadata': {
                'generatedAt': datetime.now().isoformat(),
                'email': account.email,
                'cookieCount': len(account.cookies)
            }
        }
        
        return config
    
    @staticmethod
    def encode_for_storage(config: Dict[str, any]) -> str:
        """Encode configuration for secure storage"""
        json_str = json.dumps(config, separators=(',', ':'))
        encoded = base64.b64encode(json_str.encode()).decode()
        return encoded
    
    @staticmethod
    def decode_from_storage(encoded: str) -> Dict[str, any]:
        """Decode configuration from storage"""
        json_str = base64.b64decode(encoded.encode()).decode()
        return json.loads(json_str)
    
    @staticmethod
    def validate_rettiwt_config(config: Dict[str, any]) -> bool:
        """Validate Rettiwt configuration"""
        required_fields = ['apiKey', 'username', 'cookies']
        if not all(field in config for field in required_fields):
            return False
        
        # Check cookies
        required_cookies = ['auth_token', 'ct0']
        cookies = config.get('cookies', {})
        if not all(cookie in cookies for cookie in required_cookies):
            return False
        
        return True
    
    @staticmethod
    def batch_convert(accounts: List[TwitterAccount]) -> Dict[str, Dict[str, any]]:
        """Convert multiple accounts to Rettiwt format"""
        results = {}
        
        for account in accounts:
            try:
                config = RettwiConverter.create_rettiwt_config(account)
                results[account.username] = {
                    'status': 'success',
                    'config': config
                }
            except Exception as e:
                results[account.username] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    @staticmethod
    def export_for_rettiwt(configs: List[Dict[str, any]], output_format: str = 'json') -> str:
        """Export configurations in format suitable for Rettiwt API"""
        if output_format == 'json':
            return json.dumps(configs, indent=2)
        elif output_format == 'jsonl':
            # JSON Lines format (one config per line)
            return '\n'.join(json.dumps(config) for config in configs)
        elif output_format == 'env':
            # Environment variable format
            lines = []
            for i, config in enumerate(configs):
                prefix = f"RETTIWT_ACCOUNT_{i}"
                lines.append(f"{prefix}_API_KEY={config['apiKey']}")
                lines.append(f"{prefix}_USERNAME={config['username']}")
                lines.append(f"{prefix}_COOKIES={base64.b64encode(json.dumps(config['cookies']).encode()).decode()}")
            return '\n'.join(lines)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")