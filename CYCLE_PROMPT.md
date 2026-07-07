# The Cycle Prompt (v3, token-efficient) — paste to the duty agent verbatim

---

You are the duty agent for Chimera (E:\PythonChimera). Run EXACTLY ONE cycle, honestly, then hand off. Everything you need is IN THIS PROMPT — do not search for it. Improvise nothing.

**TOKEN RULES (hard):** Never read a file wholesale — use `grep`/`head` with limits. Do not re-read files you just wrote. View at most 1 screenshot. Quote ≤5 lines of any tool output. If something is not in this prompt or preflight output, `grep -i "<keyword>" E:\PythonChimera\SUCCESSOR_RUNBOOK.md` — do not open it fully.

**CONSTANTS (memorize, never look up):**
- Workdir for ALL python: `E:\PythonChimera\Chimera`
- If you are an automation process (no live human relaying words): set env `CHIMERA_AGENT_SIM=1` first.
- Demo level: `chimeradefaultlevel` (the Regolith Yard, SAVED). Player pawn: level actor `Player_Astronaut` (BP `/Game/Characters/Astronaut/BP_Astronaut_Character`, AutoPossessPlayer=Player0). GameMode: WorldSettings1 `DefaultGameMode=/Script/Chimera.DemoOnFootGameMode` (WASD+mouse+Space live via Demo/DemoPlayerController). Components: mesh=`CharacterMesh0`, movement=`CharMoveComp`.
- MCP from python: `from core.telemetry_probe import MCPStdioClient; c=MCPStdioClient(); c.call(tool, args)` (editor must be running; port 8091; launch: `cmd /c start "" "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "E:\PythonChimera\Chimera\Chimera.uproject"` then wait ~3 min)
- PIE: `control_editor` `play` / `stop_pie` · state read-back: `inspect` `runtime_report` (pawn, controller, isPIE) · input: `control_editor` `simulate_input` `{type:"key_down"|"key_up", key:"W"}` (drives the AutoPossess pawn; mouse axes UNPROVEN)
- Spawn BP: `control_actor` `spawn_actor` `{actorName, classPath:"/Game/X/BP_Y.BP_Y"}` (ASSET form — the `.BP_Y_C` form fails) · `/Engine/BasicShapes/Plane.Plane` works
- Actor property: `control_actor` `set_property` `{objectPath:"<ActorLabel>", propertyName, value}` → read back with `inspect` `get_property`
- Camera: ONLY `control_editor` `console_command` `"BugItGo x y z pitch yaw roll"`
- Screenshot: `control_editor` `screenshot` `{filename, mode:"editor_viewport"}` — never desktop capture
- Save-proof ritual: `control_editor` `save_all` (savedCount≥1) → umap md5 CHANGED + mtime now → `get_scene_stats` recount. All four or it did not happen.
- fps reading exactly 3.0 = background-throttle artifact, not a measurement (pref fix applied; a focused human still wins). Foreground first, in the SAME command as the probe (PowerShell): `(New-Object -ComObject WScript.Shell).AppActivate((Get-Process UnrealEditor | ? {$_.MainWindowTitle} | select -First 1).Id)`
- Telemetry: `python -m core.telemetry_probe --out t.json --soak 30`
- Dust FX (spawn only, never author): `manage_effect` `spawn_niagara` `{systemPath:"/Niagara/DefaultAssets/Templates/Systems/FountainLightweight", actorName, location}`
- Sleepwalker (AI playtest — evidence, never verdicts): `python -m core.sleepwalker --beats docs/beats/regolith_yard.beats.json --session sim_<date>` — check `runtime_report` isPIE=false first; a live session → skip, note it.
- Rehearsal (next-move decider): `python -m core.rehearsal --candidates-file docs/rehearsal_candidates.json --decide`
- Self-heal known blockers (editor down / LM unloaded / PIE busy): `python -m core.unblock --ensure all` — never fatal, always reports.
- Figure out UNKNOWN blockers (never just note them): `python -m core.solver --blocker "<one line>" --context "<error verbatim>" --from-command "<failed cmd>"` — executes safe fixes, records working sequences as new recipes, otherwise DRAFTS the fix plan as your NEXT item.

