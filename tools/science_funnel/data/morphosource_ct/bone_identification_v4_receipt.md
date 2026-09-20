# Bone identification v4 — companion tiebreak, mutual corroboration, labeled overlays receipt

- **Lane:** `agent/bone-id-v3-companion` (base `59098314`, tip of `buffy/bone-id-transfer-20260919`)
- **Agent:** GLM 5.3
- **Data:** `bone_identification_v3.json` (membranes + transfer state) + `bone_identification_v2.json` (the surface-gap adjacency, derived 3.0 mm joint-touching cut) + the committed preview meshes of both infant *Macaca mulatta* — A = `000875604` (seg threshold 118), B = `000875599` (seg threshold 148).
- **Outputs (new files only, nothing pre-existing modified):** `companion_correlate_v4.py`, `bone_identification_v4.json`, `render_overlays_v4.py`, `overlays/` (6 overlay PNGs + `overlay_render_receipt.json`), this receipt.

## 1. Rule 0 membranes (stated in the output JSON before computing)

**Task 1 — companion-proximity tiebreak (B-2, B-6).**
STATEMENT: an unlabeled B bone whose limb kind is undecidable in isolation takes the limb kind (fore/hind) of its joint-touching partners (surface gap ≤ 3.0 mm in v2's adjacency); a partner is kind-decisive iff it is a thin-rod fibula-morphology bone (elongation > 10, length > 30 mm) = hind, or an already-labeled bone (= its recorded chain_kind). Exactly one kind in the partner set → the bone takes that kind, **only that**; the class must then be the unique within-10% A-envelope match among kind-compatible classes (v3's gate, unchanged); a tie that remains a tie stays refused.
PREDICTION: **B reaches 16/24** (both ambiguous bones resolve).
FALSIFIER: two partners of different kinds touching the same bone = still ambiguous; every assignment carries partner evidence; NON-CIRCULARITY LAW — companion kind is never inferred from the ambiguous bone's own extent (enforced structurally: the bone's extent is read only *after* the companion kind is fixed, and never feeds the kind decision).

**Task 2 — mutual cross-specimen corroboration.**
STATEMENT: A's medium foot bones (15, 17, 18) are medium *only* because v3 found no within-10% homolog in B's high set; B now has transferred feet (16, 17), so each A medium bone is corroborated iff its max extent agrees with ≥ 1 B transferred foot within the lane's 10% homology tolerance (rel = |a−b|/max(a,b), the v2 convention carried through v3). Agreement resolves the medium reason → high; failure keeps it medium. B's transferred feet record the symmetric corroboration.
PREDICTION: all three A medium feet corroborate (A → 21 high + 0 medium, total unchanged 21/24); each B transferred foot gains ≥ 1 link.
FALSIFIER: an upgrade whose best agreement is borderline (rel > 0.095) is flagged, never silently counted; if no A medium bone corroborated, the transfer gate itself would be falsified.

## 2. Task 1 results — **B stays 14/24; the 16/24 prediction is FALSIFIED**, refusals recorded with partner evidence

Each ambiguous bone has exactly one partner within 3.0 mm, and it is kind-decisive — the falsifier "two partners of different kinds" never fires. The tiebreak works exactly as specified and still refuses both bones, because each resolved kind leaves **two** classes within 10%:

| B rank | partner (v2 adjacency) | partner evidence | kind fixed | classes of that kind within 10% | verdict |
|---|---|---|---|---|---|
| 2 | rank 16 @ 1.24 mm | already-labeled: foot_class, chain_kind hind | **hind** | femur 0.0259 **and** tibia 0.0116 — 2 remain | **refused_tie_remains_within_kind** |
| 6 | rank 10 @ 0.36 mm | already-labeled: hand_class, chain_kind fore | **fore** | forearm_class 0.0000 **and** humerus 0.0181 — 2 remain | **refused_tie_remains_within_kind** |

Why the prediction failed: B-2 (max extent 45.21 mm) sits between the femur envelope [46.41, 46.44] and the tibia envelope [44.62, 44.69] — both admit it; B-6 (40.98 mm) sits inside the forearm envelope [40.87, 44.28] and the humerus envelope [41.74, 43.14] — both admit it. A robust 41–45 mm bone is length-ambiguous between the two proximal slots of *either* limb. The 16/24 target is reachable only by assuming anatomical contact direction (foot→tibia, hand→forearm); **both assumptions are contradicted by A's own measured contact grammar**: A's feet touch *both* femora (A15–A2 1.01 mm, A17–A3 0.69 mm) and tibiae (A25–A6 0.66, A24–A7 0.86), and A's hands touch *humeri* (A8–A4 0.73, A9–A5 0.86), never forearms. Both auxiliary readings are recorded in `falsifiers.7_companion_tiebreak.auxiliary_readings` with `counted_confident: false`; neither is counted.

**Measured B totals: 9 retained high + 5 transferred = 14/24; labels added by the companion tiebreak: 0; mission prediction 16/24: false.** B-2 and B-6 carry refusal-confidence strings naming the partner and the residual tie.

## 3. Task 2 results — all three A medium feet corroborate (one flagged borderline); A = 21 high + 0 medium (total 21/24)

Pairwise max-extent agreement (mm, rel = |a−b|/max; tolerance 0.10):

