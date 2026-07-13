"""
Configuration module for the Chimera Procedural Game Generator.
Contains all game parameters, procedural rules, project paths, and UE engine file locations.

All modules should use the shared logger from this module instead of raw print() calls.
Configure logging level via LOG_LEVEL environment variable (default: INFO).
"""

import copy
import gc
import json
import logging
import os
import re
import shutil
import socket
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List

# Configure shared logger for all Chimera modules with rotating file handler
_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logger = logging.getLogger("Chimera")
logger.setLevel(getattr(logging, _LOG_LEVEL, logging.INFO))

if not logger.handlers:
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, _LOG_LEVEL, logging.INFO))
    console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Rotating file handler - 10 MB max size, keep 5 backup files
    log_dir = Path(CHIMERA_SAVED_LOGS_DIR if 'CHIMERA_SAVED_LOGS_DIR' in globals() else Path.cwd() / "Saved" / "Logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "chimera.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        delay=True,  # defer opening chimera.log until the first emit — importing a
                     # module that pulls in this config must not crash just because
                     # the shared log is momentarily locked by another process.
    )
    file_handler.setLevel(getattr(logging, _LOG_LEVEL, logging.INFO))
    file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

# JSON logging formatter for structured logs
class JSONFormatter(logging.Formatter):
    """Format log records as JSON with timestamp, level, message, and context fields."""
    
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        if hasattr(record, 'context') and record.context:
            log_entry["context"] = record.context
        return json.dumps(log_entry)


# Suppress urllib3 noise from LM Studio HTTP calls
logging.getLogger("urllib3").setLevel(logging.WARNING)


def log(level: str, message: str) -> None:
    """Log a message at the specified level.
    
    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Message to log
    """
    getattr(logger, level.lower())(message)


def log_structured(level: str, message: str, context: dict = None) -> None:
    """Log a structured JSON message with timestamp, level, message, and context fields.
    
    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Message to log
        context: Optional dictionary of context fields to include in the log
    """
    record = logger.makeRecord(logger.name, getattr(logging, level.upper()), 
                               logging.currentframe().f_back.f_code.co_filename,
                               logging.currentframe().f_back.f_lineno, message, (), None)
    if context:
        record.context = context
    json_formatter = JSONFormatter()
    print(json_formatter.format(record))


def status(message: str) -> None:
    """Log a status message with consistent formatting."""
    log("INFO", f"[STATUS] {message}")


def progress(current: int, total: int, task: str = "Progress") -> None:
    """Log progress with percentage formatting."""
    if total <= 0:
        pct = 100.0
    else:
        pct = (current / total) * 100
    log("INFO", f"[PROGRESS] {task}: {current}/{total} ({pct:.1f}%)")


# ============================================================================
# GLOBAL PATH RESOLUTION STATE (populated by get_* functions)
# ============================================================================

_PROJECT_ROOT = None
_SOURCE_DIR = None
_CONTENT_DIR = None
_PYTHON_SCRIPTS_DIR = None


# ============================================================================
# UNREAL ENGINE 5.8 — FILE LOCATION REGISTRY
# Centralized registry of all UE engine executables, tools, and directories.
# Access via GameConfiguration.ue_* properties.
# ============================================================================

SUPPORTED_UE_VERSIONS = {"5.8", "5.7", "5.6"}

PLATFORM_FEATURES = {
    "windows": {
        "5.8": ["shader_compile_worker", "uba_agent", "live_coding_console"],
        "5.7": ["shader_compile_worker", "uba_agent"],
        "5.6": ["shader_compile_worker"]
    },
    "linux": {
        "5.8": ["shader_compile_worker"],
        "5.7": ["shader_compile_worker"],
        "5.6": ["shader_compile_worker"]
    }
}

UE_ENGINE_ROOT = Path(r"C:\Program Files\Epic Games\UE_5.8")
UE_ENGINE_ENGINE_DIR = UE_ENGINE_ROOT / "Engine"
UE_ENGINE_BINARIES_WIN64 = UE_ENGINE_ENGINE_DIR / "Binaries" / "Win64"
UE_ENGINE_BINARIES_DOTNET = UE_ENGINE_ENGINE_DIR / "Binaries" / "DotNET"

# UE Editor executables
UE_EDITOR_EXE = UE_ENGINE_BINARIES_WIN64 / "UnrealEditor.exe"
UE_EDITOR_CMD_EXE = UE_ENGINE_BINARIES_WIN64 / "UnrealEditor-Cmd.exe"
UE_EDITOR_DEBUG_GAME_EXE = UE_ENGINE_BINARIES_WIN64 / "UnrealEditor-Win64-DebugGame.exe"
UE_EDITOR_DEBUG_GAME_CMD_EXE = UE_ENGINE_BINARIES_WIN64 / "UnrealEditor-Win64-DebugGame-Cmd.exe"

# UE Game executables
UE_GAME_EXE = UE_ENGINE_BINARIES_WIN64 / "UnrealGame.exe"
UE_GAME_DEBUG_EXE = UE_ENGINE_BINARIES_WIN64 / "UnrealGame-Win64-DebugGame.exe"
UE_GAME_SHIPPING_EXE = UE_ENGINE_BINARIES_WIN64 / "UnrealGame-Win64-Shipping.exe"

# UE Build Tools (DotNET)
UBT_DOTNET_AUTOMATIONTOOL = UE_ENGINE_BINARIES_DOTNET / "AutomationTool" / "UnrealBuildTool.exe"
UBT_DOTNET_UNREALBUILDTOOL = UE_ENGINE_BINARIES_DOTNET / "UnrealBuildTool" / "UnrealBuildTool.exe"

# UE Build Accelerator (UBA)
UBA_AGENT_EXE = UE_ENGINE_ENGINE_DIR / "Binaries" / "Win64" / "UnrealBuildAccelerator" / "x64" / "UbaAgent.exe"
UBA_CACHE_SERVICE_EXE = UE_ENGINE_ENGINE_DIR / "Binaries" / "Win64" / "UnrealBuildAccelerator" / "x64" / "UbaCacheService.exe"
UBA_CLI_EXE = UE_ENGINE_ENGINE_DIR / "Binaries" / "Win64" / "UnrealBuildAccelerator" / "x64" / "UbaCli.exe"

# UE Shader Compile Worker (compiles shaders on demand)
SHADER_COMPILE_WORKER_EXE = UE_ENGINE_BINARIES_WIN64 / "ShaderCompileWorker.exe"

# UE Build Tools (Win64 native — may not exist in all installs)
UBT_WIN64_DIR = UE_ENGINE_ENGINE_DIR / "Binaries" / "Win64"

# UE Other tools
UNREAL_LIGHTMASS_EXE = UE_ENGINE_BINARIES_WIN64 / "UnrealLightmass.exe"
UNREAL_PAK_EXE = UE_ENGINE_BINARIES_WIN64 / "UnrealPak.exe"
UNREAL_PACKAGE_TOOL_EXE = UE_ENGINE_BINARIES_WIN64 / "UnrealPackageTool.exe"
UNREAL_INSIGHTS_EXE = UE_ENGINE_BINARIES_WIN64 / "UnrealInsights.exe"
UNREAL_TRACE_SERVER_EXE = UE_ENGINE_BINARIES_WIN64 / "UnrealTraceServer.exe"
UNREAL_OBJECT_PTR_TOOL_EXE = UE_ENGINE_BINARIES_WIN64 / "UnrealObjectPtrTool.exe"
CRASH_REPORT_CLIENT_EXE = UE_ENGINE_BINARIES_WIN64 / "CrashReportClient.exe"

# Automation / Live tools
LIVE_CODING_CONSOLE_EXE = UE_ENGINE_BINARIES_WIN64 / "LiveCodingConsole.exe"
LIVE_LINK_HUB_EXE = UE_ENGINE_BINARIES_WIN64 / "LiveLinkHub.exe"
SWITCHBOARD_LISTENER_EXE = UE_ENGINE_BINARIES_WIN64 / "SwitchboardListener.exe"


# ============================================================================
# CHIMERA PROJECT — FILE LOCATION REGISTRY
# Centralized registry of all Chimera project files and directories.
# Access via GameConfiguration.chimera_* properties.
# ============================================================================

CHIMERA_PROJECT_ROOT = Path(r"E:\PythonChimera\Chimera")
CHIMERA_ROOT = Path(r"E:\PythonChimera")
CHIMERA_UPROJECT_FILE = CHIMERA_PROJECT_ROOT / "Chimera.uproject"
CHIMERA_SOURCE_DIR = CHIMERA_PROJECT_ROOT / "Source" / "Chimera"
CHIMERA_CONTENT_DIR = CHIMERA_PROJECT_ROOT / "Content"
CHIMERA_PYTHON_DIR = CHIMERA_PROJECT_ROOT / "Python"
CHIMERA_INTERMEDIATE_DIR = CHIMERA_PROJECT_ROOT / "Intermediate"
CHIMERA_DERIVED_DATA_CACHE_DIR = CHIMERA_PROJECT_ROOT / "DerivedDataCache"
CHIMERA_SAVED_DIR = CHIMERA_PROJECT_ROOT / "Saved"
CHIMERA_SAVED_LOGS_DIR = CHIMERA_SAVED_DIR / "Logs"
CHIMERA_SAVED_SCREENSHOTS_DIR = CHIMERA_SAVED_DIR / "Screenshots"

# Chimera C++ source files (known paths)
CHIMERA_CPP_FILES = {
    "Chimera.h": CHIMERA_SOURCE_DIR / "Chimera.h",
    "Chimera.cpp": CHIMERA_SOURCE_DIR / "Chimera.cpp",
    "Chimera.Build.cs": CHIMERA_PROJECT_ROOT / "Source" / "Chimera.Build.cs",
    "ChimeraGameMode.h": CHIMERA_SOURCE_DIR / "ChimeraGameMode.h",
    "ChimeraGameMode.cpp": CHIMERA_SOURCE_DIR / "ChimeraGameMode.cpp",
    "ChimeraPawn.h": CHIMERA_SOURCE_DIR / "ChimeraPawn.h",
    "ChimeraPawn.cpp": CHIMERA_SOURCE_DIR / "ChimeraPawn.cpp",
    "ChimeraPlayerController.h": CHIMERA_SOURCE_DIR / "ChimeraPlayerController.h",
    "ChimeraPlayerController.cpp": CHIMERA_SOURCE_DIR / "ChimeraPlayerController.cpp",
    "ChimeraUI.h": CHIMERA_SOURCE_DIR / "ChimeraUI.h",
    "ChimeraUI.cpp": CHIMERA_SOURCE_DIR / "ChimeraUI.cpp",
    "ChimeraWheelFront.h": CHIMERA_SOURCE_DIR / "ChimeraWheelFront.h",
    "ChimeraWheelFront.cpp": CHIMERA_SOURCE_DIR / "ChimeraWheelFront.cpp",
    "ChimeraWheelRear.h": CHIMERA_SOURCE_DIR / "ChimeraWheelRear.h",
    "ChimeraWheelRear.cpp": CHIMERA_SOURCE_DIR / "ChimeraWheelRear.cpp",
    "FlightControlComponent.h": CHIMERA_SOURCE_DIR / "FlightControlComponent.h",
    "FlightControlComponent.cpp": CHIMERA_SOURCE_DIR / "FlightControlComponent.cpp",
    "ThrustVectoringComponent.h": CHIMERA_SOURCE_DIR / "ThrustVectoringComponent.h",
    "ThrustVectoringComponent.cpp": CHIMERA_SOURCE_DIR / "ThrustVectoringComponent.cpp",
    "AttitudeStabilizerComponent.h": CHIMERA_SOURCE_DIR / "AttitudeStabilizerComponent.h",
    "AttitudeStabilizerComponent.cpp": CHIMERA_SOURCE_DIR / "AttitudeStabilizerComponent.cpp",
}

