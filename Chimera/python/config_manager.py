"""
Centralized configuration manager with multi-format support, environment overrides,
hot-reload, and schema validation. Integrates with existing config.py patterns.
"""

import json
import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


class SchemaValidationError(Exception):
    """Raised when configuration fails schema validation."""
    pass


class ConfigManager:
    """Centralized configuration manager with multi-format support and hot-reload."""

    def __init__(self, config_path: Path, schema: Optional[Dict[str, Any]] = None):
        self._config_path = config_path
        self._schema = schema or {}
        self._settings: Dict[str, Any] = {}
        self._watchers: List[Callable[[Path], None]] = []
        self._lock = threading.Lock()
        self._last_mtime = 0.0
        self._load_config(config_path)

    def _load_config(self, path: Path) -> None:
        """Load settings from JSON/YAML/INI format."""
        if not path.exists():
            return
        suffix = path.suffix.lower()
        try:
            if suffix == '.json':
                with open(path, 'r') as f:
                    self._settings.update(json.load(f))
            elif suffix in ('.yaml', '.yml'):
                if not _HAS_YAML:
                    raise ImportError("PyYAML required for YAML config files")
                with open(path, 'r') as f:
                    self._settings.update(yaml.safe_load(f) or {})
            elif suffix == '.ini':
                import configparser
                parser = configparser.ConfigParser()
                parser.read(path)
                for section in parser.sections():
                    self._settings[section] = dict(parser[section])
        except Exception:
            pass

    def _apply_env_overrides(self, prefix: str = "CHIMERA") -> None:
        """Apply environment variable overrides (e.g., CHIMERA_GENERATION_SEED=99)."""
        for key, value in os.environ.items():
            if not key.startswith(f"{prefix}_"):
                continue
            inner_key = key[len(prefix) + 1:]
            try:
                self._settings[inner_key] = int(value)
            except ValueError:
                try:
                    self._settings[inner_key] = float(value)
                except ValueError:
                    if value.lower() in ('true', 'false'):
                        self._settings[inner_key] = value.lower() == 'true'
                    else:
                        self._settings[inner_key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dotted path or top-level key."""
        keys = key.split('.')
        current: Any = self._settings
        for k in keys:
            if isinstance(current, dict):
                current = current.get(k, default)
            else:
                return default
        return current

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dotted path notation."""
        keys = key.split('.')
        target: Dict[str, Any] = self._settings
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value

    def save(self) -> None:
        """Persist current settings back to the config file."""
        with open(self._config_path, 'w') as f:
            json.dump(self._settings, f, indent=2)

    def validate_schema(self) -> bool:
        """Validate required fields against schema definition."""
        for key, spec in self._schema.items():
            value = self.get(key)
            if spec.get('required') and value is None:
                raise SchemaValidationError(f"Missing required config field: {key}")
            expected_type = spec.get('type')
            if expected_type and not isinstance(value, expected_type):
                raise SchemaValidationError(
                    f"Type mismatch for '{key}': expected {expected_type.__name__}, got {type(value).__name__}"
                )
        return True

    def watch(self, callback: Optional[Callable[[Path], None]] = None) -> bool:
        """Enable hot-reload by watching the config file for changes."""
        if not self._config_path.exists():
            return False
        watcher = callback or self._reload
        self._watchers.append(watcher)
        self._last_mtime = self._config_path.stat().st_mtime
        return True

    def _check_for_changes(self) -> None:
        """Internal check for file modification time changes."""
        if not self._config_path.exists():
            return
        current_mtime = self._config_path.stat().st_mtime
        if current_mtime > self._last_mtime:
            with self._lock:
                self._reload(self._config_path)

    def _reload(self, path: Path) -> None:
        """Reload config from file and re-apply env overrides."""
        prev = dict(self._settings)
        self._load_config(path)
        self._apply_env_overrides()
        self._last_mtime = path.stat().st_mtime

    def snapshot(self) -> Dict[str, Any]:
        """Return a deep copy of current settings for comparison or serialization."""
        import copy
        return copy.deepcopy(self._settings)
