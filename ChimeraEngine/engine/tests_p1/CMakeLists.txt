cmake_minimum_required(VERSION 3.20)
project(p1_tests CXX)

# work.data.compute_harness: parallel MSVC compilation across the 24 cores.
if(MSVC)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /MP24")
endif()
set(CMAKE_BUILD_PARALLEL_LEVEL 24 CACHE STRING "Default parallel build level")

add_executable(test_p1_inventory
    test_p1_inventory.cpp
    ../membrane_tick.cpp
)
target_compile_features(test_p1_inventory PRIVATE cxx_std_17)

# worker 5: persistence (SEL2 round-trip, legacy SEL1 migration, refusals)
add_executable(test_p1_persistence
    test_p1_persistence.cpp
    ../membrane_tick.cpp
)
target_compile_features(test_p1_persistence PRIVATE cxx_std_17)
target_include_directories(test_p1_persistence PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/..")