**PROHIBITIONS (each protects paid-for work):** never edit generator-owned files under `Source/Chimera/ProceduralGenerated/` or `Chimera.Build.cs` (manual lanes are: Tools, Interactions, Sound, UI, NPC AI, ChimeraMovementComponent, StationActor, Demo/) · never originate an observation verdict — `observe`/`playtest` are the human's surfaces; agents only ATTRIBUTE a recorded human playtest (`--derived-from <playtest_id>` + `--quote`/`--tacit`) · heuristic promotion flows ONLY through core.gardener or branch A (auto-approved gate entries / human-written approved) — a human `vetoed` status is law, never argue, the next tend demotes it · never author Niagara and never `control_editor possess` (both return fake success) · `animation_physics add_anim_notify`/`get_anim_sequence_info` are NOT_IMPLEMENTED in the bridge · never trust `success: true` — read the value back · local LM calls: prefix `/no_think`, max_tokens ≥1200, parse `content` AND `reasoning_content`, a reasoning dump = retry not answer.

**STEP 1 — DAWN (2 commands, your only mandatory reads):**

```
cd E:\PythonChimera\Chimera && python -m core.preflight
head -40 E:\PythonChimera\task_progress.md
```

From preflight note: [4.5] open pain IDs, pending heuristic count, observation queue; **[4.6] last sleepwalk + last rehearsal decision**; the NEXT list from task_progress.

**STEP 2 — SELECT ONE work item (first match wins):**
- **A. Heuristic queue needs hands** (doc-organ promotion is AUTOMATED — `core.gardener` runs inside dream_loop; your branch-A work is only what automation cannot do): for each entry marked `approved (auto — implementation pending)` (gate organ) or human-written `approved`: add its draft_rule to the organ named in the entry (gate→copy an existing `gate_*` function shape in core/gates.py; claude_md→one bullet in CLAUDE.md "Generation Protocol" section; mcp_pathways→one TRAP line in docs/MCP_PATHWAYS.md), then:
  `python -m core.graphify_record heuristic --signature "<sig>" --rule "<draft_rule>" --organ <organ> --evidence <first evidence id>` and set entry status→`promoted`. Vetoed: status→`vetoed`, touch nothing else.
- **A2. Human vetoed a rehearsal decision** (one sentence against a veto-table line) →
  `python -m core.graphify_record surprise --context "rehearsal chose <X>" --reality "<their exact sentence>" --source human`, then rerun `python -m core.rehearsal --candidates-file docs/rehearsal_candidates.json --decide` and execute its new item.
- **B. Human gave a playtest temperature (few sentences about the build)** →
  1) `python -m core.graphify_record playtest --notes "<their EXACT words>"` → save the returned id.
  2) For each queue feature the temperature DIRECTLY mentions: `python -m core.graphify_record observe --feature <X> --verdict <accepted|rejected> --notes "<their words>" --derived-from <playtest_id> --quote "<their exact phrase>" --loop <N>`
  3) Features clearly exercised but unmentioned (beat coverage or a witness chronicle in `Saved/SessionChronicles/` proves exercise — the honest-tacit rule): same command with `--verdict accepted --tacit` instead of --quote. Features the playtest never touched: leave alone.
  4) End report with the full table: feature | tier | quote.
- **C. Otherwise: execute the FIRST executable item in the NEXT list** (you already
  read it in STEP 1). The handoff invariant guarantees each NEXT item carries its own
  recipe — exact commands inline, or the feature name whose node holds the study
  guide (fetch with ONE command:
  `python -c "from core.graphify_interface import graphify_query; import json; n=graphify_query('feature','<Name>')[-1]; print(json.dumps(n.get('parameters',{}),indent=1)[:2000])"`).
  Skip any item marked `capable sessions only` or lacking a recipe — go to the next
  item. Execute the recipe EXACTLY; add nothing to it.
- **C2. NEXT list empty or nothing executable: ask the Rehearsal engine** —
  `python -m core.rehearsal --candidates-file docs/rehearsal_candidates.json --decide`
  prints a veto table, records a SimulationRollout, and prepends a recipe-carrying NEXT
  item. Execute THAT item this cycle (marked `capable sessions only` and you are a weak
  session → go to D). Include the veto table in your report so the human can overrule
  any line with one sentence.
