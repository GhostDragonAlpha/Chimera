# window_input_replay — P06 offline window/input event-replay harness

Offline = no GPU, no window, no Vulkan, no OS calls. The harness compiles the
SAME translator TU the engine will link
(`ChimeraEngine/engine/platform/window_input.cpp`) and drives it with a
recording fake `WindowHost`. It is deliberately separate from the Windows
interaction suite and from future Linux window tests (P06 spec §8).

## Build + run

```bat
cmake -S tools\window_input_replay -B %TEMP%\p06_builds\replay -G "Visual Studio 18 2026" -A x64
cmake --build %TEMP%\p06_builds\replay --config Release
%TEMP%\p06_builds\replay\Release\window_input_replay.exe docs\evidence\p06\goldens\*.txt
```

No Vulkan discovery, no `find_package` — anything with a C++17 compiler works.

## Golden grammar

```
# comment (headers MUST name the behavior source revision)
mode console <0|1>      set fake console state
mode ui     <0|1>       set fake StudioUI visibility
mode sphere <float>     set SceneRef.mesh_sphere
> down|down.r|up <key>  key event (down.r = repeat bit set)
> char <int>
> move <x> <y>
> ldown <x> <y> | lup | rdown <x> <y> | rup
> wheel <steps> <x> <y>
> resize <w> <h>
|                       flush the batch through apply_input_event()
poll <dt>               run update_camera_input() (a fake frame)
! keys <key> <0|1>      g_keys[] expectation
! captured <0|1>        mouse capture expectation
! cam <field> <float>   theta|phi|radius|pan_x|pan_y|target0|target1|target2
! psize <w> <h>         pending_resize_* expectation (read from the atomics)
! calls <log>           EXACT recorded host-call log since the last ! calls
                        (<none> = empty); the log is cleared on check
```

Key tokens: single chars (`W`,`A`,`S`,`D`,`Q`,`E`,`R`,`P`), `'P'` style also
accepted, `SPACE CTRL ESC UP DOWN LEFT RIGHT GRAVE F1..F8` or a raw number.

## Coverage + limitations (P06 spec §6)

- W1 keyboard ordering / key-state parity; W2 capture + camera deltas; W3
  resize/minimize intent ordering; W4 console gating.
- The fake host NEVER consumes UI events (`ui_consume_lbutton`/`ui_on_wheel`
  return false) — the consume-before-orbit Blender law is enforced
  structurally by the translator arm order and is asserted by the Windows
  interaction suite instead (spec §8.1).
- W2 locks the OBSERVED behavior that the original right-drag pan arm is dead
  code (spec §6/W2 record): captured drags orbit; pan never executes.
- Goldens are HAND-AUTHORED bedside cases in this commit; the live recording
  session that replaces them is the Inc-2 gate (spec §7).