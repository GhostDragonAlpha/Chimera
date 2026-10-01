cmake_minimum_required(VERSION 3.20)
project(readback_probe LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Mirrors ChimeraEngine/engine/CMakeLists.txt Vulkan setup (same SDK, direct
# link against the loader import lib, no find_package magic).
set(VULKAN_SDK "C:/VulkanSDK/1.4.328.1" CACHE STRING "Vulkan SDK install path")

add_executable(readback_probe readback_probe.cpp)

target_include_directories(readback_probe PRIVATE "${VULKAN_SDK}/Include")

if(MSVC)
    # /Zi so crash offsets stay symbolizable (same rule as the engine, H-14 line)
    target_compile_options(readback_probe PRIVATE /O2 /Zi /W3)
    target_link_options(readback_probe PRIVATE /DEBUG:fastlink)
endif()

target_link_libraries(readback_probe PRIVATE
    "${VULKAN_SDK}/Lib/vulkan-1.lib"
)
