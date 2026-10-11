# Round-08 Steps 3b-4 — pack shipped; STOP at two walls (acceptance pin drift + store clobber)

Date: 2026-10-10 · Worker: Tiel · Status: **STOPPED before Steps 5-7** —
Step 3b is complete and verified; Step 4's re-pin is applied but the mandated
`acceptance.py` run (a) is red on pre-existing EXTERNAL reference-pin drift
and (b) destroyed 273 uncommitted lines another agent had added to the graph
store. Both walls need Qwen rulings. Nothing was committed.

## Step 3b — COMPLETE (all gates green)

- Patched generator run to real PACK_OUT (`tools/rig_factory_fit.py`, ROM
  overlay applied: "ROM overlay: 4 referee verdicts applied to the pack").
- `Saved/meshes/monkey_joints.bin` = `8ef83b7f1f5d707ab29ee1d5be8b944019d2c2e21a19a9aff32eac405dbf496f`
  — `cmp` BIT-EXACT vs `_scratch_gen/step2_pack.bin`.
- Diff vs backup (`_diff_step2.py` → `realpack_diff.txt`): joint tables
  J/AX/ROM/parents identical; 6102 verts changed (foot 2436 / hand 2538 /
  OTHER 1128); transitions spine_lower→ankle 888, spine_lower→wrist 647,
  tail_base→wrist 377, knee→ankle 311, elbow→wrist 215, wrist→elbow 203,
  ankle→knee 108, wrist→shoulder 46 (×2 sides); owner-changed 5590,
  w/j2/w2-only 512; share law max 2.98e-08.
  `diff realpack_diff.txt _scratch_gen/step2_diff.txt` → IDENTICAL.
  (The scope doc's prose "ankle_L→knee_L 100" was a typo — the recorded
  scratch artifact itself says 108; totals only sum with 108.)
- `Saved/meshes/monkey_joints.bin.pre_refit.bak` already existed (Sep 3), so
  the generator's built-in backup step created nothing new. Generator's
  companion outputs went to gitignored `.tmp/skeleton/` scratch (its standard
  behavior).

## Step 4 — re-pin applied; acceptance gate RED (wall 1, external)

- Single-line edit at `tools/creature_graph/data/creature_graph.json:580973`:
  `binding_sha256: 74b3ab04…c1662 → 8ef83b7f…496f` (verified `@@ -580973
  +580973 @@`, 1 insertion 1 deletion).
- `python tools/creature_graph/acceptance.py` → EXIT 1, dies in [item 6] at
  `import_reference.import_all()` with `PIN DRIFT for
  qudt.units::qudt/unit_PA.ttl` (run 2: `unit_SEC.ttl` — thread-order
  reporting). Full log: `acceptance_run1.txt`.
- Diagnosis (read-only audit → `pin_audit.txt`): **30 of 33 reference pins
  drifted** (all QUDT units/quantity-kinds + BodyParts3D HTML). Cause:
  `tools/reference_data/data/cache/` (gitignored) was EMPTY before this
  session — the acceptance run re-fetched live bytes from qudt.org today, and
  upstream re-published since the pins were recorded (pins.json, Sep 25,
  UNMODIFIED — `save_pins` never ran; SystemExit precedes it). The failing
  code path (`fetch_cache.ensure_cached`) reads only pins.json + cache +
  network; the pack binary and the store line are NOT inputs. The committed
  28/28 baseline (`acceptance_results.json`, run_utc 2026-09-15) predates the
  upstream drift window — this red is pre-existing/environmental, NOT caused
  by the pack fix. The code's own remedy is `--refresh`, explicitly "a human
  decision", and it rewrites `pins.json` — outside this worker's file scope.
  `--offline` cannot help (it verifies the same drifted cached bytes).

## INCIDENT — acceptance.py clobbered the graph store (wall 2)

`acceptance.py` → `build_graph.build()` + `g.save()` writes the canonical
store `tools/creature_graph/data/creature_graph.json` IN PLACE (`store.py:279`
— no backup, no temp). The run rebuilt it from the (clean) authored seeds,
destroying **273 uncommitted lines another agent had added** (pre-run
`git diff --numstat`: 273 insertions / 0 deletions; main hunk `@@ -603114,0
+603115,259 @@` = ~259 lines appended at the end of the objects dict, right
after `doc.workflow.coupled_native`, plus ~14 lines in other hunks). My
single-line pin edit was destroyed too.

Recovery attempted, in order:
1. Semantic diff of the clobbered file vs HEAD: objects/layout identical,
   relations multiset identical (order differs) — the rebuild reproduced HEAD
   content only; the 273 lines were NOT seed-derived.
2. Git index: stage-0 blob == HEAD (never staged). `git log --all` since
   Sep 20: no commits touching the store. Stashes: unrelated.
3. `git fsck --dangling`: only older store generations (largest relevant
   blob = Sep-17-era 657-object store, extracted to `.tmp_diagnostics/
   dangling_b43f.json`); no blob near the pre-clobber size.
4. VS Code / editor local history: no snapshot of the file.
5. ZCode session artifacts: no other session references the edit.
**The 273 lines are unrecoverable from this machine.** The owning agent must
re-apply from their own records (Qwen to coordinate).

State restored:
- Clobbered rebuild preserved: `creature_graph.json.clobbered-by-acceptance-1306`
  (sha256 `b6ffb7e2…3d12`).
- `git checkout HEAD -- tools/creature_graph/data/creature_graph.json`
  (byte-exact committed store), then the pin line re-applied. Current
  `git diff` for the file: exactly 1/1 (the binding_sha256 line).
- Collateral check: `docs/evidence/agent_fleet/SHIP/CREATURE_GRAPH/acceptance_results.json` UNCHANGED
  (run died before writing); `pins.json` UNCHANGED; `reference_store.json`
  UNCHANGED; only `data/cache/` (gitignored) gained today's fetched bytes.

## Structural finding for the re-pin design

The store's `current_asset` block (incl. `binding_sha256`) is GENERATED from
`tools/creature_graph/data/authored/project_program.json` (the seed still
carries 74b3ab04). Any future `build_graph.build()`/acceptance run reverts
the store pin. A durable re-pin belongs in the seed (+ rebuild) — Qwen's
call; the assignment scoped the edit to the store line only.

## Consequences for the procedure

- Step 4 gate ("acceptance fully green") cannot pass today without a human
  `--refresh` decision on the drifted upstream sources → STOP per procedure.
- Steps 5-6 (engine + browser) NOT started; pack + store-pin are in place and
  self-consistent if Qwen rules to proceed.
- Rollback path unchanged: restore
  `tools/game_shell/evidence/round-08/monkey_joints.bin.bak-74b3ab04` and the
  old pin hash `74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662`.
