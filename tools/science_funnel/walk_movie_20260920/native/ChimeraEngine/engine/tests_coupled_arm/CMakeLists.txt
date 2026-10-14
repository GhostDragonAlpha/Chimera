cmake_minimum_required(VERSION 3.20)
project(gait_statedump LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
# The walk-movie prestage's state-dump variant of the wave-26 gait_unit
# (lane agent/walk-movie-prestage-20260920). Same flags as the wave-26 lane's
# trace target: /W4 /fp:precise, GAIT_EVENT_TRACE (the stderr traces this
# lane's repro falsifier compares against the wave-26 fixed26_trace.err).
add_executable(gait_unit_statedump gait_unit_statedump.cpp)
if(MSVC)
 target_compile_options(gait_unit_statedump PRIVATE /W4 /fp:precise)
 target_compile_definitions(gait_unit_statedump PRIVATE GAIT_EVENT_TRACE)
endif()