# Chimera C++ subdirectory files
CHIMERA_OFFROAD_FILES = {
    "ChimeraOffroadCar.h": CHIMERA_SOURCE_DIR / "OffroadCar" / "ChimeraOffroadCar.h",
    "ChimeraOffroadCar.cpp": CHIMERA_SOURCE_DIR / "OffroadCar" / "ChimeraOffroadCar.cpp",
    "ChimeraOffroadWheelFront.h": CHIMERA_SOURCE_DIR / "OffroadCar" / "ChimeraOffroadWheelFront.h",
    "ChimeraOffroadWheelFront.cpp": CHIMERA_SOURCE_DIR / "OffroadCar" / "ChimeraOffroadWheelFront.cpp",
    "ChimeraOffroadWheelRear.h": CHIMERA_SOURCE_DIR / "OffroadCar" / "ChimeraOffroadWheelRear.h",
    "ChimeraOffroadWheelRear.cpp": CHIMERA_SOURCE_DIR / "OffroadCar" / "ChimeraOffroadWheelRear.cpp",
}

CHIMERA_SPORTSCAR_FILES = {
    "ChimeraSportsCar.h": CHIMERA_SOURCE_DIR / "SportsCar" / "ChimeraSportsCar.h",
    "ChimeraSportsCar.cpp": CHIMERA_SOURCE_DIR / "SportsCar" / "ChimeraSportsCar.cpp",
    "ChimeraSportsWheelFront.h": CHIMERA_SOURCE_DIR / "SportsCar" / "ChimeraSportsWheelFront.h",
    "ChimeraSportsWheelFront.cpp": CHIMERA_SOURCE_DIR / "SportsCar" / "ChimeraSportsWheelFront.cpp",
    "ChimeraSportsWheelRear.h": CHIMERA_SOURCE_DIR / "SportsCar" / "ChimeraSportsWheelRear.h",
    "ChimeraSportsWheelRear.cpp": CHIMERA_SOURCE_DIR / "SportsCar" / "ChimeraSportsWheelRear.cpp",
}

CHIMERA_TIMETRIAL_FILES = {
    "TimeTrialGameMode.h": CHIMERA_SOURCE_DIR / "Variant_TimeTrial" / "TimeTrialGameMode.h",
    "TimeTrialGameMode.cpp": CHIMERA_SOURCE_DIR / "Variant_TimeTrial" / "TimeTrialGameMode.cpp",
    "TimeTrialPlayerController.h": CHIMERA_SOURCE_DIR / "Variant_TimeTrial" / "TimeTrialPlayerController.h",
    "TimeTrialPlayerController.cpp": CHIMERA_SOURCE_DIR / "Variant_TimeTrial" / "TimeTrialPlayerController.cpp",
    "TimeTrialTrackGate.h": CHIMERA_SOURCE_DIR / "Variant_TimeTrial" / "TimeTrialTrackGate.h",
    "TimeTrialTrackGate.cpp": CHIMERA_SOURCE_DIR / "Variant_TimeTrial" / "TimeTrialTrackGate.cpp",
    "TimeTrialStartUI.h": CHIMERA_SOURCE_DIR / "Variant_TimeTrial" / "UI" / "TimeTrialStartUI.h",
    "TimeTrialStartUI.cpp": CHIMERA_SOURCE_DIR / "Variant_TimeTrial" / "UI" / "TimeTrialStartUI.cpp",
    "TimeTrialUI.h": CHIMERA_SOURCE_DIR / "Variant_TimeTrial" / "UI" / "TimeTrialUI.h",
    "TimeTrialUI.cpp": CHIMERA_SOURCE_DIR / "Variant_TimeTrial" / "UI" / "TimeTrialUI.cpp",
}

CHIMERA_OFFROAD_MODE_FILES = {
    "OffroadGameMode.h": CHIMERA_SOURCE_DIR / "Variant_OffRoad" / "OffroadGameMode.h",
    "OffroadGameMode.cpp": CHIMERA_SOURCE_DIR / "Variant_OffRoad" / "OffroadGameMode.cpp",
}

# Python scripts
CHIMERA_PYTHON_SCRIPTS = {
    "config.py": CHIMERA_PYTHON_DIR / "config.py",
    "cpp_generator.py": CHIMERA_PYTHON_DIR / "cpp_generator.py",
    "procedural_game_generator.py": CHIMERA_PYTHON_DIR / "procedural_game_generator.py",
    "unreal_api_operations.py": CHIMERA_PYTHON_DIR / "unreal_api_operations.py",
    "screenshot_lmstudio_workflow.py": CHIMERA_PYTHON_DIR / "screenshot_lmstudio_workflow.py",
    "play_test.py": CHIMERA_PYTHON_DIR / "play_test.py",
    "run_flight_physics.py": CHIMERA_PYTHON_DIR / "run_flight_physics.py",
    "run_screenshot_analysis.py": CHIMERA_PYTHON_DIR / "run_screenshot_analysis.py",
}


# ============================================================================
# KILO / DEVELOPMENT ENVIRONMENT — FILE LOCATION REGISTRY
# Centralized registry of Kilo CLI and development tool paths.
# ============================================================================

KLO_CONFIG_GLOBAL = Path(r"C:\Users\allen\.config\kilo")
KLO_CONFIG_PROJECT = CHIMERA_PROJECT_ROOT / ".kilo"
KLO_CONFIG_FILE = KLO_CONFIG_GLOBAL / "kilo.jsonc"
KLO_EXTENSION_DIR = r"C:\Users\allen\.vscode\extensions\kilocode.kilo-code-7.3.54-win32-x64"

# LM Studio (local/remote)
LM_STUDIO_BASE_URL = "http://192.168.3.169:1234"
LM_STUDIO_MODELS_ENDPOINT = f"{LM_STUDIO_BASE_URL}/api/v1/models"
LM_STUDIO_CHAT_COMPLETIONS_ENDPOINT = f"{LM_STUDIO_BASE_URL}/v1/chat/completions"
LM_STUDIO_MODEL = "dhruvallabs/qwen-agentworld-35b-a3b"


# ============================================================================
# PATH RESOLUTION HELPERS (for when unreal module is available)
# ============================================================================

def get_project_root() -> str:
    """Get the project root directory."""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        try:
            import unreal
            _PROJECT_ROOT = str(unreal.Paths.project_root())
        except Exception:
            _PROJECT_ROOT = str(CHIMERA_PROJECT_ROOT)
    return _PROJECT_ROOT

def get_source_dir() -> str:
    """Get the C++ source directory."""
    global _SOURCE_DIR
    if _SOURCE_DIR is None:
        try:
            import unreal
            root = str(unreal.Paths.project_root())
            _SOURCE_DIR = str(Path(root) / "Source" / "Chimera")
        except Exception:
            _SOURCE_DIR = str(CHIMERA_SOURCE_DIR)
    return _SOURCE_DIR

def get_content_dir() -> str:
    """Get the Content directory."""
    global _CONTENT_DIR
    if _CONTENT_DIR is None:
        try:
            import unreal
            root = str(unreal.Paths.project_root())
            _CONTENT_DIR = str(Path(root) / "Content")
        except Exception:
            _CONTENT_DIR = str(CHIMERA_CONTENT_DIR)
    return _CONTENT_DIR

def get_python_scripts_dir() -> str:
    """Get the Python scripts directory."""
    global _PYTHON_SCRIPTS_DIR
    if _PYTHON_SCRIPTS_DIR is None:
        try:
            import unreal
            root = str(unreal.Paths.project_root())
            _PYTHON_SCRIPTS_DIR = str(Path(root) / "Python")
        except Exception:
            _PYTHON_SCRIPTS_DIR = str(CHIMERA_PYTHON_DIR)
    return _PYTHON_SCRIPTS_DIR


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, creating it if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _get_env_override(key, default):
    """Get an overridden config value from CHIMERA_<key> environment variable."""
    env_key = f"CHIMERA_{key.upper()}"
    env_value = os.environ.get(env_key)
    if env_value is not None:
        try:
            return int(env_value)
        except ValueError:
            pass
        try:
            return float(env_value)
        except ValueError:
            pass
        if env_value.lower() in ('true', 'false'):
            return env_value.lower() == 'true'
        return env_value
    return default


# ============================================================================
# GAME CONFIGURATION CLASS
# Central configuration for all procedural generation parameters.
# Access engine paths via ue_* properties, project paths via chimera_* properties.
# ============================================================================

class GameConfiguration:
    """Central configuration for the Chimera game project."""

    # --- UE Engine executables and tools ---
    
    @staticmethod
    def ue_editor():
        """Return path to Unreal Editor executable."""
        return UE_EDITOR_EXE
    
    @staticmethod
    def ue_game():
        """Return path to standard Unreal Game executable."""
        return UE_GAME_EXE
    
    @staticmethod
    def ue_shipping():
        """Return path to Unreal Shipping (release) game executable."""
        return UE_GAME_SHIPPING_EXE
    
    @staticmethod
    def ubt():
        """UnrealBuildTool (DotNET AutomationTool version)."""
        return UBT_DOTNET_AUTOMATIONTOOL
    
    @staticmethod
    def shader_compile_worker():
        """Return path to ShaderCompileWorker executable."""
        return SHADER_COMPILE_WORKER_EXE
    
    @staticmethod
    def unreal_pak():
        """Return path to UnrealPak executable for pak file management."""
        return UNREAL_PAK_EXE
    
    @staticmethod
    def unreal_lightmass():
        """Return path to UnrealLightmass executable for lighting builds."""
        return UNREAL_LIGHTMASS_EXE
    
    # --- Chimera project paths ---
    
    @staticmethod
    def chimera_root():
        """Return the Chimera project root directory path."""
        return CHIMERA_PROJECT_ROOT
    
    @staticmethod
    def uproject_file():
        """Return the path to the Chimera.uproject file."""
        return CHIMERA_UPROJECT_FILE
    
    @staticmethod
    def source_dir():
        """Return the C++ source directory path."""
        return get_source_dir()
    
    @staticmethod
    def content_dir():
        """Return the Content directory path."""
        return get_content_dir()
    
    @staticmethod
    def python_scripts_dir():
        """Return the Python scripts directory path."""
        return get_python_scripts_dir()
    
    @staticmethod
    def saved_logs_dir():
        """Return the Saved/Logs directory path."""
        return CHIMERA_SAVED_LOGS_DIR
    
    @staticmethod
    def screenshots_dir():
        """Return the Saved/Screenshots directory path."""
        return CHIMERA_SAVED_SCREENSHOTS_DIR
    
    # --- C++ file accessors ---
    
    @staticmethod
    def cpp_file(name):
        """Get the full path of a C++ source file by name."""
        all_cpp = {**CHIMERA_CPP_FILES, **CHIMERA_OFFROAD_FILES, 
                   **CHIMERA_SPORTSCAR_FILES, **CHIMERA_TIMETRIAL_FILES,
                   **CHIMERA_OFFROAD_MODE_FILES}
        return all_cpp.get(name)
    
    @staticmethod
    def cpp_files():
        """Get dict of all known C++ files."""
        return {**CHIMERA_CPP_FILES, **CHIMERA_OFFROAD_FILES, 
                **CHIMERA_SPORTSCAR_FILES, **CHIMERA_TIMETRIAL_FILES,
                **CHIMERA_OFFROAD_MODE_FILES}

    # --- Python script accessors ---
    
    @staticmethod
    def python_script(name):
        """Get the full path of a Python script by name."""
        return CHIMERA_PYTHON_SCRIPTS.get(name)
    
    @staticmethod
    def python_scripts():
        """Get dict of all known Python scripts."""
        return CHIMERA_PYTHON_SCRIPTS

    # --- Procedural generation settings ---
    
    GENERATION_SEED = _get_env_override("generation_seed", 42)
    ENABLE_DEBUG_LOGGING = _get_env_override("enable_debug_logging", True)

    VEHICLE_TEMPLATES = {
        "offroad": "/Game/Vehicles/OffroadCar/BP_OffroadCar.BP_OffroadCar_C",
        "sports": "/Game/Vehicles/SportsCar/BP_SportsCar.BP_SportsCar_C",
        "flight": "/Game/FlightVehicle/BP_FlightVehicle.BP_FlightVehicle_C"
    }

    VARIANT_DIRECTORIES = [
        "/Game/Variant_OffRoad",
        "/Game/Variant_TimeTrial",
        "/Game/Variant_Flight"
    ]
    
    GENERATION_MODULES = {
        "vehicles": True,
        "levels": True,
        "terrain": False,
        "materials": True
    }
    
    VEHICLE_PLACEMENT = {
        "offroad_location": (0, 0, 0),
        "sports_location": (300, 0, 0),
        "spacing_between_vehicles": 300
    }
    
    LEVEL_GENERATION = {
        "base_level_name": "VehicleBasic",
        "procedural_levels_dir": "/Game/ProceduralGenerated/Levels",
        "variant_levels": ["OffRoadLevel", "TimeTrialLevel"],
        "flight_test_level_name": "FlightTestLevel"
    }

    FLIGHT_TEST_ENVIRONMENT = {
        "level_size_x": 10000.0,
        "level_size_y": 10000.0,
        "level_size_z": 5000.0,
        "launch_pad_location": (0, 0, 0),
        "launch_pad_radius": 200.0,
        "ground_reference_height": -50.0,
        "lighting_type": "sky_and_lights",
        "screenshot_light_intensity": 1.5,
        "grid_reference_enabled": True,
        "grid_spacing": 500.0
    }

    FLIGHT_VEHICLE = {
        "thrust_power": 1500.0,
        "rotation_speed": 90.0,
        "angular_damping_when_idle": 5.0,
        "max_velocity": 500.0,
        "velocity_damping": 0.98,
        "enable_flight_mode_key": "F",
        "thrust_input_key": "W",
        "reverse_thrust_key": "S",
        "strafe_left_key": "A",
        "strafe_right_key": "D",
        "strafe_up_key": "Z",
        "strafe_down_key": "E",
        "pitch_up_key": "MouseY_Neg",
        "pitch_down_key": "MouseY_Pos",
        "yaw_left_key": "MouseX_Neg",
        "yaw_right_key": "MouseX_Pos"
    }

    # LM Studio configuration (module-level LM_STUDIO_MODEL is used by all imports)
    LM_STUDIO_TEMPERATURE = _get_env_override("lm_studio_temperature", 0.3)
    LM_STUDIO_MAX_TOKENS = _get_env_override("lm_studio_max_tokens", 1024)


