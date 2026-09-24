# A4 AUDIT REPORT — local-to-world transforms + bilateral correspondence

**Auditor:** A4 (audit agent) · **Date:** 2026-09-24 · **Scope:** baseline_snapshot (read-only)
**Method:** independent recompute from snapshot inputs. Every input hash-verified before use:
`source_xml/chimanoid.xml` sha256 `675e00d0…` == fit's `meta.source_identity.raw_sha256`;
`inputs/monkey_birth.bin` `550a5b3e…` and `inputs/monkey_joints.bin` `74b3ab04…` == fit's
`meta.provenance.input_files[*].sha256`. Baseline code was copied to `work/code/` and the
source ONB + correspondence were REBUILT from the XML (not trusted from the packet).

**HEADLINE: all five criteria PASS. Preregistered falsifier NOT triggered.**
Reconstruction max 1.1525e-09 m (claim 1.15e-9, reproduced bit-for-bit; full-precision 5.6e-17 m).
Mirror max 0.6306 mm / mean 0.0547 mm across x = 0 (claims 0.63 mm / 0.055 mm); 0 pairs > 20 mm.
Handedness = **preserve**, recorded at `runs/actual_monkey_fit.json:119`; `mirror_plane_normal: null` (:120).

---

## Criterion 1 — per-body transform audit table — PASS

The packet carries exactly two bodies (`assert set(packet["bodies"]) == {"radius","radius_l"}` in
`scripts/a4_audit.py`), 16 sites each, all 32 resolved. Export rounding per
`code/attachment_candidates.py`: R at 12 decimals (:178), t at 9 (:179), fitted_pos_local/global
at 9 (:141-142).

| body | ‖RᵀR−I‖max | det(R) | singular values (all ≈ s) | s = fit scale | ‖QᵀQ−I‖max (Q=R/s) | det(Q) | t (packet, m) | t vs fit `fitted_origin` max abs |
|---|---|---|---|---|---|---|---|---|
| radius | 0.9508460968 | 0.0108977544 | 0.22170679566588 / 0.22170679566531 / 0.22170679566499 | 0.22170679566544982 | 2.64e-12 | **+1.0000000000** | (−0.115480984, 0.319109077, −0.006076556) | 4.54e-10 |
| radius_l | 0.9508460968 | 0.0108977544 | 0.22170679566595 / 0.22170679566541 / 0.22170679566505 | 0.22170679566544982 | 2.62e-12 | **+1.0000000000** | (+0.115480984, 0.319109077, −0.006076556) | 4.54e-10 |

**The brief's raw orthonormality number needs interpretation (finding, not defect):** R is NOT a
rotation — it is a uniform scale times a rotation, exactly as the packet's declared composition
`R = Bp @ diag(scale) @ B.T` (`code/attachment_candidates.py:180`) produces with the fit's uniform
`scale = [0.22170679566544982]×3` (`runs/actual_monkey_fit.json`, segments). Measured ‖RᵀR−I‖max
= 0.9508460968 = |s²−1| exactly (s² = 0.0491539032), i.e. RᵀR = s²I to machine precision — pure
uniform scale × rotation, zero shear (singular-value spread ≤ 9.1e-13). The underlying rotation
Q = R/s is orthonormal to 2.6e-12.

**det sign vs policy:** `code/correspondence.py:42-43` (docstring): "Segment frames downstream are
always proper (det +1) by construction." Measured det(Q) = +1.0000000000 both bodies — consistent.
det(R) = s³ = 0.0108977544 (matches ∏scale = 0.0108977544 to 8e-15). The fit's global chirality is
also proper: `actual_monkey_fit.json:48850 "chirality_det": 0.9999999999999998`.

