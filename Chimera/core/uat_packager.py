"""
Unreal Automation Tool (UAT) Packager - Cooks assets and packages project for target platforms.

Detection order:
1. UE_ROOT/ENGINE_ROOT environment variables
2. Windows registry (HKEY_LOCAL_MACHINE\\SOFTWARE\\Epic Games\\Unreal Engine\\Builds)
3. Chimera/config/ue_config.json

Always verifies {UE_ROOT}/Engine/Binaries/DotNET/AutomationTool/UnrealAutomationTool.exe exists before invoking.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List


class UATPackager:
    """Packager class for Unreal Automation Tool packaging."""

    def __init__(self):
        self.ue_root: Optional[str] = None
        self.uat_path: Optional[str] = None

    def detect_ue_root(self) -> Optional[str]:
        """Detect Unreal Engine root directory using the detection order."""
        # 1) Check UE_ROOT/ENGINE_ROOT env vars
        for env_var in ["UE_ROOT", "ENGINE_ROOT"]:
            ue_root = os.environ.get(env_var)
            if ue_root:
                # UE 5.8+ path
                uat_test_path_new = Path(ue_root) / "Engine" / "Binaries" / "DotNET" / "AutomationTool" / "UnrealAutomationTool.exe"
                if uat_test_path_new.exists():
                    return str(Path(ue_root).resolve())
                
                # Legacy path
                uat_test_path_legacy = Path(ue_root) / "Engine" / "Binaries" / "DotNET" / "AutomationTool.exe"
                if uat_test_path_legacy.exists():
                    return str(Path(ue_root).resolve())

        # 2) Check Windows registry
        try:
            import winreg
            key_path = r"SOFTWARE\Epic Games\Unreal Engine\Builds"
            try:
                reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            except FileNotFoundError:
                reg_key = None
            
            if reg_key:
                try:
                    build_count = winreg.QueryInfoKey(reg_key)[0]
                    for i in range(build_count):
                        build_name = winreg.EnumKey(reg_key, i)
                        try:
                            build_key_path = rf"{key_path}\{build_name}"
                            version_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, build_key_path)
                            engine_root_val, _ = winreg.QueryValueEx(version_key, "EngineRoot")
                            # UE 5.8+ path
                            uat_test_path_new = Path(engine_root_val) / "Engine" / "Binaries" / "DotNET" / "AutomationTool" / "UnrealAutomationTool.exe"
                            if uat_test_path_new.exists():
                                return str(Path(engine_root_val).resolve())
                            
                            # Legacy path
                            uat_test_path_legacy = Path(engine_root_val) / "Engine" / "Binaries" / "DotNET" / "AutomationTool.exe"
                            if uat_test_path_legacy.exists():
                                return str(Path(engine_root_val).resolve())
                        except Exception:
                            continue
                finally:
                    winreg.CloseKey(reg_key)
        except Exception:
            pass

        # 3) Check Chimera/config/ue_config.json or Chimera/Config/ue_config.json
        config_paths = [
            Path(__file__).parent.parent / "config" / "ue_config.json",
            Path(__file__).parent.parent / "Config" / "ue_config.json",
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    ue_root_from_config = config.get("ue_root") or config.get("engine_root")
                    if ue_root_from_config:
                        # UE 5.8+ path
                        uat_test_path_new = Path(ue_root_from_config) / "Engine" / "Binaries" / "DotNET" / "AutomationTool" / "UnrealAutomationTool.exe"
                        if uat_test_path_new.exists():
                            return str(Path(ue_root_from_config).resolve())
                        
                        # Legacy path
                        uat_test_path_legacy = Path(ue_root_from_config) / "Engine" / "Binaries" / "DotNET" / "AutomationTool.exe"
                        if uat_test_path_legacy.exists():
                            return str(Path(ue_root_from_config).resolve())
                except Exception:
                    pass

        # 4) Fallback: Search common UE installation directories
        common_paths = [
            Path("C:\\Program Files\\Epic Games"),
            Path("E:\\UnrealEngine"),
        ]
        
        for base_path in common_paths:
            if not base_path.exists():
                continue
            
            try:
                for ue_dir in base_path.glob("UE_5.*"):
                    if ue_dir.is_dir():
                        # UE 5.8+ path
                        uat_test_path_new = ue_dir / "Engine" / "Binaries" / "DotNET" / "AutomationTool" / "UnrealAutomationTool.exe"
                        if uat_test_path_new.exists():
                            return str(ue_dir.resolve())
                        
                        # Legacy path
                        uat_test_path_legacy = ue_dir / "Engine" / "Binaries" / "DotNET" / "AutomationTool.exe"
                        if uat_test_path_legacy.exists():
                            return str(ue_dir.resolve())
            except Exception:
                pass

        return None

    def setup(self) -> bool:
        """Setup UAT packager by detecting UE root and verifying UAT exists."""
        self.ue_root = self.detect_ue_root()
        
        if not self.ue_root:
            raise RuntimeError("Could not detect Unreal Engine root directory.")
        
        # UE 5.8+ path
        uat_path_new = Path(self.ue_root) / "Engine" / "Binaries" / "DotNET" / "AutomationTool" / "UnrealAutomationTool.exe"
        if uat_path_new.exists():
            self.uat_path = str(uat_path_new)
        else:
            # Legacy path
            uat_path_legacy = Path(self.ue_root) / "Engine" / "Binaries" / "DotNET" / "AutomationTool.exe"
            if not uat_path_legacy.exists():
                raise RuntimeError(f"UnrealAutomationTool.exe not found at {self.ue_root}/Engine/Binaries/DotNET/AutomationTool or {self.ue_root}/Engine/Binaries/DotNET/AutomationTool.exe")
            self.uat_path = str(uat_path_legacy)
        
        return True

    def package_project(self, uproject_path: str, target_platforms: List[str], output_dir: Path, 
                        cook_assets: bool = True, stage_files: bool = True) -> Dict[str, Any]:
        """
        Package the Unreal project for specified target platforms.
        
        Args:
            uproject_path: Path to the .uproject file
            target_platforms: List of target platforms (e.g., ["Win64", "PS5"])
            output_dir: Output directory for packaged game
            cook_assets: Whether to cook assets before packaging
            stage_files: Whether to stage files before packaging
            
        Returns:
            Dict with 'success', 'package_path', or 'error' message
        """
        if not self.uat_path or not Path(self.uat_path).exists():
            if not self.setup():
                raise RuntimeError("UAT Packager not properly setup.")

        uproject_file = Path(uproject_path)
        project_name = uproject_file.stem
        
        # Determine primary platform (Win64 for PC, Ps5 for PlayStation, etc.)
        primary_platform = "Win64"
        for platform in target_platforms:
            if platform.startswith("Win"):
                primary_platform = platform
                break
        
        # Build UAT command for packaging
        uat_command = [
            self.uat_path,
            "-ProjectPath=" + str(uproject_file),
            f"-Target={primary_platform}",
            "-Command=Packaged",
        ]
        
        if cook_assets:
            uat_command.extend(["-Cook", "-Stage"])
        
        uat_command.extend([f"-Package={str(output_dir / project_name)}"])
        
        print(f"Invoking UAT packaging: {' '.join(uat_command)}")
        
        try:
            result = subprocess.run(uat_command, check=True, capture_output=False)
            package_path = output_dir / project_name / f"{project_name}-{primary_platform.lower()}.exe"
            
            return {
                "success": True,
                "package_path": str(package_path),
                "platforms": target_platforms
            }
        except subprocess.CalledProcessError as e:
            print(f"UAT packaging failed with return code: {e.returncode}")
            return {
                "success": False,
                "error": f"Packaging failed with return code: {e.returncode}"
            }
        except Exception as e:
            print(f"UAT packaging error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global UAT packager instance
uat_packager = UATPackager()
