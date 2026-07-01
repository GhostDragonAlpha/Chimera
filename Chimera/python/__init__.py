# Chimera Procedural Game Generator Package
# Exports key entry points and configuration for external callers.

from .config import (
    CHIMERA_PROJECT_ROOT,
    CHIMERA_ROOT,
    LM_STUDIO_BASE_URL,
    LM_STUDIO_MODEL,
    GameConfiguration,
)

from .procedural_game_generator import (
    generate_all,
    run_startup_workflow,
    sync_cpp_project_state,
    get_expected_cpp_files,
    get_all_cpp_files,
)

from .cpp_generator import (
    ensure_directories,
    generate_all_cpp_components,
    generate_flight_control_component,
)

from .unreal_api_operations import (
    generate_levels_and_actors,
    create_procedural_level,
)

from .lmstudio_client import (
    send_to_lmstudio,
    display_response,
    get_available_models,
    get_vision_capable_models,
    auto_select_model,
)

from .play_test import FlightPlayTest, run_playtest

from .runtime_screenshot_playtest import RuntimeScreenshotPlayTest, run_runtime_screenshot_playtest

from .screenshot_lmstudio_workflow import (
    LMStudioClient,
    capture_viewport_screenshot,
    run_screenshot_analysis_workflow,
    display_lmstudio_response,
)

from .utils import (
    generate_timestamp,
    format_string,
    sanitize_filename,
    capitalize_words,
)

# Test modules
from . import flight_test_suite
from . import integration_test
from . import validation_test_suite
