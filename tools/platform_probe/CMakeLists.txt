cmake_minimum_required(VERSION 3.20)
project(chimera_portable_capture_probe LANGUAGES CXX)

# Separate instrument: never builds/launches the Windows engine or needs Vulkan.
add_executable(capture_fixture capture_fixture.cpp)
target_compile_features(capture_fixture PRIVATE cxx_std_17)
target_include_directories(capture_fixture PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/../../ChimeraEngine/engine")
find_package(Python3 REQUIRED COMPONENTS Interpreter)
enable_testing()
add_test(NAME lossless_capture_transport
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/check.py"
            --executable "$<TARGET_FILE:capture_fixture>")
