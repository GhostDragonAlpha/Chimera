# ANATOMY COMPILER 02 — ACTUAL-MONKEY FIT (V2 AXES + UNRESOLVED LEDGER)

**Agent:** bigpickle | **Date:** 2026-09-23 | **Scope:** `.tmp/anatomy_compiler/` (build only; no production edits, no commit, no MuJoCo, no training/attachment-force/display-mesh work)
**Membrane:** `.tmp/anatomy_compiler/DERIVATION.md` (F1–F7) **amended in-session by** v2: one scale per axis, each axis EVIDENCE or an AUTHORED ASSUMPTION; segments whose endpoints the target does not declare stay **UNRESOLVED** (never a silently inherited length); preregistered aspect-bounds policy REFUSE|FLAG (never silent repair); nonuniform affine-image mass/inertia closed forms with `mass_kind`.
**Inputs (read-only):** `Saved/meshes/monkey_birth.bin` (sha256 `550A5B3EC927EA13614AD250963B23E2948E76A238AC110DA9889F339AABFA3C`, 18459 verts / 36630 tris) + `monkey_joints.bin` (sha256 `74B3AB044B7ADAED4A0F9349A81F5D3C87441084B2EC8981F4E0AFABA50C1662`, 28 joints); authored prototype scale 0.065 m/unit.

**Verdict: F1–F7 + G0 + S1–S4 all pass (`python run_tests.py` → exit 0). The actual-monkey fit packet is written: `runs/actual_monkey_fit.json`. The aspect-bounds policy DID its job — the radius transverse scale is implausible (band contaminated by the palm) and is FLAGGED, never repaired.**

---

## 1. Trace closed: the 7.155 / 157.7 kg hand inflation (fixture coupling, not a compiler bug)

`trace_hand_scale.py` — exact numbers, grounded against the REAL XML:

| Quantity | Value |
|---|---|
| grounded source hand piece `s_src_real` (hand_r origin → farthest referenced site, `ECRL-P4`) | **0.042783 m** |
| authored target hand length `TARGET_LENS['hand_r']` | **0.300000 m** |
| grounded axial ratio | **7.012075** |
| synthetic-twin ratio (twin proportion 0.98) | **7.155179** ← the number that was printed |
| grounded `detS` | `344.778` (grounded) ≡ ratio³ |
| twin `detS` | `366.321` ≡ ratio³ |
| mass chain | `0.4575 kg × 344.778 = 157.736 kg` (≈157.74 was the printed twin number) |

**Root cause:** the fixture *authored* `hand_r = 0.30 m` and the real XML's hand has a 0.0428 m site span — a 7× fixture coupling. Mass explosions downstream were `mass_src × detS`. Not a compiler defect; the v1 compiler had no mechanism to refuse a length it could not measure.

## 2. v2 design executed

- **CorrespondenceSegment v2** (`schema.py`): `axis_evidence` (4 landmark ids per axis: target pair + source pair), `axis_assumptions` (`value/note/provenance`), `transverse_required`, `axial_unresolved`, `axial_pair`, `transverse_pair`.
- **FittedSegment v2**: `scale_provenance`, `axis_sources` (`axial/b/c` ∈ `evidence|assumption|unresolved`), `assumption_notes`, `status` = `SEG_RESOLVED | SEG_UNRESOLVED | SEG_FLAGGED`.
- **`_Segment`** resolves each axis independently. Legacy semantics preserved exactly (F1–F7, S1 re-run green): `uniform` remains the default and is now *labelled* `uniform_legacy: b/c inherit axial (blanket, not evidence)` → `AXIS_ASSUMED`, counted in the audit.
- **`build_segments`** returns `(ordered, seen, unresolved_bodies)`; missing segments are **reported, not refused**. `fit()` keeps all shared measured joints, orders all sites, and leaves unresolved ones **ordered-but-unplaced** (`NaN`, `FittedSite.unresolved`); unresolved tendons get `path_incomplete:<body>` status with `rest_length = NaN`; a segment is only claimed when **all three axes** are sourced.
- **Aspect bounds** `aspect_bounds.py`: profiles `unbounded` (default = legacy byte-exact), `policed` (max_magnitude 5.0, min 0.2, max_aspect 6.0, `refuse`), `policed_flag` (same, `flag`). Refusal named `aspect_out_of_bounds`; flags go to `residuals["aspect_flag.<body>"]`.
- **Physiology**: `mass_kind = source_effective_x_det_scale`, `density_assumption = uniform_constant_density_scale`, `nonphysical_inertia` refusal on non-positive-definite fitted inertia; closed forms (DERIVATION §9) unchanged — `mass' = m·|detD|`, `Σ' = |detD|·D·Σ·Dᵀ`, `I' = tr(Σ')I − Σ'`.

## 3. Actual-target correspondence (measured, nothing invented)

Two corrections found by measuring, not assumption:

1. **The source FOREARM bone is the RADIUS, not the ulna.** Source `ulna→radius` = 0.023 m (a 2.3 cm elbow-head piece); `radius→hand_r` = 0.292 m (the forearm). The pack `elbow→wrist` corresponds to the **radius** (pack elbow_R = its proximal articular, wrist_R = its distal/hand root). First mapping attached it to `ulna` and produced the absurd fitted ulna 2.81×; the corrected radius fits at **0.222×** — consistent with the humerus 0.229×.
2. **The pack spine joints map 1:1 onto the source spine column origins** (verified by height alignment): `spine_lower` ↔ pelvis origin, `spine_mid` ↔ thorax_dummy origin, `spine_upper` ↔ thorax origin (shoulder height). So `thorax_dummy` ↔ `spine_mid→spine_upper` (0.0844/0.3785 = **0.223**). The `spine_lower→spine_mid` piece (pelvis→waist) has **no source body** carrying it → pelvis keeps scale 1 as root; the spine_mid region is honestly left unscaled. `thorax` is UNRESOLVED (its source piece runs to the shoulder, not up the spine).

Final ledger — **9 resolved / 9 unresolved**, aperture F1 shared-joint separation **exactly 0.000e+00 m**, chirality **+1.000 (right)**:

| segment | pack pair (evidence) | fitted scale [a b c] | sources |
|---|---|---|---|
| femur_r/l | hip→knee | [0.3632 0.9939 0.6108] | EEE |
| tibia_r/l | knee→ankle | [0.3386 0.4884 0.8252] | EEE |
| humerus/_l | shoulder→elbow | [0.2290 1.2848 1.1619] | EEE |
| radius/_l | elbow→wrist | [0.2217 **2.6372** 0.4434] | EEE **→ FLAGGED** |
| thorax_dummy | spine_mid→spine_upper | [0.2226 1.0 1.0] | EAA (b/c authored) |
| thorax, ulna/_l, hand/_l, talus/_l, toes/_l | — | **unresolved** | declared_unresolved |

**Rule-0 falsifier that LOST here (the good kind):** "the radius transverse scale can be trusted." Falsified by the aspect policy — `b/axial = 2.637/0.222 = 11.9 > 6.0`. Cause: the wrist band's primary-owner vertices include the palm; the transverse "width" of the bone is not measurable at that band. The fit **proceeded but flagged** (`SEG_FLAGGED`, `aspect_flag.radius`), and under `policed` it would REFUSE. The forearm's b/c remain unmeasurable from the pack; reported, not trusted.

## 4. Numbers that came out fitted (measured, deterministic)

- Sites: **300 placed / 168 ordered-unplaced** (468 total). Tendons: **42 derived / 78 path_incomplete** (all wrist/ankle/finger muscle-belly paths cross unresolved bodies; their `rest_length` is NaN, never a fabricated value).
- Physiology (affine-image transport, `source_effective_x_det_scale`): pelvis 11.777 kg (root, detS 1,000); femur_r/l 1.435 each (src 6.511); tibia_r/l 0.354 (src 2.595); humerus/_l 0.834 (src 2.439); radius/_l 0.189 (src 0.729, **flagged**); **TOTAL fitted 17.402 kg**. These are transported *source effective* values (constant density), **not reconstructed tissue masses** — the trunk and digits are not in the total because they are unresolved.

## 5. Falsifier surface, session 2 (all green)

| ID | Promise | Result |
|---|---|---|
| S2 | NONUNIFORM affine-image mass/inertia closed forms, recomputed **independently** from correspondence landmarks (not re-read from packet) | PASS (every resolved body, incl. root; inertia rigid to 1e-9, positivity asserted) |
| S3 | aspect bounds: `unbounded` proceeds unflagged (legacy byte-identical), `policed_flag` sets `aspect_flag.radius`, `policed` REFUSES `aspect_out_of_bounds` naming radius — never silent repair | PASS |
| S4 | actual-monkey packet invariants: chirality +1/right, closure 0.0, exact 9/9 ledger, axial ratios re-derived from raw pack/source distances (femur 0.3632, tibia 0.3386, humerus 0.2290, radius 0.2217, thorax_dummy 0.2226 to 1e-6), n_axis_evidence 25 / n_axis_assumptions 2 / blanket_uniform False, pelvis detS 1, total 17.402±0.05, inertia spectra positive, 120 tendons (42 derived / 78 NaN), deterministic re-fit byte-identical | PASS |
| (regression) | F1–F7, S1, whole-body example: behaviors byte-identical, `example_whole_body.py` double-run SHA-equal | PASS |

## 6. Artifacts (`runs/` unless stated)

- `actual_monkey_fit.json` — the actual-target fit packet (v2 schema, full ledger).
- `actual_monkey_tables.txt` — human table of the packet.
- `figure_actual_fit.png` — static inspection figure (front + side): grey mesh, pack joints, resolved skeleton with axial scalars, flagged radius in red, unresolved anchors as orange x, root star. **I cannot visually confirm the png (no image input) — it needs an eyeball.**
- `probe_target.py`, `probe_transverse.py`, `trace_hand_scale.py`, `mesh_target.py`, `aspect_bounds.py`, `actual_target_fit.py`, `figure_fit.py`, `_inspect_packet.py` — reproducible measurement/build scripts.
- `run_tests.py` gains S2/S3/S4 (F1–F7 unchanged). Suite: `exit 0`.

## 7. What ISN'T claimed (honest boundaries)

- The trunk (`thorax`), elbow-head (`ulna`), hands and feet scale is **unknown** from the pack: no target joint declares their endpoints. Leaving them unresolved is the law's answer, not a stall.
- Fitted masses are affine transports of the model's own effective masses, not tissue reconstructions.
- The radius b/c are **flagged**; the forearm's true cross-section is not in the pack's coords.
- The spine_mid→spine_lower piece and root pelvis keep scale 1 (root bone).
- No production file was modified; nothing committed.