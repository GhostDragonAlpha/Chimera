# R5 Forest Review — Bounded Diagnostic (over-completion correction)

**Reviewer:** TIE2 · **Date:** 2026-09-24 · **Scope:** reconcile R5's report + the
forest completion map against the live board; preserve verified findings, correct
the over-completion claim.

---

## Verdict

R5's three receipts are **verified and preserved** — all green, byte-exact in fresh
subprocesses. The board headline "**FOREST FRONT F01-F08 COMPLETE** — W10 scene-ready"
is an **over-completion claim** that must be corrected to two precise statements:

1. The **static forest artifacts are complete and verified**: F01, F02, F03, F04,
   F07, F08. (Six items — not all of F01–F08.)
2. **W10 itself is NOT scene-ready.** It remains blocked on prerequisites OUTSIDE this
   front: the walking chain W05–W09 (GPU legs QUEUED-BEHIND-BROKER), the engine
   heightfield/prop contact service (G04/W10, separately gated), and U02's camera.

The board's "F01-F08 COMPLETE" range label is misleading: it reads as all six items,
but **F05 ("Specify the terrain range for walking") and F06 ("Implement and qualify
terrain-aware walking") are native-walking items that depend on W06/W07** — which the
board itself marks QUEUED-BEHIND-BROKER / BLOCKED. They are **not done**.

---

## 1. Preserved verified findings (unchanged, all green)

R5 recompiled ALL FOUR route declarations from recipe modules in a FRESH subprocess:
byte-identical to committed `route_declaration.json`. Receipts:

- **identity_receipt.json** — 70/70 checks across identity/integrated/citations.
- **F04 contact** — APPROVE; 13/13 with firing controls; decisive numbers independently
  recomputed; L2 gap honestly recorded (engine = point-spheres-vs-one-plane ONLY).
- **F07 routes** — APPROVE-WITH-NOTES; scene numbers all reproduce; one note N1.
- **F08 loading** — APPROVE; recompile-not-copy proven; CLI receipt byte-exact vs its
  own claim; refusal matrix real.

These are the static artifacts and they are sound. Nothing here is revised.

---

## 2. The over-completion claim, corrected

### Board claim (line 13 of PLAY_BOARD.md)
> **FOREST FRONT F01-F08 COMPLETE** — W10 scene-ready

### Why it over-completes
- **"F01-F08 COMPLETE"** as a range implies all six items done. The completion map shows
  F05 and F06 are native-walking items with deps **W06 / W07**. The board's own Walking
  chain row marks GPU legs QUEUED-BEHIND-BROKER — so W06/W07 are not complete, and by
  dependency **F05/F06 cannot be done**. Only F01, F02, F03, F04, F07, F08 (the static
  artifacts) are complete. The detailed per-item breakdown in the board correctly lists
  only those six as DONE; the range label is the error.
- **"W10 scene-ready"** conflates two distinct claims:
  - *The forest front's static artifacts are ready to serve W10* — TRUE (R5 confirms).
  - *W10 itself (native walking acceptance) is scene-ready* — FALSE; blocked on external
    prerequisites.

### Corrected statement
> **FOREST FRONT STATIC ARTIFACTS COMPLETE (F01, F02, F03, F04, F07, F08); W10 NOT
> scene-ready — blocked on walking chain W05–W09 (GPU legs QUEUED-BEHIND-BROKER), engine
> contact service G04/W10, and U02 camera.**

---

## 3. R5's own honesty row is consistent with the correction

R5 explicitly separates the two claims in its report (lines 23–31):

> "W10-readiness: the forest front is genuinely scene-ready — the map's W10 row can
> consume this front today via `ForestScene` + `terrain_query.TerrainSurface` + the
> `engine_shutdown` injection point. **W10 itself remains blocked by things OUTSIDE this
> front**, all already recorded by the authors, none hidden: (1) the frozen engine has
> no heightfield/prop contact service (F04's L2 statement — a separately-gated engine
> task owed to G04/W10); (2) walking training/execution W05–W09; (3) U02's camera
> (separate lane). No further gap is owed by F01–F08."

This is exactly the corrected statement. R5 does **not** claim F05/F06 are done, nor that
native walking works — it claims only that the static artifacts are ready to be consumed
by W10 once those external prerequisites land. The board headline drops this nuance.

---

## 4. Net effect on the campaign map

- **No artifact rework needed.** The six verified static artifacts stand as-is.
- **F05/F06 remain legitimately blocked** on W06/W07 (GPU legs QUEUED-BEHIND-BROKER).
  Their completion-map "done when" rows require walking-runtime agreement that does not
  exist until the walking chain is unblocked:
  - F05 — "Slope, obstacle size and surface-friction envelope declared from evidence."
  - F06 — "Player walks the declared uneven-ground cases with certified runtime/training
    agreement."
- **W10 remains blocked** on the three external prerequisites R5 enumerated. No hidden
  gap; nothing owed by F01–F04, F07, F08 beyond what is already recorded.

---

## 5. Integrity note

This diagnostic found no fabricated receipts and no reworkable defect in the static
artifacts. The only correction is a **labeling** one: the board's range label "F01-F08"
and its compressed "W10 scene-ready" overstate completion by folding in F05/F06 (native
walking) and W10 itself, neither of which is done. R5's report is internally consistent
with the corrected reading; the board headline is not. No change to any artifact or
receipt — only a correction to the front-status label on this branch.
