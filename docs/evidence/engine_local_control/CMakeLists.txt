cmake_minimum_required(VERSION 3.20)
project(engine_local_control_harness LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(REPO_ENGINE "E:/ChimeraWork/slot-01/ChimeraEngine/engine")
add_executable(engine_local_control_harness
    harness.cpp
    "${REPO_ENGINE}/http_server.cpp")
target_include_directories(engine_local_control_harness PRIVATE "${REPO_ENGINE}")
target_link_libraries(engine_local_control_harness PRIVATE ws2_32)
