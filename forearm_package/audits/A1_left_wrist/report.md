# A1 AUDIT REPORT — LEFT ambiguous wrist sections (ECRB_l-P3, ECRL_l-P3)

Auditor: A1 (independent; right-side audit A2 run separately, no coordination).
Date: 2026-09-24. Baseline: `forearm_package/baseline_snapshot/` (MANIFEST verified 44/44 files).
Fit packet: `runs/actual_monkey_fit.json`, sha256 `a447555069748d7f…` (verified against brief).

---

## 1. VERDICTS PER ACCEPTANCE CRITERION

| # | Criterion | Verdict |
|---|-----------|---------|
| 1 | Both sites' loop enumerations reproduced with numbers (loops, ownership fractions, per-loop signed distances) | **PASS** |
| 2 | Cause classified with quantitative justification | **PASS** — cause (a) genuine mesh topology |
| 3 | Resolution-evidence checklist names specific measurable artifacts per path | **PASS** |
| 4 | Baseline integrity preserved (`git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot` empty) | **PASS** — empty output, exit 0; also empty with `--ignored`; no `__pycache__` |

**PREREGISTRATION (frozen): PREDICTION CONFIRMED — the ambiguity is a section-identification
property.** Recomputation finds multiple closed loops with majority ownership at both wrist
axials (skin loop 50/50 triangles = 100.0 %; pocket loop 3/3 triangles = 100.0 %), and every
candidate loop yields a definite signed distance. **FALSIFIER DID NOT FIRE**: recomputation does
NOT yield exactly one identified loop per site (it yields 2 at both sites, matching the packet).
No machinery defect caused the recorded ambiguity.

**One-line result for Astra:** the plane at each LEFT wrist axial cuts an inward needle-sliver
pocket of the skin in addition to the forearm skin loop; BOTH loops are 100 % left-owned, and
under EITHER candidate loop both sites measure OUTSIDE with clearance >= 4.826 mm — 4.8x the
1.0 mm margin. The sites are not numerically borderline; only the identification is ambiguous,
and both candidates agree on the verdict class.

---

## 2. EVIDENCE (file + line + numbers)

### 2.1 Recorded facts (step 1)

`runs/actual_monkey_fit.json` → `measurements.envelope_containment_loop.radius_l`:

- `per_site.ECRB_l-P3`: `axial_m = 0.051510357`, `n_loops = 4`, `n_identified_loops = 2`,
  `n_open_chains = 0`, `n_degenerate_chains = 2`, `n_cut_segments = 155`,
  `verdict = "unresolved"`, reason `"ambiguous_section: 4 closed loop(s) (2 identified as this
  limb's skin by pack ownership) + 0 open chain(s) at this axial position; no bridging, no
  repair, no proximity choice"`.
- `per_site.ECRL_l-P3`: `axial_m = 0.053482959`, `n_loops = 4`, `n_identified_loops = 2`,
  `n_open_chains = 0`, `n_degenerate_chains = 2`, `n_cut_segments = 161`, same verdict/reason.
- `sections["0.051510357"].loop_diagnostics` = `[{points:48, frac:0.0}, {50,1.0}, {50,0.0},
  {3,1.0}]`; `sections["0.053482959"]` = `[{50,0.0}, {50,1.0}, {54,0.0}, {3,1.0}]`.
