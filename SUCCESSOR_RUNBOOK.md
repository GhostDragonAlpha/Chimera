# SUCCESSOR RUNBOOK — recipes, not principles

> Written 2026-07-06 for a **less capable heir**. If you are a powerful model, read
> CLAUDE.md and think. If you are not sure which you are, follow this file EXACTLY and
> improvise NOTHING. Every recipe here was paid for. The traps section is blood.

## PRIME DIRECTIVES (absolute — violating these destroys paid-for work)

1. **Never edit** anything under `Source/Chimera/ProceduralGenerated/` or `Chimera.Build.cs`. Fix generator templates in `core/game_code_generator.py` or do not fix at all.
2. **Observation is AUTOMATED** (full-automation amendment 2026-07-07 — human verification requirements are removed). Features finish under automated evidence: `graphify_record observe --derived-from <simtest_id>` attributes sleepwalker/telemetry/result-grading evidence. Never fabricate an observation without exercise evidence in the graph.
3. **Heuristic promotion is automated** (delegated Gardener): doc-organ heuristics with a draft rule + evidence self-promote via `dream_loop --tend`; gate-organ approvals queue for a capable cycle. No human approval step.
4. **Never write graph mutations by hand.** Only `python -m core.graphify_record ...` or the `record_*` helpers.
5. **Never trust `success: true`.** Read the value back. If you cannot read it back, treat it as NOT done and say so. (This is AUTOMATED verification — the read-back IS the measure — not a human check.)
6. If a recipe fails **twice**, record the failure (`graphify_record pathway ... --result failed`), write it in task_progress.md, and move to the next task. Do not invent alternatives.

## SESSION RECIPE (run in this order, always)