**Composition independently verified:** B rebuilt from the fit's own landmark resolution
(`corr.source_landmarks` via rebuilt `build_correspondence_envelope`):
radius: prox `body_origin:radius` (−0.0911, 0.823047, 0.177699) · dist `body_origin:hand_r`
(−0.0731, 0.532647, 0.202699) · roll `site:PT-P2` (−0.08304, 0.80082, 0.14338);
radius_l: prox `body_origin:radius_l` · dist `body_origin:hand_l` · roll `site:PT_l-P2` (z-mirrored).
Rebuilt R (= Bp @ diag(scale) @ Bᵀ, Bp/scale from the fit's full-precision segment records) vs the
packet's exported R: **max abs element diff 3.93e-13 (radius) / 4.73e-13 (radius_l)** — exactly the
packet's 12-decimal export rounding bound (5e-13).

**t audit:** packet t == fit `segments[*].fitted_origin` within 4.54e-10 ≤ 5e-10 (9-decimal export
rounding). t_radius and t_radius_l are exact x-mirrors at export precision (±0.115480984).

## Criterion 2 — 32-site reconstruction errors — PASS

Recomputed `t + R @ source_pos_local` for all 32 sites from the packet's exported (rounded) values
vs the packet's stored `fitted_pos_global` (both at export precision — the quantity step A claimed):

- **max = 1.1525314521376605e-09 m, mean = 7.5466e-10 m; worst site: BIClong-P9** (then
  ECRB_l-P2 1.068e-09, BICshort-P6 1.059e-09, ECRB_l-P3 1.050e-09, ECRB-P2 1.030e-09).
- Claim (`runs/experiment_transverse_candidate.json` → `step_A_verification.reconstruction_max_err_m`
  = 1.1525314521376605e-09): **reproduced bit-for-bit** by this independent recompute (deterministic
  path over identical rounded inputs).
- Preregistration bound: ≤ 1e-8 m → met with 8.7x margin. Falsifier (> 1 µm): not triggered
  (max = 0.00115 µm).
- Packet's own per-body `max_world_reconstruction_error_m` = 0.0 (both bodies) — that field is the
  IN-MEMORY full-precision reconstruction, and my full-precision check confirms it.

`source_pos_local` equality: all 32 exported values == the fit's `sites[*].source_pos_local`
bit-exact (max abs diff 0.0) — session-5 correction 1 (report 05 §1) holds in the shipped packet.

## Criterion 3 — 16-pair bilateral table — PASS

Pairing: name map (BRD-P2 ↔ BRD_l-P2) — 16/16 matched. **Tendon-family identity verified two
ways, all 16 pairs OK:** (a) packet `tendon_membership` families correspond under the `_l` map
(tendon, index_in_path, path_length, role all equal); (b) the fit's ordered `tendons[*].sites`
paths in `actual_monkey_fit.json` place each site at the same index in the corresponding family path.

**Plane from the fit's own data:** the target-mesh pack spine joints (`mt.joint_pos` — the same
derivation as `code/experiment_transverse_fit.py:199`) sit at x = 0.0 exactly
(spine_lower = spine_mid = spine_upper = 0.0); recorded `sagittal_plane_x_m` = 0.0
(`experiment_transverse_candidate.json`). Data-driven cross-check: mid-x of the 16 paired points
= −1.15e-05 m; re-running the mirror on that plane gives max 0.612 mm / mean 0.0746 mm — no verdict
changes. Mirror used: (x,y,z) → (−x, y, z).

| pair | dist (mm) | pair | dist (mm) |
|---|---|---|---|
| BIClong-P11 | 0.000000 | FCU-P2 | **0.244653** |
| BIClong-P9 | 0.000001 | FCU-P3 | 0.000001 |
| BICshort-P6 | **0.630636** | PT-P3 | 0.000002 |
| BICshort-P8 | 0.000000 | PT-P5 | 0.000001 |
| BRD-P2 | 0.000001 | ECRB-P2 | 0.000001 |
| BRD-P3 | 0.000002 | ECRB-P3 | 0.000001 |
| ECRL-P2 | 0.000001 | ECRL-P3 | 0.000001 |
| ECU-P5 | 0.000001 | FCR-P2 | 0.000000 |

- **max = 0.6306 mm (BICshort-P6), mean = 0.0547 mm** vs claims 0.63 mm / 0.055 mm
  (recorded rounded: 0.000631 / 5.5e-05) — matched.
- Structure: 3 pairs bit-exact zeros; 11 pairs at 1–2 nm (packet 1e-9 export rounding);
  exactly TWO real deviations: **BICshort-P6 0.6306 mm and FCU-P2 0.2447 mm** — the left side is
  a near-exact mirror of the right everywhere except these two sites.
- Sanity bound: **0 pairs > 20 mm** — falsifier not triggered. All 16 pairs also far inside the
  1 mm fit margin except the two named, which are still ≤ 0.63 mm.

## Criterion 4 — handedness mode + plane evidence — PASS

**Mode = preserve for the actual-monkey fit.** Recorded in the fit artifacts:

- `runs/actual_monkey_fit.json:119` — `"handedness": "preserve"` (audit.correspondence)
- `runs/actual_monkey_fit.json:120` — `"mirror_plane_normal": null`
- `runs/actual_monkey_fit.json:48850-48851` — `"chirality_det": 0.9999999999999998`,
  `"frame_handedness": "right"` (measured proper image, consistent with preserve)
- `runs/actual_monkey_fit.json:7` — meta `"frame_handedness": "right"`; `:42` coordinate
  conventions `"handedness": "right"`; fit_mode `"grounded"` (meta).

Guard consistency: `code/correspondence.py:86-93` — mode must be preserve|mirror (:86-87);
"mirror mode requires mirror_plane_normal" (:88-89); normal must be a unit vector (:90-93).
With mode = preserve, `mirror_plane_normal: null` is the LEGAL state — the guard is satisfied,
not skipped. The x = 0 plane used in the step-A symmetry check is a verification plane derived
from the target pack's spine joints (experiment_transverse_fit.py:197-220), not a correspondence
mirror operation, so no guard interaction arises.

