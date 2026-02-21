"""Configuration manager for MediaForge."""
import os
import yaml
from typing import Any, Dict, Optional
import sys


DEFAULT_CONFIG = {
    'nsfw_mode': False,
    'library_folders': [],
    'watch_folders': [],
    'default_action': 'copy',
    'conflict_resolution': 'rename_increment',
    'duplicate_action': 'skip_and_log',
    'api_keys': {
        'stashdb': '',
        'tmdb': '',
        'omdb': '',
        'acoustid_client': ''
    },
    'api_enabled': {
        'stashdb': False,
        'tmdb': False,
        'omdb': False,
        'musicbrainz': False,
        'acoustid': False
    },
    'rules': [],
    'face_detection': {
        'enabled': True,
        'threshold': 0.6,
        'sample_rate': 1
    },
    'thumbnails': {
        'enabled': True,
        'size': 256
    },
    'theme': 'dark-pink',
}


class ConfigManager:
    """Manages YAML configuration for MediaForge."""

    def __init__(self, config_path: str = None):
        """Initialize ConfigManager."""
        if config_path is None:
            config_dir = os.path.expanduser('~/.mediaforge')
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, 'config.yaml')
        
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load config from file or create default."""
        try:
            with open(self.config_path, 'r') as f:
                loaded = yaml.safe_load(f)
                if loaded is None:
                    loaded = {}
                # Merge with defaults to ensure all keys exist
                merged = DEFAULT_CONFIG.copy()
                merged.update(loaded)
                return merged
        except FileNotFoundError:
            # Create default config file
            with open(self.config_path, 'w') as f:
                yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
            return DEFAULT_CONFIG.copy()

    def load(self, path: str = None) -> Dict[str, Any]:
        """Load config from a specific path."""
        if path is None:
            path = self.config_path
        
        try:
            with open(path, 'r') as f:
                loaded = yaml.safe_load(f)
                if loaded is None:
                    loaded = {}
                merged = DEFAULT_CONFIG.copy()
                merged.update(loaded)
                return merged
        except FileNotFoundError:
            return DEFAULT_CONFIG.copy()

    def save(self, path: str = None) -> bool:
        """Save config to file."""
        if path is None:
            path = self.config_path
        
        try:
            os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
            with open(path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}", file=sys.stderr)
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dotted key."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value

    def set(self, key: str, value: Any) -> bool:
        """Set config value by dotted key."""
        keys = key.split('.')
        current = self.config
        
        # Navigate to parent
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set value
        current[keys[-1]] = value
        return self.save()

    def get_all(self) -> Dict[str, Any]:
        """Get entire config."""
        return self.config.copy()

    def reload(self) -> bool:
        """Reload config from disk."""
        try:
            self.config = self._load_config()
            return True
        except Exception:
            return False
