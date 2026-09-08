cmake_minimum_required(VERSION 3.20)
project(chimera_membrane_gpu_probe LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Vulkan REQUIRED)

set(SHADER_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/membrane.comp")
set(SHADER_BINARY "${CMAKE_CURRENT_BINARY_DIR}/membrane.comp.spv")
if(WIN32)
    if(DEFINED ENV{VULKAN_SDK} AND EXISTS "$ENV{VULKAN_SDK}/Bin/glslc.exe")
        set(GLSLC "$ENV{VULKAN_SDK}/Bin/glslc.exe")
    elseif(EXISTS "C:/VulkanSDK/1.4.328.1/Bin/glslc.exe")
        set(GLSLC "C:/VulkanSDK/1.4.328.1/Bin/glslc.exe")
    else()
        message(FATAL_ERROR "glslc not found; set VULKAN_SDK to an installed Vulkan SDK")
    endif()
else()
    find_program(GLSLC glslc REQUIRED)
endif()

add_custom_command(
    OUTPUT "${SHADER_BINARY}"
    COMMAND "${GLSLC}" -O -o "${SHADER_BINARY}" "${SHADER_SOURCE}"
    DEPENDS "${SHADER_SOURCE}"
    COMMENT "Compiling membrane compute shader"
    VERBATIM
)
add_custom_target(membrane_shader DEPENDS "${SHADER_BINARY}")

add_executable(membrane_gpu_probe probe.cpp)
add_dependencies(membrane_gpu_probe membrane_shader)
target_link_libraries(membrane_gpu_probe PRIVATE Vulkan::Vulkan)
target_compile_definitions(membrane_gpu_probe PRIVATE
    CHIMERA_PROBE_SHADER_PATH="$<TARGET_FILE_DIR:membrane_gpu_probe>/membrane.comp.spv"
)

# GLM-RELAX-GPU-01: the GPU-driven relaxation gate. Same verified shader,
# same probe core; the loop lives in relax.cpp with one derived stage-4
# trial kernel compiled at runtime.
add_executable(relax_gpu_probe relax.cpp)
add_dependencies(relax_gpu_probe membrane_shader)
target_link_libraries(relax_gpu_probe PRIVATE Vulkan::Vulkan)
target_compile_definitions(relax_gpu_probe PRIVATE
    CHIMERA_PROBE_SHADER_PATH="$<TARGET_FILE_DIR:membrane_gpu_probe>/membrane.comp.spv"
)
target_include_directories(relax_gpu_probe PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
add_custom_command(TARGET membrane_gpu_probe POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${SHADER_BINARY}" "$<TARGET_FILE_DIR:membrane_gpu_probe>/membrane.comp.spv"
)

if(MSVC)
    target_compile_options(membrane_gpu_probe PRIVATE /W4 /permissive-)
else()
    target_compile_options(membrane_gpu_probe PRIVATE -Wall -Wextra -Wpedantic)
endif()

include(CTest)
if(BUILD_TESTING)
    add_test(NAME membrane_gpu_probe_b2_fan12
        COMMAND membrane_gpu_probe
            --fixtures "${CMAKE_CURRENT_SOURCE_DIR}/../../docs/evidence/gpu_fixtures"
            --shader "$<TARGET_FILE_DIR:membrane_gpu_probe>/membrane.comp.spv")
endif()
