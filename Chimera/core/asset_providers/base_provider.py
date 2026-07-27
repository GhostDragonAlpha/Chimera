"""
Asset Generation Provider Interface — Abstract base class for AI asset generation services.

Defines the interface that all asset providers must implement:
- Text-to-image (textures, concepts)
- Text-to-3D (meshes)
- Text-to-audio (SFX, music cues)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path


class AssetGenerationProvider(ABC):
    """Base interface for AI asset generation providers."""

    def __init__(self, provider_name: str, config: Dict[str, Any] = None):
        self.provider_name = provider_name
        self.config = config or {}

    @abstractmethod
    def generate_texture(self, description: str, style: str, color_palette: str, 
                         output_path: Path) -> Optional[Path]:
        """Generate a texture image from text description."""
        pass

    @abstractmethod
    def generate_mesh(self, description: str, style: str, output_path: Path) -> Optional[Path]:
        """Generate a 3D mesh from text description."""
        pass

    @abstractmethod
    def generate_sound_effect(self, description: str, duration_seconds: float, 
                              output_path: Path) -> Optional[Path]:
        """Generate a sound effect from text description."""
        pass

    @abstractmethod
    def generate_music_cue(self, description: str, mood: str, loop: bool, 
                           output_path: Path) -> Optional[Path]:
        """Generate a music cue from text description."""
        pass

    def validate_texture(self, image_path: Path, expected_palette: str) -> bool:
        """Validate that generated texture matches expected color palette."""
        # Default implementation: always valid (can be overridden)
        return True

    def validate_mesh(self, mesh_path: Path, max_polygons: int = 10000) -> bool:
        """Validate that generated mesh is within polygon budget."""
        # Default implementation: always valid (can be overridden)
        return True

    def validate_audio(self, audio_path: Path, expected_duration: float, tolerance_seconds: float = 0.5) -> bool:
        """Validate that generated audio matches expected duration."""
        # Default implementation: always valid (can be overridden)
        return True


class MockAssetProvider(AssetGenerationProvider):
    """Mock asset provider that creates placeholder files for testing."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("mock", config or {})

    def generate_texture(self, description: str, style: str, color_palette: str, 
                         output_path: Path) -> Optional[Path]:
        """Create placeholder texture file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"// Placeholder Texture\n")
            f.write(f"Description: {description}\n")
            f.write(f"Style: {style}\n")
            f.write(f"ColorPalette: {color_palette}\n")
        return output_path

    def generate_mesh(self, description: str, style: str, output_path: Path) -> Optional[Path]:
        """Create placeholder mesh file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"// Placeholder Mesh\n")
            f.write(f"Description: {description}\n")
            f.write(f"Style: {style}\n")
        return output_path

    def generate_sound_effect(self, description: str, duration_seconds: float, 
                              output_path: Path) -> Optional[Path]:
        """Create placeholder sound file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"// Placeholder Sound Effect\n")
            f.write(f"Description: {description}\n")
            f.write(f"Duration: {duration_seconds}s\n")
        return output_path

    def generate_music_cue(self, description: str, mood: str, loop: bool, 
                           output_path: Path) -> Optional[Path]:
        """Create placeholder music file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"// Placeholder Music Cue\n")
            f.write(f"Description: {description}\n")
            f.write(f"Mood: {mood}\n")
            f.write(f"Loop: {loop}\n")
        return output_path
