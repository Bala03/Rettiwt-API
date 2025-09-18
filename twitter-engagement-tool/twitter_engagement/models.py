"""Data models for Twitter Engagement Tool"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
import json


@dataclass
class TwitterAccount:
    """Represents a Twitter account with authentication details"""
    username: str
    password: str
    email: str
    email_password: str
    cookies: Dict[str, str] = field(default_factory=dict)
    user_agent: Optional[str] = None
    proxy: Optional[str] = None
    rettiwt_api_key: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    is_active: bool = True
    error_msg: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage"""
        return {
            'username': self.username,
            'password': self.password,
            'email': self.email,
            'email_password': self.email_password,
            'cookies': json.dumps(self.cookies),
            'user_agent': self.user_agent,
            'proxy': self.proxy,
            'rettiwt_api_key': self.rettiwt_api_key,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'is_active': int(self.is_active),
            'error_msg': self.error_msg
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TwitterAccount':
        """Create from dictionary (database row)"""
        data = data.copy()
        cookie_data = data.get('cookies', '{}')
        if cookie_data == '""' or cookie_data == '':
            data['cookies'] = {}
        else:
            try:
                data['cookies'] = json.loads(cookie_data)
            except (json.JSONDecodeError, TypeError):
                data['cookies'] = {}
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('last_used'):
            data['last_used'] = datetime.fromisoformat(data['last_used'])
        data['is_active'] = bool(data.get('is_active', 1))
        return cls(**data)


@dataclass
class RettiwtCredentials:
    """Represents Rettiwt API credentials"""
    username: str
    api_key: str
    cookies: Dict[str, str]
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_json(self) -> str:
        """Convert to JSON string for storage"""
        return json.dumps({
            'username': self.username,
            'apiKey': self.api_key,
            'cookies': self.cookies,
            'generatedAt': self.generated_at.isoformat()
        })