- Per-side baseline counts: `n_inside=6, n_inside_insufficient_clearance=1, n_outside=7,
  n_unresolved=2` (matches the brief's 6/1/7/2).

`runs/admission_actual_monkey.json` → `envelope.radius_l.loop_ambiguous =
["ECRB_l-P3","ECRL_l-P3"]`; `falsifier_flags.envelope_containment_loop_ok = false`. Note:
`envelope.radius_l.containment_unresolved` (the RETAINED hull diagnostic) also lists
ECRB_l-P3/ECRL_l-P3 — the hull path does not already answer these sites either.

`session_reports/anatomy_compiler_05.md` line 41 (§4-B): "Triangle–plane section loops at each
site's exact axial position … IDENTIFIED mechanically by majority pack-vertex ownership
(>= 50 % of cut-segment triangles owned by the side's proximal/distal joints — the pack's own
`assign` data, no proximity choice, no bridging; exactly one loop must identify) … ECRB-P3/ECRL-P3
stay ambiguous (wrist-level sections yield multiple ownership-identified loops)." Line 43 (§4-C):
the failed transverse candidate "loop authority improved to 0 outside / 14 inside / 0 tight /
2 ambiguous — the two ambiguous sections remain ambiguous (section identification, not placement)."

Loop machinery, `code/target_envelope.py` (copied byte-identical to `work/`):

- Identification rule (L477-488): each closed loop's cut triangles vote
  `owned = sum(1 for t in tris if int(tri_owner[t]) in owner_set)`; `frac = owned/len(tris)`;
  `if frac >= 0.5: identified.append(...)` — majority owner of a triangle is
  `np.where(o1 == o2, o1, o3)` over `mt.assign` of its 3 vertices (L471-473).
- Ambiguity branch (L512-520): `if len(identified) != 1:` → `verdict = "unresolved"` with the
  ambiguous_section reason quoted above. Docstring L453-461: "EXACTLY ONE loop must identify;
  0 or >= 2 identified loops (or open chains) leave every site at that axial position UNRESOLVED.
  No bridging, no repair, no choosing by size."
- Chaining (L384-434): endpoint-key matching at tol 1e-7 m; `closed and len(chain) >= 4` → loop;
  closed with len < 4 → degenerate; else open.

### 2.2 Recomputation (step 2)

Harness: `scripts/recompute_loops.py` run from `work/` (byte-identical copies of
`mesh_target.py`, `target_envelope.py`, `compiler.py`, `schema.py`, `correspondence.py`;
snapshot inputs passed read-only by explicit path; `PYTHONDONTWRITEBYTECODE=1`).
Input hashes at run: birth `550A5B3E…`, pack `74B3AB04…` (= admission meta, = MANIFEST).

Harness validation (independent of the wrist question):
- All 16 radius_l sites' axials reconstructed from the packet's `fitted_pos_global` via the
  baseline's own ONB rule match the recorded `axial_m` to <= 4.882e-10 m (max).
- Resolved site ECRL_l-P2: recomputed `dist_to_loop_m = 0.004597397` vs recorded
  `0.004597397` (|diff| 3.745e-10 m) — the harness reproduces the recorded machinery exactly.

**ECRL_l-P3 @ axial 0.053482959 m** — 161 cut segments, 4 closed loops, 0 open, 2 degenerate
(repeat run bit-identical; matches recorded 4/2/0/2/161):

| loop | pts | cut tris | owner fraction | owners | signed dist to site | 2D area |
|------|-----|----------|----------------|--------|---------------------|---------|
| forearm skin | 50 | 50 | **1.0000** | wrist_L 40, elbow_L 10 | **+5.5113 mm (outside)** | 352.621 mm² |
| skin pocket | 3 | 3 (true set {34872, 34874, 34888}, all majority elbow_L → true frac 1.0000) | **1.0000** | elbow_L 3 | **+5.5113 mm (outside)** | 0.325 mm² |
| other body | 50 | 50 | 0.0 | hip_L 50 | +95.284 mm | — |
| other body | 54 | 54 | 0.0 | hip_R 54 | +167.833 mm | — |

**ECRB_l-P3 @ axial 0.051510357 m** — 155 cut segments, 4 closed loops, 0 open, 2 degenerate
(repeat bit-identical; matches recorded 4/2/0/2/155):

| loop | pts | cut tris | owner fraction | owners | signed dist to site | 2D area |
|------|-----|----------|----------------|--------|---------------------|---------|
| forearm skin | 50 | 50 | **1.0000** | wrist_L 38, elbow_L 12 | **+4.8258 mm (outside)** | 353.385 mm² |
| skin pocket | 3 | 3 (true set {34872, 34874, 34888}, all majority elbow_L) | **1.0000** | elbow_L 3 | **+4.8724 mm (outside)** | 0.009 mm² |
| other body | 48 | 48 | 0.0 | hip_L 48 | +94.888 mm | — |
| other body | 50 | 50 | 0.0 | hip_R 50 | +167.110 mm | — |

All four loop diagnostics per axial reproduce the packet's `sections` entries exactly (multiset
of (points, owner_fraction) identical). No mesh vertices lie within 1e-9 m of either cut plane
(0 at both axials) — the equal distances are pure geometry, not a vertex-on-plane artifact.

