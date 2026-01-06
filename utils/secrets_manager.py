"""
Secure secrets management utility
Reads API keys and secrets from .secrets.json file
Never commits secrets to version control
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any


class SecretsManager:
    """Manages secure access to API keys and secrets"""
    
    def __init__(self, secrets_file: str = ".secrets.json"):
        """Initialize with path to secrets file"""
        # Look for secrets file in multiple locations
        possible_paths = [
            Path(secrets_file),  # Current directory
            Path.home() / secrets_file,  # Home directory
            Path(__file__).parent.parent / secrets_file,  # Project root
            Path.cwd() / secrets_file,  # Working directory
        ]
        
        self.secrets_path = None
        for path in possible_paths:
            if path.exists():
                self.secrets_path = path
                break
        
        self.secrets = self._load_secrets()
    
    def _load_secrets(self) -> Dict[str, Any]:
        """Load secrets from JSON file"""
        if not self.secrets_path:
            return {}
            
        try:
            with open(self.secrets_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"ERROR: Invalid JSON in {self.secrets_path}")
            return {}
        except Exception as e:
            print(f"ERROR loading secrets: {e}")
            return {}
    
    def get(self, service: str, key: str = None, required: bool = True) -> Optional[str]:
        """
        Get a secret value
        
        Args:
            service: The service name (e.g., 'picovoice', 'openai')
            key: The specific key within the service (e.g., 'access_key')
            required: If True, exit if key not found
        
        Returns:
            The secret value or None if not found
        """
        if not self.secrets:
            if required:
                print("\n" + "!" * 60)
                print("SECRETS FILE NOT FOUND!")
                print("!" * 60)
                print("\n1. Create a .secrets.json file in the project root")
                print("2. Copy the template from .secrets.json.template")
                print("3. Add your API keys")
                print("4. Make sure .secrets.json is in .gitignore\n")
                sys.exit(1)
            return None
        
        # Get service secrets
        service_secrets = self.secrets.get(service, {})
        
        # If no key specified, return the whole service dict
        if key is None:
            # If service has a single key that's not 'description', return it
            keys = [k for k in service_secrets.keys() if k != 'description']
            if len(keys) == 1:
                return service_secrets.get(keys[0])
            return service_secrets
        
        # Get specific key
        value = service_secrets.get(key)
        
        # Check if it's still a placeholder
        if value and "YOUR_" in value and "_HERE" in value:
            if required:
                print("\n" + "!" * 60)
                print(f"API KEY NOT CONFIGURED: {service}.{key}")
                print("!" * 60)
                description = service_secrets.get('description', '')
                if description:
                    print(f"\nHow to get this key:\n{description}")
                print(f"\n1. Open .secrets.json")
                print(f"2. Replace {value} with your actual key")
                print(f"3. Save the file and run again\n")
                sys.exit(1)
            return None
        
        return value
    
    def set(self, service: str, key: str, value: str) -> bool:
        """
        Set a secret value (updates the file)
        
        Args:
            service: The service name
            key: The key within the service
            value: The value to set
        
        Returns:
            True if successful
        """
        if not self.secrets_path:
            print("ERROR: No secrets file found")
            return False
        
        # Update in memory
        if service not in self.secrets:
            self.secrets[service] = {}
        self.secrets[service][key] = value
        
        # Save to file
        try:
            with open(self.secrets_path, 'w') as f:
                json.dump(self.secrets, f, indent=2)
            return True
        except Exception as e:
            print(f"ERROR saving secrets: {e}")
            return False
    
    def list_services(self) -> list:
        """List all configured services"""
        return [k for k in self.secrets.keys() if isinstance(self.secrets[k], dict)]


# Convenience functions
_manager = None

def get_secret(service: str, key: str = None, required: bool = True) -> Optional[str]:
    """Get a secret value (convenience function)"""
    global _manager
    if _manager is None:
        _manager = SecretsManager()
    return _manager.get(service, key, required)

def set_secret(service: str, key: str, value: str) -> bool:
    """Set a secret value (convenience function)"""
    global _manager
    if _manager is None:
        _manager = SecretsManager()
    return _manager.set(service, key, value)
