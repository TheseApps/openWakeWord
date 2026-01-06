"""
Secure secrets management utility
Reads API keys and secrets from a .secrets file that is never committed to git
"""

import os
from pathlib import Path
from typing import Optional, Dict
import sys


class SecretsManager:
    """Manages secure loading of API keys and secrets"""
    
    def __init__(self, secrets_file: str = ".secrets"):
        """Initialize the secrets manager
        
        Args:
            secrets_file: Path to the secrets file (relative to project root)
        """
        # Find project root (where .secrets should be)
        self.project_root = self._find_project_root()
        self.secrets_path = self.project_root / secrets_file
        self._secrets_cache: Optional[Dict[str, str]] = None
        
    def _find_project_root(self) -> Path:
        """Find the project root by looking for key files"""
        current = Path.cwd()
        
        # Look for indicators of project root
        indicators = ['.git', 'README.md', 'pyproject.toml', 'setup.py', '.secrets']
        
        while current != current.parent:
            for indicator in indicators:
                if (current / indicator).exists():
                    return current
            current = current.parent
            
        # If not found, use current directory
        return Path.cwd()
    
    def _load_secrets(self) -> Dict[str, str]:
        """Load secrets from file"""
        if self._secrets_cache is not None:
            return self._secrets_cache
            
        secrets = {}
        
        if not self.secrets_path.exists():
            # Create template file if it doesn't exist
            self._create_template()
            print(f"\n{'='*60}")
            print("SECRETS FILE CREATED")
            print(f"{'='*60}")
            print(f"A new .secrets file has been created at:")
            print(f"  {self.secrets_path}")
            print("\nPlease add your API keys to this file.")
            print(f"{'='*60}\n")
            return secrets
        
        try:
            with open(self.secrets_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    # Parse KEY=value format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        secrets[key.strip()] = value.strip()
                        
        except Exception as e:
            print(f"Warning: Could not read secrets file: {e}")
            
        self._secrets_cache = secrets
        return secrets
    
    def _create_template(self):
        """Create a template .secrets file"""
        template = """# Secret Keys Configuration
# This file should NEVER be committed to version control!
# Add your keys here in the format: KEY_NAME=value

# Picovoice Access Key (get from https://console.picovoice.ai/)
PICOVOICE_ACCESS_KEY=your_key_here

# Add more keys as needed following the pattern:
# SERVICE_NAME_KEY=value
"""
        self.secrets_path.write_text(template)
    
    def get(self, key_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret value by key name
        
        Args:
            key_name: The name of the secret to retrieve
            default: Default value if key not found
            
        Returns:
            The secret value or default if not found
        """
        secrets = self._load_secrets()
        value = secrets.get(key_name, default)
        
        if value in [None, "your_key_here", ""]:
            print(f"\n{'!'*60}")
            print(f"MISSING SECRET: {key_name}")
            print(f"{'!'*60}")
            print(f"\n1. Open: {self.secrets_path}")
            print(f"2. Add your key: {key_name}=your_actual_key")
            print(f"3. Save the file and run again\n")
            print(f"{'!'*60}\n")
            return None
            
        return value
    
    def get_required(self, key_name: str) -> str:
        """Get a required secret value (exits if not found)
        
        Args:
            key_name: The name of the secret to retrieve
            
        Returns:
            The secret value
            
        Raises:
            SystemExit: If the key is not found or invalid
        """
        value = self.get(key_name)
        if not value:
            print(f"ERROR: Required secret '{key_name}' not found.")
            print(f"Please add it to {self.secrets_path}")
            sys.exit(1)
        return value
    
    def list_keys(self) -> list:
        """List all available secret keys"""
        secrets = self._load_secrets()
        return list(secrets.keys())


# Global instance for easy access
secrets = SecretsManager()


# Convenience functions
def get_secret(key_name: str, default: Optional[str] = None) -> Optional[str]:
    """Get a secret value by key name"""
    return secrets.get(key_name, default)


def get_required_secret(key_name: str) -> str:
    """Get a required secret value (exits if not found)"""
    return secrets.get_required(key_name)


def ensure_secrets_file():
    """Ensure the secrets file exists and is properly configured"""
    if not secrets.secrets_path.exists():
        secrets._create_template()
        return False
    return True


# Also check for .gitignore
def ensure_gitignore():
    """Ensure .secrets is in .gitignore"""
    gitignore_path = secrets.project_root / ".gitignore"
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
            
        if '.secrets' not in content:
            print("\nAdding .secrets to .gitignore...")
            with open(gitignore_path, 'a') as f:
                f.write("\n# Secret keys file\n.secrets\n")
    else:
        # Create .gitignore with .secrets
        with open(gitignore_path, 'w') as f:
            f.write("# Secret keys file\n.secrets\n")
            f.write("\n# Python\n__pycache__/\n*.pyc\n.venv*/\n")


# Run setup on import
ensure_gitignore()
