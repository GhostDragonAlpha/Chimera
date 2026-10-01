cmake_minimum_required(VERSION 3.20)
project(gait_statedump_w28 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
# The record-walk lane's state-dump variant of the WAVE-28 gait_unit
# (lane agent/record-movie-20260921, base agent/gait-wave28-hind-step 0557fc99),
# same shape as the walk-movie prestage's variant (lane
# agent/walk-movie-prestage-20260920). Two targets from the SAME vendor tree:
#   gait_unit_tracebase  -- the UNMODIFIED wave-28 gait_unit.cpp (the repro
#                           baseline: its stderr trace is what the statedump
#                           variant's must match line-for-line)
#   gait_unit_statedump  -- the variant (29 added lines, all marked
#                           "WALK-MOVIE PRESTAGE": the GAIT_STATE_DUMP q/v
#                           stream; reads only)
# Same flags as the wave-26 lane's trace target: /W4 /fp:precise,
# GAIT_EVENT_TRACE (the stderr traces the repro falsifier compares).
add_executable(gait_unit_tracebase gait_unit.cpp)
add_executable(gait_unit_statedump gait_unit_statedump.cpp)
if(MSVC)
 target_compile_options(gait_unit_tracebase PRIVATE /W4 /fp:precise)
 target_compile_definitions(gait_unit_tracebase PRIVATE GAIT_EVENT_TRACE)
 target_compile_options(gait_unit_statedump PRIVATE /W4 /fp:precise)
 target_compile_definitions(gait_unit_statedump PRIVATE GAIT_EVENT_TRACE)
endif()
