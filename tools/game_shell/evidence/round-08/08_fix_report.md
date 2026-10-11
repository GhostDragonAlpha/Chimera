# Round-08 Steps 4b-7 — durable seed re-pin, rebuild, reload, live verification, regression

Date: 2026-10-10 · Worker: Tiel · Per Qwen's rulings on `08_step4_incident.md`
((a) proceed despite environmental acceptance red, no acceptance.py, no
--refresh; (b) clobber stands; (c) durable re-pin in the seed + rebuild with
backup guard). Nothing committed, nothing pushed.

## Step 4b — durable seed re-pin (backup-guarded)

Seed line (was the only 74b3ab04 occurrence in the seed; `mesh_sha256`
`550a5b3e…fa3c` untouched, verified before and after):

```diff
 tools/creature_graph/data/authored/project_program.json  (git diff: exactly 1/1)
-      "binding_sha256": "74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662",
+      "binding_sha256": "8ef83b7f1f5d707ab29ee1d5be8b944019d2c2e21a19a9aff32eac405dbf496f",
```

Backup guard: pre-rebuild store copied to
`creature_graph.json.pre-rebuild-8ef83b7f` (sha256
`be444723f1102b41fd9cf6b99fe69dfdd54db03c522ce2e0bb4ee20939483b61`, identical
to the live file at backup time).

Rebuild: canonical path only — `build_graph.build(with_reference=True)` +
`g.save()` (the same calls acceptance.py:65-66 makes; NO `import_reference`
step, NO network). Saved to scratch
(`_rebuild_seedrepin.json`), verified, then installed byte-identical to
`tools/creature_graph/data/creature_graph.json` (sha256
`d214be7f2a9ae8d564293eba3f3ebbbd9197dd706cab39641f9fdb732e5b78c4`).
`build()` runs `g.check()` internally and raises on error — build success is
itself a check pass.

### Rebuild verification — DEVIATION FROM THE LITERAL RULING (documented)

The ruling's verify-(i) "git diff vs HEAD = exactly 1/1" and verify-(ii)
"diff vs backup = ZERO" are **byte-wise impossible via the canonical build
path**, independent of this edit, and the prior run's own
`_rebuild_dryrun.json` (built 13:22 from the UNMODIFIED seed) proves it:

1. `save()` always stamps `meta.saved_utc = now` (store.py:282).
2. `meta.built_from["authored/project_program.json"]` records the raw
   working-tree bytes; `core.autocrlf=true` makes that the CRLF hash
   (`e9f08b20…` pre-edit) while HEAD recorded the LF hash `7e1f6bfd…`
   (proven: `git show HEAD:…project_program.json | sha256sum` = `7e1f6bfd…`;
   the other five seeds match because the Sep-17 build machine had that one
   file as LF). Any edit to the seed changes this hash by construction.
3. `meta.reference_join.source` embeds the BUILD MACHINE's absolute path
   (HEAD: `E:\ChimeraWork\codex-graph-workflow-20260916\…`; here:
   `E:\PythonChimera\…`).
4. `meta.loaded_schema_version` exists in HEAD only because HEAD was saved
   via load→save (store.py:306); a fresh build+save has no such field.
5. Object/relation INSERTION ORDER differs: HEAD was built by an older
   build_graph that joined reference objects before `project_program.json`
   (join block at object idx 183); the current code appends them after all
   authored objects (idx 4513). Content-neutral: `CreatureGraph.load` +
   `check()` and the engine are order-insensitive; `layout` is equal.

The ruling's INTENT — the rebuild must reproduce HEAD+pin content exactly and
introduce nothing else — was verified with strict equivalence instead:

* **(a) rebuild vs dryrun** (`diff _rebuild_dryrun.json _rebuild_seedrepin.json`):
  exactly 3 lines — `built_from` seed hash (`e9f08b20→bbf95833`, my seed
  edit), `saved_utc`, and the pin line (`74b3ab04→8ef83b7f`). The seed edit
  is the ONLY input change; the build is deterministic.
* **(b) rebuild vs backup** (`_semantic_cmp.py`): objects 5885/5885, same key
  set, **0 objects with different values** (the pin now agrees); relations
  9147/9147 **multiset equal**; layout **equal**. Byte diff (715671 lines) is
  fully accounted for by order + the 4 meta fields above
  (`_dryrun_vs_backup.diff` shows the identical pattern for the unmodified
  seed).
* git diff of the store vs HEAD: 359960/359961 (the reorder). This is what
  the canonical path produces on this machine; the 273-line clobber run
  would have produced the same reorder.

**`graph.check()` gate** (exact creature_scene.py:14-15 call):
`CreatureGraph.load('tools/creature_graph/data/creature_graph.json').check()`
→ `[]` — no graph_invalid, no EXTERNAL reference-pin errors. Store
`current_asset`: binding `8ef83b7f…496f`, mesh `550a5b3e…fa3c`. Pack on disk
re-verified `8ef83b7f1f5d707ab29ee1d5be8b944019d2c2e21a19a9aff32eac405dbf496f`.

## Step 5 — reload + live numeric verification

Old stack verified as ours before stopping: PID 40524 =
`.tmp\body-engine\Release\chimera_engine.exe 8110 --hidden 1600 900
--no-restore`, PID 21248 = `python.exe -B tools/game_shell/server.py 8210
--engine http://127.0.0.1:8110`. Killed only those two. Relaunched via
`powershell -File tools/science_funnel/run_creature.ps1` (full build +
admission). New stack: engine PID 65724 (:8110), shell PID 72228 (:8210),
runtime.json graph_hash `b0e30d6c…`.

