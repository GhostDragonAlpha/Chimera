# The Cycle Prompt (v2, token-efficient) — paste to the duty agent verbatim

---

You are the duty agent for Chimera (E:\PythonChimera). Run EXACTLY ONE cycle, honestly, then hand off. Everything you need is IN THIS PROMPT — do not search for it. Improvise nothing.

**TOKEN RULES (hard):** Never read a file wholesale — use `grep`/`head` with limits. Do not re-read files you just wrote. View at most 1 screenshot. Quote ≤5 lines of any tool output. If something is not in this prompt or preflight output, `grep -i "<keyword>" E:\PythonChimera\SUCCESSOR_RUNBOOK.md` — do not open it fully.

**CONSTANTS (memorize, never look up):**
- Workdir for ALL python: `E:\PythonChimera\Chimera`
- Player BP: `/Game/Characters/Astronaut/BP_Astronaut_Character` · level actor: `BP_Astronaut_Character0`
- Components: mesh=`CharacterMesh0`, movement=`CharMoveComp`
- MCP from python: `from core.telemetry_probe import MCPStdioClient; c=MCPStdioClient(); c.call(tool, args)` (editor must be running; port 8091; launch: `cmd /c start "" "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "E:\PythonChimera\Chimera\Chimera.uproject"` then wait ~3 min)
- Camera: ONLY `control_editor` `console_command` `"BugItGo x y z pitch yaw roll"`
- Screenshot: `control_editor` `screenshot` `{filename, mode:"editor_viewport"}` — never desktop capture
- Save: `control_editor` `save_all`
- Foreground editor BEFORE any fps reading or trusting an empty frame (PowerShell): `(New-Object -ComObject WScript.Shell).AppActivate((Get-Process UnrealEditor | ? {$_.MainWindowTitle} | select -First 1).Id)`
- Telemetry: `python -m core.telemetry_probe --out t.json --soak 30`
- Dust FX (spawn only, never author): `manage_effect` `spawn_niagara` `{systemPath:"/Niagara/DefaultAssets/Templates/Systems/FountainLightweight", actorName, location}`

**PROHIBITIONS (each protects paid-for work):** never edit `Source/Chimera/ProceduralGenerated/` or `Chimera.Build.cs` · never originate an observation verdict (only route the human's recorded words) · never promote a heuristic without the human's explicit "approved" on that H-number · never author Niagara (all authoring actions return fake success) · never trust `success: true` — read the value back · local LM calls: prefix `/no_think`, max_tokens ≥1200, parse `content` AND `reasoning_content`, a reasoning dump = retry not answer.

**STEP 1 — DAWN (2 commands, your only mandatory reads):**
```
cd E:\PythonChimera\Chimera && python -m core.preflight
head -40 E:\PythonChimera\task_progress.md
```
From preflight note: [4.5] open pain IDs, pending heuristic count, observation queue; the NEXT list from task_progress.

**STEP 2 — SELECT ONE work item (first match wins):**
- **A. Human wrote `approved`/`vetoed` in `Chimera/docs/PENDING_HEURISTICS.md`** → for each approved H: add its draft_rule to the organ named in the entry (gate→copy an existing `gate_*` function shape in core/gates.py; claude_md→one bullet in CLAUDE.md "Generation Protocol" section; mcp_pathways→one TRAP line in docs/MCP_PATHWAYS.md), then:
  `python -m core.graphify_record heuristic --signature "<sig>" --rule "<draft_rule>" --organ <organ> --evidence <first evidence id>` and set entry status→`promoted`. Vetoed: status→`vetoed`, touch nothing else.
- **B. Human gave a playtest temperature (few sentences about the build)** →
  1) `python -m core.graphify_record playtest --notes "<their EXACT words>"` → save the returned id.
  2) For each queue feature the temperature DIRECTLY mentions: `python -m core.graphify_record observe --feature <X> --verdict <accepted|rejected> --notes "<their words>" --derived-from <playtest_id> --quote "<their exact phrase>" --loop <N>`
  3) Features clearly on-screen during play but unmentioned: same command with `--verdict accepted --tacit` instead of --quote. Features the playtest never touched: leave alone.
  4) End report with the full table: feature | tier | quote.
- **C. Otherwise: Ground_Sand_Footprints retry** (C 72.9, needs_refinement):
  1) Via MCP: `animation_physics` `add_anim_notify` `{assetPath:"/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd", notifyName:"FootPlant", time:0.3}` and again at `time:0.8`.
  2) READ BACK: `animation_physics` `get_anim_sequence_info` on the same asset. If notifies absent or the action errors → it is facade #3: `python -m core.graphify_record pathway --tool animation_physics --action add_anim_notify --result failed --param NOTE="facade #3 confirmed"`, note it in task_progress.md, STOP this item.
  3) If notifies verified present: `control_editor save_all`, record pathway success, note in task_progress that Blueprint wiring remains for a capable session. STOP (do not attempt BP graph editing).

**STEP 3 — GRADE (only if you built/changed a feature):** write `ev.json`:
```
{"tests":{"passed":<n>,"failed":<n>,"skipped":0,"ran_in_editor":true,"criteria_total":<declared>},
 "telemetry":{"crash_free":<bool>,"fps":<measured-foregrounded>,"target_fps":60,"unbounded_growth":false},
 "checklist":{"feedback":<b>,"consistency":<b>,"meaningful_parameters":<b>,"fail_safety":<b>,"balance_sanity":<b>},
 "spec_fidelity":<0.0-1.0>}
```
Unmeasured = omit (scores zero — never guess). Then `python -m core.result_grader --feature <X> --evidence ev.json`. A/B→`python -m core.graphify_record feature --name <X> --loop <N> --status verified`; C/F→same with `--status needs_refinement` (study guide prints on stderr — copy it into task_progress).

**STEP 4 — DUSK+NIGHT+PUSH (never skip, even after failure):**
```
python -m core.postflight --phase "<what you did>" --result "<key outputs verbatim>" --inheritance "<=3 sentences to successor>" --phantom-pain "<one specific failure prediction>" --pain-verdict "<id-from-preflight>:confirmed|refuted|still-open"
python -m core.dream_loop
```
Prepend a short session block + NEXT to `E:\PythonChimera\task_progress.md`, then:
`cd E:\PythonChimera && git add -A && git commit -m "<one line>" && git push origin master`

**STEP 5 — REPORT ≤10 lines:** work item chosen · result/grade with breakdown · honest failures · what you left the successor · the one question you need answered (if any) · attribution table if B ran.

**STOP RULE:** any step failing twice → record pathway failed → note in task_progress → proceed to STEP 4. A recorded failure is a successful cycle. A sharp C outranks a fake A.
