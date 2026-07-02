"""
Asset Generator — Creates declared assets at specified paths using AI tools or providers.

Uses art_direction block in DSL for style guidance.
Generates meshes, textures, animations, sounds via configurable asset providers.

Provider Configuration (in dsl_data or separate config):
{
    "asset_providers": {
        "textures": {"provider": "stable_diffusion", "type": "procedural"},
        "meshes": {"provider": "meshy_3d", "type": "procedural"},
        "audio": {"provider": "stable_audio", "type": "procedural"}
    }
}
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from core.asset_providers.base_provider import AssetGenerationProvider, MockAssetProvider
    from core.asset_providers.image_provider import StableDiffusionImageProvider, ProceduralTextureProvider
    from core.asset_providers.mesh_provider import Meshy3DProvider, ProceduralMeshProvider
    from core.asset_providers.audio_provider import StableAudioProvider, ProceduralAudioProvider
except ImportError:
    try:
        from asset_providers.base_provider import AssetGenerationProvider, MockAssetProvider
        from asset_providers.image_provider import StableDiffusionImageProvider, ProceduralTextureProvider
        from asset_providers.mesh_provider import Meshy3DProvider, ProceduralMeshProvider
        from asset_providers.audio_provider import StableAudioProvider, ProceduralAudioProvider
    except ImportError:
        # Fallback to mock providers
        class MockAssetProvider:
            pass
        class StableDiffusionImageProvider:
            def __init__(self, config=None): pass
        class Meshy3DProvider:
            def __init__(self, config=None): pass
        class StableAudioProvider:
            def __init__(self, config=None): pass


class AssetGenerator:
    """Generates game assets based on DSL specifications and art_direction guidance using providers."""

    def __init__(self, content_dir: str, provider_config: Dict[str, Any] = None):
        self.content_dir = Path(content_dir) / "ProceduralGenerated" / "Assets"
        self.content_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize asset providers
        self.providers = self._initialize_providers(provider_config)

    def _initialize_providers(self, config: Dict[str, Any]) -> Dict[str, AssetGenerationProvider]:
        """Initialize asset generation providers based on configuration."""
        providers = {}
        
        # Default to mock/procedural providers if no real API keys/config provided
        asset_providers_config = config.get("asset_providers", {}) if config else {}
        
        # Texture provider
        tex_config = asset_providers_config.get("textures", {"provider": "procedural"})
        if tex_config.get("provider") == "stable_diffusion":
            providers["textures"] = StableDiffusionImageProvider(tex_config)
        else:
            providers["textures"] = ProceduralTextureProvider()
            
        # Mesh provider
        mesh_config = asset_providers_config.get("meshes", {"provider": "procedural"})
        if mesh_config.get("provider") == "meshy_3d":
            providers["meshes"] = Meshy3DProvider(mesh_config)
        else:
            providers["meshes"] = ProceduralMeshProvider()
            
        # Audio provider
        audio_config = asset_providers_config.get("audio", {"provider": "procedural"})
        if audio_config.get("provider") == "stable_audio":
            providers["audio"] = StableAudioProvider(audio_config)
        else:
            providers["audio"] = ProceduralAudioProvider()
            
        return providers

    def generate_assets_from_dsl(self, dsl_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate all assets from DSL data based on art_direction guidance and providers."""
        generated_assets = {
            "meshes": [],
            "textures": [],
            "animations": [],
            "sounds": []
        }

        # Get art direction guidance
        art_direction = dsl_data.get("art_direction", {})
        style = art_direction.get("style", "default")
        color_palette = art_direction.get("color_palette", "neutral")

        print(f"Generating assets with style: {style}, color palette: {color_palette}")
        print(f"Using providers: {[p.provider_name for p in self.providers.values()]}")

        # Generate biome textures if survival stats or world generation is present
        if "survival_stats" in dsl_data.get("gameplay", {}) or "world" in dsl_data:
            biome_texture_paths = self._generate_biome_textures_with_provider(style, color_palette)
            generated_assets["textures"].extend(biome_texture_paths)

        # Generate crafting station meshes if crafting systems are present
        if "crafting_systems" in dsl_data.get("gameplay", {}):
            crafting_mesh_paths = self._generate_crafting_station_meshes(style)
            generated_assets["meshes"].extend(crafting_mesh_paths)

        # Generate survival UI elements if survival stats are present
        if "survival_stats" in dsl_data.get("gameplay", {}):
            ui_texture_paths = self._generate_survival_ui_elements_with_provider(style, color_palette)
            generated_assets["textures"].extend(ui_texture_paths)

        # Generate meshes for levels and NPCs using mesh provider
        if "world" in dsl_data and "levels" in dsl_data["world"]:
            for level in dsl_data["world"]["levels"]:
                level_name = level.get("name", "MainCity")
                mesh_path = self._generate_environment_mesh(level_name, style)
                generated_assets["meshes"].append(mesh_path)

        if "world" in dsl_data and "npcs" in dsl_data["world"]:
            for npc in dsl_data["world"]["npcs"]:
                npc_name = npc.get("name", "Blacksmith")
                mesh_path = self._generate_npc_mesh(npc_name, style)
                generated_assets["meshes"].append(mesh_path)

        # Generate textures using image provider
        texture_paths = self._generate_textures_with_provider(style, color_palette)
        generated_assets["textures"].extend(texture_paths)

        # Generate animations for abilities and characters
        if "gameplay" in dsl_data and "abilities" in dsl_data["gameplay"]:
            for ab in dsl_data["gameplay"]["abilities"]:
                ab_name = ab.get("name", "Dash")
                anim_path = self._generate_ability_animation(ab_name, style)
                generated_assets["animations"].append(anim_path)

        # Generate sounds using audio provider
        if "audio" in dsl_data:
            audio_config = dsl_data["audio"]
            
            # Generate music cues
            if "music_cues" in audio_config:
                for mc in audio_config["music_cues"]:
                    mc_name = mc.get("name", "Exploration")
                    loop = mc.get("loop", False)
                    mood = style  # Use style as mood fallback
                    music_path = self._generate_music_cue_with_provider(mc_name, mood, loop)
                    generated_assets["sounds"].append(music_path)
                    
            # Generate SFX
            if "sfx" in audio_config:
                for sfx in audio_config["sfx"]:
                    sfx_name = sfx.get("name", "SwordSwing")
                    sfx_path = self._generate_sfx_with_provider(sfx_name)
                    generated_assets["sounds"].append(sfx_path)

        return generated_assets

    def _generate_environment_mesh(self, level_name: str, style: str) -> str:
        """Generate environment mesh using provider or fallback."""
        content_dir = self.content_dir / "Environment" / level_name
        content_dir.mkdir(parents=True, exist_ok=True)
        
        mesh_path = content_dir / f"SM_{level_name}_Environment.uasset"
        
        # Try to use mesh provider if available
        mesh_provider = self.providers.get("meshes")
        if mesh_provider and hasattr(mesh_provider, 'generate_mesh'):
            desc = f"{level_name} environment terrain and structures"
            result_path = mesh_provider.generate_mesh(desc, style, mesh_path)
            if result_path:
                return str(result_path)
        
        # Fallback to placeholder
        with open(mesh_path, 'w', encoding='utf-8') as f:
            f.write(f"/Script/Engine.StaticMesh\n")
            f.write(f'{{\n')
            f.write(f'\tAssetName="{level_name}_Environment"\n')
            f.write(f'\tStyle="{style}"\n')
            f.write(f'}}\n')
            
        return str(mesh_path)

    def _generate_npc_mesh(self, npc_name: str, style: str) -> str:
        """Generate NPC mesh using provider or fallback."""
        content_dir = self.content_dir / "Characters" / "NPCs"
        content_dir.mkdir(parents=True, exist_ok=True)
        
        mesh_path = content_dir / f"SK_{npc_name}.uasset"
        
        # Try to use mesh provider
        mesh_provider = self.providers.get("meshes")
        if mesh_provider and hasattr(mesh_provider, 'generate_mesh'):
            desc = f"{npc_name} character model"
            result_path = mesh_provider.generate_mesh(desc, style, mesh_path)
            if result_path:
                return str(result_path)
        
        # Fallback to placeholder
        with open(mesh_path, 'w', encoding='utf-8') as f:
            f.write(f"/Script/Engine.SkeletalMesh\n")
            f.write(f'{{\n')
            f.write(f'\tAssetName="SK_{npc_name}"\n')
            f.write(f'\tStyle="{style}"\n')
            f.write(f'}}\n')
            
        return str(mesh_path)

    def _generate_textures_with_provider(self, style: str, color_palette: str) -> List[str]:
        """Generate textures using image provider."""
        content_dir = self.content_dir / "Textures"
        content_dir.mkdir(parents=True, exist_ok=True)
        
        texture_files = []
        image_provider = self.providers.get("textures")
        
        # Generate base textures
        textures_to_generate = [
            ("T_Material_Base", "base_material texture"),
            ("T_Texture_Environment", "environment texture"),
            ("T_Texture_UI", "ui elements texture")
        ]
        
        for tex_name, tex_desc in textures_to_generate:
            tex_path = content_dir / f"{tex_name}.uasset"
            
            # Try to use image provider
            if image_provider and hasattr(image_provider, 'generate_texture'):
                result_path = image_provider.generate_texture(tex_desc, style, color_palette, tex_path)
                if result_path:
                    texture_files.append(str(result_path))
                    continue
            
            # Fallback to placeholder
            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(f"/Script/Engine.Texture2D\n")
                f.write(f'{{\n')
                f.write(f'\tAssetName="{tex_name}"\n')
                f.write(f'\tType="{tex_desc.split()[0]}"\n')
                f.write(f'\tStyle="{style}"\n')
                f.write(f'\tColorPalette="{color_palette}"\n')
                f.write(f'}}\n')
                
            texture_files.append(str(tex_path))
            
        return texture_files

    def _generate_ability_animation(self, ability_name: str, style: str) -> str:
        """Generate animation for an ability."""
        content_dir = self.content_dir / "Animations" / "Abilities"
        content_dir.mkdir(parents=True, exist_ok=True)
        
        anim_filename = f"AM_{ability_name}"
        anim_path = content_dir / f"{anim_filename}.uasset"
        
        with open(anim_path, 'w', encoding='utf-8') as f:
            f.write(f"/Script/Engine.AnimMontage\n")
            f.write(f'{{\n')
            f.write(f'\tAssetName="{anim_filename}"\n')
            f.write(f'\tAbility="{ability_name}"\n')
            f.write(f'\tStyle="{style}"\n')
            f.write(f'}}\n')
            
        return str(anim_path)

    def _generate_music_cue_with_provider(self, cue_name: str, mood: str, loop: bool) -> str:
        """Generate music cue using audio provider."""
        content_dir = self.content_dir / "Audio" / "Music"
        content_dir.mkdir(parents=True, exist_ok=True)
        
        cue_path = content_dir / f"MC_{cue_name}.uasset"
        
        # Try to use audio provider
        audio_provider = self.providers.get("audio")
        if audio_provider and hasattr(audio_provider, 'generate_music_cue'):
            result_path = audio_provider.generate_music_cue(cue_name, mood, loop, cue_path)
            if result_path:
                return str(result_path)
        
        # Fallback to placeholder
        with open(cue_path, 'w', encoding='utf-8') as f:
            f.write(f"/Script/AudioMixer.MusicCue\n")
            f.write(f'{{\n')
            f.write(f'\tAssetName="MC_{cue_name}"\n')
            f.write(f'\tMood="{mood}"\n')
            f.write(f'\tLoop={loop}\n')
            f.write(f'}}\n')
            
        return str(cue_path)

    def _generate_sfx_with_provider(self, sfx_name: str) -> str:
        """Generate sound effect using audio provider."""
        content_dir = self.content_dir / "Audio" / "SFX"
        content_dir.mkdir(parents=True, exist_ok=True)
        
        sfx_path = content_dir / f"SFX_{sfx_name}.uasset"
        
        # Try to use audio provider
        audio_provider = self.providers.get("audio")
        if audio_provider and hasattr(audio_provider, 'generate_sound_effect'):
            result_path = audio_provider.generate_sound_effect(sfx_name, 2.0, sfx_path)
            if result_path:
                return str(result_path)
        
        # Fallback to placeholder
        with open(sfx_path, 'w', encoding='utf-8') as f:
            f.write(f"/Script/AudioDevice.WaveInstance\n")
            f.write(f'{{\n')
            f.write(f'\tAssetName="SFX_{sfx_name}"\n')
            f.write(f'\tDuration="2.0s"\n')
            f.write(f'}}\n')
            
        return str(sfx_path)

    def _generate_biome_textures_with_provider(self, style: str, color_palette: str) -> List[str]:
        """Generate biome textures using image provider."""
        content_dir = self.content_dir / "Textures" / "Biomes"
        content_dir.mkdir(parents=True, exist_ok=True)
        
        texture_files = []
        image_provider = self.providers.get("textures")
        
        # Generate biome-specific textures
        biomes_to_generate = [
            ("T_Biome_Forest", "forest biome ground and foliage texture"),
            ("T_Biome_Desert", "desert biome sand texture"),
            ("T_Biome_Tundra", "tundra biome snow and ice texture")
        ]
        
        for tex_name, tex_desc in biomes_to_generate:
            tex_path = content_dir / f"{tex_name}.uasset"
            
            # Try to use image provider
            if image_provider and hasattr(image_provider, 'generate_texture'):
                result_path = image_provider.generate_texture(tex_desc, style, color_palette, tex_path)
                if result_path:
                    texture_files.append(str(result_path))
                    continue
            
            # Fallback to placeholder
            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(f"/Script/Engine.Texture2D\n")
                f.write(f'{{\n')
                f.write(f'\tAssetName="{tex_name}"\n')
                f.write(f'\tType="biome_texture"\n')
                f.write(f'\tStyle="{style}"\n')
                f.write(f'\tColorPalette="{color_palette}"\n')
                f.write(f'}}\n')
                
            texture_files.append(str(tex_path))
            
        return texture_files

    def _generate_crafting_station_meshes(self, style: str) -> List[str]:
        """Generate crafting station meshes using provider or fallback."""
        content_dir = self.content_dir / "Environment" / "CraftingStations"
        content_dir.mkdir(parents=True, exist_ok=True)
        
        mesh_files = []
        mesh_provider = self.providers.get("meshes")
        
        # Generate crafting station meshes
        stations_to_generate = [
            ("SM_Crafting_Workbench", "crafting workbench station"),
            ("SM_Smithy_Anvil", "smithy anvil workstation"),
            ("SM_Fire_Pit", "campfire pit for survival crafting")
        ]
        
        for mesh_name, mesh_desc in stations_to_generate:
            mesh_path = content_dir / f"{mesh_name}.uasset"
            
            # Try to use mesh provider
            if mesh_provider and hasattr(mesh_provider, 'generate_mesh'):
                result_path = mesh_provider.generate_mesh(mesh_desc, style, mesh_path)
                if result_path:
                    mesh_files.append(str(result_path))
                    continue
            
            # Fallback to placeholder
            with open(mesh_path, 'w', encoding='utf-8') as f:
                f.write(f"/Script/Engine.StaticMesh\n")
                f.write(f'{{\n')
                f.write(f'\tAssetName="{mesh_name}"\n')
                f.write(f'\tType="crafting_station"\n')
                f.write(f'\tStyle="{style}"\n')
                f.write(f'}}\n')
                
            mesh_files.append(str(mesh_path))
            
        return mesh_files

    def _generate_survival_ui_elements_with_provider(self, style: str, color_palette: str) -> List[str]:
        """Generate survival UI element textures using image provider."""
        content_dir = self.content_dir / "Textures" / "UI" / "Survival"
        content_dir.mkdir(parents=True, exist_ok=True)
        
        texture_files = []
        image_provider = self.providers.get("textures")
        
        # Generate survival UI element textures
        ui_elements_to_generate = [
            ("T_UI_Hunger_Icon", "hunger stat icon for survival HUD"),
            ("T_UI_Thirst_Icon", "thirst stat icon for survival HUD"),
            ("T_UI_Temperature_Icon", "temperature stat icon for survival HUD")
        ]
        
        for tex_name, tex_desc in ui_elements_to_generate:
            tex_path = content_dir / f"{tex_name}.uasset"
            
            # Try to use image provider
            if image_provider and hasattr(image_provider, 'generate_texture'):
                result_path = image_provider.generate_texture(tex_desc, style, color_palette, tex_path)
                if result_path:
                    texture_files.append(str(result_path))
                    continue
            
            # Fallback to placeholder
            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(f"/Script/Engine.Texture2D\n")
                f.write(f'{{\n')
                f.write(f'\tAssetName="{tex_name}"\n')
                f.write(f'\tType="survival_ui_icon"\n')
                f.write(f'\tStyle="{style}"\n')
                f.write(f'\tColorPalette="{color_palette}"\n')
                f.write(f'}}\n')
                
            texture_files.append(str(tex_path))
            
        return texture_files
