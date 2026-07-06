# SUCCESSOR RUNBOOK — recipes, not principles

> Written 2026-07-06 for a **less capable heir**. If you are a powerful model, read
> CLAUDE.md and think. If you are not sure which you are, follow this file EXACTLY and
> improvise NOTHING. Every recipe here was paid for. The traps section is blood.

## PRIME DIRECTIVES (absolute — violating these destroys paid-for work)

1. **Never edit** anything under `Source/Chimera/ProceduralGenerated/` or `Chimera.Build.cs`. Fix generator templates in `core/game_code_generator.py` or do not fix at all.
2. **Never record an Observation** (`graphify_record observe`). Only the human does that. Ever.
3. **Never promote a heuristic** unless the human said "approved" for that specific H-number.
4. **Never write graph mutations by hand.** Only `python -m core.graphify_record ...` or the `record_*` helpers.
5. **Never trust `success: true`.** Read the value back. If you cannot read it back, treat it as NOT done and say so.
6. If a recipe fails **twice**, record the failure (`graphify_record pathway ... --result failed`), write it in task_progress.md, and move to the next task. Do not invent alternatives.

## SESSION RECIPE (run in this order, always)

```powershell
cd E:\PythonChimera\Chimera
python -m core.preflight          # DAWN. Read [4.5] carefully: Will, pains, queues.
# ... do ONE work item from "YOUR TASKS" below ...
python -m core.postflight --phase "<what you did>" --result "<verbatim outputs>" `
  --inheritance "<=3 sentences for the next session>" `
  --phantom-pain "<one specific prediction of failure>" `
  --pain-verdict "<id>:confirmed|refuted|still-open"   # for each open pain you tested
python -m core.dream_loop         # NIGHT. Never skip.
git add -A ; git commit -m "<summary>" ; git push origin master
```
Update `task_progress.md` (prepend a session block + NEXT list) before committing.

## YOUR TASKS (in order — stop at the first one that applies)

1. **If the human gave heuristic verdicts** (docs/PENDING_HEURISTICS.md): for each
   `approved` entry, add the rule to the organ named in the entry (gate → new function
   in core/gates.py copying an existing gate's shape; claude_md → one bullet in
   CLAUDE.md's Generation Protocol section; mcp_pathways → a TRAP line in
   docs/MCP_PATHWAYS.md), then run
   `python -m core.graphify_record heuristic --signature "<sig>" --rule "<rule>" --organ <organ> --evidence <node_id>`
   and change the entry's status to `promoted`. Vetoed entries: change status to
   `vetoed`, touch nothing else.
2. **If the human gave a PLAYTEST TEMPERATURE** (a few sentences about the WHOLE
   experience — this is how the Observer actually works; do not expect per-feature
   verdicts):
   a. Record it VERBATIM first:
      `python -m core.graphify_record playtest --notes "<their exact words>" --build <commit>`
      → note the returned playtest node id.
   b. **Attribution** (this is YOUR job — "the AI has to guess on intentions, but
      now it has the information"). For each feature in the observation queue,
      decide ONE tier and act:
      - **Directly implicated** — the temperature praises/indicts it. Run
        `... observe --feature <X> --verdict <accepted|rejected> --notes "<their words>" --derived-from <playtest_id> --quote "<their exact phrase>" --loop <N>`
      - **Exercised but unmentioned** — it was on screen / in play and drew no
        complaint. Silence passed the glance:
        `... observe --feature <X> --verdict accepted --derived-from <playtest_id> --tacit --loop <N>`
      - **Not exercised** — the playtest couldn't have touched it (e.g. SaveLoad
        if they never saved). LEAVE IT QUEUED. Do not attribute.
   c. End your session summary with the full attribution table (feature → tier →
      quote) so the human can overrule any line with one sentence. If they do,
      record their sentence as a `surprise --source human` and flip the feature.
   If you are a weaker model: do tier 1 (direct mentions) ONLY; leave tacit calls
   to a capable session.
3. **If the human gave an explicit per-feature verdict** (rare): run exactly
   `python -m core.graphify_record observe --feature <X> --verdict <accepted|rejected> --notes "<their words>" --loop <N>`.
4. **Ground_Sand_Footprints retry** (status: needs_refinement, grade C 72.9). The study
   guide is on the feature node and in task_progress.md. Steps, exactly:
   a. Call `animation_physics` action `add_anim_notify` on
      `/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd`
      with a notify name like `FootPlant` at ~0.3s and ~0.8s.
   b. READ BACK (get_anim_sequence_info or re-query). If the notify is not readable
      back or the action errors: this is facade #3 — record it, set the feature note,
      STOP this task.
   c. If notifies stick: wire is beyond this runbook — record what you did and leave
      the wiring for a capable session. Do not attempt Blueprint graph editing.
5. **Run the pipeline for a health check**: `python run_deep_space_trader_pipeline.py`
   — record the UBT line verbatim via postflight. If it fails, do NOT fix generated
   C++; record and stop.

## PROVEN RECIPES (copy exactly)

- **Connect to the editor (Python):**
  `from core.telemetry_probe import MCPStdioClient; c = MCPStdioClient(); resp = c.call(tool, args)`
  Editor must be running; bridge port is 8091. Launch editor:
  `cmd /c start "" "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "E:\PythonChimera\Chimera\Chimera.uproject"` then wait ~2–5 min.
