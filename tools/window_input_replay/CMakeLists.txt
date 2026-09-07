cmake_minimum_required(VERSION 3.20)
project(window_input_replay LANGUAGES CXX)

# P06 offline window/input event-replay harness.
# Deliberately NO Vulkan and NO OS headers: it must build and run anywhere
# with a C++17 compiler. It compiles the SAME translator TU the engine will
# link (ChimeraEngine/engine/platform/window_input.cpp) against a fake host.

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(window_input_replay
    replay_main.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/../../ChimeraEngine/engine/platform/window_input.cpp
)
target_include_directories(window_input_replay PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../../ChimeraEngine/engine
)

enable_testing()
add_test(NAME window_input_replay
         COMMAND window_input_replay
                 ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/evidence/p06/goldens/P06_GOLDEN_TRANSCRIPT_W1.txt
                 ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/evidence/p06/goldens/P06_GOLDEN_TRANSCRIPT_W2.txt
                 ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/evidence/p06/goldens/P06_GOLDEN_TRANSCRIPT_W3.txt
                 ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/evidence/p06/goldens/P06_GOLDEN_TRANSCRIPT_W4.txt)

# BP-PAN (2026-09-07): offline fixture for the PROPOSED right-drag-pan routing
# patch (docs/evidence/p06/PAN_ROUTING_PATCH.md). Compiles the PATCH AS SPEC
# (pan_routing_replay.cpp) against the SAME P06 types (platform/window_input.h)
# — NOT the engine and NOT the current translator window_input.cpp. See the
# file top for the separation.
add_executable(pan_routing_replay
    pan_routing_replay.cpp
)
target_include_directories(pan_routing_replay PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../../ChimeraEngine/engine
)
add_test(NAME pan_routing_replay
         COMMAND pan_routing_replay
                 ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/evidence/p06/goldens/PAN_ROUTING_P1.txt
                 ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/evidence/p06/goldens/PAN_ROUTING_P2.txt
                 ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/evidence/p06/goldens/PAN_ROUTING_P3.txt
                 ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/evidence/p06/goldens/PAN_ROUTING_P4.txt)