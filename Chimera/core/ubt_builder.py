"""
Unreal Build Tool (UBT) Builder - Detects and invokes UnrealBuildTool for project compilation.

Detection order:
1. UE_ROOT/ENGINE_ROOT environment variables
2. Windows registry (HKEY_LOCAL_MACHINE\\SOFTWARE\\Epic Games\\Unreal Engine\\Builds) -> use raw string in code
3. Chimera/config/ue_config.json

Always verifies {UE_ROOT}/Engine/Binaries/DotNET/UnrealBuildTool.exe exists before invoking.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any


class UBTBuilder:
    """Builder class for Unreal Build Tool compilation."""

    def __init__(self):
        self.ue_root: Optional[str] = None
        self.ubt_path: Optional[str] = None

    def detect_ue_root(self) -> Optional[str]:
        """Detect Unreal Engine root directory using the detection order."""
        # 1) Check UE_ROOT/ENGINE_ROOT env vars
        for env_var in ["UE_ROOT", "ENGINE_ROOT"]:
            ue_root = os.environ.get(env_var)
            if ue_root:
                # UE 5.8+ path: {UE_ROOT}/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe
                ubt_test_path_new = Path(ue_root) / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool" / "UnrealBuildTool.exe"
                if ubt_test_path_new.exists():
                    return str(Path(ue_root).resolve())
                
                # Legacy path: {UE_ROOT}/Engine/Binaries/DotNET/UnrealBuildTool.exe
                ubt_test_path_legacy = Path(ue_root) / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool.exe"
                if ubt_test_path_legacy.exists():
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
                            ubt_test_path_new = Path(engine_root_val) / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool" / "UnrealBuildTool.exe"
                            if ubt_test_path_new.exists():
                                return str(Path(engine_root_val).resolve())
                            
                            # Legacy path
                            ubt_test_path_legacy = Path(engine_root_val) / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool.exe"
                            if ubt_test_path_legacy.exists():
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
                        ubt_test_path_new = Path(ue_root_from_config) / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool" / "UnrealBuildTool.exe"
                        if ubt_test_path_new.exists():
                            return str(Path(ue_root_from_config).resolve())
                        
                        # Legacy path
                        ubt_test_path_legacy = Path(ue_root_from_config) / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool.exe"
                        if ubt_test_path_legacy.exists():
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
            
            # Look for UE_5.x directories
            try:
                for ue_dir in base_path.glob("UE_5.*"):
                    if ue_dir.is_dir():
                        # UE 5.8+ path
                        ubt_test_path_new = ue_dir / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool" / "UnrealBuildTool.exe"
                        if ubt_test_path_new.exists():
                            return str(ue_dir.resolve())
                        
                        # Legacy path
                        ubt_test_path_legacy = ue_dir / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool.exe"
                        if ubt_test_path_legacy.exists():
                            return str(ue_dir.resolve())
            except Exception:
                pass

        return None

    def verify_ubt_exists(self, ue_root: str) -> bool:
        """Verify that UnrealBuildTool.exe exists at the expected path."""
        # UE 5.8+ uses: {UE_ROOT}/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe
        ubt_path_new = Path(ue_root) / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool" / "UnrealBuildTool.exe"
        if ubt_path_new.exists():
            return True
        
        # Legacy path: {UE_ROOT}/Engine/Binaries/DotNET/UnrealBuildTool.exe
        ubt_path_legacy = Path(ue_root) / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool.exe"
        return ubt_path_legacy.exists()

    def setup(self) -> bool:
        """Setup UBT builder by detecting UE root and verifying UBT exists."""
        self.ue_root = self.detect_ue_root()
        
        if not self.ue_root:
            raise RuntimeError("Could not detect Unreal Engine root directory.")
        
        # UE 5.8+ uses: {UE_ROOT}/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe
        ubt_path_new = Path(self.ue_root) / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool" / "UnrealBuildTool.exe"
        if ubt_path_new.exists():
            self.ubt_path = str(ubt_path_new)
        else:
            # Legacy path: {UE_ROOT}/Engine/Binaries/DotNET/UnrealBuildTool.exe
            ubt_path_legacy = Path(self.ue_root) / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool.exe"
            if not ubt_path_legacy.exists():
                raise RuntimeError(f"UnrealBuildTool.exe not found at {self.ue_root}/Engine/Binaries/DotNET/UnrealBuildTool or {self.ue_root}/Engine/Binaries/DotNET/UnrealBuildTool.exe")
            self.ubt_path = str(ubt_path_legacy)
        
        return True

    def compile_project(self, project_name: str, uproject_path: str, build_configuration: str = "Development") -> bool:
        """
        Compile the Unreal project using UBT's built-in incremental build system.
        
        Invokes command: {UE_ROOT}/Engine/Binaries/DotNET/UnrealBuildTool.exe {ProjectName}Editor Win64 Development {ProjectPath}.uproject -TargetType=Editor -Progress -NoEngineChanges -NoHotReloadFromIDE
        """
        if not self.ubt_path or not Path(self.ubt_path).exists():
            if not self.setup():
                raise RuntimeError("UBT Builder not properly setup.")

        uproject_file = Path(uproject_path)
        
        ubt_command = [
            self.ubt_path,
            f"{project_name}Editor",
            "Win64",
            build_configuration,
            str(uproject_path),
            "-TargetType=Editor",
            "-Progress",
            "-NoEngineChanges",
            "-NoHotReloadFromIDE"
        ]

        print(f"Invoking UBT: {' '.join(ubt_command)}")
        
        try:
            result = subprocess.run(ubt_command, check=True, capture_output=False)
            print("UBT compilation completed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"UBT compilation failed with return code: {e.returncode}")
            return False
        except Exception as e:
            print(f"UBT compilation error: {e}")
            return False


# Global UBT builder instance
ubt_builder = UBTBuilder()