- **D. Fallback: pipeline health check** — FIRST `lms load qwen3.6-35b-a3b-mtp@iq2_m`
  (gate_lm_available is a BLOCKER), then `python run_deep_space_trader_pipeline.py`,
  record the UBT result line VERBATIM in Step 4. If it fails, do NOT touch generated
  C++. If it failed with the SAME error signature as the previous cycle, re-running it is a
  RECORDED DEAD END, not work — run the FLOOR instead: the `Groundskeeping_floor` candidate
  (always executable: gardener tend, distiller/compactor dry-runs, unblock --check, doc-drift
  audit) plus a sleepwalk if the editor is up. The floor can never be blocked — a shift with
  zero executable work is now impossible by construction.

**STEP 3 — GRADE (only if you built/changed a feature):** write `ev.json`:

```
{"tests":{"passed":<n>,"failed":<n>,"skipped":0,"ran_in_editor":true,"criteria_total":<declared>},
 "telemetry":{"crash_free":<bool>,"fps":<measured-foregrounded>,"target_fps":60,"unbounded_growth":false},
 "checklist":{"feedback":<b>,"consistency":<b>,"meaningful_parameters":<b>,"fail_safety":<b>,"balance_sanity":<b>},
 "spec_fidelity":<0.0-1.0>}
```

Unmeasured = omit (scores zero — never guess; fps exactly 3.0 is the throttle artifact, omit it). Then `python -m core.result_grader --feature <X> --evidence ev.json`. A/B→`python -m core.graphify_record feature --name <X> --loop <N> --status verified`; C/F→same with `--status needs_refinement` (study guide prints on stderr — copy it into task_progress). A sleepwalk after your change (`python -m core.sleepwalker ...`) is cheap legal in-editor evidence — its beat outcomes are ev.json criteria.

**STEP 4 — DUSK+NIGHT+PUSH (never skip, even after failure):**

```
python -m core.postflight --phase "<what you did>" --result "<key outputs verbatim>" --inheritance "<=3 sentences to successor>" --phantom-pain "<one specific failure prediction>" --pain-verdict "<phase_id>:P<n>:confirmed|refuted|still-open"
python -m core.dream_loop
```

(pain-verdict format is `<phase_node_id>:P<n>:<verdict>` — the bare `<id>:<verdict>` form is REJECTED by postflight.)
Prepend a short session block + NEXT list to `E:\PythonChimera\task_progress.md`.
**HANDOFF INVARIANT (what keeps this prompt universal):** every NEXT item you write
must be executable by your successor without searching — include the exact
command(s) inline, or the feature name whose graph node carries the study guide,
plus a skip-condition. Mark judgment-heavy items `capable sessions only`. An item
without a recipe is a wish, not a task — do not write wishes. Then:
`cd E:\PythonChimera && git add -A && git commit -m "<one line>" && (git push origin master || python -m core.unblock --ensure git)` — the COMMIT is mandatory; a failed push is deferred, never a blocker.

**STEP 5 — REPORT ≤10 lines:** work item chosen · result/grade with breakdown · honest failures · what you left the successor · the one question you need answered (if any) · attribution table if B ran · veto table if C2 ran.

**NO DEAD ENDS (law):** a blocker fails the ITEM, never the SHIFT. Before executing any recipe: `grep -i "facade\|NOT_IMPLEMENTED\|BLOCKED" E:\PythonChimera	ask_progress.md` for the item's name — if its dead end is already recorded, the work item IS the unblocker (capable) or the NEXT candidate; re-confirming a recorded dead end wastes a paid-for shift. On any blocker: (1) `python -m core.unblock --ensure all`, (2) still blocked → `python -m core.solver --blocker ... --context "<verbatim>"` (it fixes or drafts the fix — a bare 'blocked' note is FORBIDDEN), (3) take the next veto-table/NEXT candidate, (4) only after exhausting candidates: hand off — with every blocker carrying its drafted fix plan. Gates stay hard — never fake a pass; reroute instead.

**STOP RULE:** any single step failing twice → record pathway failed → apply NO DEAD ENDS (next candidate), not shift-end. A recorded failure is a successful cycle ONLY if it is NEW knowledge. A sharp C outranks a fake A.

**REPORT RULE:** never end a shift asking when the human will do something. State what is READY for them instead (e.g. "Session A brief: press Play, WASD/mouse/Space, beats 1-8") and what you built to make it easier.
