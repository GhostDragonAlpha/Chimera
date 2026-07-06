# Chimera Workspace Rules (all modes)

The master brief is `AGENTS.md` at the workspace root — read it before substantive work.
These rules are the operational deltas every mode must follow.

## Recording (DNA graph)

- **Never hand-write `g.mutate` detail dicts.** Use the typed helpers from
  `Chimera/core/graphify_interface.py` (`record_feature`, `record_pathway`,
  `record_loop`, `record_phase`, `record_grade`, `record_build`) or the CLI:
  `python -m core.graphify_record feature --name X --loop 8 --status verified --param k=v`
  (run from `E:/PythonChimera/Chimera`).
- Mis-keyed dicts are **rejected** with a `rejected_*` return string and nothing is
  recorded — if you see that string, your keys are wrong; nothing happened.
- Recording history after the fact? Pass `--backfilled` / `backfilled=True`.
  Never fake timestamps. Every node is auto-stamped `recorded_by` + `run_id`.

## The Contract (mandatory bookends)

- Session start: `python -m core.preflight` — prints graph health, GPA trend, the
  spiral loop board, pending technical_research, last pipeline run, and whether
  LM Studio / Unreal / DNA API are reachable. Report findings before proceeding.
- Session end: `python -m core.postflight --phase "..." --result "..."` — records
  PhaseComplete and prints the closing checklist. Report UBT output **verbatim**.

## Building

- The Pipeline is authoritative: `python run_deep_space_trader_pipeline.py`
  (from `E:/PythonChimera/Chimera`). MCP is for discovery, not routine builds.
- The build **fails fast** if anything besides `Chimera/` and the two `*.Target.cs`
  files exists under `Chimera/Source/` (stale-tree guard, Known Bug #1). Do not
  create parallel module trees; if the guard trips, delete the stale trees.
- Compilation failures auto-record ProfessorGrade **F**, non-pass visual
  verifications auto-record **C** — a falling GPA is signal, not noise. Report it
  with corrective action, never suppress it.

## MCP usage

- Before any MCP call: `g.query("pathway", <action>)`. Pathway exists → follow it
  exactly. No pathway → try the simplest approach, then record the attempt with
  `record_pathway` (success **and** failure). 14 known-good sequences live in
  `Chimera/docs/MCP_PATHWAYS.md`.
- Material parameters: `manage_asset.add_*_parameter` creates **orphaned nodes**.
  Use `system_control.execute_python` with a **single-line** semicolon-separated
  script (the handler crashes on multi-line scripts).

## Screenshots / visual verification

- Only `pyautogui` via `Chimera/core/visual_verifier.py` — never MCP screenshot
  modes (wrong window / wrong camera / low-res). The verifier aborts unless
  **Unreal Editor is the foreground window** and records `aborted_wrong_window`.
- Prefer checklist verification: `run_visual_verification(project_path,
  checklist=["criterion 1", ...], feature="Feature_Name")` — strict per-item
  YES/NO; unanswered items count as NO. Verify PNG > 100 KB before sending.

## Source conventions

- Canonical module: `Chimera/Source/Chimera/`, macro `CHIMERA_API`, UE 5.8, C++20.
- UE gotchas already paid for here: `TMap::operator[]` asserts on missing keys —
  use `FindOrAdd`; `TickComponent` must match the exact UActorComponent signature;
  price/economy math lives in `ProceduralGenerated/Economy/` (formula:
  `BasePrice * clamp(pow(D/S, elasticity), 0.25, 4.0)`).
- Complete all features in Loop N before Loop N+1 (Spiral Growth). Current state
  lives in the DNA graph — check `python -m core.preflight`, not assumptions.
