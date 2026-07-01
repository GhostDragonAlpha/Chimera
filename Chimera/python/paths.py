"""
Path management utilities: project root detection, config resolution, asset mapping,
and cross-platform path handling. Follows existing config.py patterns.
"""

import os
from pathlib import Path
from typing import Optional


# Cached state (mirrors config.py _PROJECT_ROOT pattern)
_PROJECT_ROOT: Optional[Path] = None
_ASSET_CACHE: dict[str, Path] = {}


def find_project_root(start: Optional[Path] = None, markers: list[str] | None = None) -> Path:
    """Search upward from start (or cwd) for project root by looking for known marker files/dirs."""
    if start is None:
        start = Path.cwd()
    default_markers = ['.git', 'Chimera.uproject', 'config.py']
    markers = markers or default_markers

    current = start.resolve()
    while True:
        for marker in markers:
            if (current / marker).exists():
                return current
        parent = current.parent
        if parent == current:
            raise RuntimeError(f"No project root found searching from {start}")
        current = parent


def get_project_root(start: Optional[Path] = None) -> Path:
    """Get cached or newly resolved project root."""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        try:
            _PROJECT_ROOT = find_project_root(start)
        except RuntimeError:
            _PROJECT_ROOT = start or Path.cwd()
    return _PROJECT_ROOT


def resolve_config_path(config_name: str, base_dir: Optional[Path] = None) -> Path:
    """Resolve config path with fallback chain: user override → env → default.

    Priority:
      1. CHIMERA_CONFIG_<name> environment variable (absolute or relative to HOME)
      2. <base_dir>/config/<config_name>.json if base_dir provided
      3. <project_root>/.chimera/configs/<config_name>.json
      4. <project_root>/<config_name>.json
    """
    env_key = f"CHIMERA_CONFIG_{config_name.upper()}"
    env_path = os.environ.get(env_key)
    if env_path:
        candidate = Path(env_path)
        if not candidate.is_absolute():
            candidate = Path.home() / candidate
        if candidate.exists():
            return candidate

    project_root = get_project_root(base_dir)

    candidates = [
        project_root / "config" / config_name,
        project_root / ".chimera" / "configs" / config_name,
        project_root / config_name,
    ]
    for c in candidates:
        if c.exists():
            return c
    # Return first candidate as the canonical default location
    return candidates[0]


def map_asset(asset_rel_path: str, base_dir: Optional[Path] = None) -> Path:
    """Map a relative asset path to an absolute path within the project.

    Handles both forward-slash and backslash separators; resolves '..' components.
    Caches results for repeated lookups of the same relative path.
    """
    if asset_rel_path in _ASSET_CACHE:
        return _ASSET_CACHE[asset_rel_path]

    project_root = get_project_root(base_dir)
    # Normalize separators and resolve
    normalized = str(asset_rel_path).replace('\\', '/')
    resolved = (project_root / normalized).resolve()
    _ASSET_CACHE[asset_rel_path] = resolved
    return resolved


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, creating it if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def is_cross_platform_safe(path: Path) -> bool:
    """Check if a path uses cross-platform compatible separators and no absolute Windows paths."""
    parts = str(path)
    # Reject hardcoded drive letters (C:\, D:\, etc.)
    if len(parts) > 1 and parts[1] == ':':
        return False
    # Check for mixed separators
    if '\\' in parts and '/' in parts:
        return False
    return True


def to_forward_slash(path: Path) -> str:
    """Convert a path to forward-slash string (UE-friendly format)."""
    return str(path).replace('\\', '/')