### 2.3 What the second loop IS (measured)

- The pocket loop is the cut of a needle-thin inward sliver in the LEFT distal-forearm skin:
  coincident vertex pairs **6586 ≡ 6596** and **6585 ≡ 6601** (identical 3D coordinates,
  0.000 mm separation), tip at radial **1.764 mm** from the elbow→wrist axis at axial
  **51.122 mm** (79.0 % of the 64.745 mm forearm). The section's skin polygon radius spans
  1.6-19.1 mm, i.e. the sliver penetrates ~17.3 mm deep, to within ~9 % of the axis.
  Sliver triangles 34872 (edges 6.673/9.215/14.961 mm) and 34888 (12.759/16.053/14.961 mm).
- The whole left arm is ONE edge-connected manifold component (1046 triangles from the seed,
  0 boundary edges) — the pocket is an invagination of the skin, not a separate mesh part.
- Pocket-loop axial window (bisection + scan): present for axial in **[51.122, 57.723) mm**,
  absent at 57.723+ mm; both sites (51.510, 53.483 mm) lie inside the window. The section
  scan 46.0-57.5 mm at 0.5 mm steps shows exactly 3 loops / 1 identified up to 51.0 mm and
  4 loops / 2 identified from 51.5 mm through 57.5 mm (receipts `recompute_loops.json`).
- In the section plane the pocket is nearly tangent to the skin boundary: pocket centroid
  INSIDE the skin polygon by 0.032 mm (ECRB axial) / 0.196 mm (ECRL axial); the nearest
  pocket vertex and nearest skin vertex coincide in (b,c) at both axials
  (e.g. (-0.001670, -0.000117) mm at the ECRL axial) — which is why the site's distance to
  both loops is identical for the ECRL site (5.5113 mm at both axials) and near-identical for
  the ECRB site (4.8258 vs 4.8724 mm at its own axial).

### 2.4 Cause classification (step 3) — cause (a), with the numbers

- **(a) Genuine mesh topology — CONFIRMED.** Two distinct closed loops both clear the >= 0.5
  majority bar: skin 50/50 = 1.0000 vs pocket 3/3 = 1.0000 (true per-segment triangle set
  verified directly from the segment list: seg150→tri 34872, seg151→tri 34874, seg152→tri
  34888; all majority-owned by elbow_L). Manual chain walk: seg150 → seg152 → seg151 → closed,
  exactly the three segments.
- **(b) Ownership-data ambiguity — EXCLUDED.** Fractions are 1.0000 vs 1.0000. No threshold in
  [0,1] separates the loops; nothing is near 0.5 (the non-limb loops are at 0.0).
- **(c) Machinery defect — EXCLUDED as the cause.** Determinism: full repeat of the pipeline at
  both axials is identical. Chaining: verified correct by hand (above); 0 open chains.
  Recorded counts/fractions reproduce exactly. (One benign bookkeeping quirk found — see §5.)

---

## 3. RESOLUTION-EVIDENCE CHECKLIST (step 4) — no placement changes; artifacts only

1. **Denser axial sampling near the wrist — ruled out by measurement.** The pocket loop exists
   continuously over [51.122, 57.723) mm; a 0.5 mm scan (46.0-57.5 mm) never shows a
   single-identified section inside the window. Artifact that settles this path negatively:
   the onset/exit bisection + scan table (receipts `recompute_loops.json: axial_scan`,
   `final_measurements.txt`). No axial in the window resolves the section by sampling.
2. **Ownership-threshold evidence — ownership is not the discriminator.** Artifact: per-loop
   owner histograms (§2.2 tables; `recompute_loops.json: loops[].owner_histogram`). Both
   candidates are at 1.0000; no measurable threshold change (>= 50 % is the recorded rule,
   `target_envelope.py` L458) can pick one.
