cmake_minimum_required(VERSION 3.20)
project(mesh_instr LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(mesh_instr importer_instr.cpp harness_main.cpp)
if(MSVC)
    target_compile_options(mesh_instr PRIVATE /O2 /W3)
else()
    target_compile_options(mesh_instr PRIVATE -O2)
endif()
