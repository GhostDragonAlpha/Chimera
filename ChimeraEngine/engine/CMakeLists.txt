cmake_minimum_required(VERSION 3.20)
project(chimera_engine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Vulkan SDK path
set(VULKAN_SDK "C:/VulkanSDK/1.4.328.1" CACHE STRING "Vulkan SDK install path")
set(ENV{VULKAN_SDK} "${VULKAN_SDK}")

find_package(Vulkan REQUIRED)

# Locate glslangValidator for GLSL -> SPIR-V compilation
if(EXISTS "${VULKAN_SDK}/Bin/glslangValidator.exe")
    set(GLSL_VALIDATOR "${VULKAN_SDK}/Bin/glslangValidator.exe")
elseif(EXISTS "${VULKAN_SDK}/Bin32/glslangValidator.exe")
    set(GLSL_VALIDATOR "${VULKAN_SDK}/Bin32/glslangValidator.exe")
else()
    message(WARNING "glslangValidator not found -- shaders must be pre-compiled .spv files")
    set(GLSL_VALIDATOR "")
endif()

set(SHADER_DIR "${CMAKE_CURRENT_SOURCE_DIR}/shaders")
set(SPIRV_DIR  "${CMAKE_BINARY_DIR}/shaders")

# Compile GLSL -> SPIR-V at build time (hardcoded shader names)
if(GLSL_VALIDATOR)
    set(COMPILED_SHADERS
        "${SPIRV_DIR}/render.vert.spv"
        "${SPIRV_DIR}/render.frag.spv"
        "${SPIRV_DIR}/compute.spv"
        "${SPIRV_DIR}/sort.spv"
        "${SPIRV_DIR}/skin.spv"
    )

    add_custom_command(
        OUTPUT "${SPIRV_DIR}/render.vert.spv"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${SPIRV_DIR}"
        COMMAND "${GLSL_VALIDATOR}" -S vert -V "${SHADER_DIR}/render.vert" -o "${SPIRV_DIR}/render.vert.spv"
        DEPENDS "${SHADER_DIR}/render.vert"
        COMMENT "Compiling render.vert -> render.vert.spv"
    )

    add_custom_command(
        OUTPUT "${SPIRV_DIR}/render.frag.spv"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${SPIRV_DIR}"
        COMMAND "${GLSL_VALIDATOR}" -S frag -V "${SHADER_DIR}/render.frag" -o "${SPIRV_DIR}/render.frag.spv"
        DEPENDS "${SHADER_DIR}/render.frag"
        COMMENT "Compiling render.frag -> render.frag.spv"
    )

    add_custom_command(
        OUTPUT "${SPIRV_DIR}/compute.spv"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${SPIRV_DIR}"
        COMMAND "${GLSL_VALIDATOR}" -S comp -V "${SHADER_DIR}/compute.glsl" -o "${SPIRV_DIR}/compute.spv"
        DEPENDS "${SHADER_DIR}/compute.glsl"
        COMMENT "Compiling compute.glsl -> compute.spv"
    )

    add_custom_command(
        OUTPUT "${SPIRV_DIR}/sort.spv"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${SPIRV_DIR}"
        COMMAND "${GLSL_VALIDATOR}" -S comp -V "${SHADER_DIR}/sort.comp" -o "${SPIRV_DIR}/sort.spv"
        DEPENDS "${SHADER_DIR}/sort.comp"
        COMMENT "Compiling sort.comp -> sort.spv"
    )

    add_custom_command(
        OUTPUT "${SPIRV_DIR}/skin.spv"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${SPIRV_DIR}"
        COMMAND "${GLSL_VALIDATOR}" -S comp -V "${SHADER_DIR}/skin.comp" -o "${SPIRV_DIR}/skin.spv"
        DEPENDS "${SHADER_DIR}/skin.comp"
        COMMENT "Compiling skin.comp -> skin.spv"
    )

    add_custom_target(all_shaders ALL DEPENDS ${COMPILED_SHADERS})
else()
    message(WARNING "No glslangValidator; copying .spv files if present")
endif()

add_executable(chimera_engine
    main.cpp
    engine.cpp
    physics.cpp
    http_server.cpp
)

target_include_directories(chimera_engine PRIVATE
    "${VULKAN_SDK}/Include"
    "${CMAKE_CURRENT_SOURCE_DIR}"
)

target_link_libraries(chimera_engine PRIVATE
    "${VULKAN_SDK}/Lib/vulkan-1.lib"
    ws2_32
    secur32
    crypt32
    ncrypt
    bcrypt
)

# Copy shaders (GLSL source + compiled SPIR-V) to build output
add_custom_command(TARGET chimera_engine POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        "${SHADER_DIR}"
        "$<TARGET_FILE_DIR:chimera_engine>/shaders"
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        "${SPIRV_DIR}"
        "$<TARGET_FILE_DIR:chimera_engine>/shaders"
)
