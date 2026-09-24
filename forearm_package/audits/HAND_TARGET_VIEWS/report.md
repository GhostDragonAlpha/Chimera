# REPORT — M-handtgt: R1 target-view deliverable candidates (opposed orthographic views of the hash-pinned target hand region)

**Agent:** M-handtgt · **Date:** 2026-09-24 · **Brief (frozen):** `brief.md` (verbatim copy) · **Prereg:** `PREREG.md` + `PREREG_AMENDMENT_1.md` (both frozen BEFORE the official renders)
**Fulfills:** `audits/HAND_EVIDENCE_REQUEST/HAND_EVIDENCE_REQUEST.md` §R1 — two opposed orthographic renders of the hash-pinned birth mesh's right-hand distal band with declared camera extrinsics, for HUMAN palm/dorsum labeling; left-hand mirror check; CPU-only.
**Headline:** **ACCEPTANCE 6/6 MET — the opposed pair + mirror check are rendered, reproducible (byte-identical across two unmodified runs), and the human labeling card is prepared.** One substantive pre-render finding was measured and prereg-amended (the R1.4 default camera is near edge-on to the measured broad faces; the face-on ±T_R pair is the primary deliverable, the literal R1.4 pair is kept as a declared record that FAILS the R1.5-3 visibility bar — recorded, not tuned away). No palm sign is authored here; the verdict is reserved for the human terminal per R1.3-D.

---

## 0. ACCEPTANCE VERDICTS (the brief's six)