Context (negative finding preserved): `runs/mirror_read.json` is the SYNTHETIC-twin read, not the
actual-monkey fit — `meta.fit_mode = "synthetic"`, `frame_handedness = "left"`, `mirror_reflect =
"true"`, and its correspondence carries `handedness = "preserve"` with `mirror_plane_normal =
[0.0, 1.0, 0.0]`. It must not be cited as the actual-monkey policy record; the actual fit's record
is actual_monkey_fit.json:119-120 (grounded / preserve / null).

## Criterion 5 — baseline integrity — PASS

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty; 0 lines; rc=0; 45 files tracked under the path; not git-ignored — check-ignore rc=1)
```
Re-verified at audit end. No baseline file was written by this audit (baseline modules were
copied to `work/code/`; the audit imports run from there with PYTHONDONTWRITEBYTECODE=1).

## Cross-check — export precision reconciliation (criterion/task 4)

- Report 05 §3 (`session_reports/anatomy_compiler_05.md:30`): "Reconstruction error recorded per
  body (0.0 at export precision; verified < 1 µm in step A)." Both halves verified:
  - "0.0 at export precision" = full-precision internal reconstruction: my rebuilt-transform
    reconstruction vs the fit's full-precision `fitted_pos_global` gives **max 5.55e-17 m**
    (14/32 sites exactly 0.0; the rest 1e-19…5.6e-17 — float64 noise), which rounds to the
    packet's recorded 0.0 at 15 decimals (`attachment_candidates.py:181`).
  - "< 1 µm in step A" = packet-export reconstruction: **1.1525e-09 m** (this audit, bit-identical
    to the recorded step-A value). The gap between the two numbers is fully accounted for by
    export rounding: t at 9 decimals (≤5e-10) + stored `fitted_pos_global` at 9 decimals
    (≤5e-10) + R at 12 decimals (≤5e-13 × ~0.13 m lever ≈ 7e-14) ⇒ expected ≤ ~1.0e-09;
    observed max 1.15e-09 (worst-case rounding stack) — reconciled, nothing unexplained.
- Hash chain for the audited artifacts: `runs/attachment_candidates.json` sha256 `854f7097…` ==
  MANIFEST.json:183; `runs/actual_monkey_fit.json` sha256 `a4475550…` == MANIFEST.json:168 ==
  the packet's declared `fitted_packet_sha256` (attachment_candidates.json:1736) == report 05
  header. Naming note (documented in-file, no defect): the packet field named
  `fitted_packet_sha256` holds the hash of the FIT packet (actual_monkey_fit.json), not of the
  candidates packet itself — the field's `note` and MANIFEST's H-1 crosscheck both say so
  (names_fit_packet: true, names_candidates_packet: false).

## Preregistration verdict (frozen)

| prediction | result | verdict |
|---|---|---|
| reconstruction max ≤ 1e-8 m | 1.1525e-09 m (full-precision 5.6e-17 m) | met |
| mirror max in 0.4–0.9 mm, mean < 0.1 mm | 0.6306 mm / 0.0547 mm | met |
| mode recorded explicitly in fit artifacts | actual_monkey_fit.json:119 "preserve" | met |
| FALSIFIER: any recon err > 1 µm OR any pair > 20 mm | max recon 0.00115 µm; max pair 0.63 mm | **not triggered** |

## Uncertainties / limitations

- Exact step-A reproducibility (bit-identical 1.1525314521376605e-09) follows from running the
  same declared arithmetic on the same rounded inputs; independence here is in method
  (recomputed from packet file + rebuilt correspondence), not in a divergent implementation.
- The mirror test is at packet export precision (1e-9 floor): nm-level pair errors are
  indistinguishable from rounding noise; only BICshort-P6 (0.63 mm) and FCU-P2 (0.245 mm) are
  unambiguously real deviations from symmetry.
- The plane x = 0 is exactly supported by the pack spine joints (all x = 0.0); the paired points'
  own best midplane is x = −1.15e-05 m (11.5 µm) — inside rounding-and-fit noise, no verdict impact.
- This audit verifies geometry/transforms only; containment verdicts, endpoint roles, and
  qualification status are out of scope (packet ships mechanical_qualification=false everywhere).

## Receipts

- `scripts/a4_audit.py` — the audit (single run; `work/a4_results.json` = full per-site/per-pair data).
- `receipts/a4_audit_run1.txt` — full console output of the run.
- Command: `cd /e/PythonChimera/forearm_package/audits/A4_transforms && PYTHONDONTWRITEBYTECODE=1 python scripts/a4_audit.py`
- Inputs hash-verified pre-run (sha256sum, see Method); baseline untouched (criterion 5).
