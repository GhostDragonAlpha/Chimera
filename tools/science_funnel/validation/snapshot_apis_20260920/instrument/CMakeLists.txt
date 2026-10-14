cmake_minimum_required(VERSION 3.20)
project(chimera_snapshot_api LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(ENGINE native/ChimeraEngine/engine)
# LEG-A fence target: the SHIPPED harness source (verbatim copy) on the
# instrument header copy, flag OFF -- must be byte-identical to the pristine
# build (stdout 8c537cdb..., trace stderr c6f9b6c0... at this base).
add_executable(gait_unit_snapoff ${ENGINE}/tests_coupled_arm/gait_unit.cpp)
target_include_directories(gait_unit_snapoff PRIVATE ${ENGINE})
if(MSVC)
 target_compile_options(gait_unit_snapoff PRIVATE /W4 /fp:precise)
endif()
# The exercised instrument: ref (ship behavior + recording), restore, probe.
add_executable(gait_snap ${ENGINE}/tests_coupled_arm/gait_snap.cpp)
target_include_directories(gait_snap PRIVATE ${ENGINE})
target_compile_definitions(gait_snap PRIVATE GAIT_EVENT_TRACE GAIT_SNAPSHOT_API)
if(MSVC)
 target_compile_options(gait_snap PRIVATE /W4 /fp:precise)
endif()
