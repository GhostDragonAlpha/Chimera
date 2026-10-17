cmake_minimum_required(VERSION 3.20)
project(chimera_artificial_protein_batch LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
find_package(Vulkan REQUIRED COMPONENTS glslc)
set(PROBE "${CMAKE_CURRENT_SOURCE_DIR}/../../membrane_scale_lab/membrane_gpu_probe")
add_executable(artificial_protein_batch batch.cpp)
target_include_directories(artificial_protein_batch PRIVATE "${PROBE}")
target_link_libraries(artificial_protein_batch PRIVATE Vulkan::Vulkan)
add_custom_command(OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/membrane.comp.spv"
  COMMAND "${Vulkan_GLSLC_EXECUTABLE}" -O "${PROBE}/membrane.comp" -o "${CMAKE_CURRENT_BINARY_DIR}/membrane.comp.spv"
  DEPENDS "${PROBE}/membrane.comp" VERBATIM)
add_custom_target(ap_shader DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/membrane.comp.spv")
add_dependencies(artificial_protein_batch ap_shader)
add_custom_command(TARGET artificial_protein_batch POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CMAKE_CURRENT_BINARY_DIR}/membrane.comp.spv" "$<TARGET_FILE_DIR:artificial_protein_batch>/membrane.comp.spv")
