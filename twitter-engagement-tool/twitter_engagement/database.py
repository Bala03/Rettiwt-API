"""Database management for Twitter accounts"""

import aiosqlite
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from .models import TwitterAccount, RettiwtCredentials
from .utils import generate_rettiwt_api_key


class AccountDatabase:
    """Manage Twitter accounts in SQLite database"""
    
    def __init__(self, db_path: str = "twitter_accounts.db"):
        self.db_path = Path(db_path)
    
    async def init_db(self):
        """Initialize the database schema"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    email TEXT NOT NULL,
                    email_password TEXT NOT NULL,
                    cookies TEXT DEFAULT '{}',
                    user_agent TEXT,
                    proxy TEXT,
                    rettiwt_api_key TEXT,
                    created_at TEXT NOT NULL,
                    last_used TEXT,
                    is_active INTEGER DEFAULT 1,
                    error_msg TEXT
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS rettiwt_credentials (
                    username TEXT PRIMARY KEY,
                    api_key TEXT NOT NULL,
                    cookies TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    FOREIGN KEY (username) REFERENCES accounts(username)
                )
            ''')
            
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_accounts_active 
                ON accounts(is_active)
            ''')
            
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_accounts_rettiwt 
                ON accounts(rettiwt_api_key)
            ''')
            
            await db.commit()
    
    async def add_account(self, account: TwitterAccount) -> bool:
        """Add or update an account in the database"""
        async with aiosqlite.connect(self.db_path) as db:
            data = account.to_dict()
            
            # Check if account exists
            cursor = await db.execute(
                "SELECT username FROM accounts WHERE username = ?",
                (account.username,)
            )
            exists = await cursor.fetchone()
            
            if exists:
                # Update existing account
                update_fields = [f"{k} = ?" for k in data.keys() if k != 'username']
                values = [v for k, v in data.items() if k != 'username']
                values.append(account.username)
                
                await db.execute(
                    f"UPDATE accounts SET {', '.join(update_fields)} WHERE username = ?",
                    values
                )
            else:
                # Insert new account
                fields = list(data.keys())
                placeholders = ['?' for _ in fields]
                values = list(data.values())
                
                await db.execute(
                    f"INSERT INTO accounts ({', '.join(fields)}) VALUES ({', '.join(placeholders)})",
                    values
                )
            
            await db.commit()
            return True
    
    async def get_account(self, username: str) -> Optional[TwitterAccount]:
        """Get an account by username"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM accounts WHERE username = ?",
                (username,)
            )
            row = await cursor.fetchone()
            
            if row:
                return TwitterAccount.from_dict(dict(row))
            return None
    
    async def get_all_accounts(self) -> List[TwitterAccount]:
        """Get all accounts"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM accounts ORDER BY username")
            rows = await cursor.fetchall()
            
            return [TwitterAccount.from_dict(dict(row)) for row in rows]
    
    async def get_active_accounts(self) -> List[TwitterAccount]:
        """Get all active accounts"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM accounts WHERE is_active = 1 ORDER BY username"
            )
            rows = await cursor.fetchall()
            
            return [TwitterAccount.from_dict(dict(row)) for row in rows]
    
    async def update_account_status(self, username: str, is_active: bool, error_msg: Optional[str] = None):
        """Update account active status"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE accounts SET is_active = ?, error_msg = ? WHERE username = ?",
                (int(is_active), error_msg, username)
            )
            await db.commit()
    
    async def generate_rettiwt_keys(self) -> Dict[str, str]:
        """Generate Rettiwt API keys for all active accounts with cookies"""
        results = {}
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM accounts WHERE is_active = 1 AND cookies != '{}'"
            )
            rows = await cursor.fetchall()
            
            for row in rows:
                account = TwitterAccount.from_dict(dict(row))
                
                try:
                    # Generate API key
                    api_key = generate_rettiwt_api_key(account)
                    
                    # Update account with API key
                    await db.execute(
                        "UPDATE accounts SET rettiwt_api_key = ? WHERE username = ?",
                        (api_key, account.username)
                    )
                    
                    # Store in rettiwt_credentials table
                    creds = RettiwtCredentials(
                        username=account.username,
                        api_key=api_key,
                        cookies=account.cookies
                    )
                    
                    await db.execute(
                        '''INSERT OR REPLACE INTO rettiwt_credentials 
                           (username, api_key, cookies, generated_at) 
                           VALUES (?, ?, ?, ?)''',
                        (creds.username, creds.api_key, json.dumps(creds.cookies), 
                         creds.generated_at.isoformat())
                    )
                    
                    results[account.username] = api_key
                except Exception as e:
                    results[account.username] = f"Error: {str(e)}"
            
            await db.commit()
        
        return results
    
    async def get_rettiwt_credentials(self) -> List[Dict[str, Any]]:
        """Get all Rettiwt credentials"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                '''SELECT r.*, a.is_active, a.error_msg 
                   FROM rettiwt_credentials r
                   JOIN accounts a ON r.username = a.username
                   ORDER BY r.username'''
            )
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                data = dict(row)
                data['cookies'] = json.loads(data['cookies'])
                results.append(data)
            
            return results
    
    async def delete_account(self, username: str) -> bool:
        """Delete an account and its credentials"""
        async with aiosqlite.connect(self.db_path) as db:
            # Delete from both tables
            await db.execute("DELETE FROM rettiwt_credentials WHERE username = ?", (username,))
            await db.execute("DELETE FROM accounts WHERE username = ?", (username,))
            await db.commit()
            
            return True
    
    async def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Total accounts
            cursor = await db.execute("SELECT COUNT(*) FROM accounts")
            stats['total_accounts'] = (await cursor.fetchone())[0]
            
            # Active accounts
            cursor = await db.execute("SELECT COUNT(*) FROM accounts WHERE is_active = 1")
            stats['active_accounts'] = (await cursor.fetchone())[0]
            
            # Accounts with cookies
            cursor = await db.execute("SELECT COUNT(*) FROM accounts WHERE cookies != '{}'")
            stats['accounts_with_cookies'] = (await cursor.fetchone())[0]
            
            # Accounts with Rettiwt keys
            cursor = await db.execute("SELECT COUNT(*) FROM accounts WHERE rettiwt_api_key IS NOT NULL")
            stats['accounts_with_rettiwt'] = (await cursor.fetchone())[0]
            
            # Failed accounts
            cursor = await db.execute("SELECT COUNT(*) FROM accounts WHERE error_msg IS NOT NULL")
            stats['failed_accounts'] = (await cursor.fetchone())[0]
            
            return stats