# A2 — RIGHT ambiguous wrist section: ECRB-P3 / ECRL-P3 (independent audit report)

**Auditor:** A2 (independent; left-side investigation is A1's, uncoordinated)
**Date:** 2026-09-24
**Baseline:** `E:/PythonChimera/forearm_package/baseline_snapshot/` (READ-ONLY; all work under
`E:/PythonChimera/forearm_package/audits/A2_right_wrist/`)
**Inputs verified:** snapshot `inputs/monkey_birth.bin` sha256 `550A5B3E…AABFA3C` and
`inputs/monkey_joints.bin` sha256 `74B3AB04…50C1662` both match the recorded fit's
`target_inputs` (fits packet sha256 `A4475550…` — matches the campaign's `a4475550…`).

---

## 1. VERDICTS PER ACCEPTANCE CRITERION

| # | Criterion | Verdict |
|---|---|---|
| 1 | Both sites' loop enumerations reproduced with numbers (loops, ownership fractions, per-loop signed distances) | **PASS** |
| 2 | Cause classified with quantitative justification | **PASS** |
| 3 | Resolution-evidence checklist names specific measurable artifacts per path | **PASS** |
| 4 | Baseline integrity preserved (`git status --porcelain` on baseline_snapshot empty) | **PASS** (output pasted in §6) |

**PREREGISTRATION TEST (frozen, tested not rewritten):** PREDICTION confirmed —
multiple closed loops obtain majority ownership at the wrist axial positions (2 identified
per site, both at owner_fraction 1.00), and each candidate loop yields a definite signed
distance (all candidates: OUTSIDE, +4.8…+5.5 mm — not numerically borderline).
**FALSIFIER NOT FIRED:** recomputation yields exactly **2** identified loops per site, not 1
(receipts `receipts/step2_recompute.log` [7]); the recorded ambiguity is **not** a machinery defect.

---

## 2. WHAT THE RECORDED BASELINE SAYS (step 1)

**Fit packet** `runs/actual_monkey_fit.json` → `measurements.envelope_containment_loop.radius`:

- `unresolved: ["ECRB-P3","ECRL-P3"]`; counts 6 inside / 1 tight (PT-P3) / 7 outside / 2 ambiguous — matches session report 05 §4-B verbatim.
- ECRB-P3 record: `axial_m 0.051510357, n_loops 4, n_identified_loops 2, n_open_chains 0, n_degenerate_chains 2, n_cut_segments 155, verdict "unresolved"`, reason `"ambiguous_section: 4 closed loop(s) (2 identified as this limb's skin by pack ownership) + 0 open chain(s)…"`.
- ECRL-P3 record: `axial_m 0.053482959, n_loops 4, n_identified_loops 2, n_open_chains 0, n_degenerate_chains 2, n_cut_segments 161`, same verdict/reason.
- Stored section diagnostics at both axials: loop inventory `{54 pts, 0.0}, {50 pts, 0.0}, {50 pts, 1.0}, {3 pts, 1.0}` (ECRL axial) / `{54,0},{50,0},{50,1.0},{3,1.0}` — the **3-point loop at 1.0** is the second identified loop, visible in the recorded packet itself.
- Residuals: `envelope_containment_loop.ambiguous_section.radius = true`; `envelope_containment_loop_ok = false`.

**Admission** `runs/admission_actual_monkey.json` → `envelope.radius.loop_ambiguous = ["ECRB-P3","ECRL-P3"]` (and `loop_outside` 7 sites, `loop_tight` PT-P3). Hull diagnostic for both sites: `{"verdict":"unresolved","reason":"local_narrowing: no sampled section band near this axial position"}`.

**Loop machinery** `code/target_envelope.py`:

- Identification rule (L477-488, quoted): each loop's segments' triangles vote the majority pack-owner (`_tri_owner`, L473: `np.where(o1 == o2, o1, o3)`); `frac = owned / len(tris) if tris else 0.0`; `if frac >= 0.5: identified.append(...)`. Declared law (L460-461): *"A closed loop is IDENTIFIED as the evaluated limb's skin boundary when >= 50 % of its segments' triangles are owned by the segment's proximal/distal joints. EXACTLY ONE loop must identify; 0 or >= 2 identified loops (or open chains) leave every site at that axial position UNRESOLVED. No bridging, no repair, no choosing by size."*
- Ambiguity branch (L512-518): `if len(identified) != 1: rec["verdict"] = "unresolved"; rec["reason"] = f"ambiguous_section: {n_loops} closed loop(s) ({len(identified)} identified …)"`.
- Call context `code/actual_target_fit.py` L522-557: right side `P = joint_pos("elbow_R")`, `P_d = joint_pos("wrist_R")`, roll witness = elbow_R band vertex farthest off-axis (`_band_roll`, L89-97), `owner_joint_names = ("elbow_R","wrist_R")`.

## 3. RECOMPUTATION (step 2) — exact reproduction

Work copies: `work/target_envelope.py` (verbatim, sha256 `1752c0fd…` identical to baseline),
`work/mesh_target.py` (only the two input-path constants repointed to the snapshot inputs),
`work/frame_utils.py` (`onb_from_points` + `_unit` extracted verbatim from `compiler.py` L50-71).
Script `scripts/01_recompute_right_wrist.py`, log `receipts/step2_recompute.log`.

- Frame reconstruction: max |recomputed (axial,b,c) − stored `fitted_pos_local|` = **3.469e-17 m** over all 16 right sites.
- Authority re-run vs stored packet: counts 6/1/7/2 = stored; **0 per-site record mismatches** over all compared fields (verdict, reason, axial, n_loops, n_identified_loops, open, degenerate, segments, dist, loop_points).
- Determinism: cut+chain re-run produces **identical loop signatures** at both axials (`[5] … True`).

### Full enumeration at the two axials (owner set = {elbow_R, wrist_R})

**ECRB-P3 @ axial 51.510357 mm** (155 cut segments, 4 closed loops, 0 open, 2 degenerate):

| loop | pts/tris | owner histogram (majority-of-3 per tri) | frac | site signed dist | class |
|---|---|---|---|---|---|
| 0 | 50/50 | hip_L ×50 | 0.00 | +167.110 mm | outside (irrelevant far field) |
| 1 | 48/48 | hip_R ×48 | 0.00 | +94.888 mm | outside (irrelevant far field) |
| 2 | 50/50 | wrist_R ×38, elbow_R ×12 | **1.00** | **+4.826 mm** | **outside** (the forearm/wrist skin loop) |
| 3 | 3 pts, 2 unique tris | elbow_R ×2 | **1.00** | **+4.872 mm** | **outside** (the crease fold sliver) |

**ECRL-P3 @ axial 53.482959 mm** (161 cut segments, 4 closed loops, 0 open, 2 degenerate):

| loop | pts/tris | owner histogram | frac | site signed dist | class |
|---|---|---|---|---|---|
| 0 | 54/54 | hip_L ×54 | 0.00 | +167.833 mm | outside |
| 1 | 50/50 | hip_R ×50 | 0.00 | +95.284 mm | outside |
| 2 | 50/50 | wrist_R ×40, elbow_R ×10 | **1.00** | **+5.511 mm** | **outside** |
| 3 | 3 pts, 2 unique tris | elbow_R ×2 | **1.00** | **+5.511 mm** | **outside** |

Cross-reads (each site judged at the OTHER site's axial, receipts `step2b_sliver_anatomy.json`): every candidate loop at every evaluated (site, section) pair gives **d > 0, OUTSIDE**, by 4.826–5.511 mm — 4.8–5.5× the 1 mm margin. Max delta between candidate loops' distances: **0.077 mm** (ECRB-P3 at ECRL's axial), **0.000 mm** for ECRL-P3 at its own axial. **The ambiguity is verdict-invariant: loop choice does not change the containment class.**

## 4. CAUSE CLASSIFICATION (step 3) — (a) genuine mesh topology, mechanism identified

**Measured mechanism (receipts `step2c_pinch_forensics.log`, `step2d_pinch_segments.log`, `step2e_seam_vertices.log`):**

1. **The two identified loops share one exact cut point.** Min 3D distance sliver-point ↔ main-loop-point = **0.000000e+00 m** at both axials; four segment-ends meet at that point (segment-endpoint valence **4**: segments 117/131/152/153), pairwise distances all exactly 0.0.
2. **The pinch is an unwelded seam in the authored mesh.** Vertex coordinates: `V[15146] == V[15159]` **exactly** (distance 0.0) and `V[15151] == V[15172]` **exactly** (0.0). Two welded triangle pairs share one geometric edge — tris 27728 [15144,15146,15151] and 35882 [15150,15151,15146] share edge (15146,15151); tris 27767 [15156,15172,15159] and 35884 [15159,15172,15167] share its duplicate (15172,15159). The plane crosses that edge once geometrically; four segment-ends (two per edge-copy) meet at one point, and the declared chaining law (`_chain_closed_loops`, endpoint-key matching, no bridging) necessarily splits the section into two closed loops. **The wrist cross-section there is a self-touching (figure-eight) curve** — the mesh's skin folds along a crease whose ridge is a seam of 1255 duplicated-coordinate vertices mesh-wide (18 459 vertices, 17 204 unique coordinates).
3. **The fold is real, persistent geometry, not float noise.** The sliver's source triangles are non-degenerate (areas 19.7 / 24.3 / 89.8 mm²; the cut is small because the plane crosses near the ridge). Sliver perimeter 0.73 mm (ECRB axial) / 4.46 mm (ECRL axial) — 4 orders of magnitude above the chaining tolerance (1e-7 m). Fold onset bracketed by bisection: between axial **51.1219 mm and 51.1220 mm** (count flips 1→2 within that 1 µm bracket — a tangency onset); count = 2 for **every** axial from 51.1220 mm through 80 mm (end of sweep, past the wrist joint at 64.745 mm, receipts `step2_axial_sweep.json`). Count = 1 for the whole 40.0–51.1219 mm span. Site axials sit 0.388 mm (ECRB-P3) and 2.361 mm (ECRL-P3) distal of the onset.
4. **Ownership is not borderline.** Fractions 1.00/1.00 at both axials. Margins: the main loop would need 25 of 50 foreign triangles to drop below 0.5; the sliver needs 1 of 2. Pack blend weights at the fold-ridge vertices: 15146/15151/15159/15167 = **0.5 elbow_R / 0.5 wrist_R**, 15150 = 0.9997 wrist_R — the ridge is the pack's own elbow→wrist ownership transition, entirely on the RIGHT side's joints.
5. **The degenerate chains (2 per axial) are unrelated far-field pinches**: 2-point chains owned hip_L (perimeter 0.150 mm) and hip_R (0.063 mm) at the thigh cuts — excluded from identification by `len(chain) >= 4`, correctly not implicated.

**Classification:**

- **(a) Genuine mesh topology — CONFIRMED, with the mechanism pinned down.** The ambiguity is a section-identification property of the mesh itself: at wrist-level axials the skin cross-section is one curve that self-touches at an unwelded seam crease, so the declared "exactly one identified loop" law necessarily sees two 100 %-owned loops. Not two anatomically distinct body parts (the far-field loops are the hips at +95/+167 mm; the crease sliver is right-side skin).
- **(b) Ownership-data ambiguity — EXCLUDED.** Fractions 1.00 vs 1.00 (nothing near 50 %); even continuous blend weights at the ridge are 0.5/0.5 between two joints of the SAME side, so no ownership reweighting separates the loops.
- **(c) Machinery defect — EXCLUDED.** Deterministic (identical signatures on re-run); recomputation reproduces the stored packet with 0 mismatches; falsifier not fired. Two machinery subtleties were measured and recorded as observations only (§5, items 4-5); neither changes any recorded verdict.

## 5. NEGATIVE FINDINGS AND OBSERVATIONS (preserved)

1. **Ownership evidence cannot resolve this ambiguity.** No assign-based threshold in (0.5, 1.0] separates the loops (both at 1.00); the pack's continuous ridge weights are 0.5/0.5 same-side. A negative result with numbers.
2. **Denser axial re-sampling at the sites' positions cannot resolve it.** Identified-loop count is 2 over the entire contiguous span [51.1220, >80] mm; it is 1 only proximal of 51.1219 mm. Sampling density is not the limiting factor; axial POSITION relative to the crease onset is.
3. **The hull diagnostic does not cover the sites.** Envelope sections sit at 22.661/32.372/42.084 mm ± 8 mm band → coverage ends at 50.084 mm < both sites' axials; recorded hull verdicts are "local_narrowing" for both. A hull-sufficiency ruling would need extended sections, and the hull's convexity cannot represent the crease (a concavity) anyway.
4. **Machinery observation (no effect here):** a 4-valent seam crossing splits one self-touching section curve into multiple loops; this is correct per the declared chaining law but means "n_loops" counts crease artifacts of unwelded seams, not only distinct body parts.
5. **Machinery observation (no effect here):** a 3-segment closed loop records its first triangle twice in the ownership denominator (chain entries `[t0, t0, t1]`, unique tris 2, entries 3 — measured both axials). A boundary case at frac = 0.5 could classify differently under unique-triangle counting. At these sites both entries are owned (1.00 either way), so no recorded verdict depends on it.
6. The sites are OUTSIDE the wrist skin loop by +4.8…+5.5 mm regardless of the ambiguity — the same verdict class as their P2 siblings (recorded: ECRB-P2 +3.75 mm, ECRL-P2 +4.60 mm outside). Nothing in this audit changes the fired outside findings.

## 6. RESOLUTION-EVIDENCE CHECKLIST (step 4) — artifacts per path (no placement changes proposed)

| Path | The measurable artifact that would settle it | Where it already exists / what to produce |
|---|---|---|
| 1. Denser axial sampling near the wrist | Identified-loop-count-vs-axial table + onset bisection. Settles the question by PROVING no axial at the sites yields exactly one identified loop (count = 2 for all of [51.1220, >80] mm; = 1 only ≤ 51.1219 mm). | **Already measured**: `receipts/step2_axial_sweep.json` (0.25 mm grid, 40–58 mm), onset bracket 51.1219–51.1220 mm (`step2c_pinch_forensics.log`). For Astra: the decisive artifact is this table, plus the site axials (51.510/53.483 mm) vs onset. |
| 2. Ownership-threshold evidence | Ownership fractions + margins + ridge blend weights. Settles it NEGATIVELY: no assign threshold separates 1.00/1.00 loops; ridge weights are 0.5/0.5 within the side. | **Already measured**: histograms in `step2_deep_loops.json`; margins in `step2c_pinch_forensics.log`; weights `w`/`w2` at vertices 15146/15150/15151/15159/15167 (`step2c` log). For Astra: rules out any ownership-based resolution. |
| 3. Mesh anatomical landmarks | Pinch/seam forensics: exact coincident vertex pairs (15146≡15159, 15151≡15172, distance 0.0), 4-valent cut point (pairwise distance 0.0), crease fold crossing the wrist joint (64.745 mm) with onset 51.1220 mm — identifies the fold as the wrist-crease seam. Settles it by naming the second loop a crease artifact of ONE skin boundary, provided Astra accepts a figure-eight interpretation rule (e.g. "identified loops sharing an exact cut point at a seam are one boundary with a crease; judge against the area-dominant component; record the crease loop as diagnostic"). | **Already measured**: `step2e_seam_vertices.log`, `step2d_pinch_segments.log`, fold span + areas in `step2b_sliver_anatomy.json`. The measurable prerequisite for such a ruling is the pinch-valence test (valence 4, distance 0.0) — produced. |
| 4. Astra ruling that the hull diagnostic suffices | Extended-hull coverage artifact: hull sections reaching the sites' axials (e.g. t = 0.80 → 51.796 mm; t = 0.85 → 55.033 mm) with recorded band vertex counts and the three band-width variants; hull verdicts at the sites. Settles it only if Astra also accepts the hull's convexity blind spot at the crease. | Not producible inside audit boundaries (requires changing `SECTION_T`, a baseline parameter). Current recorded state (quoted §2): both sites "local_narrowing"; coverage ends 50.084 mm. |
| 5. Verdict-invariance rule (emerges from these measurements) | Per-loop signed-distance table at each candidate loop. If ALL identified loops at a section agree on the signed-distance class, the section resolves to that class with min/max distance recorded. Here: all candidates OUTSIDE (+4.826…+5.511 mm, Δ ≤ 0.077 mm) at every (site, section) pair — the ambiguity currently blocks stating a verdict the data already determines. | **Already measured**: `dist_table` in `receipts/step2b_sliver_anatomy.json`. The artifact is this table; the ruling is Astra's. |

PROPOSALS-FOR-ASTRA (observations only — nothing changed): the artifacts in rows 1, 2, 3 and 5 are complete in this audit's receipts; row 4 requires a baseline-section extension only Astra can authorize.

## 7. EXPLICIT UNCERTAINTIES

1. The fold-onset bracket is [51.1219, 51.1220] mm on a 1 µm bisection of the EXACT-integer plane cut; the physical onset is a tangency, so exactly-one-loop at 51.12190 vs 51.12192 mm is a measure-zero question — irrelevant at the 0.388/2.361 mm site offsets.
2. Chaining pairings at the 4-valent pinch depend on segment list order; the law is deterministic for these inputs (verified by re-run), but a different mesh ordering could in principle chain the same cut into different loop groupings (e.g. main loop through the crease). This would change loop INVENTORIES, not the ownership fractions (still 100 % right-side), and not the verdict-invariance numbers (all candidates OUTSIDE).
3. `mt.assign` is the pack's primary owner per vertex; the audit used the pack's own `assign`/`w`/`w2` verbatim (`mesh_target.py` L65-79). No independent ground truth of anatomical ownership exists in the package — the pack IS the ownership reference, per the declared law.
4. The axial sweep extended to 80 mm (beyond the wrist joint at 64.745 mm, into the hand region) and the count stayed 2; the sweep did not extend past 80 mm, so the fold's distal end is UNMEASURED (reported as ">80 mm"). Proximal end measured exactly.
5. Python/NumPy versions here (3.14 / 2.2.6) vs the baseline sessions' may differ; reproduction was bit-faithful on the compared recorded fields (0 mismatches), so no version sensitivity was detected on this code path.

## 8. RECEIPTS (exact commands; full logs in `receipts/`)

```
python -c "import numpy; print(numpy.__version__)"          # -> 2.2.6
PYTHONDONTWRITEBYTECODE=1 python scripts/01_recompute_right_wrist.py   # -> receipts/step2_recompute.log
PYTHONDONTWRITEBYTECODE=1 python scripts/02_sliver_anatomy.py          # -> receipts/step2b_sliver_anatomy.{log,json}
PYTHONDONTWRITEBYTECODE=1 python scripts/03_pinch_forensics.py         # -> receipts/step2c_pinch_forensics.log
# inline pinch-segment dump                                            # -> receipts/step2d_pinch_segments.log
# inline seam-vertex check                                             # -> receipts/step2e_seam_vertices.log
# step-1 extraction runs                                               # -> receipts/step1_*.txt
```

Key output lines:

- `[2] rebuilt 16 resolved right sites; max |recomputed - stored fitted_pos_local| = 3.469e-17 m`
- `[3] recomputed counts: inside 6 tight 1 outside 7 unresolved 2  (stored: 6/1/7/2)` · `per-site record mismatches vs stored packet: 0`
- `[7] PREREGISTRATION: identified loops per site (recomputed): {'0.051510357': 2, '0.053482959': 2}` · `FALSIFIER … FIRED: False`
- `site ECRB-P3: signed dist main +4.826 mm (outside) | sliver +4.872 mm (outside) | delta 0.047 mm` · `site ECRL-P3: signed dist main +5.511 mm (outside) | sliver +5.511 mm (outside) | delta 0.000 mm`
- `min dist sliver<->main: 0.000000e+00 m` · `segment-endpoint valence at pinch key: 4`
- `V[15146] == V[15159]: True` · `V[15151] == V[15172]: True` · `mesh-wide: 18459 vertices, 17204 unique coordinates, 1255 duplicated-coordinate vertices`
- `axial 51.121900 mm -> identified 1` / `axial 51.121920 mm -> identified 2`

**Baseline integrity (criterion 4)** — command output:

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty)
```

No `__pycache__` or `.pyc` under `baseline_snapshot/` (checked with `find`); all audit writes confined to
`E:/PythonChimera/forearm_package/audits/A2_right_wrist/` (brief.md, report.md, scripts/ ×3, work/ ×3, receipts/ ×14).

## 9. FILES

- `E:/PythonChimera/forearm_package/audits/A2_right_wrist/brief.md` (verbatim brief)
- `E:/PythonChimera/forearm_package/audits/A2_right_wrist/report.md` (this report)
- `E:/PythonChimera/forearm_package/audits/A2_right_wrist/scripts/01_recompute_right_wrist.py`, `02_sliver_anatomy.py`, `03_pinch_forensics.py`
- `E:/PythonChimera/forearm_package/audits/A2_right_wrist/work/` (target_envelope.py verbatim copy; mesh_target.py with input paths repointed; frame_utils.py verbatim extract)
- `E:/PythonChimera/forearm_package/audits/A2_right_wrist/receipts/` (14 files: step1_*.txt, step2_recompute.log, step2_deep_loops.json, step2_axial_sweep.json, step2b_sliver_anatomy.{log,json}, step2c_pinch_forensics.log, step2d_pinch_segments.log, step2e_seam_vertices.log)
