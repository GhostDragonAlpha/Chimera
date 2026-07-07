# Visual Test Mode — regime of 2026-07-06 (SUPERSEDES the pyautogui doctrine)

- Viewport captures: `control_editor screenshot {mode: "editor_viewport", filename}` via MCP.
  NEVER desktop captures (pyautogui path is retired; core/visual_verifier.py's desktop mode is
  legacy — do not reintroduce it).
- Foreground the editor BEFORE trusting any empty frame, particle check, or fps number:
  background throttle freezes Niagara/anim simulation and clamps fps to exactly 3.0.
- Frame the shot with `BugItGo x y z pitch yaw roll` (console_command) — set_camera_position
  and focus_actor lie on locked viewports.
- Prefer engine hard facts over pixels: read-backs (find_by_class, get_component_property,
  runtime_report) are Layer-1 evidence; a screenshot is Layer-3; LM vision (qwen, localhost:1234)
  is tertiary and only when explicitly requested (gate_lm_available applies to it).
- Telemetry evidence: `python -m core.telemetry_probe --out t.json --soak 30` — crash_free,
  fps vs 60, growth. Record non-pass honestly; auto-C is signal, not noise.
- The Sleepwalker (`core/sleepwalker.py`) automates beat-level visual sessions — check
  preflight §[4.6] before duplicating a walk it already made.