| pair | A extent | B extent | rel | within 10% | |
|---|---|---|---|---|---|
| A15 ↔ B16 | 14.48 | 14.87 | 0.0262 | yes | |
| A15 ↔ B17 | 14.48 | 14.94 | 0.0308 | yes | |
| A17 ↔ B16 | 14.51 | 14.87 | 0.0242 | yes | |
| A17 ↔ B17 | 14.51 | 14.94 | 0.0288 | yes | |
| A18 ↔ B16 | 13.39 | 14.87 | **0.0995** | yes | **BORDERLINE (flagged)** |
| A18 ↔ B17 | 13.39 | 14.94 | 0.1037 | no | |

- **A-15 upgraded medium→high**, corroborated by B feet 16 and 17 (best 0.0262).
- **A-17 upgraded medium→high**, corroborated by B feet 16 and 17 (best 0.0242).
- **A-18 upgraded medium→high**, corroborated by B foot 16 only, at 0.0995 — 0.05% inside the gate; flagged BORDERLINE in the confidence string and in `falsifiers.8_mutual_corroboration`. The conservative |a−b|/own-length reading (0.1105) would refuse it; the upgrade follows the lane's preregistered |a−b|/max convention and is recorded, not tuned.
- Symmetric: **B16 is corroborated by A feet 15, 17, 18; B17 by A feet 15, 17** — recorded in `prediction_outcome.000875599.corroborated_b_feet` and `falsifiers.8_mutual_corroboration.b_side_corroboration`. B's transferred-feet confidence strings are unchanged (their labels came from the v3 transfer gate; corroboration is provenance, not a new verdict).

Which corroborates which: **A15↔{B16,B17}, A17↔{B16,B17}, A18↔{B16}; B16↔{A15,A17,A18}, B17↔{A15,A17}.**

## 4. Task 3 — labeled overlays (6 PNGs in `overlays/`)

Method (the projection history's, from `.tmp/decimate_meshes.py`): binary bone volume at the manifest threshold → `mip = bone.max(axis)` per axis (0=axial, 1=coronal, 2=sagittal) → transpose → scale so width = 900 → NEAREST. The binary volume here is the committed segmentation rasterized back onto the manifest grid (triangle barycentric lattice at 0.3-voxel step, deterministic — no random seeds, no parity fill). The base underlay is the **existing committed PNG**; on top, each pixel is colored by its per-ray **dominant** (mode) bone label, ties to the smaller rank: per-class palette (legend in-image), unlabeled bones gray, the axial composite (rank 1) left grayscale, per-bone rank numbers at the projected centroids (white text, black stroke).

| file | specimen | view | regenerated-MIP vs committed-PNG IoU |
|---|---|---|---|
| `overlay_sagittal_000875604.png` | A | sagittal | 0.7667 |
| `overlay_coronal_000875604.png` | A | coronal | 0.7730 |
| `overlay_axial_000875604.png` | A | axial | 0.8999 |
| `overlay_sagittal_000875599.png` | B | sagittal | 0.7579 |
| `overlay_coronal_000875599.png` | B | coronal | 0.8127 |
| `overlay_axial_000875599.png` | B | axial | 0.9060 |

The IoU gap (why not ~1.0) is understood, not hidden: the committed PNGs are raw-threshold MIPs and include the threshold's speckle halo; the committed meshes come from the morphologically cleaned components, so the regenerated masks are tighter. Alignment is confirmed by the mask edges sitting on the bone edges in every view (visually verified on all six). A first draft's even-odd parity fill leaked (rel diff 3.14 vs manifest voxel counts — the decimated previews are not guaranteed watertight); diagnosed and removed as unnecessary: a binary MIP lights any ray with ≥ 1 surface mark, and the per-ray dominant label only needs the entry/exit wall voxels (bones do not interpenetrate, so every mark on a ray carries that bone's label).

`overlays/overlay_render_receipt.json` carries the per-bone surface-mark counts and the IoU table.

## 5. Honesty notes (for the verifier)

- **The headline number went DOWN from the mission's prediction and is reported as measured:** B = **14/24**, not 16. The companion machinery works and its evidence is real; what fails is the implicit assumption that kind-resolution suffices. Both refusals carry the partner, the kind it fixes, and the surviving class tie, with numbers.
- The membranes were written into the output JSON **before** any measurement (they are constructed before the geometry is read in `companion_correlate_v4.py`, and sit at the top of the JSON). Nothing was tuned after seeing outcomes; the borderline flag (0.095) was in the membrane before the run and A-18's 0.0995 trips it.
- A's edits are exactly three confidence strings (ranks 15, 17, 18); every other A field is asserted identical to v3. B's edits are exactly the two refusal strings on ranks 2 and 6; every other B field is untouched v3.
- All max extents were recomputed from the meshes and asserted against v3's published tables (≤ 0.011 mm deviation) before any decision used them.

## 6. Verification and boundaries

- **Graph tests green:** `PYTHONPATH="<worktree>;<worktree>/tools/creature_graph/tests" python -B -m unittest tools.creature_graph.tests.test_contracts` — **Ran 19 tests, OK**, in this worktree.
- `bone_identification_v4.json` round-trips (`json.loads`); membrane block verified as the third top-level key (after `schema`, `lane`).
- All work confined to new files under `tools/science_funnel/data/morphosource_ct/` in worktree `E:\ChimeraWork\id3-agent`, branch `agent/bone-id-v3-companion`; nothing pre-existing modified; master untouched; port 8127 untouched; push limited to this lane.
- Commit trailer: `Agent: GLM 5.3`.
