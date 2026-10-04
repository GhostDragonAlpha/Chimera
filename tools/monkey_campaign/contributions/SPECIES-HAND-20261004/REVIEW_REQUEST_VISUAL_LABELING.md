# SERGEANT VISUAL LABELING REVIEW REQUEST — species-hand Stage 0 (through the Lieutenant)

From: wk-species-hand (text-only; made and makes NO picture claims — every
question below is exactly the independent visual review the prereg mandates).
Date: 2026-10-04. Binding law: the committed prereg (c31227e9..., blob
77513d08...) section 2; the Lieutenant's Stage-0 GO ruling.

## What is on review

Directory `E:/ChimeraWork/monkey-coordination/species-hand/stage0_review/`:

- `cand2_noplane/` — THE EXTRACTION CANDIDATE: 14 parts, volumes 24.4-1601.9
  mm^3, authored-cut fractions 0.0114-0.2526 (ALL under the declared 0.35
  ceiling), max EDT per part 0.735-0.949 mm (filled interiors). Per-part STLs
  `part001.stl`..`part014.stl` (binary STL, source units = millimeters),
  `parts_table.csv`, `contact_graph.json`, `part_meshes.json`, renders
  `cand2_ax{0,1,2}.png` (mid-slice label maps + first-hit label projections
  per axis; deterministic tab20 palette; part id = label number).
- `planes/fine_cand{0,1,2,3}/` — the declared wrist-cut-plane runs of all
  four candidates (tables + renders; cand2's plane run is superseded by
  cand2_noplane per the findings below).
- `stage0_coarse_receipt.json` — the localization record (7 candidates; the
  four large ones 0-3 extracted).
- `stage0_diag_cand{0,1}.json` — fused-mass diagnostics.
- `stage0_selftest_receipt.json` (v5) — the pipeline's synthetic validation.

Candidate boxes (source units = mm, from the sealed coarse receipt):
cand0 (-18,-4,-166)..(21,35,-85); cand1 (42,-57,-63)..(79,36,17);
cand2 (-8,-98,31)..(59,-6,81); cand3 (56,-96,-175)..(102,-27,-107).

## The measured per-candidate state (all from sealed runner jobs)

| candidate | best extraction | parts >= 15 mm^3 | cut fractions | state |
|---|---|---|---|---|
| cand0 | plane run job `b37aca3a...` | 1 (4,215.8 mm^3, ONE mass) | 0.0015 | FUSED/HOLLOW — see D |
| cand1 | plane run job `8a55f80b...` | 1 big (3,841.7) + 2 (161.8, 159.2) | 0.012-0.227 | FUSED/HOLLOW — see D |
| cand2 | NO-PLANE run job `728595fc...` | 14 (24.4-1601.9 mm^3) | 0.011-0.093 (+ one 0.253 at 24.4 mm^3) | EXTRACTION CANDIDATE — see A |
| cand3 | no-plane run job `6f133d02...` | 2 (1,012.2, 576.1) | 0.028, 0.042 | FUSED/PARTIAL — see A/D |

D (diagnostic, cand0/cand1): the fine solid is a HOLLOW unfilled shell, not
filled bone interiors — EDT deciles [0.30, 0.30, 0.30, 0.42, 0.52] mm (90
percent of voxels within 0.52 mm of background), one component, and exactly
ONE h-maxima marker at every h in {0.05, 0.10, 0.20, 0.30, 0.50} mm. The
candidate boxes slice bones at the box faces; the open rims drain the
interiors, so fill produces a thin connected shell (scan webbing + the rims)
rather than per-bone volumes. The declared wrist cut plane (sealed jobs) did
not change this class for cand0.

## The five questions (answer in order; UNRESOLVABLE is a valid answer everywhere)

- Q1 (identification): looking at the renders (and STLs in any viewer) — what
  is each candidate? Expected universe: left hand, right hand, left foot,
  right foot, other (skull fragment, pelvis, tail...). Record per candidate:
  identification + confidence + which render axes show it.
- Q2 (hand choice): IF a left and a right hand are both present, which
  candidate is the better-resolved hand for the 19-bone extraction? State
  what you see (finger separation, completeness, artifacts).
- Q3 (labeling, ONLY for a candidate you identify as a hand): for the chosen
  extraction's parts (cand2_noplane parts 1-14, or a planes/fine_candN
  extraction), label each part with the A05 bone name
  {firstmc,secondmc,thirdmc,fourthmc,fifthmc,proximal_thumb,distal_thumb,
  proxph2..5,midph2..5,distph2..5} (carpals/others = OTHER + name if known),
  or UNRESOLVABLE(part) where a part is not a single bone (fused group,
  fragment, artifact). A fused group may be recorded as
  GROUP{...names...} — that makes the part UNRESOLVED_BONE per the prereg.
- Q4 (fused candidates): confirm or refute the hollow-shell/fused-mass
  diagnosis for cand0/cand1/cand3 from the renders (do you see finger
  separation inside the mass? webbing? an open rim at the box faces?).
- Q5 (wrist-cut sides): the declared plane rule picked the low-count end bin
  as the wrist side; for cand2 it is now measured WRONG (the plane run
  discarded the fan; the no-plane run is the good one). Confirm from the
  renders which end of each candidate is the wrist, so the rule's erratum is
  recorded precisely.

## Standing law for this review

- This review gates the LADDER (no ladder run starts before it passes, per
  the Lieutenant's ruling). The labeling outcome is an INPUT to registration
  (Stage 0-B); it never sees or tunes any ladder quantity.
- The declared UNRESOLVED_BONE ceiling (0.35 authored-cut fraction) applies;
  GROUP parts and UNRESOLVABLE rows are carried honestly, never dropped.
- Everything reviewed is from sealed runner jobs (job ids in
  EVIDENCE.md); the reviewer may re-derive any number from the twinned
  artifacts. n=1 specimen (Pisa C 1549); units are millimeters (recorded
  inference, conversion 1/1000 to meters at registration).

---

## ERRATUM POINTER (2026-10-04, post-verdict)

This request's D note and the cand3 row of its table are corrected by the
EVIDENCE.md CS2.E erratum: cand1 carried 3 markers at every h (not 1), and
the cand3 numbers 1,012.2/576.1 belong to job 36652460 (the inverted plane
run), not 6f133d02 (no-plane: 6,428.1/1,679.2). cand2's parts are thin
surface shells (1.5-1.9mm walls; SURFACES not volumes) per the Sergeant's
verdict; all 14 parts are GROUP/OTHER = UNRESOLVED_BONE.