@dataclass
class GameConfigModel:
    """Class-based configuration model with type validation and default values."""
    
    generation_seed: int = 42
    enable_debug_logging: bool = True
    lm_studio_temperature: float = 0.3
    lm_studio_max_tokens: int = 1024
    
    vehicle_templates: Dict[str, str] = field(default_factory=lambda: {
        "offroad": "/Game/Vehicles/OffroadCar/BP_OffroadCar.BP_OffroadCar_C",
        "sports": "/Game/Vehicles/SportsCar/BP_SportsCar.BP_SportsCar_C",
        "flight": "/Game/FlightVehicle/BP_FlightVehicle.BP_FlightVehicle_C"
    })
    
    variant_directories: List[str] = field(default_factory=lambda: [
        "/Game/Variant_OffRoad",
        "/Game/Variant_TimeTrial",
        "/Game/Variant_Flight"
    ])
    
    generation_modules: Dict[str, bool] = field(default_factory=lambda: {
        "vehicles": True,
        "levels": True,
        "terrain": False,
        "materials": True
    })
    
    vehicle_placement: Dict[str, Any] = field(default_factory=lambda: {
        "offroad_location": (0, 0, 0),
        "sports_location": (300, 0, 0),
        "spacing_between_vehicles": 300
    })
    
    level_generation: Dict[str, Any] = field(default_factory=lambda: {
        "base_level_name": "VehicleBasic",
        "procedural_levels_dir": "/Game/ProceduralGenerated/Levels",
        "variant_levels": ["OffRoadLevel", "TimeTrialLevel"],
        "flight_test_level_name": "FlightTestLevel"
    })

    flight_test_environment: Dict[str, Any] = field(default_factory=lambda: {
        "level_size_x": 10000.0,
        "level_size_y": 10000.0,
        "level_size_z": 5000.0,
        "launch_pad_location": (0, 0, 0),
        "launch_pad_radius": 200.0,
        "ground_reference_height": -50.0,
        "lighting_type": "sky_and_lights",
        "screenshot_light_intensity": 1.5,
        "grid_reference_enabled": True,
        "grid_spacing": 500.0
    })
    
    flight_vehicle: Dict[str, Any] = field(default_factory=lambda: {
        "thrust_power": 1500.0,
        "rotation_speed": 90.0,
        "angular_damping_when_idle": 5.0,
        "max_velocity": 500.0,
        "velocity_damping": 0.98,
        "enable_flight_mode_key": "F",
        "thrust_input_key": "W",
        "reverse_thrust_key": "S",
        "strafe_left_key": "A",
        "strafe_right_key": "D",
        "strafe_up_key": "Z",
        "strafe_down_key": "E",
        "pitch_up_key": "MouseY_Neg",
        "pitch_down_key": "MouseY_Pos",
        "yaw_left_key": "MouseX_Neg",
        "yaw_right_key": "MouseX_Pos"
    })

    def validate(self) -> bool:
        """Validate configuration values with type and range checks."""
        if not isinstance(self.generation_seed, int) or self.generation_seed < 0:
            raise ValueError("generation_seed must be a non-negative integer")
        if not isinstance(self.enable_debug_logging, bool):
            raise ValueError("enable_debug_logging must be a boolean")
        if not isinstance(self.lm_studio_temperature, float) or not (0.0 <= self.lm_studio_temperature <= 1.0):
            raise ValueError("lm_studio_temperature must be a float between 0.0 and 1.0")
        if not isinstance(self.lm_studio_max_tokens, int) or self.lm_studio_max_tokens <= 0:
            raise ValueError("lm_studio_max_tokens must be a positive integer")
        
        for key, val in self.vehicle_templates.items():
            if not isinstance(key, str) or not isinstance(val, str):
                raise ValueError("vehicle_templates keys and values must be strings")
                
        for d in self.variant_directories:
            if not isinstance(d, str):
                raise ValueError("variant_directories must contain only strings")
                
        for key, val in self.generation_modules.items():
            if not isinstance(key, str) or not isinstance(val, bool):
                raise ValueError("generation_modules keys must be strings and values must be booleans")
                
        return True


# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================


def validate_paths_exist(paths):
    """Validate that all provided paths exist."""
    missing = [p for p in paths if not Path(p).exists()]
    if missing:
        log("WARNING", f"Paths do not exist: {', '.join(str(p) for p in missing)}")
    return len(missing) == 0


def validate_ue_project_path(project_path: Path) -> bool:
    """Validate that the UE project path exists."""
    if not project_path.exists():
        log("ERROR", f"UE project path does not exist: {project_path}")
        return False
    return True


def validate_uproject_file(uproject_path: Path) -> bool:
    """Validate that the .uproject file exists and is valid."""
    if not uproject_path.exists():
        log("ERROR", f".uproject file does not exist: {uproject_path}")
        return False
    
    if not uproject_path.name.endswith('.uproject'):
        log("ERROR", f"Invalid file extension, expected .uproproject: {uproject_path}")
        return False
            
    try:
        with open(uproject_path, 'r') as f:
            content = f.read()
            if '"ProjectVersion"' not in content and '"EngineAssociation"' not in content:
                log("WARNING", f".uproproject file may be invalid or empty: {uproject_path}")
    except Exception as e:
        log("ERROR", f"Failed to read .uproject file {uproject_path}: {e}")
        return False
        
    return True


def validate_content_directory_structure(content_dir: Path) -> bool:
    """Validate that the Content directory has the expected UE structure."""
    if not content_dir.exists():
        log("ERROR", f"Content directory does not exist: {content_dir}")
        return False
    
    required_subdirs = ['Game', 'Materials', 'Blueprints', 'Textures', 'Levels']
    missing_dirs = [d for d in required_subdirs if not (content_dir / d).exists()]
    
    if missing_dirs:
        log("WARNING", f"Content directory missing expected subdirectories: {', '.join(missing_dirs)}")
        return False
        
    return True


def validate_directory_permissions(dir_paths: List[Path], require_read: bool = True, require_write: bool = True) -> bool:
    """Validate that directories have required read/write permissions before file operations."""
    valid = True
    for dir_path in dir_paths:
        p = Path(dir_path)
        if not p.exists():
            log("WARNING", f"Directory does not exist for permission validation: {p}")
            valid = False
            continue
        
        try:
            if require_read and not p.is_dir():
                log("ERROR", f"Path is not a directory for read access: {p}")
                valid = False
                continue
            
            if require_read:
                try:
                    _ = list(p.iterdir())
                except PermissionError:
                    log("ERROR", f"Directory lacks read permission: {p}")
                    valid = False
                except Exception:
                    pass
            
            if require_write:
                test_file = p / '.chimera_perm_test'
                try:
                    test_file.touch(exist_ok=True)
                    test_file.unlink()
                except PermissionError:
                    log("ERROR", f"Directory lacks write permission: {p}")
                    valid = False
                except Exception:
                    pass
                    
        except Exception as e:
            log("ERROR", f"Failed to validate permissions for directory {p}: {e}")
            valid = False
            
    return valid


def is_valid_lm_studio_url(url):
    """Validate LM Studio URL format."""
    if not re.match(r'^https?://(?:localhost|127\.0\.0\.1|\d{1,3}(?:\.\d{1,3}){3}):\d+$', url):
        log("ERROR", f"Invalid LM Studio URL format: {url}. Expected format: http://localhost:PORT or http://127.0.0.1:PORT or http://<IP>:PORT")
        return False
    return True


def validate_ue_version_compatibility(ue_version: str) -> bool:
    """Validate that the configured UE version matches supported versions.
    
    Args:
        ue_version: Unreal Engine version string (e.g., '5.8', 'UE_5.8')
        
    Returns:
        bool: True if valid, raises ValueError otherwise
    """
    match = re.search(r'UE_[\d\.]+|(\d+\.\d+)', str(ue_version))
    if not match:
        log("ERROR", f"Could not extract UE version from: {ue_version}")
        raise ValueError(f"Invalid UE version format: {ue_version}")
    
    version_str = match.group(1) if match.group(1) else match.group(0).replace('UE_', '')
    version_parts = version_str.split('.')[:2]
    normalized_version = f"{version_parts[0]}.{version_parts[1]}"
    
    if normalized_version not in SUPPORTED_UE_VERSIONS:
        log("ERROR", f"Unsupported UE version: {normalized_version}. Supported versions: {', '.join(SUPPORTED_UE_VERSIONS)}")
        raise ValueError(f"Unsupported UE version: {normalized_version}")
        
    return True


def check_platform_specific_features(platform: str, ue_version: str) -> List[str]:
    """Check for platform-specific feature availability before using configuration features.
    
    Args:
        platform: Target platform (e.g., 'windows', 'linux')
        ue_version: Unreal Engine version string
        
    Returns:
        List of available features for the given platform and UE version
    """
    platform = platform.lower()
    match = re.search(r'UE_[\d\.]+|(\d+\.\d+)', str(ue_version))
    if not match:
        log("WARNING", f"Could not extract UE version for feature check: {ue_version}")
        return []
    
    version_str = match.group(1) if match.group(1) else match.group(0).replace('UE_', '')
    version_parts = version_str.split('.')[:2]
    normalized_version = f"{version_parts[0]}.{version_parts[1]}"
    
    if platform not in PLATFORM_FEATURES:
        log("WARNING", f"Unknown platform: {platform}. Returning default features.")
        return []
        
    features = PLATFORM_FEATURES[platform].get(normalized_version, [])
    if normalized_version > max(PLATFORM_FEATURES[platform].keys()):
        features = PLATFORM_FEATURES[platform][max(PLATFORM_FEATURES[platform].keys())]
        
    log("INFO", f"Platform {platform} with UE {normalized_version} supports features: {features}")
    return features


