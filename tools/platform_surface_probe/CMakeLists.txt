cmake_minimum_required(VERSION 3.20)
project(platform_surface_probe LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# P05 surface-seam probe: a STANDALONE harness that exercises BOTH backends of
# the platform seam (Win32 + Unavailable) against the REAL Vulkan loader and
# headers. It deliberately does NOT build the engine, does NOT compile shaders,
# and writes nothing outside its own build dir. On a host with no Vulkan
# headers the harness still builds and runs the Unavailable-backend leg.
set(VULKAN_SDK "C:/VulkanSDK/1.4.328.1" CACHE STRING "Vulkan SDK install path")
set(SEAM_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../ChimeraEngine/engine/platform")

find_package(Vulkan REQUIRED)

set(PROBE_SOURCES
    probe_surface.cpp
    "${SEAM_DIR}/vulkan_surface_unavailable.cpp"
)
if(WIN32)
    list(APPEND PROBE_SOURCES "${SEAM_DIR}/vulkan_surface_win32.cpp")
endif()

add_executable(platform_surface_probe ${PROBE_SOURCES})

target_include_directories(platform_surface_probe PRIVATE
    "${VULKAN_SDK}/Include"
    "${CMAKE_CURRENT_SOURCE_DIR}/../../ChimeraEngine/engine"
)

target_link_libraries(platform_surface_probe PRIVATE Vulkan::Vulkan)
if(WIN32)
    target_link_libraries(platform_surface_probe PRIVATE user32 gdi32)
endif()