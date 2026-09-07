cmake_minimum_required(VERSION 3.20)
project(platform_surface_probe LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# P05-R1: the standalone probe uses DISCOVERED Vulkan dependencies
# (find_package -> Vulkan::Vulkan), NOT a hard-coded SDK path.
# R1 correction: this target REQUIRES Vulkan headers + discovery; it does NOT
# "still build without Vulkan headers" (the R0 comment was wrong and is
# removed). On a host without them, configure fails fast here on purpose.
find_package(Vulkan REQUIRED)

set(SEAM_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../ChimeraEngine/engine/platform")
set(PROBE_SOURCES
    probe_surface.cpp
    "${SEAM_DIR}/vulkan_surface_unavailable.cpp"
)
if(WIN32)
    list(APPEND PROBE_SOURCES "${SEAM_DIR}/vulkan_surface_win32.cpp")
endif()

add_executable(platform_surface_probe ${PROBE_SOURCES})

# Vulkan::Vulkan carries the discovered include directories and import lib;
# no manual SDK include path is hard-coded here.
target_include_directories(platform_surface_probe PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/../../ChimeraEngine/engine"
)

target_link_libraries(platform_surface_probe PRIVATE Vulkan::Vulkan)
if(WIN32)
    target_link_libraries(platform_surface_probe PRIVATE user32 gdi32)
endif()