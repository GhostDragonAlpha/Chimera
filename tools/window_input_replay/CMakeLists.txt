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