def validate_configured_features(features: List[str], platform: str, ue_version: str) -> bool:
    """Validate that configured features match supported UE engine versions and platform capabilities.
    
    Args:
        features: List of feature names to validate (e.g., ['shader_compile_worker', 'uba_agent'])
        platform: Target platform (e.g., 'windows', 'linux')
        ue_version: Unreal Engine version string (e.g., 'UE_5.8' or '5.8')
        
    Returns:
        bool: True if all features are supported, raises ValueError otherwise
    """
    validate_ue_version_compatibility(ue_version)
    
    platform = platform.lower()
    match = re.search(r'UE_[\d\.]+|(\d+\.\d+)', str(ue_version))
    if not match:
        log("ERROR", f"Could not extract UE version for feature validation: {ue_version}")
        raise ValueError(f"Invalid UE version format: {ue_version}")
    
    version_str = match.group(1) if match.group(1) else match.group(0).replace('UE_', '')
    version_parts = version_str.split('.')[:2]
    normalized_version = f"{version_parts[0]}.{version_parts[1]}"
    
    if platform not in PLATFORM_FEATURES:
        log("ERROR", f"Unknown platform: {platform}. Supported platforms: {', '.join(PLATFORM_FEATURES.keys())}")
        raise ValueError(f"Unsupported platform: {platform}")
        
    features_for_version = PLATFORM_FEATURES[platform].get(normalized_version)
    if not features_for_version:
        available_versions = sorted([v for v in PLATFORM_FEATURES[platform].keys()], key=lambda x: [int(i) for i in x.split('.')])
        latest_version = available_versions[-1] if available_versions else None
        if latest_version:
            features_for_version = PLATFORM_FEATURES[platform][latest_version]
        else:
            log("ERROR", f"No features found for platform {platform} and UE version {normalized_version}")
            raise ValueError(f"No features defined for platform {platform} with UE version {normalized_version}")
            
    unsupported_features = [f for f in features if f not in features_for_version]
    if unsupported_features:
        log("ERROR", f"Features not supported for platform {platform} with UE {normalized_version}: {', '.join(unsupported_features)}")
        log("INFO", f"Available features: {', '.join(features_for_version)}")
        raise ValueError(f"Unsupported features for platform {platform} and UE version {normalized_version}: {', '.join(unsupported_features)}")
        
    return True


def is_endpoint_reachable(url, timeout=3):
    try:
        clean_url = url.replace('http://', '').replace('https://', '')
        if '/' in clean_url:
            clean_url = clean_url.split('/')[0]
        
        if ':' in clean_url:
            host, port_str = clean_url.split(':', 1)
        else:
            host = clean_url
            port_str = '80' if url.startswith('http://') else '443'
            
        port = int(port_str)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return True
        else:
            log("WARNING", f"Endpoint not reachable via TCP check: {url} (result code: {result})")
            return False
            
    except Exception as e:
        log("ERROR", f"Failed to validate network connectivity for endpoint {url}: {e}")
        return False


def validate_config():
    """Validate configuration paths, LM Studio URL format, and network connectivity before use."""
    project_paths = [
        CHIMERA_PROJECT_ROOT,
        CHIMERA_CONTENT_DIR,
        CHIMERA_PYTHON_DIR,
        CHIMERA_UPROJECT_FILE
    ]
    
    if not validate_ue_project_path(CHIMERA_PROJECT_ROOT):
        raise ValueError(f"Invalid UE project path: {CHIMERA_PROJECT_ROOT}")
        
    if not validate_uproject_file(CHIMERA_UPROJECT_FILE):
        raise ValueError(f"Invalid .uproject file: {CHIMERA_UPROJECT_FILE}")
        
    if not validate_content_directory_structure(CHIMERA_CONTENT_DIR):
        log("WARNING", f"Content directory structure validation failed for: {CHIMERA_CONTENT_DIR}")
        
    project_paths_exist = validate_paths_exist(project_paths)
    if not project_paths_exist:
        log("WARNING", f"Some project paths do not exist: {', '.join(str(p) for p in project_paths)}")
    
    if not is_valid_lm_studio_url(LM_STUDIO_BASE_URL):
        raise ValueError(f"Invalid LM Studio URL: {LM_STUDIO_BASE_URL}")
        
    if not is_endpoint_reachable(LM_STUDIO_BASE_URL):
        log("WARNING", f"LM Studio endpoint may be unreachable: {LM_STUDIO_BASE_URL}. Ensure LM Studio is running.")


# ============================================================================
# CONFIGURATION VERSIONING AND CHANGE HISTORY
# ============================================================================

CONFIG_VERSION = "1.0.0"

_CONFIG_CHANGE_HISTORY = []


def record_config_change(change_type: str, key_path: str, old_value=None, new_value=None, timestamp=None) -> None:
    """Record a configuration change to the change history log."""
    import datetime
    if timestamp is None:
        timestamp = datetime.datetime.now().isoformat()
    
    _CONFIG_CHANGE_HISTORY.append({
        "version": CONFIG_VERSION,
        "timestamp": timestamp,
        "change_type": change_type,
        "key_path": key_path,
        "old_value": old_value,
        "new_value": new_value
    })


def get_change_history() -> list:
    """Return the configuration change history log."""
    return list(_CONFIG_CHANGE_HISTORY)


def clear_change_history() -> None:
    """Clear the configuration change history log."""
    _CONFIG_CHANGE_HISTORY.clear()


def save_change_history_to_json(history_path: Path) -> None:
    """Save the configuration change history to a JSON file."""
    try:
        with open(history_path, 'w') as f:
            json.dump(_CONFIG_CHANGE_HISTORY, f, indent=4)
    except (IOError, OSError) as e:
        log("ERROR", f"Failed to save change history to JSON file {history_path}: {e}")
    except Exception as e:
        log("ERROR", f"Unexpected error saving change history to JSON file {history_path}: {e}")


def load_change_history_from_json(history_path: Path) -> list:
    """Load configuration change history from a JSON file."""
    try:
        with open(history_path, 'r') as f:
            return json.load(f)
    except (IOError, OSError) as e:
        log("ERROR", f"Failed to read change history from JSON file {history_path}: {e}")
        raise
    except json.JSONDecodeError as e:
        log("ERROR", f"Invalid JSON in change history file {history_path}: {e}")
        raise


# ============================================================================
# CONFIGURATION MIGRATION UTILITIES
# ============================================================================


def migrate_config_to_current_version(config_data: dict, target_version: str = None) -> dict:
    """Migrate configuration data to the current version format.
    
    Args:
        config_data: Configuration dictionary to migrate.
        target_version: Target version string (defaults to CONFIG_VERSION).
        
    Returns:
        Migrated configuration dictionary.
    """
    if target_version is None:
        target_version = CONFIG_VERSION
        
    # Ensure version field exists
    if "CONFIG_VERSION" not in config_data and "version" not in config_data:
        config_data["CONFIG_VERSION"] = "0.1.0"
        
    current_version_str = str(config_data.get("CONFIG_VERSION", config_data.get("version", "0.1.0")))
    
    # Parse version to compare
    try:
        current_parts = [int(x) for x in current_version_str.split('.')[:3]] if isinstance(current_version_str, str) else [0, 1, 0]
    except Exception:
        current_parts = [0, 1, 0]
        
    target_parts = [int(x) for x in target_version.split('.')[:3]] if isinstance(target_version, str) else [1, 0, 0]
    
    # Migrate from v0.x to v1.0.0
    if current_parts[0] < 1:
        config_data = _migrate_v0_to_v1(config_data.copy())
        
    # Ensure current version is set
    config_data["CONFIG_VERSION"] = target_version
    
    return config_data


def _migrate_v0_to_v1(config_data: dict) -> dict:
    """Migrate configuration from v0.x format to v1.0.0 format."""
    migrated = {}
    
    # Map deprecated or lowercase field names to current uppercase keys
    field_mappings = {
        "generation_seed": "GENERATION_SEED",
        "enable_debug_logging": "ENABLE_DEBUG_LOGGING",
        "vehicle_templates": "VEHICLE_TEMPLATES",
        "variant_directories": "VARIANT_DIRECTORIES",
        "generation_modules": "GENERATION_MODULES",
        "vehicle_placement": "VEHICLE_PLACEMENT",
        "level_generation": "LEVEL_GENERATION",
        "flight_vehicle": "FLIGHT_VEHICLE",
        "lm_studio_temperature": "LM_STUDIO_TEMPERATURE",
        "lm_studio_max_tokens": "LM_STUDIO_MAX_TOKENS",
        "seed": "GENERATION_SEED",
        "debug_logging": "ENABLE_DEBUG_LOGGING",
        "lm_temp": "LM_STUDIO_TEMPERATURE",
        "lm_max_tokens": "LM_STUDIO_MAX_TOKENS"
    }
    
    for key, value in config_data.items():
        mapped_key = field_mappings.get(key, key)
        migrated[mapped_key] = value
        
    # Ensure all required top-level keys exist with default values
    defaults = {
        "GENERATION_SEED": 42,
        "ENABLE_DEBUG_LOGGING": True,
        "VEHICLE_TEMPLATES": dict(GameConfiguration.VEHICLE_TEMPLATES),
        "VARIANT_DIRECTORIES": list(GameConfiguration.VARIANT_DIRECTORIES),
        "GENERATION_MODULES": dict(GameConfiguration.GENERATION_MODULES),
        "VEHICLE_PLACEMENT": dict(GameConfiguration.VEHICLE_PLACEMENT),
        "LEVEL_GENERATION": dict(GameConfiguration.LEVEL_GENERATION),
        "FLIGHT_VEHICLE": dict(GameConfiguration.FLIGHT_VEHICLE),
        "LM_STUDIO_TEMPERATURE": 0.3,
        "LM_STUDIO_MAX_TOKENS": 1024,
    }
    
    for key, default_val in defaults.items():
        if key not in migrated:
            migrated[key] = default_val
            
    return migrated


def handle_deprecated_fields(config_data: dict) -> dict:
    """Handle and transform deprecated configuration fields to current format.
    
    Args:
        config_data: Configuration dictionary with potentially deprecated fields.
        
    Returns:
        Configuration dictionary with updated field names.
    """
    return migrate_config_to_current_version(config_data, CONFIG_VERSION)


def transform_legacy_structure(config_dict: dict) -> dict:
    """Transform legacy configuration structure to current nested format.
    
    Args:
        config_dict: Legacy configuration dictionary.
        
    Returns:
        Transformed configuration dictionary with current structure.
    """
    migrated = {}
    
    # Map flat legacy keys to nested structure
    legacy_to_nested = {
        "GENERATION_SEED": ("generation_seed", int),
        "ENABLE_DEBUG_LOGGING": ("enable_debug_logging", bool),
        "LM_STUDIO_TEMPERATURE": ("lm_studio_temperature", float),
        "LM_STUDIO_MAX_TOKENS": ("lm_studio_max_tokens", int)
    }
    
    for key, value in config_dict.items():
        if key in legacy_to_nested:
            nested_key, val_type = legacy_to_nested[key]
            migrated[nested_key] = val_type(value) if isinstance(value, (str, int, float)) and not isinstance(value, bool) else value
        elif key in ("VEHICLE_TEMPLATES", "VARIANT_DIRECTORIES", "GENERATION_MODULES", 
                     "VEHICLE_PLACEMENT", "LEVEL_GENERATION", "FLIGHT_VEHICLE"):
            migrated[key.lower()] = dict(value) if isinstance(value, (dict, list)) else value
        else:
            migrated[key] = value
            
    return migrated


# ============================================================================
# CONFIGURATION JSON LOAD/SAVE UTILITIES
# ============================================================================


def save_config_to_json(config_path: Path) -> None:
    """Save GameConfiguration settings to a JSON file."""
    config_data = {
        "GENERATION_SEED": GameConfiguration.GENERATION_SEED,
        "ENABLE_DEBUG_LOGGING": GameConfiguration.ENABLE_DEBUG_LOGGING,
        "VEHICLE_TEMPLATES": GameConfiguration.VEHICLE_TEMPLATES,
        "VARIANT_DIRECTORIES": GameConfiguration.VARIANT_DIRECTORIES,
        "GENERATION_MODULES": GameConfiguration.GENERATION_MODULES,
        "VEHICLE_PLACEMENT": GameConfiguration.VEHICLE_PLACEMENT,
        "LEVEL_GENERATION": GameConfiguration.LEVEL_GENERATION,
        "FLIGHT_VEHICLE": GameConfiguration.FLIGHT_VEHICLE,
        "LM_STUDIO_TEMPERATURE": GameConfiguration.LM_STUDIO_TEMPERATURE,
        "LM_STUDIO_MAX_TOKENS": GameConfiguration.LM_STUDIO_MAX_TOKENS,
    }
    try:
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)
    except (IOError, OSError) as e:
        log("ERROR", f"Failed to save config to JSON file {config_path}: {e}")
    except Exception as e:
        log("ERROR", f"Unexpected error saving config to JSON file {config_path}: {e}")