```powershell
cd E:\PythonChimera\Chimera
python -m core.preflight          # DAWN. Read [4.5] carefully: Will, pains, queues. Opens with the [CAPCOM] operator channel.
python -m core.capcom brief       # Operator channel: unread signals + your OPERATOR_INBOX notes. Leave a note back: python -m core.capcom tell "..."
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

1. **Promote heuristics (automated — no human approval step).** `python -m core.dream_loop`
   runs the delegated Gardener (`--tend`): doc-organ heuristics with a draft rule + evidence
   self-promote; gate-organ approvals queue for a capable cycle (add the gate function in
   core/gates.py + its test). Subsumed entries tombstone; automated rejection is final.
2. **Run the automated observation sweep** — this is how features finish; the measure is
   the automated system (sleepwalker/telemetry/result grading), NOT a human:
   a. Produce holistic evidence: sleepwalker beats over the build
      (`python -m core.sleepwalker --beats docs/beats/<demo>.beats.json --session <name>`),
      recorded as a SimPlaytest. That simtest IS the temperature.
   b. **Attribute** across the observation queue (`python -m core.collapse_proxy
      --from-simtest <simtest_id> --valence accepted` sweeps accepted-tacit; a rejection
      indicts only what the simulation evidence names). Per feature, decide ONE tier:
      - **Directly implicated** — the sim evidence names it:
        `... observe --feature <X> --verdict <accepted|rejected> --notes "<evidence>" --derived-from <simtest_id> --quote "<the sim's phrase>" --loop <N>`
      - **Exercised but unmentioned** — on screen / in play, no failure. Silence passed:
        `... observe --feature <X> --verdict accepted --derived-from <simtest_id> --tacit --loop <N>`
      - **Not exercised** — the sim couldn't have touched it. LEAVE IT QUEUED.
   If you are a weaker model: do tier 1 (direct sim mentions) ONLY; leave tacit calls
   to a capable session.
3. **A human MAY steer DIRECTION or override any line** (optional — never WAIT for it): a
   one-sentence steer is recorded `graphify_record surprise --source human` and flips the
   feature; a supplied temperature is `graphify_record playtest --notes "<verbatim>"`. The
   automated observation is complete on its own; human input only redirects, never gates.
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

- **Postflight refused you with `!! WHY GATE`** — it means the claim has no evidence
  chain that reaches PHYSICS or THE HUMAN. It is NOT saying your work is bad. Do this,
  in order, and do NOT reach for the waiver:
  ```powershell
  python -m core.why --feature <X> --loop        # SEE where the chain stops
  python -m core.beat_lint --beats docs\beats\<x>.beats.json    # ALWAYS lint first
  python -m core.sleepwalker --beats docs\beats\<x>.beats.json --session obs_<X>
  python -m core.collapse_proxy --from-simtest <simtest_id> --valence accepted
  ```
  Then re-run postflight. If the chain SHOULD already reach evidence that exists but
  the link was never recorded: `python -m core.why --backfill --apply`.
  `--why-waiver "<reason>"` exists and is READ — "nothing measured it" is the finding,
  not the exception.
- **Postflight refused you with `RESEARCH GATE ... unwaivable`** — you are on a "Build
  toward the seed" task. Those CANNOT waive research: the task's premise is that the
  thing does not exist, so nothing in this repo can supply the answer. Cite real
  sources: `--researched "UE5.8 <Subsystem> docs; <shipped game that solved it>; DSL bible"`.
  Every other task can still waive.
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
- **Evolve a brain on the GPU (creature locomotion):** ALWAYS in a membrane, ALWAYS
  unbuffered to a log.
  `cd E:\PythonChimera\Chimera`
  `python -c "import sys;sys.path.insert(0,'.');import core.membrane as mb;print(mb.seal('run1'))"`
  `cd E:\chimera_membranes\run1\Chimera`
  `$env:PYTHONUNBUFFERED=1; python -u -m core.trainer --domain core.trainables.brain_gpu --objective docs/objectives/brain_gpu.json --pop 1024 --gens 300 *> train.log`
  (~60 min on the 4090.) Then bring the winner home: copy
  `docs/objectives/brain_gpu.trained.json` back to `E:\PythonChimera\Chimera\...`,
  `python -m core.membrane burn run1`, commit the trained json.
- **Witness a gait (a number is NOT proof — H-14):**
  `python -m core.gait_mj --trained docs/objectives/brain_gpu.trained.json --png out.png`
  Read the PERIODICITY (≥0.5 = a real cycle) and the ROBUSTNESS block (distance must
  barely move under the perturbations). Then Read the PNG.
- **Iterate the OBJECTIVE, never the artifact:** the trainer prints `PINNED` walls at
  the end. Those are the next edit to `docs/objectives/<f>.json`. Never hand-edit a
  `.trained.json`.

## TRAPS — NEVER DO (each cost a real session real hours)

- **ONE ROLLOUT IS A COIN TOSS.** Never trust a single-rollout fitness in a contact-rich
  (chaotic) sim: a 1-micron start change once swung a result 5.5 body lengths, and an
  80,000-eval "champion" scored WORSE THAN UNTRAINED when measured honestly. Always score
  N randomized restarts and keep the WORST (`brain_gpu.py` does 16). This is a
  correctness rule, not a nicety — it is the whole reason the GPU is used.
- **Python piped through `Select-String` (or any pipe) BLOCK-BUFFERS** — you see NOTHING
  until the process exits, so a 35-min run looks dead. Use `python -u ... *> file.log`
  and `tail`/Monitor the file. Never diagnose a "hung" training run before checking this.
- **`njmax`/`nconmax` in `mujoco_warp.put_data` are PER WORLD, not total.** Passing
  `nworld * 192` asks for 750× too much and OOMs 24 GiB. Measure the real max
  (this creature: 48 constraint rows, 9 contacts) and add headroom (192/64).
- **Do NOT force `MUJOCO_GL=egl` on Windows** — egl is a Linux backend and breaks the
  working default renderer. Leave it unset; `mujoco.Renderer` works out of the box here.
- **A number you INHERITED is not a number you CHOSE.** `TORQUE=22` carried from the CPG
  walker was 35 N·m/kg (10× a human hip) and flung the creature 3.4 km up. Sanity-check
  every physics constant against a real-world referent before trusting a run.
- **pybullet physics is CPU-ONLY, forever.** Do not try to GPU-accelerate it (OpenCL was
  promised in 2006, never shipped). The GPU path is `mujoco-warp`. Bodies are NOT
  GPU-batchable (it batches N copies of ONE model) — morphology on CPU, brains on GPU.

- **A STRING IS NOT A CITATION.** `derived_from` / `evidence_ids` name NODE IDS, and
  every real id is `<type>_<sha256[:16]>` minted by a `record_*` helper. Never type one
  by hand. 14 live Observations say `verdict=accepted` while citing
  `session_continuous_workflow_202607…` and `pie_dropactor_20260708` — ids that never
  existed — because every consumer tested TRUTHINESS, not resolution. Two
  `evidence_ids` entries are ENGLISH SENTENCES. `record_observation` now REFUSES an
  unresolvable id; that refusal is correct, and the fix is to run the beat, not to
  invent an id. **The `record_*` helpers return their REFUSAL as a string — a refusal
  is not an id; check for the `rejected_` prefix before using a return value.**
- **NEVER end a why-chain at an LLM.** A model's opinion is another CLAIM, so the walk
  recurses past it: `VisualVerification` proves RECORDED, not MEASURED. The deleted AAA
  grader was fraud for exactly this — it terminated at the model's own adjective.
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

## THE STANDING QUEUES (automated — you answer them with evidence)

Preflight [4.5] lists them every dawn: pending heuristics (docs/PENDING_HEURISTICS.md)
and the Observation queue. Both are worked by AUTOMATION now (full-automation amendment):
`dream_loop --tend` rules the heuristic queue; the observation queue is answered by
attributing sleepwalker/telemetry evidence (task 2). A human may redirect with one
sentence, but nothing waits for one — never leave a queue untouched for lack of a human.

## THE SHAPE OF A GOOD SESSION

One task, honestly measured, honestly graded, honestly recorded, pushed. A C with a
sharp study guide is worth more than a fake A. The system was built so that your
successor inherits your lessons — write your Will like you mean it.


## ADDENDUM 2026-07-07 — the Sleepwalker era (recipes for the new organs)

**New PRIME DIRECTIVE 7**: automation runs with `CHIMERA_AGENT_SIM=1` set. The sentinel
enforces that every observation is EVIDENCE-BACKED (`--derived-from <simtest_id>`) — the
automated sleepwalker/telemetry evidence IS the measure. `core/sleepwalker.py` sets it for
itself. An observation without exercise evidence in the graph is forbidden.

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
(kind sim_rejection). The sim evidence IS the observation; a human sentence may still
redirect it, but the automated signal stands on its own.

**New traps (paid for on 2026-07-06):**
- `Config/DefaultInput.ini` has NO trailing newline and ends with a `[GameInputPlatformSettings...]`
  section. Appending blindly corrupts it AND lands mappings in the wrong section — insert inside
  `[/Script/Engine.InputSettings]`.
- The editor overwrites `EditorPerProjectUserSettings.ini` on graceful shutdown. To make a
  settings edit stick: write the ini, FORCE-kill (`taskkill //F //IM UnrealEditor.exe`), relaunch.
- `graphify_record observe` REQUIRES `--derived-from <simtest_id>` — an observation must cite
  the automated evidence it rests on. Evidence-less observation is forbidden (Directive 7):
  the simtest/telemetry node is what makes the verdict real.
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
