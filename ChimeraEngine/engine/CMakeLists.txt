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

# 2026-09-03, the stale-spv incident: the old hand-list compiled SEVEN shaders
# while the triangle lane (render_tri*, shadow, frost, joints, hinge, gait,
# volp, water_*) shipped PREHISTORIC .spv files — a lighting change to
# render_tri.frag built clean and changed NOTHING on screen because its .spv
# was copied, not compiled. The list is now DERIVED: every .vert/.frag/.comp/
# .glsl in shaders/ compiles to a .spv. A new shader file is wired by existing;
# a deleted one stops building. No shader can silently rot again.

# Compile GLSL -> SPIR-V at build time (derived from the source tree)
if(GLSL_VALIDATOR)
    file(GLOB SHADER_SOURCES
        "${SHADER_DIR}/*.vert"
        "${SHADER_DIR}/*.frag"
        "${SHADER_DIR}/*.comp"
        "${SHADER_DIR}/*.glsl"
    )
    set(SHADER_STAGE_vert vert)
    set(SHADER_STAGE_frag frag)
    set(SHADER_STAGE_comp comp)
    set(SHADER_STAGE_glsl comp)
    set(COMPILED_SHADERS "")
    foreach(src ${SHADER_SOURCES})
        get_filename_component(name "${src}" NAME)
        get_filename_component(stem "${src}" NAME_WE)
        string(REGEX REPLACE "^.*\\." "" ext "${name}")
        set(stage "${SHADER_STAGE_${ext}}")
        if(NOT stage)
            message(FATAL_ERROR "unknown shader stage for ${name}")
        endif()
        # Output naming (matches the engine's read_file names exactly):
        #   render.vert -> render.vert.spv     (stages keep the extension —
        #   render.frag -> render.frag.spv      vert/frag PAIRS share a stem)
        #   compute.glsl -> compute.spv        (compute sources use the bare stem)
        if(stage STREQUAL "comp")
            set(out "${SPIRV_DIR}/${stem}.spv")
        else()
            set(out "${SPIRV_DIR}/${name}.spv")
        endif()
        if(COMPILED_SHADERS)
            list(FIND COMPILED_SHADERS "${out}" dup)
            if(NOT dup EQUAL -1)
                message(FATAL_ERROR "shader output collision: ${out}")
            endif()
        endif()
        add_custom_command(
            OUTPUT "${out}"
            COMMAND "${CMAKE_COMMAND}" -E make_directory "${SPIRV_DIR}"
            COMMAND "${GLSL_VALIDATOR}" -S "${stage}" -V "${src}" -o "${out}"
            DEPENDS "${src}"
            COMMENT "Compiling ${name} -> ${name}.spv"
        )
        list(APPEND COMPILED_SHADERS "${out}")
    endforeach()

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

    add_custom_command(
        OUTPUT "${SPIRV_DIR}/ui.vert.spv"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${SPIRV_DIR}"
        COMMAND "${GLSL_VALIDATOR}" -S vert -V "${SHADER_DIR}/ui.vert" -o "${SPIRV_DIR}/ui.vert.spv"
        DEPENDS "${SHADER_DIR}/ui.vert"
        COMMENT "Compiling ui.vert -> ui.vert.spv"
    )

    add_custom_command(
        OUTPUT "${SPIRV_DIR}/ui.frag.spv"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${SPIRV_DIR}"
        COMMAND "${GLSL_VALIDATOR}" -S frag -V "${SHADER_DIR}/ui.frag" -o "${SPIRV_DIR}/ui.frag.spv"
        DEPENDS "${SHADER_DIR}/ui.frag"
        COMMENT "Compiling ui.frag -> ui.frag.spv"
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
    ui.cpp
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
    gdi32
    user32
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