def load_config_from_json(config_path: Path) -> dict:
    """Load configuration from a JSON file and return as dict."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (IOError, OSError) as e:
        log("ERROR", f"Failed to read config from JSON file {config_path}: {e}")
        raise
    except json.JSONDecodeError as e:
        log("ERROR", f"Invalid JSON in config file {config_path}: {e}")
        raise


def _validate_type_match(base_value, override_value) -> None:
    """Validate that override value is compatible with base value type."""
    if isinstance(override_value, dict) and not isinstance(base_value, dict):
        raise TypeError(f"Type mismatch for config key: cannot merge dict into non-dict value {base_value}")
    if isinstance(base_value, dict) and not isinstance(override_value, dict):
        raise TypeError(f"Type mismatch for config key: cannot replace dict with non-dict value {override_value}")
    if type(base_value) is not type(override_value) and not (isinstance(override_value, type(base_value)) or isinstance(base_value, type(override_value))):
        # Allow int/float mixing, but reject other incompatible types
        base_is_numeric = isinstance(base_value, (int, float)) and not isinstance(base_value, bool)
        override_is_numeric = isinstance(override_value, (int, float)) and not isinstance(override_value, bool)
        if not (base_is_numeric and override_is_numeric):
            raise TypeError(f"Type mismatch for config value: base type {type(base_value).__name__} vs override type {type(override_value).__name__}")


def merge_config_dicts(base_dict: dict, override_dict: dict) -> dict:
    """Merge multiple config dictionaries, with override_dict values taking precedence.
    
    Args:
        base_dict: Base configuration dictionary.
        override_dict: Override configuration dictionary.
        
    Returns:
        Merged configuration dictionary.
    """
    merged = copy.deepcopy(base_dict)
    for key, value in override_dict.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = merge_config_dicts(merged[key], value)
        else:
            _validate_type_match(merged.get(key), value)
            merged[key] = value
    
    # Explicitly trigger garbage collection for large merged configs
    gc.collect()
    
    return merged


def update_config_value(config_dict: dict, key_path: str, value) -> None:
    """Update a specific config value dynamically using dotted path notation.
    
    Args:
        config_dict: Configuration dictionary to update.
        key_path: Dotted path to the value (e.g., 'LEVEL_GENERATION.base_level_name').
        value: New value to set.
    """
    keys = key_path.split('.')
    current = config_dict
    for i, key in enumerate(keys[:-1]):
        if key not in current or not isinstance(current[key], dict):
            raise KeyError(f"Invalid config path: {key_path}")
        current = current[key]
    
    if keys[-1] not in current:
        raise KeyError(f"Invalid config path: {key_path}")
    
    _validate_type_match(current[keys[-1]], value)
    current[keys[-1]] = value


def get_config_diffs(base_dict: dict, new_dict: dict, prefix: str = "") -> dict:
    """Compare two config dictionaries and return only the differences or changed values.
    
    Args:
        base_dict: Base configuration dictionary.
        new_dict: New configuration dictionary to compare against.
        prefix: Internal prefix for dotted path notation.
        
    Returns:
        Dictionary of differences with dotted path keys and (old_value, new_value) tuples.
    """
    diffs = {}
    
    all_keys = set(base_dict.keys()) | set(new_dict.keys())
    
    for key in all_keys:
        full_key = f"{prefix}.{key}" if prefix else key
        
        if key not in base_dict:
            diffs[full_key] = (None, new_dict[key])
        elif key not in new_dict:
            diffs[full_key] = (base_dict[key], None)
        elif isinstance(base_dict[key], dict) and isinstance(new_dict[key], dict):
            nested_diffs = get_config_diffs(base_dict[key], new_dict[key], full_key)
            if nested_diffs:
                diffs.update(nested_diffs)
        elif base_dict[key] != new_dict[key]:
            diffs[full_key] = (base_dict[key], new_dict[key])
            
    return diffs


def get_changed_values(base_dict: dict, new_dict: dict) -> dict:
    """Compare two config dictionaries and return only the changed values with dotted path keys.
    
    Args:
        base_dict: Base configuration dictionary.
        new_dict: New configuration dictionary to compare against.
        
    Returns:
        Dictionary of changed values with dotted path keys.
    """
    diffs = get_config_diffs(base_dict, new_dict)
    return {key: new_val for key, (old_val, new_val) in diffs.items() if new_val is not None}


def validate_config_against_schema(config_dict: dict, schema_path: Path) -> bool:
    """Validate configuration dictionary against a JSON schema file.
    
    Args:
        config_dict: Configuration dictionary to validate.
        schema_path: Path to the JSON schema file.
        
    Returns:
        True if validation passes, False otherwise.
    """
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        errors = []
        if "required" in schema:
            for req_field in schema["required"]:
                if req_field not in config_dict:
                    errors.append(f"Missing required field: {req_field}")
        
        if "properties" in schema:
            for prop, prop_schema in schema["properties"].items():
                if prop in config_dict:
                    expected_type = prop_schema.get("type")
                    value = config_dict[prop]
                    if expected_type == "object" and not isinstance(value, dict):
                        errors.append(f"Field {prop} should be an object/dict, got {type(value).__name__}")
                    elif expected_type == "array" and not isinstance(value, list):
                        errors.append(f"Field {prop} should be an array/list, got {type(value).__name__}")
                    elif expected_type == "string" and not isinstance(value, str):
                        errors.append(f"Field {prop} should be a string, got {type(value).__name__}")
                    elif expected_type in ("integer", "int") and (not isinstance(value, int) or isinstance(value, bool)):
                        errors.append(f"Field {prop} should be an integer, got {type(value).__name__}")
                    elif expected_type == "number" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
                        errors.append(f"Field {prop} should be a number, got {type(value).__name__}")
                    elif expected_type == "boolean" and not isinstance(value, bool):
                        errors.append(f"Field {prop} should be a boolean, got {type(value).__name__}")
        
        if errors:
            log("ERROR", f"Schema validation failed for config against {schema_path}: {'; '.join(errors)}")
            return False
        
        log("INFO", f"Configuration validated successfully against schema: {schema_path}")
        return True
    except json.JSONDecodeError as e:
        log("ERROR", f"Invalid JSON in schema file {schema_path}: {e}")
        return False
    except FileNotFoundError:
        log("ERROR", f"Schema file not found: {schema_path}")
        return False
    except Exception as e:
        log("ERROR", f"Error validating config against schema {schema_path}: {e}")
        return False


def validate_game_config_model_against_schema(config_model: GameConfigModel, schema_path: Path) -> bool:
    """Validate GameConfigModel instance against a JSON schema file.
    
    Args:
        config_model: GameConfigModel instance to validate.
        schema_path: Path to the JSON schema file.
        
    Returns:
        True if validation passes, False otherwise.
    """
    config_dict = {
        "generation_seed": config_model.generation_seed,
        "enable_debug_logging": config_model.enable_debug_logging,
        "lm_studio_temperature": config_model.lm_studio_temperature,
        "lm_studio_max_tokens": config_model.lm_studio_max_tokens,
        "vehicle_templates": config_model.vehicle_templates,
        "variant_directories": config_model.variant_directories,
        "generation_modules": config_model.generation_modules,
        "vehicle_placement": config_model.vehicle_placement,
        "level_generation": config_model.level_generation,
        "flight_vehicle": config_model.flight_vehicle,
    }
    return validate_config_against_schema(config_dict, schema_path)


SNAPSHOTS_DIR = CHIMERA_SAVED_DIR / "Snapshots"


def get_snapshot_path(snapshot_name: str) -> Path:
    """Generate the file path for a configuration snapshot."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    return SNAPSHOTS_DIR / f"{snapshot_name}_snapshot.json"


def create_config_snapshot(snapshot_name: str, config_dict: dict = None) -> Path:
    """Create a configuration snapshot and save to JSON file.
    
    Args:
        snapshot_name: Name for the snapshot (will be appended with _snapshot.json).
        config_dict: Configuration dictionary to snapshot (defaults to current GameConfiguration).
        
    Returns:
        Path to the saved snapshot file.
    """
    import datetime
    if config_dict is None:
        config_dict = {
            "GENERATION_SEED": GameConfiguration.GENERATION_SEED,
            "ENABLE_DEBUG_LOGGING": GameConfiguration.ENABLE_DEBUG_LOGGING,
            "VEHICLE_TEMPLATES": dict(GameConfiguration.VEHICLE_TEMPLATES),
            "VARIANT_DIRECTORIES": list(GameConfiguration.VARIANT_DIRECTORIES),
            "GENERATION_MODULES": dict(GameConfiguration.GENERATION_MODULES),
            "VEHICLE_PLACEMENT": dict(GameConfiguration.VEHICLE_PLACEMENT),
            "LEVEL_GENERATION": dict(GameConfiguration.LEVEL_GENERATION),
            "FLIGHT_VEHICLE": dict(GameConfiguration.FLIGHT_VEHICLE),
            "LM_STUDIO_TEMPERATURE": GameConfiguration.LM_STUDIO_TEMPERATURE,
            "LM_STUDIO_MAX_TOKENS": GameConfiguration.LM_STUDIO_MAX_TOKENS,
        }
    
    snapshot_path = get_snapshot_path(snapshot_name)
    snapshot_data = {
        "snapshot_name": snapshot_name,
        "timestamp": datetime.datetime.now().isoformat(),
        "config_version": CONFIG_VERSION,
        "config": config_dict
    }
    
    try:
        with open(snapshot_path, 'w') as f:
            json.dump(snapshot_data, f, indent=4)
        log("INFO", f"Configuration snapshot created: {snapshot_path}")
    except (IOError, OSError) as e:
        log("ERROR", f"Failed to create config snapshot {snapshot_path}: {e}")
        raise
    return snapshot_path


def restore_config_snapshot(snapshot_path: Path | str) -> dict:
    """Restore configuration from a saved snapshot file.
    
    Args:
        snapshot_path: Path to the snapshot JSON file.
        
    Returns:
        Restored configuration dictionary.
    """
    snapshot_path = Path(snapshot_path)
    if not snapshot_path.exists():
        log("ERROR", f"Snapshot file does not exist: {snapshot_path}")
        raise FileNotFoundError(f"Snapshot file not found: {snapshot_path}")
    
    try:
        with open(snapshot_path, 'r') as f:
            snapshot_data = json.load(f)
        
        config_dict = snapshot_data.get("config", {})
        log("INFO", f"Configuration restored from snapshot: {snapshot_path.name}")
        return config_dict
    except (IOError, OSError) as e:
        log("ERROR", f"Failed to read snapshot file {snapshot_path}: {e}")
        raise
    except json.JSONDecodeError as e:
        log("ERROR", f"Invalid JSON in snapshot file {snapshot_path}: {e}")
        raise


def list_config_snapshots(snapshot_dir: Path = None) -> list[dict]:
    """List available configuration snapshots in the snapshots directory.
    
    Args:
        snapshot_dir: Directory containing snapshots (defaults to SNAPSHOTS_DIR).
        
    Returns:
        List of snapshot metadata dictionaries.
    """
    if snapshot_dir is None:
        snapshot_dir = SNAPSHOTS_DIR
    
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshots = []
    
    for snap_file in snapshot_dir.glob("*_snapshot.json"):
        try:
            with open(snap_file, 'r') as f:
                data = json.load(f)
                snapshots.append({
                    "name": data.get("snapshot_name", snap_file.stem),
                    "path": str(snap_file),
                    "timestamp": data.get("timestamp"),
                    "config_version": data.get("config_version")
                })
        except Exception:
            pass
    
    return sorted(snapshots, key=lambda x: x.get("timestamp", ""), reverse=True)


def validate_game_config_model_constraints(config_model: GameConfigModel) -> bool:
    if not isinstance(config_model.generation_seed, int) or isinstance(config_model.generation_seed, bool):
        raise ValueError("generation_seed must be an integer")
    if config_model.generation_seed < 0:
        raise ValueError("generation_seed must be a non-negative integer")
        
    if not isinstance(config_model.enable_debug_logging, bool):
        raise ValueError("enable_debug_logging must be a boolean")
        
    if not isinstance(config_model.lm_studio_temperature, float) or isinstance(config_model.lm_studio_temperature, bool):
        raise ValueError("lm_studio_temperature must be a float")
    if not (0.0 <= config_model.lm_studio_temperature <= 1.0):
        raise ValueError("lm_studio_temperature must be between 0.0 and 1.0")
        
    if not isinstance(config_model.lm_studio_max_tokens, int) or isinstance(config_model.lm_studio_max_tokens, bool):
        raise ValueError("lm_studio_max_tokens must be an integer")
    if config_model.lm_studio_max_tokens <= 0:
        raise ValueError("lm_studio_max_tokens must be a positive integer")
        
    if not isinstance(config_model.vehicle_templates, dict):
        raise ValueError("vehicle_templates must be a dictionary")
    
    return True


