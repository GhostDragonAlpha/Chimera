> **DEPRECATED** — This document describes the old approach.
> Read `AGENT_ONBOARDING.md`, `DECISION_METHOD.md`, and `EMERGENT_WORKFLOW.md` instead.
> The thought chain is at `docs/THOUGHT_CHAIN.md`.

# Asset Providers & Static Analysis Configuration

## Overview

This document explains the asset generation provider system and static analysis configuration for the Chimera pipeline.

---

## Mock Asset Providers (Issue #2)

### Why 0 Meshes, 6 Mock Textures, 0 Sounds/Animations?

The pipeline generates **placeholder/mock assets** by design when no real API keys are configured:

| Provider | Default Mode | When Real Assets Are Generated |
|----------|-------------|-------------------------------|
| **MeshProvider** (`mesh_provider.py`) | `ProceduralMeshProvider` (text placeholder) | Configure `"provider": "meshy_3d"` with valid API key |
| **ImageProvider** (`image_provider.py`) | `ProceduralTextureProvider` (text placeholder) | Configure `"provider": "stable_diffusion_local"` or `"dalle_api"` with API key |
| **AudioProvider** (`audio_provider.py`) | `ProceduralAudioProvider` (text placeholder) | Configure `"provider": "stable_audio"` with API key |

### How It Works

1. [`AssetGenerator._initialize_providers()`](../../core/asset_generator.py:54) reads the DSL config
2. If no provider is specified or no API keys are found, **procedural fallbacks** are used
3. Procedural providers write text metadata files (`.uasset` stubs) — not real assets

### This Is Expected Behavior

The mock/procedural fallback is intentional:
- **Safe default**: Pipeline doesn't fail when APIs are unavailable
- **Development mode**: Enables rapid iteration without external dependencies
- **Production mode**: Configure real providers for actual asset generation

### How to Enable Real Asset Generation

Create a config file at `Chimera/core/asset_config.json`:

```json
{
    "asset_providers": {
        "textures": {
            "provider": "stable_diffusion_local",
            "model": "sd-xl-base",
            "prompt_prefix": "Unreal Engine texture, high quality, ",
            "negative_prompt": "low quality, blurry, distorted",
            "resolution": [1024, 1024]
        },
        "meshes": {
            "provider": "meshy_3d",
            "format": "obj",
            "poly_budget": 10000
        },
        "audio": {
            "provider": "stable_audio",
            "model": "stable-audio-open-1.0",
            "sample_rate": 44100
        }
    },
    "api_keys": {
        "stable_diffusion_api": "your_sd_api_key_here",
        "meshy_api": "your_meshy_api_key_here",
        "stable_audio_api": "your_stable_audio_api_key_here"
    }
}
```

Then load it in your pipeline:
```python
from core.asset_config import AssetGenerationConfig
config = AssetGenerationConfig("Chimera/core/asset_config.json")
# Pass config to AssetGenerator constructor
```

### TODO Items in Provider Code

All real provider implementations have `TODO` stubs:
- [`mesh_provider.py:58`](../../core/asset_providers/mesh_provider.py:58): Meshy API integration
- [`image_provider.py:71`](../../core/asset_providers/image_provider.py:71): Stable Diffusion inference
- [`audio_provider.py:74`](../../core/asset_providers/audio_provider.py:74): Stable Audio inference

These are placeholders awaiting actual API integration.

---

## Static Analysis — cppcheck (Issue #3)

### Current Behavior

[`build_orchestrator.run_static_analysis()`](../../core/build_orchestrator.py:39) attempts cppcheck first, then falls back to basic syntax validation:

1. Searches for `cppcheck.exe` in these locations:
   - System PATH (`shutil.which("cppcheck")`)
   - `C:\Program Files\CPPCheck\cppcheck.exe`
   - `C:\Tools\cppcheck\cppcheck.exe`
2. If found, runs: `cppcheck --enable=all --quiet --error-exitcode=1 <source_dir>`
3. If not found, falls back to [`_basic_static_analysis()`](../../core/build_orchestrator.py:87)

### Basic Static Analysis Checks

The fallback performs lightweight checks:
- **Balanced braces** in `.h` and `.cpp` files
- **Balanced parentheses** in `.h` and `.cpp` files
- **Correct API macro**: `CHIMERA_API` (not `DEEPSPACETRADER_API`)

### How to Install cppcheck on Windows

#### Option A: Chocolatey (Recommended)
```powershell
choco install cppcheck
# Or for PowerShell 7+: winget installCppCheck.CppCheck
```

#### Option B: Manual Download
1. Download from https://cppcheck.sourceforge.io/ or https://github.com/danmar/cppcheck/releases
2. Extract to `C:\Program Files\CPPCheck\` (matches the search path)
3. Ensure `cppcheck.exe` is in PATH

#### Option C: Portable Copy
Place cppcheck binary at any of these paths:
- `C:\Tools\cppcheck\cppcheck.exe`
- Any directory on your system PATH

### Verification After Installation

```powershell
# Verify installation
cppcheck --version

# Test on source directory (from Chimera folder)
cppcheck --enable=all --quiet --error-exitcode=1 "Source/Chimera/ProceduralGenerated"
```

---

## Summary

| Issue | Status | Action Required |
|-------|--------|-----------------|
| DSL Patch deviations | **Fixed** — improved deviation descriptions in [`validation_reporter.py`](../../core/validation_reporter.py:95) | None; pipeline now provides actionable guidance |
| Mock asset providers | **Expected behavior** — see above for configuration | Configure real API keys if desired |
| cppcheck not found | **Fallback working** — basic analysis runs automatically | Install cppcheck for full static analysis (optional) |
| Playtest skipped | **Documented** — see [`MANUAL_STEPS_PLAYTEST.md`](./MANUAL_STEPS_PLAYTEST.md) | Run `Automation RunTests ChimeraTests` in-editor |
