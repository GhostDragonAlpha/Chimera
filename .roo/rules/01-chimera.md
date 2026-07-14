# Chimera Workspace Rules (all modes) — constitution core

The master brief is `AGENTS.md` at the workspace root; the live spec of the circadian
process is `Chimera/docs/GENERATION_PROTOCOL.md`. Read before substantive work.
Workdir for ALL python commands: `E:/PythonChimera/Chimera`.

## Recording (DNA graph — typed surfaces only)

- **Never hand-write `g.mutate` detail dicts.** Use the typed helpers from
  `Chimera/core/graphify_interface.py` (`record_feature`, `record_pathway`, `record_loop`,
  `record_phase`, `record_grade`, `record_build`, `record_surprise`, `record_simtest`,
  `record_rollout`) or the CLI `python -m core.graphify_record <kind> ...`.
  Mis-keyed dicts return a `rejected_*` string and record NOTHING.
- `observe`/`playtest` are EVIDENCE surfaces (full-automation amendment — the automated
  system is the measure). An observation must ATTRIBUTE recorded evidence
  (`--derived-from <simtest_id>` + `--quote`/`--tacit`) — a SimPlaytest from the sleepwalker
  or a telemetry sweep. Automation runs with `CHIMERA_AGENT_SIM=1`; the interface rejects
  evidence-less observations. A human may still supply a temperature, but it is optional.
- Capture surprises AS THEY HAPPEN: `python -m core.graphify_record surprise
  --context "..." --reality "..." --source human|agent|engine`. They are dream fodder.

## The Contract (mandatory bookends)

- Start: `python -m core.preflight` — read §[4.5] (Will, phantom pains, Observation queue,
  pending heuristics) and §[4.6] (last sleepwalk / rehearsal decision). Preflight opens with
  the **CAPCOM operator channel** — this Roo harness is exactly why CAPCOM is agent-agnostic
  (project-native Python, not a Claude Code hook): run `python -m core.capcom brief` and leave
  the operator a note with `python -m core.capcom tell "..."` or by editing `Chimera/docs/OPERATOR_INBOX.md`.
- End: `python -m core.postflight --phase "..." --result "<UBT verbatim>"
  --inheritance "<=3 sentences" --phantom-pain "<one specific prediction>"
  --pain-verdict "<phase_id>:P<n>:confirmed|refuted|still-open"`, then
  `python -m core.dream_loop`, then prepend a session block + recipe-carrying NEXT list
  to `task_progress.md` (the handoff invariant: an item without a recipe is a wish).

## Building & grading

- The Pipeline is authoritative: `python run_deep_space_trader_pipeline.py`. It needs
  qwen3.6-35b-a3b-mtp@iq2_m loaded in LM Studio (`lms load ...`) — gate_lm_available is a BLOCKER.
- Direct UBT (no LM needed): close the editor first (DLL lock), build, relaunch:
  `& "C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" ChimeraEditor Win64 Development "E:\PythonChimera\Chimera\Chimera.uproject" -waitmutex`
- **The gate is the RESULT grade** (`core/result_grader.py`, zero-LM): A>=90 B>=75 C>=60;
  C/F -> back to research with the study guide. Build failure auto-F. Unmeasured = omit
  (scores zero) — never guess. Declare `criteria_total` up front; measure every criterion.
- Stale-tree guard: only `Chimera/` + the two `*.Target.cs` under `Chimera/Source/`.
- Never hand-edit generator-owned files under `Source/Chimera/ProceduralGenerated/`
  (Flight, Ship, GameMode, Missions, Docking, Economy, Save, Combat, Factions, PirateAI,
  QuantumTravel, PCGVolumeManager) or `Chimera.Build.cs` — fix templates in
  `core/game_code_generator.py`. Manual loop-built files (Tools, Interactions, Sound, UI,
  NPC AI, ChimeraMovementComponent, StationActor, Demo/) are hand-editable.

## MCP usage

- Before any MCP call, check `Chimera/docs/MCP_PATHWAYS.md` (**26 proven pathways + traps**).
  Pathway exists -> follow EXACTLY. None -> simplest attempt, then `record_pathway`
  (success AND failure).
- **Never trust `success: true` — read the value back.** Every mutation gets a read-back
  (get_property / get_component_property / find_by_class / runtime_report).

## Screenshots / visual evidence (regime of 2026-07-06 — supersedes pyautogui doctrine)

- Viewport captures via MCP: `control_editor screenshot {mode: "editor_viewport", filename}`.
  Never desktop captures.
- Foreground the editor before trusting ANY empty frame or fps number (background throttle
  freezes Niagara/anim and clamps fps to exactly 3.0). Permanent fix is applied
  (bThrottleCPUWhenNotForeground=False) but an actively-focused human still wins focus.
- Camera moves: ONLY `control_editor console_command "BugItGo x y z pitch yaw roll"`.
- LM vision (qwen) is tertiary evidence, only when explicitly requested.

## Current game state (2026-07-07)

- The **Regolith Yard** demo (Chimera/docs/DEMO_ARCHITECTURE.md) is built and saved in
  `chimeradefaultlevel`: 3 material pads, astronaut (AutoPossess Player0), display suit,
  props. WorldSettings.DefaultGameMode = `/Script/Chimera.DemoOnFootGameMode`
  (Demo/DemoPlayerController provides WASD+mouse+space and a runtime chase camera).
  The sleepwalker plays SESSION A (beats 1-8) automatically as SimPlaytest evidence — the
  standing observation path. A human may also play it, but the automated sweep is the measure.
- Spiral Growth: complete Loop N before N+1; live state = preflight board, never assumptions.