- **Move the editor camera:** `control_editor` `console_command` with
  `BugItGo x y z pitch yaw roll`. (`set_camera_position` and `focus_actor` LIE — they
  report success and do nothing.)
- **Screenshot:** `control_editor` `screenshot` `{filename, mode: "editor_viewport"}`.
  NEVER desktop/pyautogui screenshots.
- **Before trusting ANY empty/frozen frame or any fps number:** foreground the editor:
  PowerShell `(New-Object -ComObject WScript.Shell).AppActivate((Get-Process UnrealEditor | ? {$_.MainWindowTitle} | select -First 1).Id)`
  A backgrounded editor runs at 3fps and simulates NOTHING (particles/anims freeze).
- **Telemetry evidence:** `python -m core.telemetry_probe --out t.json --soak 30`
  (foreground first).
- **Grade a feature:** write evidence JSON (schema in core/result_grader.py docstring),
  then `python -m core.result_grader --feature <X> --evidence ev.json`. Missing
  evidence scores ZERO — never guess numbers.
- **Read a component property back:** `control_actor` `get_component_property`
  `{actorName, componentName, propertyName}`. The Character's movement component is
  named **CharMoveComp**. The mesh is **CharacterMesh0**.
- **Save everything:** `control_editor` `save_all` (manage_asset has NO save).
- **Spawn a Niagara system:** `manage_effect` `spawn_niagara`
  `{systemPath, actorName, location}` — engine template paths work directly.
- **PIE motion without input:** set on CharMoveComp: BrakingDecelerationWalking=0,
  GroundFriction=0, BrakingFrictionFactor=0, then Velocity={x,y,z}. Read Velocity back.

## TRAPS — NEVER DO (each cost a real session real hours)

- Niagara **authoring is broken**: create_niagara_system / add_emitter_to_system /
  add_*_module / set_niagara_parameter all return success and do NOTHING.
  get_niagara_info reports emitterCount=0 even for working systems.
  validate_niagara_system says isValid for broken ones. Duplicating engine Niagara
  templates breaks their data interfaces. **Spawn stock templates; author nothing.**
  The real fix is repairing Plugins/McpAutomationBridge (capable sessions only).
- `possess` reports success but the PIE controller keeps DefaultPawn. Move
  DefaultPawn0 as your camera instead (its view = its position, rotation is fixed).
- `simulate_input` accepts ONLY type `key_down` / `key_up`.
- Local LM (qwen) output MUST be schema-validated; prefix prompts with `/no_think`
  and give max_tokens ≥ 1200, check `content` AND `reasoning_content`. A reasoning
  dump is a RETRY, never an answer.
- An error message containing a `[DynamicToolManager]` banner means you captured
  stdout, not the error. Capture the response's error field.
- `attach` needs `parentActor` (not parentActorName) and keeps world transform —
  snap with set_transform after.
- Ground_Sand_Sound is **blocked on assets** (no audio files exist anywhere). Do not
  attempt until the human imports sounds.
- The env vars `ANTHROPIC_MODEL` / `ANTHROPIC_DEFAULT_*` = deepseek-* (User scope)
  break the permission classifier, WebSearch, and subagents when bypass is off.
  Removing them is the HUMAN's call (P3, confirmed twice).

## THE STANDING QUEUES (human-only; your job is to surface, never to answer)

Preflight [4.5] lists them every dawn: pending heuristics (docs/PENDING_HEURISTICS.md)
and the Observation queue. If the human is present, ask for verdicts. If not, work
task 3/4 and leave the queues untouched.

## THE SHAPE OF A GOOD SESSION

One task, honestly measured, honestly graded, honestly recorded, pushed. A C with a
sharp study guide is worth more than a fake A. The system was built so that your
successor inherits your lessons — write your Will like you mean it.