* `scene.json` `source_binding_sha256 = 8ef83b7f…496f` — NEW pack admitted.
* `/tick_state` `body_model = JNT3_hierarchical`.

Live probes (`_live_verts_probe_r2.py` → `08_live_verts_probe_r2.txt`;
all poses by NAME via `/tick_pose`, each reset after; sim predictions from
`08_step3_scope.md`):

| probe | live result | sim / pre-fix |
|---|---|---|
| rest vs mesh | max dev 4.77e-07 (float32 rounding; binding law exact in f64 per pack probe) | bit-identical intent |
| knee_L=40 sole mean | **1.4474** (max 1.6269) | sim 1.447 · pre-fix 0.1641 |
| knee_L=40 foot mean | 1.4033 | sim 1.403 |
| knee_L=40 shin box | 0.2753 | sim 0.275 (crease relocated) |
| knee_L=40 shin UNCHANGED-binding (53 verts) | **0.2247** | sim 0.225 = pre-fix 0.225 (identical) |
| ankle_L=30 sole mean | **0.5090** | sim 0.509 |
| ankle_L=30 foot mean | 0.4507 | sim 0.451 |
| wrist_L=40 hand_L mean/max | **0.6251 / 1.0811** | sim with the SAME box: 0.6251/1.0811 exact (scope table's 0.659 used a slightly different box; pre-fix 0.017) |
| tail_mid=30 tail_mid band | mean 0.6413 max 1.4430 | coherent sweep |
| tail_mid=30 tail_tip band | mean 1.1435 max 1.3808 | follows |
| tail_mid=30 tail_base band (seam blend) | mean 0.2132 | tail_base owner band 1085→331 (−754 = −377/side, as predicted); mid/tip bands untouched |
| every pose reset | max dev **0.00e+00** | exact return to rest |

## Step 6 — visible verification + regression (browser drive)

`_drive_r08_02b.py` (headless Chromium, fresh profile, real pointer events):

* **wake_the_cell: PASSED**, pageErrors=0. Verdict: "PASSED — you pressed,
  the cell woke, and the water healed itself. the world is real." (the
  lesson's exact pass_line). Note: a naive 50000 N belly hold RUPTURES the
  cell (RUPTURE_PA=500k fires while holding — first driver attempt recorded
  this honestly in the superseded v1 run); v2 presses 15000 N and releases
  while watching the page's own pressure gauge.
* **bend_the_knee: PASSED**, pageErrors=0. Verdict: "PASSED — the creature
  obeyed a wish, not a touch." knee_L=40 via the lesson's own slider+post;
  engine `body_model=JNT3_hierarchical` at capture.
* Screenshots: `08_02_knee_bent_foot_follows.png` (knee 40°),
  `08_02_knee_0.png` (rest, same view), `08_02_wake_passed.png`.
  Machine record: `08_02_drive.txt`.
* Visual claims verified numerically (this session cannot view images):
  rest-vs-posed screenshot diff = 18647 px (1.6%), 78.8% of them in the
  lower-45% legs/feet band — the foot visibly follows. Triangle quality
  (knee_L=40, both packs, offline sim): OLD pack **39 pose-induced slivers**
  (q<0.02, fine at rest) and real-edge stretch max **58.4×** (p99.9 17.2×);
  NEW pack **0 slivers**, max 5.04× (p99.9 1.92×) — the stretched-triangle
  distortion is gone.
* Stack left RUNNING at rest: engine 65724 (:8110), shell 72228 (:8210,
  HTTP 200), `/verts` at rest = mesh (4.77e-07). http://127.0.0.1:8210 is
  playable.

## Rollback path

1. Pack: copy `tools/game_shell/evidence/round-08/monkey_joints.bin.bak-74b3ab04`
   → `Saved/meshes/monkey_joints.bin`.
2. Seed: revert the one-line diff in
   `tools/creature_graph/data/authored/project_program.json`
   (`git checkout --` it).
3. Store: copy `creature_graph.json.pre-rebuild-8ef83b7f` (this directory)
   → `tools/creature_graph/data/creature_graph.json` (HEAD+old-pin bytes),
   or `git checkout HEAD -- tools/creature_graph/data/creature_graph.json`
   to drop the pin too.
4. Restart the stack with `run_creature.ps1`.

## Incident summary (for escalation)

On 2026-10-10 the mandated `acceptance.py` run rebuilt the canonical store
IN PLACE (store.py:279 `save()` — no backup, no temp) from the clean authored
seeds and destroyed 273 uncommitted lines another agent had added to
`tools/creature_graph/data/creature_graph.json`; the lines are unrecoverable
from this machine (full record: `08_step4_incident.md`; clobbered bytes
preserved in `creature_graph.json.clobbered-by-acceptance-1306`). The hazard
is structural: any `build_graph.build()`/acceptance run rewrites the store
from the seeds, so hand-edits to the store are silently lost — this round's
fix moves the pin into the authored seed (where it now survives any rebuild)
and every future store edit should go through the authored seeds plus a
backup-guarded rebuild, never by editing the generated file (and ideally
`save()` should write atomically via temp+rename with a pre-save backup).