class DependencyValidationError(Exception):
    """Exception raised when dependency validation fails."""
    pass


def validate_dependencies() -> bool:
    """Validate that required packages like psutil, cryptography, pyyaml are available and meet minimum version requirements."""
    required_packages = {
        "psutil": (5, 9, 0),
        "cryptography": (41, 0, 0),
        "pyyaml": (6, 0, 0)
    }
    
    missing_packages = []
    outdated_packages = []
    
    for pkg_name, min_version in required_packages.items():
        try:
            import importlib.metadata as metadata
            installed_version_str = metadata.version(pkg_name.replace("-", "_"))
        except Exception:
            try:
                import pkg_resources
                installed_version_str = pkg_resources.get_distribution(pkg_name.replace("-", "_")).version
            except Exception:
                missing_packages.append(pkg_name)
                continue
        
        try:
            installed_parts = [int(x) for x in installed_version_str.split('.')[:3]]
            while len(installed_parts) < 3:
                installed_parts.append(0)
        except Exception:
            outdated_packages.append(f"{pkg_name} (version: {installed_version_str})")
            continue
            
        if tuple(installed_parts) < min_version:
            outdated_packages.append(f"{pkg_name} (installed: {installed_version_str}, required: >={'.'.join(map(str, min_version))})")
    
    if missing_packages:
        log("ERROR", f"Missing required packages: {', '.join(missing_packages)}")
        raise DependencyValidationError(f"Missing required packages: {', '.join(missing_packages)}")
    
    if outdated_packages:
        log("ERROR", f"Outdated required packages: {', '.join(outdated_packages)}")
        raise DependencyValidationError(f"Outdated required packages: {', '.join(outdated_packages)}")
    
    return True


def get_system_hardware_info():
    """Get system hardware info including RAM and CPU cores using psutil or platform detection."""
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count() or 1
    except Exception:
        import os
        ram_gb = 0.0
        cpu_cores = os.cpu_count() or 1
    
    try:
        import platform
        gpu_available = platform.system() in ['Windows', 'Linux']
    except Exception:
        gpu_available = False
        
    return {
        "ram_gb": ram_gb,
        "cpu_cores": cpu_cores,
        "gpu_available": gpu_available
    }


def validate_hardware_constraints(config_model: GameConfigModel) -> bool:
    """Validate configuration settings are appropriate for current system RAM and CPU cores."""
    hw_info = get_system_hardware_info()
    
    if hw_info["ram_gb"] > 0 and hw_info["ram_gb"] < 4.0:
        log("WARNING", f"Low system RAM: {hw_info['ram_gb']:.1f}GB. Minimum 4GB recommended for procedural generation.")
        
    if hw_info["cpu_cores"] > 0 and hw_info["cpu_cores"] < 2:
        log("WARNING", f"Low CPU core count: {hw_info['cpu_cores']}. Recommended minimum is 2 cores.")
        
    return True


