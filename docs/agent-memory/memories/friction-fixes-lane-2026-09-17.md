---
name: friction-fixes-lane-2026-09-17
description: FRICTION-FIXES lane shipped (review findings F1-F4 closed, branch
  lane/friction-fixes-20260917 @ 88196e03) + the upstream connector double-merge
  defect on master that errors test_batch/test_batch_muscle
metadata:
  node_type: memory
  type: project
  originSessionId: sess_34fd4830-fea1-4446-8e42-6b104eda6f9c
---

The FRICTION-FIXES lane (2026-09-17) closed all four independent-review findings on the published Coulomb friction slice and pushed `lane/friction-fixes-20260917` (tip 88196e03, based on master aa79903c): F1 exact-rest sign fix in `friction_solve` + `friction_unit.cpp` seam (27 checks; negative control fails on the old sign; NOTE: the engine classes use implicit default-private so the seam needs `#define class struct` alongside `#define private public`), F2 derived critical-mu pair (settle bisection 0.78523; demanded-ratio 0.78201043433 reproduces the frozen settle number exactly; mu=0.6 → 2253 slide ticks exact match; mu=0.8 holds), F3 per-tick impact-cone guard, F4 live scope string (live qualifier intentionally not run — operator scene on 8127). Receipt: `tools/science_funnel/validation/coupled_friction_fixes_20260917/receipt.json`. Every frozen reference stayed bit-exact through THREE master collisions (intake lanes landing every ~15 min); the collision protocol (rebase, take upstream on graph JSONs, re-run idempotent `.tmp/admit_friction_fixes.py` + `build_graph.py`, requalify via the frozen gate) is scripted in the worktree at `E:\ChimeraWork\friction-fixes-20260917`.

**UPSTREAM DEFECT CLOSED (was open on master aa79903c)**: `tools/science_funnel/batch/connectors.py` merged lane connector modules TWICE (the 2f0b0ff8 unifier loop AND `_load_lane_modules()` from the muscle integration), refusing `connector_id_collision: guimaraes_arch` on clean checkouts. The integrator's dedupe edit had gone UNCOMMITTED through the gait publish (the publish script only staged graph JSONs + validation — a lesson: put every verified fix in the stage list). Fixed and pushed as master commit 9c6c2853 ("single lane loader, dynamic reprove dirs"), verified by the friction lane's rebase cycle finding it live.

**INTEGRATED 2026-09-17**: merged to master at 7415fa29 — graph JSONs took the LANE side (its rebase base WAS the current master's graph, so their admission records rode in with zero loss; registry files kept ours/the fix), graphify HONEST, evidence 11/11, funnel 176→192 OK after the full four-lane set. F1–F4 are now closed ON MASTER with every frozen reference bit-exact.

**How to apply:** when a lane report claims "suite green" after 2026-09-17 ~19:00Z, check whether the double-merge was fixed; when testing private members of these engine classes, use the class->struct seam; PowerShell gotchas that cost time here: `Convert-Json` (correct: `ConvertFrom-Json`), `>` redirection writes UTF-16 (use `[IO.File]::WriteAllText`), and capturing `git merge-base --is-ancestor` result needs `$LASTEXITCODE`, not output.
