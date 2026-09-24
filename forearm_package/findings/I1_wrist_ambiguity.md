# I1 — Wrist-Section Ambiguity: Consolidated Finding (A1 ⊕ A2)

**Status:** VERIFIED (both investigations PASS 4/4, receipts independently re-run by the coordinator).
**Inputs:** `baseline_snapshot/` @ MANIFEST (frozen Session-5 baseline). **Authors:** A1 (left, independent), A2 (right, independent) — no communication; consolidated by the coordinator (I1).
**Law:** the four-class containment machinery and the frozen baseline STAND. This document records evidence; it reclassifies nothing.

## The question

Session-5 loop authority reads `unresolved` (ambiguous) at ECRB-P3 + ECRL-P3 (right) and ECRB_l-P3 + ECRL_l-P3 (left): wrist-level sections yield multiple ownership-identified loops, and the declared law requires exactly one.

## What the two investigations found (bilateral agreement to sub-micron)

| site | skin-loop signed distance | sliver-loop signed distance | both loops |
|---|---|---|---|
| ECRB_l-P3 (A1) | **+4.8258 mm** | **+4.8724 mm** | OUTSIDE |
| ECRL_l-P3 (A1) | **+5.5113 mm** | **+5.5113 mm** | OUTSIDE |
| ECRB-P3 (A2) | **+4.826 mm** | **+4.872 mm** | OUTSIDE |
| ECRL-P3 (A2) | **+5.511 mm** | **+5.511 mm** | OUTSIDE |

Clearance ≥ 4.83 mm against the 1.0 mm margin — the sites are not borderline under EITHER loop. Loop structure at both axials, both sides: 4 closed loops / 2 identified / 0 open / 2 degenerate; the identified pair is the true 50-point forearm skin loop (ownership fraction 1.00; wrist 38–40 + elbow 10–12 tri-owners) and a 3-point degenerate sliver (fraction 1.00, elbow-owned).

**Verdict-invariance (A2):** every candidate loop yields OUTSIDE at every (site, section) pair, Δ ≤ 0.077 mm.

## Mechanism (measured, both sides)

- Coincident-coordinate vertex pairs at the wrist crease: left 6586≡6596 and 6585≡6601; right 15146≡15159 and 15151≡15172 — separation exactly 0.000 mm. A2 counts **1,255 duplicated-coordinate vertices mesh-wide**: an unwelded seam.
- At wrist axials the skin cross-section is a self-touching figure-eight; the declared no-bridging chaining law (S14) NECESSARILY splits it into two 100 %-owned loops. The ambiguity is a consequence of the seam + the law, not of uncertain data.
- The sliver is persistent geometry, not numerical noise: perimeters 0.73 / 4.46 mm vs the 1e-7 m chaining tolerance; onset bracketed by bisection to 51.1219–51.1220 mm; identified-loop count = 2 for every axial from 51.122 mm through 80 mm (right); pocket axial window [51.122, 57.723) mm (left).
- Excluded causes: ownership ambiguity (fractions 1.00/1.00, nothing near 0.5); machinery defect (bit-deterministic on re-run; preregistered falsifier NOT fired on either side; 0 open chains; harness reproduces all 16 site records per side with 0 mismatches).

## Consequences (PROJECTION ONLY — not a reclassification)

Under any resolution rule that respects loop agreement or excludes degenerate slivers, the four sites classify **OUTSIDE by ≥ 4.83 mm**, and the per-side loop-authority tally would read 6 inside / 1 tight / **9 outside** / **0 ambiguous**. Note this is NOT the failed Candidate-C projection (0 outside / 14 inside / 0 tight / 2 ambiguous — that belonged to the rejected transverse shift and stays dead). A resolved-OUTSIDE wrist joins the existing outside family (BRD-P2/P3, ECRB-P2, ECRL-P2, PT-P5, BIClong-P9, BICshort-P6): the source-authored wrist sites sit outside the fitted envelope — a documented geometric divergence (A6: containment says nothing about anatomical correctness in either direction).

## Resolution paths for Astra (evidence status)

| path | artifact that settles it | status |
|---|---|---|
| P1 axial-sweep + onset table | A2 `receipts/step2_axial_sweep.json` | COMPLETE |
| P2 ownership margins/weights | A2 step2c/2d | COMPLETE — resolves NEGATIVELY (ownership is not the cause) |
| P3 seam/pinch forensics | A1 `spike_characterization.py`; A2 step2b/2e | COMPLETE (unwelded seam; valence-4 cut point; vertex ids named) |
| P4 hull-diagnostic read at wrist | baseline `SECTION_T` band extension | **BLOCKED on Astra** — current hull coverage ends at 50.084 mm < 51.51 mm; extending the band set is a baseline change (pure measurement, no fit change, no margin change — the smallest authorized change that adds independent confirmation) |
| P5 per-loop distance table (verdict-invariance rule) | this document + A1/A2 receipts | COMPLETE |

## Astra decision request

Choose the resolution rule: **(a)** degenerate-loop exclusion (area/perimeter threshold), **(b)** loop-agreement verdict (all identified loops agree → adopt the common verdict), **(c)** authorize P4 (hull band extension) for independent confirmation, **(d)** accept permanent documented uncertainty. On current evidence (a) and (b) both yield OUTSIDE for all four sites; (c) adds a second authority's voice; (d) keeps the packet honest but leaves T1 (32/32 classified) unmet. The choice is architectural; this campaign executes it, it does not make it.

## Receipts

- A1: `audits/A1_left_wrist/report.md`, `receipts/recompute_loops.json` (coordinator fresh re-run OK)
- A2: `audits/A2_right_wrist/report.md`, `receipts/step2_*`, `step2b_sliver_anatomy.json` (coordinator fresh re-run OK)
- Baseline integrity: `git status --porcelain -- forearm_package/baseline_snapshot` empty before/after all runs.