| # | criterion | verdict | evidence |
|---|---|---|---|
| 1 | frozen prereg | **PASS** | `PREREG.md` (camera pair, crop, annotation plan, falsifiers, stop rule) frozen before any render; one amendment `PREREG_AMENDMENT_1.md` — also frozen before the OFFICIAL renders and driven only by render-free arithmetic + a debug-render occlusion finding (§2 below); no image was inspected for palm/dorsum content before the amendment was frozen, so F-R1a's "no re-framing after a failed identification" is untouched |
| 2 | render script CPU-only (Agg stated) | **PASS** | `scripts/render_hand_views.py`: `matplotlib.use("Agg")` BEFORE pyplot import (O1/O2 precedent); imports are numpy + matplotlib only; grep for OpenGL/Vulkan/WebGL/GLFW/pyglet/moderngl/vispy/CUDA finds NO import (only the docstring's "NO GPU" sentence); custom numpy z-buffer orthographic rasterizer, supersample 2 |
| 3 | the opposed pair + mirror check at declared paths | **PASS** | `figures/hand_target_R_view1_plusT.png`, `figures/hand_target_R_view2_minusT.png` (primary, letters A/B), `figures/hand_target_L_mirror_check.png` (mirror consistency), plus the two record-only literal-camera PNGs; sidecar JSON per render with the §R1.3-C fields |
| 4 | reproducibility hashes | **PASS** | two unmodified runs (`receipts/run1.log`, `run2.log`): ALL 10 output files byte-identical (`receipts/hashes_run1.txt` = `hashes_run2.txt`) — falsifier (a) does NOT fire |
| 5 | the labeling card | **PASS** | `LABELING_CARD.md`: the two figures, the question ("which lettered face is the PALM (ventral) — A or B?"), camera declarations, what each answer closes, answer template naming the human terminal, F-R1a/F-R1c handling |
| 6 | integrity: baseline porcelain empty (paste) | **PASS** | `git status --porcelain -- forearm_package/baseline_snapshot` → **empty** at start and at end (HEAD `768f3de04a3b5539a80cf85d9a4587505da8385d`); no git writes; no `__pycache__`/`.pyc` anywhere under the audit dir; all writes confined to `forearm_package/audits/HAND_TARGET_VIEWS/` |

**Stop rule:** the pair rendered + reproducibility proven + the human-question card prepared → STOPPING here. No curvature/assembly/scale/production quantity was computed; §R1's non-requests (§4 of the request) were not touched.

## 1. IDENTITY PINS (re-asserted before rendering; falsifier F-R1b clean)

| pin | asserted | result |
|---|---|---|
| `monkey_birth.bin` sha256 `550a5b3ec927ea13…` (661,076 B) | before every render | OK (run logs) |
| `monkey_joints.bin` sha256 `74b3ab044b7adaed…` (296,589 B) | before every render | OK |
| loader copy `work/mesh_target_htv.py` ≡ `baseline_snapshot/code/mesh_target.py`, sha256 `268f139a9e90e561…` | before reuse | OK (byte-identical) |
| `mesh_unit_to_m = 0.065` (authored) | from the loader | OK |
| derived frame vs R1.4/O2 recorded values | asserted at recording precision | all OK: wrist_R maxdiff 4.6e−7; a_R 2.7e−7; T_R 2.6e−7; n_t 2.2e−6; look_at 5.7e−7 (elbow_R 2.3e−5 vs its 4-decimal recording); left-hand mirror values likewise |
| mesh repair/resampling | — | **NONE**: the rendered surface derives from the pinned file verbatim (declared in every sidecar) |

## 2. THE PRE-RENDER GEOMETRY FINDING (measured; why the prereg was amended)

The R1.4 default camera opposes its pair along `n_t = a × T_R ≈ world +z`, calling n_t the "broad-face normal candidate". Render-free measurement of the pinned mesh (`scripts/geometry_probe.py`, receipt `receipts/geometry_probe.txt/.json`):

- Per-station exact sections of the distal band: extent along **T_R = 15.7→5.7 mm**; extent along **n_t = 50.0→23.1 mm**; section PCA major axis · n_t = ±0.999 at every station.
- Far end (80–111.4 mm, r<42 mm): PCA major extent **47.1 mm** (matches B1's recorded 47.1) with major direction · n_t = **−0.9989** — the 47.1 mm extent lies ALONG n_t.

**Consequence:** the band's sections are lenses ~46–50 mm wide along n_t and ~6–16 mm thick along T_R. The two BROAD faces (O2's ±T faces, the ones its curvature test measured) are normal to **T_R**, not to n_t; n_t is the lens's WIDTH direction. The literal R1.4 ±n_t camera therefore views the lens nearly edge-on: the whole band projects to a **567.0 px** screen-right span — below R1.5-3's 600 px bar (the 47.1 mm face is spread along the view direction, where it cannot span the frame). R1.4 itself declares deviations acceptable "if fully declared in the sidecar (the requirement is REPRODUCIBILITY, not these numbers)", and §R1.3-A's design intent is "both broad faces are photographed". AMENDMENT-1 therefore added the face-on **±T_R pair as the PRIMARY deliverable** (letters A/B), kept the literal ±n_t pair as a **declared RECORD** of the frozen-prereg execution (no letters, its failing span recorded), and tightened the visibility metric to the far-end face population on which B1's 47.1 mm was recorded.

Debug-render finding, also amendment-driven: the +T_R eye position faces the monkey's torso, and in-column body skin at depths 0–150 mm occluded the band; measured in-column depth distributions (band at 260–333 mm in every view; body ≤ ~150 mm; far body ≥ ~520 mm) froze a declared **band depth slab [0.24, 0.36] m** along f (AMENDMENT-1 §A2.7) — the render is of the BAND REGION, exactly the task brief's "rasterize the band's silhouette + shading by the declared camera". Projection stays orthographic; extrinsics unchanged; slab declared in every sidecar.

## 3. THE DELIVERABLE VIEWS (all constants frozen in `scripts/render_hand_views.py`)

**PRIMARY pair (the human question):** opposed along ±T̂_R, `up = a`, ortho half-width 0.040 m, 2048×2048 px, eye distance 0.30 m, light `unit(0.25, 0.30, −1.0)` in the camera frame (identical relative geometry in both views — neither face favored), Lambert `I = 0.25 + 0.75·max(0, n̂·L̂)`, albedo 0.62, background 0.94, supersample 2.

- `figures/hand_target_R_view1_plusT.png` — **VIEW 1, +T_R-side view, FACE A toward camera**, eye (+0.084188, +0.050855, −0.005517) m, view dir (−0.890060, +0.455843, −0.000951)
- `figures/hand_target_R_view2_minusT.png` — **VIEW 2, −T_R-side view, FACE B toward camera**, eye (−0.449848, +0.324360, −0.006088) m, view dir (+0.890060, −0.455843, +0.000951)
- look_at = (−0.182830, +0.187608, −0.005802) m (= wrist_R + 0.083·a; full precision in the sidecars); `right` vectors and every §R1.3-B annotation on-image (title-strip camera declaration, 10 mm = 256 px scale bar, world axis triad with the toward/away-from-camera rule for the view-aligned axis, axial ruler ticks 48/55/80/111 mm in-frame + 0 mm = wrist_R as a frame-edge arrow 83 mm below frame, band edges marked, face letters with leader lines, O2 guidance line, depth-relief inset of the band pad)

**RECORD pair (literal R1.4 ±n_t cameras, no letters):** `hand_target_R_view1_literal_nt_record.png`, `hand_target_R_view2_literal_nt_record.png` — band span 567.0 px, far-end face span 462.3 px, both **< 600 px** (recorded FAIL of the R1.5-3 bar under the literal camera; kept byte-reproducibly as the frozen execution record).

**Mirror check:** `figures/hand_target_L_mirror_check.png` (2048×4096, both opposed L views) — letters by the declared MIRROR RELATION (+T_L = −M·T_R, O2's anti-mirror; so if the reader names the same letter on both sides, mirror consistency holds). Mesh x-mirror exactness measured 90.87 % verts / 88.11 % triangles → the check is visual; informational pixel receipt: L panel 1 vs x-flipped R view 1 mean |diff| 7.33/255, max 54, 25.3 % of pixels differ by > 8.

## 4. VISIBILITY BAR (R1.5-3; falsifier b assertions)

| view | whole-band u-span | far-end face (80–111.4 mm) u-span | bar ≥ 600 px |
|---|---:|---:|---|
| primary v1 (+T_R) | 1855.1 px | **1205.1 px** | PASS |
| primary v2 (−T_R) | 1855.1 px | **1205.1 px** | PASS |
| record v1/v2 (literal ±n_t) | 567.0 px | 462.3 px | FAIL — recorded (expected: the 47.1 mm face lies along that view direction) |

Crop assertions (falsifier b): all 715 band verts (t ∈ [55, 111.4] mm, r < 42 mm) project inside the frozen frame in every view (worst offset 39.88 mm of 40 mm, primary; 28.35 mm, record); band edges ≥ 3 mm inside the frame; band-edge stations of the ruler marked on-image. All assertions passed in both official runs.

## 5. OBSERVATIONS RECORDED FOR THE DOWNSTREAM TERMINALS (not verdicts)

1. At the full sampling of the pinned mesh, both ±T_R faces show **digit-like ridges** (the views read as a mitt with finger-like columns) — C2's "zero digit-distinguishable structure" was established on the r < 25 mm tube sampling and stands for that sampling; the face-on views supersede it as visual evidence and materially feed **§R3 / F-R1c** (the region reads as hand-like anatomy, not obviously tail/limb skin — for the human to confirm or deny on the card).
2. The depth-relief insets are consistent with O2's lens reading: in VIEW 1 (+T_R) the band pad reads flat (uniform relief); in VIEW 2 (−T_R) the pad carries a strong curvature gradient (the bulged side) — recorded as an observation only. **The card deliberately omits this and every ±T anatomical lean so the human's identification is not anchored.**
3. The literal-R1.4 record pair is itself evidence for the geometry finding: an edge-on blade of the recorded widths, 567 px, exactly as the probe arithmetic predicted.

## 6. INTEGRITY RECEIPT

- Baseline read-only: `git status --porcelain -- forearm_package/baseline_snapshot` → **empty at start and end**; HEAD `768f3de04a3b5539a80cf85d9a4587505da8385d`; no git writes.
- Inputs hashed before every run (`receipts/run1.log`, `run2.log`): birth `550A5B3E…` (661,076 B), pack `74B3AB04…` (296,589 B) — equal to MANIFEST; loader copy `268F139A…` byte-identical, verified before first use.
- Gaming-safety: all figures are matplotlib **Agg set before pyplot import** + a numpy z-buffer rasterizer; import list is numpy/matplotlib only; no OpenGL/Vulkan/WebGL/GLFW/pyglet/moderngl/vispy/CUDA import (grep receipt in §0.2 evidence; the only grep hit is the docstring's "NO GPU" sentence). No GPU broker queue was needed — the verified CPU-only path was used and is stated here per the law.
- `PYTHONDONTWRITEBYTECODE=1` on every invocation; no `__pycache__`/`.pyc` under the audit dir.
- All writes confined to `forearm_package/audits/HAND_TARGET_VIEWS/` (brief.md, PREREG.md, PREREG_AMENDMENT_1.md, LABELING_CARD.md, report.md, scripts/, figures/, receipts/, work/).
- Reproducibility: `receipts/hashes_run1.txt` ≡ `receipts/hashes_run2.txt` (10/10 files byte-identical). Final artifact sha256s (full table in `receipts/hashes_run2.txt`):
  - `hand_target_R_view1_plusT.png` `a05bc5f91912c5752cab9656675c35b7a38c2e8ac43927c0786aa4982a7aa066`
  - `hand_target_R_view2_minusT.png` `2c89036dde88cf0f680a316b1795795af31729bba212b531076bbf620dd16f75`
  - `hand_target_L_mirror_check.png` `23450745dc79cf7d25b6185e441232bc607c24cfcad4966a4cc14dbe340430ce`
  - `hand_target_R_view1_literal_nt_record.png` `232df880f6560974be26ad94a6b771bbc1c9ba5437174b5068ff710352b7c7f1`
  - `hand_target_R_view2_literal_nt_record.png` `5076da52270658f0c80844bc2edf3697e77d4a1149b471f4e6f907c699846e87`
  - (+ the 5 sidecar JSONs, hashed in the same receipts)

## 7. FALSIFIER DISPOSITION

- **(a) render not reproducible from the script constants** — did NOT fire (byte-identical runs).
- **(b) crop missing the distal band** — did NOT fire (all crop assertions passed; note the debug run's initial firing was a projection bug in the CHECK, not the camera — fixed and documented in AMENDMENT-1 §A2.4).
- **(c) any GPU usage** — did NOT fire (Agg + numpy only; no GPU contexts; receipt above).
- **F-R1a** — pending the human (the card asks; "cannot decide" fires it and is a recordable answer).
- **F-R1b** — clean (hashes asserted; no mesh modification).
- **F-R1c** — pending the human (the card asks whether the region reads as hand anatomy; observation §5.1 recorded to inform, not answer it).

STOP: acceptance 6/6 verdicted; the palm sign now belongs to the human terminal via `LABELING_CARD.md`.
