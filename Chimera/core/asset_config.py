"""
Asset Generation Configuration — Settings for AI asset generation providers.

Configuration structure:
{
    "asset_providers": {
        "textures": {
            "provider": "stable_diffusion" | "dalle_api" | "procedural",
            "model": "sd-xl-base",
            "prompt_prefix": "Unreal Engine texture, high quality, ",
            "negative_prompt": "low quality, blurry, distorted",
            "resolution": [1024, 1024]
        },
        "meshes": {
            "provider": "meshy_api" | "luma_ai" | "procedural",
            "format": "obj" | "fbx" | "gltf",
            "poly_budget": 10000
        },
        "audio": {
            "provider": "stable_audio" | "audiocraft" | "procedural",
            "model": "stable-audio-open-1.0",
            "sample_rate": 44100
        }
    },
    "api_keys": {
        "stable_diffusion_api": "...",
        "dalle_api": "...",
        "meshy_api": "...",
        "luma_ai_api": "...",
        "stable_audio_api": "..."
    }
}
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class AssetGenerationConfig:
    """Configuration manager for AI asset generation providers."""

    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else None
        self.config = self._load_default_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration with procedural fallbacks."""
        return {
            "asset_providers": {
                "textures": {
                    "provider": "procedural",
                    "model": "sd-xl-base",
                    "prompt_prefix": "Unreal Engine texture, high quality, ",
                    "negative_prompt": "low quality, blurry, distorted",
                    "resolution": [1024, 1024]
                },
                "meshes": {
                    "provider": "procedural",
                    "format": "obj",
                    "poly_budget": 10000
                },
                "audio": {
                    "provider": "procedural",
                    "model": "stable-audio-open-1.0",
                    "sample_rate": 44100
                }
            },
            "api_keys": {}
        }

    def load_config(self, config_path: str):
        """Load configuration from JSON file."""
        path = Path(config_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

    def get_provider_config(self, asset_type: str) -> Dict[str, Any]:
        """Get provider configuration for a specific asset type."""
        return self.config.get("asset_providers", {}).get(asset_type, {})

    def get_api_key(self, service_name: str) -> Optional[str]:
        """Get API key for a specific service."""
        return self.config.get("api_keys", {}).get(service_name)

    def set_provider_config(self, asset_type: str, config: Dict[str, Any]):
        """Set provider configuration for a specific asset type."""
        if "asset_providers" not in self.config:
            self.config["asset_providers"] = {}
        self.config["asset_providers"][asset_type] = config

    def set_api_key(self, service_name: str, api_key: str):
        """Set API key for a specific service."""
        if "api_keys" not in self.config:
            self.config["api_keys"] = {}
        self.config["api_keys"][service_name] = api_key

    def save_config(self, config_path: str):
        """Save configuration to JSON file."""
        path = Path(config_path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)


# Default configuration instance
default_asset_config = AssetGenerationConfig()
