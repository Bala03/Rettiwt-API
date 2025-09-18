"""Parser for account files"""

import json
import base64
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from .models import TwitterAccount
from .utils import parse_cookies


class AccountParser:
    """Parse Twitter accounts from various file formats"""
    
    @staticmethod
    def guess_delimiter(line_format: str) -> str:
        """Guess the delimiter used in the line format"""
        # Remove spaces and look for common delimiters
        common_delims = [':', ',', '|', ';', '\t']
        for delim in common_delims:
            if delim in line_format:
                return delim
        return ':'
    
    @staticmethod
    def parse_line_format(line_format: str) -> Tuple[str, List[str]]:
        """Parse the line format string to extract delimiter and fields"""
        delim = AccountParser.guess_delimiter(line_format)
        fields = [f.strip() for f in line_format.split(delim)]
        return delim, fields
    
    @staticmethod
    def validate_line_format(fields: List[str]) -> None:
        """Validate that required fields are present"""
        required_fields = {'username', 'password', 'email', 'email_password'}
        provided_fields = set(fields) - {'_'}  # Exclude skip marker
        
        missing = required_fields - provided_fields
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
    
    @staticmethod
    def parse_file(filepath: str, line_format: str) -> List[TwitterAccount]:
        """Parse accounts from a file"""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Parse format specification
        delimiter, fields = AccountParser.parse_line_format(line_format)
        AccountParser.validate_line_format(fields)
        
        accounts = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):  # Skip empty lines and comments
                    continue
                
                try:
                    account = AccountParser.parse_line(line, delimiter, fields)
                    accounts.append(account)
                except Exception as e:
                    print(f"Error parsing line {line_num}: {e}")
                    continue
        
        return accounts
    
    @staticmethod
    def parse_line(line: str, delimiter: str, fields: List[str]) -> TwitterAccount:
        """Parse a single line into a TwitterAccount"""
        values = line.split(delimiter)
        
        if len(values) < len(fields):
            raise ValueError(f"Not enough values in line. Expected {len(fields)}, got {len(values)}")
        
        # Trim to expected length
        values = values[:len(fields)]
        
        # Create mapping of field to value
        data = {}
        for field, value in zip(fields, values):
            if field == '_':  # Skip marker
                continue
            
            value = value.strip()
            
            # Special handling for cookies
            if field == 'cookies' and value:
                try:
                    data['cookies'] = parse_cookies(value)
                except Exception as e:
                    print(f"Warning: Failed to parse cookies: {e}")
                    data['cookies'] = {}
            else:
                data[field] = value
        
        # Create account with parsed data
        return TwitterAccount(**data)