def generate_config_schema_with_examples() -> dict:
    """Generate a JSON schema with example values for GameConfigModel configuration."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "GameConfiguration",
        "description": "Schema for Chimera procedural game generator configuration with examples.",
        "type": "object",
        "properties": {
            "generation_seed": {
                "type": "integer",
                "description": "Seed value for procedural generation.",
                "example": 42
            },
            "enable_debug_logging": {
                "type": "boolean",
                "description": "Enable debug logging.",
                "example": True
            },
            "lm_studio_temperature": {
                "type": "number",
                "description": "LM Studio temperature parameter.",
                "minimum": 0.0,
                "maximum": 1.0,
                "example": 0.3
            },
            "lm_studio_max_tokens": {
                "type": "integer",
                "description": "Maximum tokens for LM Studio responses.",
                "example": 1024,
                "minimum": 1
            },
            "vehicle_templates": {
                "type": "object",
                "description": "Vehicle template paths.",
                "example": {
                    "offroad": "/Game/Vehicles/OffroadCar/BP_OffroadCar.BP_OffroadCar_C",
                    "sports": "/Game/Vehicles/SportsCar/BP_SportsCar.BP_SportsCar_C",
                    "flight": "/Game/FlightVehicle/BP_FlightVehicle.BP_FlightVehicle_C"
                }
            },
            "variant_directories": {
                "type": "array",
                "description": "Variant directory paths.",
                "items": {"type": "string"},
                "example": [
                    "/Game/Variant_OffRoad",
                    "/Game/Variant_TimeTrial",
                    "/Game/Variant_Flight"
                ]
            },
            "generation_modules": {
                "type": "object",
                "description": "Enabled generation modules.",
                "example": {
                    "vehicles": True,
                    "levels": True,
                    "terrain": False,
                    "materials": True
                }
            },
            "vehicle_placement": {
                "type": "object",
                "description": "Vehicle placement settings.",
                "example": {
                    "offroad_location": [0, 0, 0],
                    "sports_location": [300, 0, 0],
                    "spacing_between_vehicles": 300
                }
            },
            "level_generation": {
                "type": "object",
                "description": "Level generation settings.",
                "example": {
                    "base_level_name": "VehicleBasic",
                    "procedural_levels_dir": "/Game/ProceduralGenerated/Levels",
                    "variant_levels": ["OffRoadLevel", "TimeTrialLevel"]
                }
            },
            "flight_vehicle": {
                "type": "object",
                "description": "Flight vehicle configuration.",
                "example": {
                    "thrust_power": 150.0,
                    "rotation_speed": 90.0,
                    "angular_damping_when_idle": 5.0,
                    "max_velocity": 500.0,
                    "velocity_damping": 0.98,
                    "enable_flight_mode_key": "F",
                    "thrust_input_key": "W",
                    "reverse_thrust_key": "S",
                    "strafe_left_key": "A",
                    "strafe_right_key": "D",
                    "strafe_up_key": "Q",
                    "strafe_down_key": "E",
                    "pitch_up_key": "MouseY_Neg",
                    "pitch_down_key": "MouseY_Pos",
                    "yaw_left_key": "MouseX_Neg",
                    "yaw_right_key": "MouseX_Pos"
                }
            }
        },
        "required": [
            "generation_seed",
            "enable_debug_logging",
            "lm_studio_temperature",
            "lm_studio_max_tokens",
            "vehicle_templates",
            "variant_directories",
            "generation_modules",
            "vehicle_placement",
            "level_generation",
            "flight_vehicle"
        ]
    }


def generate_config_schema_json() -> str:
    """Generate JSON string representation of the configuration schema with examples."""
    import json
    return json.dumps(generate_config_schema_with_examples(), indent=2)


def validate_game_configuration_against_openapi_schema(config_data: dict | GameConfigModel, openapi_spec_path: Path | str) -> bool:
    """Validate configuration data against an OpenAPI JSON schema or external API specification document.
    
    Args:
        config_data: Configuration dictionary or GameConfigModel instance to validate.
        openapi_spec_path: Path to the OpenAPI JSON/YAML schema file or external API spec document.
        
    Returns:
        True if validation passes, False otherwise.
    """
    if isinstance(config_data, GameConfigModel):
        config_dict = {
            "generation_seed": config_data.generation_seed,
            "enable_debug_logging": config_data.enable_debug_logging,
            "lm_studio_temperature": config_data.lm_studio_temperature,
            "lm_studio_max_tokens": config_data.lm_studio_max_tokens,
            "vehicle_templates": config_data.vehicle_templates,
            "variant_directories": config_data.variant_directories,
            "generation_modules": config_data.generation_modules,
            "vehicle_placement": config_data.vehicle_placement,
            "level_generation": config_data.level_generation,
            "flight_vehicle": config_data.flight_vehicle,
        }
    else:
        config_dict = config_data
        
    openapi_spec_path = Path(openapi_spec_path)
    
    try:
        with open(openapi_spec_path, 'r') as f:
            spec_content = f.read()
            
        import json
        if spec_content.strip().startswith('{'):
            spec = json.loads(spec_content)
        else:
            try:
                import yaml
                spec = yaml.safe_load(spec_content)
            except ImportError:
                log("ERROR", "YAML parsing not available. Please install pyyaml for OpenAPI YAML specs.")
                return False
                
        schema = None
        if 'components' in spec and 'schemas' in spec['components']:
            schemas = spec['components']['schemas']
            if 'GameConfiguration' in schemas:
                schema = schemas['GameConfiguration']
            elif schemas:
                schema = list(schemas.values())[0]
        elif 'definitions' in spec:
            definitions = spec['definitions']
            if 'GameConfiguration' in definitions:
                schema = definitions['GameConfiguration']
            elif definitions:
                schema = list(definitions.values())[0]
        else:
            schema = spec.get('schema') or spec.get('$schema')
            
        if not schema:
            log("WARNING", f"No schema found in OpenAPI specification: {openapi_spec_path}")
            return False
            
        errors = []
        
        def validate_field(field_name, value, field_schema):
            if 'type' in field_schema:
                expected_type = field_schema['type']
                if expected_type == 'object' and not isinstance(value, dict):
                    errors.append(f"Field {field_name} should be an object/dict, got {type(value).__name__}")
                elif expected_type == 'array' and not isinstance(value, list):
                    errors.append(f"Field {field_name} should be an array/list, got {type(value).__name__}")
                elif expected_type == 'string':
                    if not isinstance(value, str):
                        errors.append(f"Field {field_name} should be a string, got {type(value).__name__}")
                    else:
                        fmt = field_schema.get('format')
                        if fmt:
                            if fmt == 'date' and not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                                errors.append(f"Field {field_name} with format 'date' has invalid value: {value}")
                            elif fmt == 'date-time' and not re.match(r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', value):
                                errors.append(f"Field {field_name} with format 'date-time' has invalid value: {value}")
                            elif fmt == 'uuid' and not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', value, re.I):
                                errors.append(f"Field {field_name} with format 'uuid' has invalid value: {value}")
                            elif fmt == 'email' and not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
                                errors.append(f"Field {field_name} with format 'email' has invalid value: {value}")
                            elif fmt == 'uri' and not re.match(r'^https?://', value):
                                errors.append(f"Field {field_name} with format 'uri' has invalid value: {value})")
                                
                        if 'pattern' in field_schema:
                            if not re.search(field_schema['pattern'], value):
                                errors.append(f"Field {field_name} does not match pattern: {field_schema['pattern']}")
                                
                        if 'minLength' in field_schema and len(value) < field_schema['minLength']:
                            errors.append(f"Field {field_name} has length {len(value)}, minimum is {field_schema['minLength']}")
                        if 'maxLength' in field_schema and len(value) > field_schema['maxLength']:
                            errors.append(f"Field {field_name} has length {len(value)}, maximum is {field_schema['maxLength']}")
                            
                elif expected_type in ('integer', 'int'):
                    if not isinstance(value, int) or isinstance(value, bool):
                        errors.append(f"Field {field_name} should be an integer, got {type(value).__name__}")
                    else:
                        if 'minimum' in field_schema and value < field_schema['minimum']:
                            errors.append(f"Field {field_name} value {value} is less than minimum {field_schema['minimum']}")
                        if 'maximum' in field_schema and value > field_schema['maximum']:
                            errors.append(f"Field {field_name} value {value} is greater than maximum {field_schema['maximum']}")
                            
                elif expected_type == 'number':
                    if not isinstance(value, (int, float)) or isinstance(value, bool):
                        errors.append(f"Field {field_name} should be a number, got {type(value).__name__}")
                    else:
                        if 'minimum' in field_schema and value < field_schema['minimum']:
                            errors.append(f"Field {field_name} value {value} is less than minimum {field_schema['minimum']}")
                        if 'maximum' in field_schema and value > field_schema['maximum']:
                            errors.append(f"Field {field_name} value {value} is greater than maximum {field_schema['maximum']}")
                            
                elif expected_type == 'boolean':
                    if not isinstance(value, bool):
                        errors.append(f"Field {field_name} should be a boolean, got {type(value).__name__}")
                        
            if 'enum' in field_schema:
                if value not in field_schema['enum']:
                    errors.append(f"Field {field_name} value {value} is not in allowed values: {field_schema['enum']}")
                    
            if isinstance(value, dict) and 'properties' in field_schema:
                for prop_name, prop_schema in field_schema['properties'].items():
                    if prop_name in value:
                        validate_field(f"{field_name}.{prop_name}", value[prop_name], prop_schema)
                        
        if 'properties' in schema:
            for prop_name, prop_schema in schema['properties'].items():
                if prop_name in config_dict:
                    validate_field(prop_name, config_dict[prop_name], prop_schema)
                    
        if errors:
            log("ERROR", f"OpenAPI schema validation failed for config against {openapi_spec_path}: {'; '.join(errors)}")
            return False
            
        log("INFO", f"Configuration validated successfully against OpenAPI schema: {openapi_spec_path}")
        return True
        
    except json.JSONDecodeError as e:
        log("ERROR", f"Invalid JSON in OpenAPI spec file {openapi_spec_path}: {e}")
        return False
    except FileNotFoundError:
        log("ERROR", f"OpenAPI spec file not found: {openapi_spec_path}")
        return False
    except Exception as e:
        log("ERROR", f"Error validating config against OpenAPI schema {openapi_spec_path}: {e}")
        return False


def validate_schema_draft_compatibility(schema_path: Path, supported_drafts: List[str] = None) -> bool:
    """Validate that a JSON schema file is compatible with specific draft versions.
    
    Args:
        schema_path: Path to the JSON schema file.
        supported_drafts: List of supported JSON Schema draft identifiers (e.g., 'draft-07', 'draft-2019-09', 'draft-2020-12').
        
    Returns:
        True if schema is compatible with one of the supported drafts, False otherwise.
    """
    if supported_drafts is None:
        supported_drafts = ["draft-07", "draft-2019-09", "draft-2020-12"]
    
    draft_urls = {
        "draft-07": "https://json-schema.org/draft-07/schema#",
        "draft-2019-09": "https://json-schema.org/draft/2019-09/schema",
        "draft-2020-12": "https://json-schema.org/draft/2020-12/schema"
    }
    
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        schema_url = schema.get("$schema")
        if not schema_url:
            log("INFO", f"Schema {schema_path} has no $schema property, assuming draft-07 compatibility")
            return True
        
        for draft in supported_drafts:
            expected_url = draft_urls.get(draft)
            if schema_url == expected_url or draft in schema_url or schema_url.startswith(f"https://json-schema.org/draft-{draft.split('-')[1]}"):
                log("INFO", f"Schema {schema_path} is compatible with JSON Schema draft: {draft}")
                return True
        
        log("WARNING", f"Schema {schema_path} has $schema '{schema_url}' which may not be in supported drafts: {supported_drafts}")
        return False
        
    except json.JSONDecodeError as e:
        log("ERROR", f"Invalid JSON in schema file {schema_path}: {e}")
        return False
    except FileNotFoundError:
        log("ERROR", f"Schema file not found: {schema_path}")
        return False
    except Exception as e:
        log("ERROR", f"Error validating schema draft compatibility for {schema_path}: {e}")
        return False


def validate_schema_draft_and_config(schema_path: Path, config_dict: dict, supported_drafts: List[str] = None) -> bool:
    """Validate configuration dictionary against a JSON schema file and check draft compatibility.
    
    Args:
        schema_path: Path to the JSON schema file.
        config_dict: Configuration dictionary to validate.
        supported_drafts: List of supported JSON Schema draft identifiers.
        
    Returns:
        True if both draft compatibility and validation pass, False otherwise.
    """
    if not validate_schema_draft_compatibility(schema_path, supported_drafts):
        return False
    return validate_config_against_schema(config_dict, schema_path)


def extract_openapi_extensions(obj, path=""):
    """Extract OpenAPI x-* extension properties from a schema or specification object."""
    extensions_found = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            if key.startswith('x-') or key.startswith('X-'):
                extensions_found[current_path] = value
            elif isinstance(value, (dict, list)):
                nested_exts = extract_openapi_extensions(value, current_path)
                if nested_exts:
                    extensions_found.update(nested_exts)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            nested_exts = extract_openapi_extensions(item, f"{path}[{i}]")
            if nested_exts:
                extensions_found.update(nested_exts)
    return extensions_found


def validate_openapi_extensions(schema_path: Path, config_dict: dict) -> bool:
    """Validate configuration against OpenAPI specification extensions like x-* properties in JSON schema documents.
    
    Args:
        schema_path: Path to the JSON schema or OpenAPI specification file.
        config_dict: Configuration dictionary to validate.
        
    Returns:
        True if validation passes or no extensions are found, False otherwise.
    """
    try:
        with open(schema_path, 'r') as f:
            spec_content = f.read()
            
        import json
        if spec_content.strip().startswith('{'):
            schema = json.loads(spec_content)
        else:
            try:
                import yaml
                schema = yaml.safe_load(spec_content)
            except ImportError:
                log("ERROR", "YAML parsing not available. Please install pyyaml for OpenAPI YAML specs.")
                return False
                
        extensions = extract_openapi_extensions(schema)
        
        if not extensions:
            log("INFO", f"No OpenAPI x-* extensions found in schema: {schema_path}")
            return True
            
        log("INFO", f"Found OpenAPI extensions in schema {schema_path}: {list(extensions.keys())}")
        
        def validate_extension_markers(ext_schema, config_data):
            validation_errors = []
            for ext_key, ext_value in ext_schema.items():
                if isinstance(ext_value, dict):
                    if 'validate_against' in ext_value:
                        target_field = ext_value.get('validate_against')
                        if target_field and target_field not in config_data:
                            validation_errors.append(f"Extension {ext_key} requires field '{target_field}' which is missing from config")
                    if 'properties' in ext_value and isinstance(ext_value.get('properties'), dict):
                        for prop_name, prop_schema in ext_value['properties'].items():
                            if isinstance(prop_schema, dict) and 'enum' in prop_schema:
                                pass
            return validation_errors
            
        ext_errors = validate_extension_markers(extensions, config_dict)
        if ext_errors:
            log("ERROR", f"Extension validation failed for schema {schema_path}: {'; '.join(ext_errors)}")
            return False
            
        log("INFO", f"Configuration validated successfully against OpenAPI extensions in schema: {schema_path}")
        return True
        
    except json.JSONDecodeError as e:
        log("ERROR", f"Invalid JSON in schema file {schema_path}: {e}")
        return False
    except FileNotFoundError:
        log("ERROR", f"Schema file not found: {schema_path}")
        return False
    except Exception as e:
        log("ERROR", f"Error validating config against OpenAPI extensions {schema_path}: {e}")
        return False


def auto_backup_config(config_dict: dict = None) -> Path:
    """Automatically create a configuration backup with timestamp before changes."""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_name = f"auto_backup_{timestamp}"
    
    if config_dict is None:
        config_dict = {
            "GENERATION_SEED": GameConfiguration.GENERATION_SEED,
            "ENABLE_DEBUG_LOGGING": GameConfiguration.ENABLE_DEBUG_LOGGING,
            "VEHICLE_TEMPLATES": dict(GameConfiguration.VEHICLE_TEMPLATES),
            "VARIANT_DIRECTORIES": list(GameConfiguration.VARIANT_DIRECTORIES),
            "GENERATION_MODULES": dict(GameConfiguration.GENERATION_MODULES),
            "VEHICLE_PLACEMENT": dict(GameConfiguration.VEHICLE_PLACEMENT),
            "LEVEL_GENERATION": dict(GameConfiguration.LEVEL_GENERATION),
            "FLIGHT_VEHICLE": dict(GameConfiguration.FLIGHT_VEHICLE),
            "LM_STUDIO_TEMPERATURE": GameConfiguration.LM_STUDIO_TEMPERATURE,
            "LM_STUDIO_MAX_TOKENS": GameConfiguration.LM_STUDIO_MAX_TOKENS,
        }
    
    backup_path = SNAPSHOTS_DIR / f"{snapshot_name}_backup.json"
    backup_data = {
        "backup_type": "auto_backup",
        "timestamp": datetime.datetime.now().isoformat(),
        "config_version": CONFIG_VERSION,
        "config": config_dict
    }
    
    try:
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=4)
        log("INFO", f"Configuration auto-backup created: {backup_path}")
    except (IOError, OSError) as e:
        log("ERROR", f"Failed to create config auto-backup {backup_path}: {e}")
        raise
    return backup_path


def restore_latest_backup() -> dict:
    """Restore configuration from the latest backup snapshot."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    backup_files = sorted([f for f in SNAPSHOTS_DIR.glob("*_backup.json")], key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not backup_files:
        log("ERROR", "No backup files found to restore from.")
        raise FileNotFoundError("No backup files found.")
    
    latest_backup = backup_files[0]
    return restore_config_snapshot(latest_backup)
    for key, val in config_model.vehicle_templates.items():
        if not isinstance(key, str) or not isinstance(val, str):
            raise ValueError("vehicle_templates keys and values must be strings")
            
    if not isinstance(config_model.variant_directories, list):
        raise ValueError("variant_directories must be a list")
    for d in config_model.variant_directories:
        if not isinstance(d, str):
            raise ValueError("variant_directories must contain only strings")
            
    if not isinstance(config_model.generation_modules, dict):
        raise ValueError("generation_modules must be a dictionary")
    for key, val in config_model.generation_modules.items():
        if not isinstance(key, str) or not isinstance(val, bool):
            raise ValueError("generation_modules keys must be strings and values must be booleans")
            
    if not isinstance(config_model.vehicle_placement, dict):
        raise ValueError("vehicle_placement must be a dictionary")
    if "offroad_location" in config_model.vehicle_placement:
        loc = config_model.vehicle_placement["offroad_location"]
        if not (isinstance(loc, (list, tuple)) and len(loc) == 3):
            raise ValueError("offroad_location must be a list or tuple of 3 numbers")
        for coord in loc:
            if not isinstance(coord, (int, float)) or isinstance(coord, bool):
                raise ValueError("offroad_location coordinates must be numbers")
    if "sports_location" in config_model.vehicle_placement:
        loc = config_model.vehicle_placement["sports_location"]
        if not (isinstance(loc, (list, tuple)) and len(loc) == 3):
            raise ValueError("sports_location must be a list or tuple of 3 numbers")
        for coord in loc:
            if not isinstance(coord, (int, float)) or isinstance(coord, bool):
                raise ValueError("sports_location coordinates must be numbers")
    if "spacing_between_vehicles" in config_model.vehicle_placement:
        spacing = config_model.vehicle_placement["spacing_between_vehicles"]
        if not isinstance(spacing, int) or isinstance(spacing, bool):
            raise ValueError("spacing_between_vehicles must be an integer")
        if spacing < 0:
            raise ValueError("spacing_between_vehicles must be non-negative")
            
    if not isinstance(config_model.level_generation, dict):
        raise ValueError("level_generation must be a dictionary")
    if "base_level_name" in config_model.level_generation and not isinstance(config_model.level_generation["base_level_name"], str):
        raise ValueError("base_level_name must be a string")
    if "procedural_levels_dir" in config_model.level_generation and not isinstance(config_model.level_generation["procedural_levels_dir"], str):
        raise ValueError("procedural_levels_dir must be a string")
    if "variant_levels" in config_model.level_generation:
        vl = config_model.level_generation["variant_levels"]
        if not isinstance(vl, list):
            raise ValueError("variant_levels must be a list")
        for v in vl:
            if not isinstance(v, str):
                raise ValueError("variant_levels must contain only strings")
                
    if not isinstance(config_model.flight_vehicle, dict):
        raise ValueError("flight_vehicle must be a dictionary")
        
    flight_numeric_keys = [
        "thrust_power", "rotation_speed", "angular_damping_when_idle",
        "max_velocity", "velocity_damping"
    ]
    for key in flight_numeric_keys:
        if key in config_model.flight_vehicle:
            val = config_model.flight_vehicle[key]
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise ValueError(f"{key} must be a number")
                
    flight_string_keys = [
        "enable_flight_mode_key", "thrust_input_key", "reverse_thrust_key",
        "strafe_left_key", "strafe_right_key", "strafe_up_key", "strafe_down_key",
        "pitch_up_key", "pitch_down_key", "yaw_left_key", "yaw_right_key"
    ]
    for key in flight_string_keys:
        if key in config_model.flight_vehicle and not isinstance(config_model.flight_vehicle[key], str):
            raise ValueError(f"{key} must be a string")
            
    return True


