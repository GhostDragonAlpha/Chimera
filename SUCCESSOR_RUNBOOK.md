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

## PARALLEL ENTRY (2026-07-12 — if other agents may be running, claim from the board)

The task list is now the single entry. Instead of freely picking work, claim a
parallel-safe lane so you never collide with another agent (exact commands):

```powershell
python -m core.task_board claim --agent <your-id>              # opens your work packet
# ... do the recipe it prints, staying inside the file scopes it shows ...
python -m core.task_board done --agent <your-id> --id tb-N --result "<verbatim evidence>"
# or:  block --agent <id> --id tb-N --reason "<cause>"   (bare 'blocked' is forbidden)
```

Two storage facts changed under you, both TRANSPARENT (your recipes are unchanged):
- The DNA graph is now **SQLite** (`core.world_store`), not JSON. `record_*` / `graphify_record`
  work exactly as before. Fast search: `python -m core.dna_sqlite_backend search --query <term>`.
- The **2000-node gate is RETIRED**. NEVER run `archive_old_mutations.py` — the graph
  scales now; growth is fine.

`capable_only` board tasks require a `journeyman` credential earned via
`python -m core.gauntlet enter --agent <id>` (7 verified stations). If that is beyond
you, take a non-capable task instead — do NOT improvise around the gate.

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
4. **The first executable item in task_progress.md's NEXT list.** The handoff
   invariant means each item carries its recipe inline (or names the feature whose
   graph node holds the study guide). Execute it EXACTLY; add nothing. Skip items
   marked `capable sessions only` or lacking a recipe.
5. **If nothing above applies — pipeline health check**:
   `python run_deep_space_trader_pipeline.py` — record the UBT line verbatim via
   postflight. If it fails, do NOT fix generated C++; record and stop.

When YOU write the NEXT list at dusk: same invariant — exact commands or a named
feature node + skip-condition per item. An item without a recipe is a wish; do not
write wishes.

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


## ADDENDUM 2026-07-07 — the Sleepwalker era (recipes for the new organs)

**New PRIME DIRECTIVE 7**: if you are an automation process (not relaying a live human),
run with `CHIMERA_AGENT_SIM=1` set. It makes faking a human observation technically
impossible. `core/sleepwalker.py` sets it for itself.

**When your NEXT list is empty (branch C2 — do this BEFORE the pipeline fallback):**
```powershell
python -m core.rehearsal --candidates-file docs/rehearsal_candidates.json --decide
```
It prints a veto table, records the decision, and prepends a recipe-carrying NEXT item.
Execute THAT item. If it is marked `capable sessions only` and you are not: run the
pipeline fallback instead.

**To let the game play itself (evidence, never verdicts):**
```powershell
python -m core.sleepwalker --beats docs/beats/regolith_yard.beats.json --session sim_<date>
```
5/5 beats = healthy demo. Failures auto-record surprises the dream loop clusters
(kind sim_rejection — always ranked below the human's voice).

**New traps (paid for on 2026-07-06):**
- `Config/DefaultInput.ini` has NO trailing newline and ends with a `[GameInputPlatformSettings...]`
  section. Appending blindly corrupts it AND lands mappings in the wrong section — insert inside
  `[/Script/Engine.InputSettings]`.
- The editor overwrites `EditorPerProjectUserSettings.ini` on graceful shutdown. To make a
  settings edit stick: write the ini, FORCE-kill (`taskkill //F //IM UnrealEditor.exe`), relaunch.
- `graphify_record observe` without `--derived-from` is an HONOR-SYSTEM surface (it cannot know
  who is typing). Directive 2 is what protects it. Automation must never touch it.
- BP spawning: use `/Game/X/BP_Y.BP_Y` (asset form). The `_C` class form fails via the bridge.

**Delegated Gardener (2026-07-07)**: you no longer wait for human heuristic approval.
`python -m core.gardener --tend` runs inside every dream_loop: doc-organ rules self-promote,
`approved (auto — implementation pending)` gate entries are YOUR branch-A work (capable
sessions write the gate function + its test), tombstones are final. If the human edits any
status to `vetoed`, the next tend demotes it automatically — never argue with a veto.

**No-blockers toolkit (2026-07-07)**: known env blockers -> `python -m core.unblock --ensure all`.
UNKNOWN blockers -> `python -m core.solver --blocker "<line>" --context "<verbatim>"` (fixes or
drafts the fix — never write a bare 'blocked' note). Zero-dependency floor work always exists:
the `Groundskeeping_floor` rehearsal candidate. Nightly rhythm is ARMED (00:45/01:00/02:15).
Doc drift check: `python -m core.doc_audit`.

**Level clobber recovery (2026-07-07)**: if preflight prints [4.55] DEMO LEVEL CLOBBERED
(umap md5 B734CFF5... = template bytes): taskkill //F //IM UnrealEditor.exe -> copy
Chimera/Content/Levels/L_RegolithYard.umap over chimeradefaultlevel.umap ->
`python -m core.unblock --ensure editor` -> verify with a regolith sleepwalk (5/5).
Root cause is FIXED (build_orchestrator seed-only) — if it recurs, something new is stamping
levels: run the solver with the evidence.