3. **Mesh anatomical-landmark / topology evidence — two measurable artifacts:**
   - Coincident-vertex census: pairs 6586≡6596, 6585≡6601 at exactly 0.000 mm separation.
     Artifact: welded-mesh re-cut — count section loops before/after welding; if welding
     removes the pocket loop at both axials, the ambiguity is a seam artifact, measurable in
     one run.
   - Sliver-depth profile: pocket tip at radial 1.764 mm vs section outer radius ~19.0 mm
     (depth ~17.3 mm). Artifact: radial profile of the pocket (receipts
     `spike_characterization.txt`) — identifies the feature as a modeling sliver, not a
     cross-section of the limb.
4. **Astra ruling paths, each with its artifact:**
   - a. "Outermost/largest-area loop identifies": artifact = enclosed 2D area + ray-cast
     containment of the same cut (skin 353.4 vs pocket 0.009-0.325 mm², ratio >= 10^3; pocket
     centroid inside the skin polygon at both axials). Decisive and already computed.
   - b. "All identified loops must agree on the verdict class": artifact = per-candidate-loop
     signed distances (§2.2) — both loops say OUTSIDE, min clearance 4.8258 mm vs the 1.0 mm
     margin. Resolves both sites to `outside` while recording the ambiguity.
   - c. "Minimum identified-loop size": artifact = vertex counts (50 vs 3) and pocket perimeter
     (~0.73 mm at 51.5 mm; ~4.4 mm at 53.5 mm axial). The existing degeneracy filter already
     excludes < 3-point chains (`target_envelope.py` L426: `len(chain) >= 4`); a >= 4-point rule
     removes the pocket.
   - d. "Hull diagnostic suffices at the wrist": NOT currently backed — the retained hull path
     ALSO records these two sites unresolved (`admission.envelope.radius_l.containment_unresolved`).
     Artifact for this path: the recorded hull verdict + the agreement analysis in §2.2; a hull
     ruling would need a new rule, it cannot inherit an existing hull answer.

**PROPOSALS-FOR-ASTRA (observations only; no baseline change made or suggested as an edit):**
- The packet records NO signed distance for `unresolved` sites (the distance fields are emitted
  only on the exactly-one-loop path, `target_envelope.py` L521-526). The single most informative
  missing artifact is the per-candidate-loop signed distance for ambiguous sections; it is what
  shows the verdict is not borderline (proposal to record `candidate_distances` alongside the
  ambiguity reason — a measurement addition, not an authority change).
- `_chain_closed_loops` bookkeeping quirk (benign here): the seed segment's triangle is written
  on both initial chain entries and the closing segment's triangle is dropped by `chain[:-1]`
  (L408, L427-428), so every loop's reported triangle list double-counts its seed triangle and
  omits the closing one (here: reported [34872, 34872, 34888] vs true {34872, 34874, 34888}).
  Measured effect at these sites: none — all involved triangles are left-owned, fraction 1.0
  either way; in general each loop's reported fraction carries a ±1-triangle uncertainty
  (<= 0.02 for these loops; no verdict in this packet is within 0.02 of the 0.5 bar).

---

## 4. EXPLICIT UNCERTAINTIES

- The fit was NOT re-run. Sites were reconstructed from the packet's own `fitted_pos_global`
  via the baseline's exact projection rule (`_fitted_sites_bc`, `actual_target_fit.py` L309-335);
  validated by 16/16 axial matches (<= 4.9e-10 m) and one resolved-site distance match
  (3.7e-10 m). Any fit-stage nondeterminism is therefore out of scope, but the loop pipeline
  itself is fully deterministic (bit-identical repeats).
- The pocket's intended identity (modeling seam/slit vs deliberate landmark) is not decidable
  from geometry; I report its measurable signature (coincident vertices, depth, window) and
  leave the interpretation to Astra.
- The ±1-triangle fraction uncertainty from the bookkeeping quirk was quantified only for the
  loops at these two axials, not audited across all 32 sites.