def reload_config_from_env() -> None:
    """Reload configuration values from environment variables without restarting the application."""
    GameConfiguration.GENERATION_SEED = _get_env_override("generation_seed", 42)
    GameConfiguration.ENABLE_DEBUG_LOGGING = _get_env_override("enable_debug_logging", True)
    GameConfiguration.LM_STUDIO_TEMPERATURE = _get_env_override("lm_studio_temperature", 0.3)
    GameConfiguration.LM_STUDIO_MAX_TOKENS = _get_env_override("lm_studio_max_tokens", 1024)


def reload_config_from_disk(config_path: Path) -> None:
    """Reload configuration values from a JSON config file without restarting the application."""
    config_data = load_config_from_json(config_path)
    
    if "GENERATION_SEED" in config_data:
        GameConfiguration.GENERATION_SEED = config_data["GENERATION_SEED"]
    if "ENABLE_DEBUG_LOGGING" in config_data:
        GameConfiguration.ENABLE_DEBUG_LOGGING = config_data["ENABLE_DEBUG_LOGGING"]
    if "VEHICLE_TEMPLATES" in config_data:
        GameConfiguration.VEHICLE_TEMPLATES = config_data["VEHICLE_TEMPLATES"]
    if "VARIANT_DIRECTORIES" in config_data:
        GameConfiguration.VARIANT_DIRECTORIES = config_data["VARIANT_DIRECTORIES"]
    if "GENERATION_MODULES" in config_data:
        GameConfiguration.GENERATION_MODULES = config_data["GENERATION_MODULES"]
    if "VEHICLE_PLACEMENT" in config_data:
        GameConfiguration.VEHICLE_PLACEMENT = config_data["VEHICLE_PLACEMENT"]
    if "LEVEL_GENERATION" in config_data:
        GameConfiguration.LEVEL_GENERATION = config_data["LEVEL_GENERATION"]
    if "FLIGHT_VEHICLE" in config_data:
        GameConfiguration.FLIGHT_VEHICLE = config_data["FLIGHT_VEHICLE"]
    if "LM_STUDIO_TEMPERATURE" in config_data:
        GameConfiguration.LM_STUDIO_TEMPERATURE = config_data["LM_STUDIO_TEMPERATURE"]
    if "LM_STUDIO_MAX_TOKENS" in config_data:
        GameConfiguration.LM_STUDIO_MAX_TOKENS = config_data["LM_STUDIO_MAX_TOKENS"]


def get_config_as_json() -> str:
    """Return GameConfiguration settings as a JSON string."""
    config_data = {
        "GENERATION_SEED": GameConfiguration.GENERATION_SEED,
        "ENABLE_DEBUG_LOGGING": GameConfiguration.ENABLE_DEBUG_LOGGING,
        "VEHICLE_TEMPLATES": GameConfiguration.VEHICLE_TEMPLATES,
        "VARIANT_DIRECTORIES": GameConfiguration.VARIANT_DIRECTORIES,
        "GENERATION_MODULES": GameConfiguration.GENERATION_MODULES,
        "VEHICLE_PLACEMENT": GameConfiguration.VEHICLE_PLACEMENT,
        "LEVEL_GENERATION": GameConfiguration.LEVEL_GENERATION,
        "FLIGHT_VEHICLE": GameConfiguration.FLIGHT_VEHICLE,
        "LM_STUDIO_TEMPERATURE": GameConfiguration.LM_STUDIO_TEMPERATURE,
        "LM_STUDIO_MAX_TOKENS": GameConfiguration.LM_STUDIO_MAX_TOKENS,
    }
    return json.dumps(config_data, indent=4)


def _to_yaml_value(val, indent=0):
    """Convert a value to a YAML string representation."""
    prefix = "  " * indent
    if isinstance(val, dict):
        lines = []
        for k, v in val.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.append(_to_yaml_value(v, indent + 1))
            else:
                v_str = _to_yaml_value(v)
                lines.append(f"{prefix}{k}: {v_str}")
        return "\n".join(lines) + ("\n" if lines else "")
    elif isinstance(val, list):
        lines = []
        for item in val:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.append(_to_yaml_value(item, indent + 1))
            else:
                item_str = _to_yaml_value(item)
                lines.append(f"{prefix}- {item_str}")
        return "\n".join(lines) + ("\n" if lines else "")
    elif isinstance(val, bool):
        return f"{str(val).lower()}"
    elif val is None:
        return "null"
    else:
        return str(val)


def _config_to_yaml(d):
    """Convert config dict to YAML string."""
    lines = []
    for key, val in d.items():
        if isinstance(val, (dict, list)):
            lines.append(f"{key}:")
            yaml_val = _to_yaml_value(val, 1)
            lines.append(yaml_val)
        else:
            val_str = _to_yaml_value(val)
            lines.append(f"{key}: {val_str}")
    return "\n".join(lines) + "\n"


def get_config_as_yaml() -> str:
    """Return GameConfiguration settings as a YAML string."""
    config_data = {
        "GENERATION_SEED": GameConfiguration.GENERATION_SEED,
        "ENABLE_DEBUG_LOGGING": GameConfiguration.ENABLE_DEBUG_LOGGING,
        "VEHICLE_TEMPLATES": GameConfiguration.VEHICLE_TEMPLATES,
        "VARIANT_DIRECTORIES": GameConfiguration.VARIANT_DIRECTORIES,
        "GENERATION_MODULES": GameConfiguration.GENERATION_MODULES,
        "VEHICLE_PLACEMENT": GameConfiguration.VEHICLE_PLACEMENT,
        "LEVEL_GENERATION": GameConfiguration.LEVEL_GENERATION,
        "FLIGHT_VEHICLE": GameConfiguration.FLIGHT_VEHICLE,
        "LM_STUDIO_TEMPERATURE": GameConfiguration.LM_STUDIO_TEMPERATURE,
        "LM_STUDIO_MAX_TOKENS": GameConfiguration.LM_STUDIO_MAX_TOKENS,
    }
    return _config_to_yaml(config_data)


def export_config_to_yaml(config_path: Path) -> None:
    """Save GameConfiguration settings to a YAML file."""
    yaml_str = get_config_as_yaml()
    try:
        with open(config_path, 'w') as f:
            f.write(yaml_str)
    except (IOError, OSError) as e:
        log("ERROR", f"Failed to save config to YAML file {config_path}: {e}")
    except Exception as e:
        log("ERROR", f"Unexpected error saving config to YAML file {config_path}: {e}")


def get_config_as_env_strings() -> str:
    """Return GameConfiguration settings as environment variable format strings."""
    lines = []
    lines.append(f'CHIMERA_GENERATION_SEED={GameConfiguration.GENERATION_SEED}')
    lines.append(f'CHIMERA_ENABLE_DEBUG_LOGGING={"true" if GameConfiguration.ENABLE_DEBUG_LOGGING else "false"}')
    lines.append(f'CHIMERA_LM_STUDIO_TEMPERATURE={GameConfiguration.LM_STUDIO_TEMPERATURE}')
    lines.append(f'CHIMERA_LM_STUDIO_MAX_TOKENS={GameConfiguration.LM_STUDIO_MAX_TOKENS}')
    
    lines.append(f'CHIMERA_VEHICLE_TEMPLATES={json.dumps(GameConfiguration.VEHICLE_TEMPLATES)}')
    lines.append(f'CHIMERA_VARIANT_DIRECTORIES={json.dumps(GameConfiguration.VARIANT_DIRECTORIES)}')
    lines.append(f'CHIMERA_GENERATION_MODULES={json.dumps(GameConfiguration.GENERATION_MODULES)}')
    lines.append(f'CHIMERA_VEHICLE_PLACEMENT={json.dumps(GameConfiguration.VEHICLE_PLACEMENT)}')
    lines.append(f'CHIMERA_LEVEL_GENERATION={json.dumps(GameConfiguration.LEVEL_GENERATION)}')
    lines.append(f'CHIMERA_FLIGHT_VEHICLE={json.dumps(GameConfiguration.FLIGHT_VEHICLE)}')
    
    return "\n".join(lines) + "\n"


def export_config_to_env(env_path: Path) -> None:
    """Export GameConfiguration settings to a .env file format.

    Args:
        env_path: Path to the output .env file.
    """
    env_str = get_config_as_env_strings()
    try:
        with open(env_path, 'w') as f:
            f.write(env_str)
    except (IOError, OSError) as e:
        log("ERROR", f"Failed to export config to .env file {env_path}: {e}")
    except Exception as e:
        log("ERROR", f"Unexpected error exporting config to .env file {env_path}: {e}")


def validate_environment_constraints(config_model=None):
    """Validate configuration is suitable for current OS, UE version, or hardware constraints based on detected environment."""
    import platform
    
    system = platform.system()
    if system != "Windows":
        log("WARNING", f"UE 5.8 is primarily supported on Windows, current OS: {system}")
    
    if not UE_ENGINE_ROOT.exists():
        log("WARNING", f"UE Engine root does not exist: {UE_ENGINE_ROOT}")
    elif not (UE_ENGINE_BINARIES_WIN64 / "UnrealEditor.exe").exists():
        log("WARNING", f"UE Editor executable not found at: {UE_EDITOR_EXE}")
        
    try:
        usage = shutil.disk_usage(CHIMERA_PROJECT_ROOT)
        free_space_gb = usage.free / (1024**3)
        if free_space_gb < 10:
            log("WARNING", f"Low disk space available: {free_space_gb:.2f} GB for UE project")
    except Exception:
        pass
        
    return True


def validate_ue_project_memory_and_disk_constraints(config_model=None):
    """Validate that configured project settings do not exceed reasonable memory limits or UE project size constraints based on system RAM and disk space availability."""
    hw_info = get_system_hardware_info()
    
    min_ram_gb_for_ue = 8.0
    recommended_ram_gb_for_ue = 16.0
    
    if hw_info["ram_gb"] > 0:
        if hw_info["ram_gb"] < min_ram_gb_for_ue:
            log("WARNING", f"System RAM ({hw_info['ram_gb']:.1f}GB) is below minimum recommended for UE 5.8 projects ({min_ram_gb_for_ue}GB).")
        elif hw_info["ram_gb"] < recommended_ram_gb_for_ue:
            log("INFO", f"System RAM ({hw_info['ram_gb']:.1f}GB) is below recommended for UE 5.8 projects ({recommended_ram_gb_for_ue}GB). Consider increasing memory for optimal performance.")
    
    try:
        usage = shutil.disk_usage(CHIMERA_PROJECT_ROOT)
        free_space_gb = usage.free / (1024**3)
        
        min_disk_gb_for_ue_project = 20.0
        
        if free_space_gb < min_disk_gb_for_ue_project:
            log("WARNING", f"Low disk space available: {free_space_gb:.2f} GB. Minimum {min_disk_gb_for_ue_project} GB recommended for UE project size and intermediate files.")
        elif free_space_gb < 50.0:
            log("INFO", f"Disk space available: {free_space_gb:.2f} GB. Consider ensuring at least 50GB free for UE project builds and shader compilation.")
    except Exception:
        pass
        
    return True


def validate_storage_quota_limits(dir_paths=None, min_free_space_gb=10.0):
    """Validate that configured project directories, content folders, or snapshot locations do not exceed file system quota limits or storage capacity constraints."""
    if dir_paths is None:
        dir_paths = [CHIMERA_PROJECT_ROOT, CHIMERA_CONTENT_DIR, SNAPSHOTS_DIR]
    
    valid = True
    for dir_path in dir_paths:
        p = Path(dir_path)
        if not p.exists():
            try:
                p.mkdir(parents=True, exist_ok=True)
            except Exception:
                log("WARNING", f"Cannot create directory for quota validation: {p}")
                continue
        
        try:
            usage = shutil.disk_usage(p)
            free_space_gb = usage.free / (1024**3)
            
            if free_space_gb < min_free_space_gb:
                log("WARNING", f"Storage capacity constraint warning for {p}: {free_space_gb:.2f} GB free space available. Minimum {min_free_space_gb} GB recommended.")
                valid = False
                
        except Exception as e:
            log("ERROR", f"Failed to validate storage quota limits for directory {p}: {e}")
            valid = False
            
    return valid