- The right side was not examined (A2's scope). The same pocket feature may or may not exist
  there; nothing in this report assumes either way.

## 5. NEGATIVE FINDINGS (preserved)

- Falsifier did not fire: recomputation yields 2 identified loops per site, matching the packet.
- No open chains at either axial (0 open, matching the record); the ambiguity is not a
  chaining failure.
- No mesh vertex lies on either cut plane (|d| < 1e-9 m count = 0) — no vertex-on-plane
  degeneracy contributes.
- The hull diagnostic does not already answer these sites (both are hull-`unresolved` too).
- Two of my own intermediate measurements were wrong and are discarded/disclosed: a 3D-vs-2D
  norm bug (the "100 mm / 879 mm" tiny-to-skin distances in the first dissect run) and a
  last-50-pt-loop selection bug at the ECRB axial (picked the hip loop; the corrected,
  ownership-based selection is in `geometry_correction.py`). The recorded receipts keep the
  buggy outputs next to the corrected ones so the correction chain is auditable.
- Denser sampling alone cannot resolve the sections (window measurement, §3.1).

## 6. RECEIPTS (exact commands; outputs in `receipts/`)

Environment: Python 3.14.3, NumPy 2.2.6 (`python -c "import numpy; print(numpy.__version__)"`).

```
# packet hash (matches brief: a4475550…)
python - <<EOF  # hashlib.sha256(actual_monkey_fit.json) -> a447555069748d7fe421ff2a4ddeaa108729924ae088478741c86c38c3880937
# MANIFEST verification: 44/44 files hash-verified, 0 mismatches

# module copies (byte-identical, sha256-checked): mesh_target.py target_envelope.py
#   compiler.py schema.py correspondence.py  -> audits/A1_left_wrist/work/

# recompute (from work/, PYTHONDONTWRITEBYTECODE=1)
python ../scripts/recompute_loops.py            # -> receipts/recompute_loops.json
python ../scripts/dissect_tiny_loop.py          # -> receipts/dissect_tiny_loop.txt
python ../scripts/spike_characterization.py     # -> receipts/spike_characterization.txt
python ../scripts/geometry_correction.py        # -> receipts/geometry_correction.txt
python (inline final pass)                      # -> receipts/final_measurements.txt

# integrity
git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
#   (empty, exit 0; also empty with --ignored; no __pycache__ in baseline tree)
```

Key output lines (all in `receipts/`):

```
VALIDATION ECRL_l-P2: recomputed dist 0.004597397 m vs recorded 0.004597397 m (|diff| 3.745e-10)
=== ECRL_l-P3 @ axial 0.053482959 m === cut segments 161, closed loops 4, open 0, degenerate 2, repeat-identical True
  loop[1] pts= 50 tris= 50 frac=1.0000 owners={'wrist_L': 40, 'elbow_L': 10} dist +5.511301 mm
  loop[3] pts=  3 tris=  3 frac=1.0000 owners={'elbow_L': 3}                dist +5.511301 mm
=== ECRB_l-P3 @ axial 0.051510357 m === cut segments 155, closed loops 4, open 0, degenerate 2, repeat-identical True
  loop[1] pts= 50 tris= 50 frac=1.0000 owners={'wrist_L': 38, 'elbow_L': 12} dist +4.825766 mm
  loop[3] pts=  3 tris=  3 frac=1.0000 owners={'elbow_L': 3}                dist +4.872384 mm
triangles with >1 segment: {}                    # segment dump: 3 distinct tris {34872,34874,34888}
tip 6586 == 6596: True, radial distance from axis 1.764 mm, axial 51.122 mm
tiny loop present axials: [0.051121910, 0.057723148] m ; absent at 0.057723148 m
axial cross-check: 16 radius_l sites, max |recomputed-recorded| axial diff = 4.882e-10 m
ECRB_l-P3: identified loop pts=50 area=353.385 mm^2 | pts=3 area=0.009 mm^2
ECRL_l-P3: identified loop pts=50 area=352.621 mm^2 | pts=3 area=0.325 mm^2
```

— A1, end of report.
