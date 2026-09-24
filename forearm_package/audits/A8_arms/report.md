# A8 — Moment Arms & Force Transmission Audit (forearm grasp tendons)

**Auditor:** A8 (evidence only; decisions owned by Astra) · **Date:** 2026-09-24
**Scope:** tendons touching the 32 declared forearm attachment sites (16/side, `radius`/`radius_l`),
at the fitted static pose, over the already-declared pose range.
**Baseline (read-only):** `E:/PythonChimera/forearm_package/baseline_snapshot/`
**Preregistration:** frozen in `brief.md` (copied verbatim, first action). No falsifier fired.

---

## VERDICT SUMMARY

| # | Criterion | Verdict |
|---|---|---|
| 1 | Zero-arm law verification (baseline vs recorded candidate) | **PASS** — max \|Δ arm\| = 2.776e-17 m (floor 1e-12) |
| 2 | Nonzero-arm census | **PASS** — nonzero set is EMPTY (max finite \|arm\| = 1.388e-17 m); census + coverage gap recorded |
| 3 | FD crosscheck (ε=5e-7, DERIVATION §8.3) | **PASS** — 140 pairs, max ratio 5.551e-11 < 1e-9, incl. every nonzero pair |
| 4 | Declared-window audit | **PASS** — L₀ inside lengthrange′ for the only 2 tendons that have one; margins 0.986 / 0.975 mm; 16/18 tendons have NO window (path_incomplete) — recorded as coverage finding |
| 5 | Transmission set + dead set | **PASS (statement)** — transmission set is EMPTY; elbow/wrist are UNDEFINED (not dead); unresolved-hand limitation noted |
| 6 | Baseline integrity | **PASS** — `git status --porcelain -- forearm_package/baseline_snapshot` EMPTY; 6/6 sha256 match MANIFEST |

**Preregistered prediction accounting:** zero-arm law HELD (2.78e-17 ≪ 1e-12); FD HELD (5.55e-11 < 1e-9);
L₀-inside HELD (2/2 tendons that possess a window). "Nonzero arms only at path bends" — no nonzero finite
arms exist at all; the bends that DO exist (elbow entry, 20–65 deg) sit on coordinates whose arms are
**not computed** (owner unresolved). The falsifier ("any FD disagreement > 1e-9, any L₀ outside lengthrange′,
any nonzero arm on a straight run") did not fire.

---

## 0. Method (independent re-implementation)

All machinery was re-implemented in `work/a8_arms_audit.py` (canonical copy `scripts/a8_arms_audit.py`)
directly from `DERIVATION.md` — NOT by importing `compiler.py`:

- analytic arm = DERIVATION §8.2 (`dL/dq = Σ_j u_j·(∂s_{j+1}/∂q − ∂s_j/∂q)`, hinge `∂s/∂q = ω̂×(s−J)`
  iff site body in joint subtree), with the recorded rules: root coords → 0.0 (`rigid_reference`),
  unresolved owner → NaN, path with an unresolved site → NaN (matches `compiler.py` L514-525).
- FD = §8.3 central difference, ε=5e-7, re-pathing the polyline under Rodrigues rotation of the joint
  subtree about (J = fitted child origin, ω̂ = fitted axis).
- A second algebraic form (per-segment accumulation without endpoint pairing) agreed to ≤1.258e-17 (max).
- Kinematic tree parsed independently from `source_xml/chimanoid.xml` body nesting (19 bodies;
  subtree(ulna) = {ulna, radius, hand_r}, subtree(humerus) = {humerus, ulna, radius, hand_r}, left mirrored).
- Candidate geometry reconstructed FROM RECORDED DATA ONLY: `w' = w + db·b̂u + dc·ĉu` with recorded
  (db, dc) = (+6.24, +2.02) mm right / (+6.24, −2.02) mm left (`experiment_transverse_candidate.json`
  `step_C_candidate.*.db_m/dc_m` — exact multiples of the 1e-5 m grid step, so the 6dp recording is
  lossless) and the envelope frame (b̂u, ĉu) rebuilt exactly as `experiment_transverse_fit.py::_side_frames`
  (mesh joints elbow/wrist + band roll witness) from the snapshot inputs
  (`receipts/a8_envelope_frames.json`). No optimization re-run. Rebuilt displacement magnitudes match the
  recorded `per_site_displacement_m` (9dp) to **1.32e-10 m** — the recorded rounding floor.
- Recomputation vs recorded packet (18 tendons × 39 coords = 702 records):
  **max |my analytic − recorded analytic| = 0.0 (bit-exact)**, **max |my FD@1e-5 − recorded FD| = 0.0**.
  The fit JSON round-trips floats losslessly (Python repr), so recorded-data recomputation is exact.

---

## 1. Zero-arm law — PASS

**Law (measured form):** at the fitted static pose, the recorded transverse candidate (a rigid shift of
all 16 resolved radius sites per side by one shared (db, dc)) changes **no finite moment arm**:
every finite (tendon, coordinate) arm pair is identical between baseline and candidate to double precision.

**Verification numbers** (18 scoped tendons × 39 coords = 702 pairs):
- finite in both revisions: **140**; NaN in both: **562**; finiteness mismatches: **0**
- **max |arm_candidate − arm_baseline| = 2.776e-17 m** over the 140 finite pairs
  (max |arm value| itself = 1.388e-17 m — everything sits at the machine-zero floor, far below the 1e-12 floor)
- recorded `tendon_deltas.moment_arm_max_abs_delta_m` for the 18 scoped tendons: max = **0.0 exactly**
  (recorded at round(,12); the recorded experiment used live unrounded objects, hence exact 0.0 where my
  full-precision recomputation shows ≤2.8e-17 — same fact at a different reporting floor)
- path-length crosscheck (only comparable scoped tendon): BRD recomputed ΔL = **−0.000901639694 m** vs
  recorded −0.000901640 m (|diff| 3.1e-10 = recorded 9dp rounding); BRD_l −0.000901336717 vs −0.000901337.
  This confirms the shift DOES change path lengths (−0.90 mm on BRD, as recorded in session report 05 §4-C)
  while leaving every finite arm unchanged.

## 2. Nonzero-arm census at baseline — PASS (empty nonzero set)

**Census over 702 pairs (18 tendons × 39 coordinates):**

| class | count | detail |
|---|---|---|
| root rigid-reference zeros | 108 | 18 tendons × 6 pelvis coords (pelvis_tx/ty/tz slides, tilt/list/rotation hinges) — arm 0 by definition (`compiler.py` L514-519; DERIVATION §8.1) |
| computed finite pairs | 32 | BRD_tendon and BRD_l_tendon only (the only complete chains) × 16 resolved non-root coords each (shoulder_elv/rot/elv_angle + lumbar_extension/bending + hip_flexion/adduction/rotation + knee_angle, both sides) |
| …of which exactly 0.0 | 24 | all-out-subtree pairs (e.g. BRD right-tendon vs left hip/knee/shoulder coords) and some telescoped in-subtree pairs |
| …of which float-noise "nonzero" | **8** | max \|value\| = 1.388e-17 m — listed below; numerically zero |
| NaN pairs | 562 | unresolved_owner 306 (elbow_flexion(_l), wrist_dev/flex/3_r/l, ankle×6, mtp×2, lumbar_rotation — owner bodies unresolved, axes NaN) + path_incomplete 256 (16 incomplete tendons × 16 non-root coords) |

**The 8 nominal-nonzero pairs (all machine noise, all on all-in-subtree telescoped chains — NOT arms):**

| tendon | coordinate | value (m) |
|---|---|---|
| BRD_l_tendon | lumbar_extension | −1.3878e-17 |
| BRD_l_tendon | lumbar_bending | +1.3878e-17 |
| BRD_l_tendon | shoulder_elv_l | +3.0358e-18 |
| BRD_l_tendon | shoulder_rot_l | +1.0842e-18 |
| BRD_l_tendon | elv_angle_l | +1.7347e-18 |
| BRD_tendon | shoulder_elv | −6.0715e-18 |
| BRD_tendon | shoulder_rot | −3.2526e-19 |
| BRD_tendon | elv_angle | −3.4694e-18 |

**Per-tendon forearm-run straightness (measured, resolved radius-run):**
every tendon's forearm (radius) run is **straight**: max interior off-chord deviation = **0.000 mm**
(runs are 1–2 resolved points; lengths 7.1–22.9 mm). The paths DO bend where they cross into the forearm:
elbow-entry indices = 1 (BRD, ECRL, ECRB, ECU, FCR, FCU, PT) / 5 (BICshort) / 8 (BIClong), with measured
entry bend angles 20.1° (BRD), 26.6° (ECRL), 38.0° (ECRB), 42.3/43.1° (FCU), 63.1/65.0° (BICshort/BIClong).
(PT entry bend not computable: entry site is the NaN ulna waypoint.) Per-tendon finite/nan counts:
BRD/BRD_l 22 finite (6 root + 16 computed) / 17 NaN; the other 16 tendons 6 finite (root zeros) / 33 NaN.

**Structural law this census actually measures:** a finite arm ≠ 0 requires the path to cross a **RESOLVED**
joint boundary. Every complete scoped chain (BRD/BRD_l: humerus → radius) crosses exactly one boundary —
the elbow, `elbow_flexion`, owned by `ulna`, an **unresolved** body (`fit.joints` status `unresolved_body`,
axis NaN) — so its arm is NaN, not zero. All resolved joints see all-in or all-out chains → exact
structural zeros. The prediction "arms arise only at path bends" is therefore vacuously consistent:
the only bends are on unresolved coordinates whose arms were never computed.

## 3. FD crosscheck — PASS

ε = 5e-7 per DERIVATION §8.3 (NOT the code's ε — see Finding A), criterion |analytic−FD|/(1+|FD|) < 1e-9.

- Pairs compared (both finite): **140** (includes every one of the 8 nonzero/noise pairs; the brief's
  ≥10-sample requirement is exceeded by the full finite set). NaN pairs: 562 (matched-undefined both sides).
- **max ratio = 5.551e-11** (BRD_tendon × lumbar_bending); top ratios: 5.551e-11, 4.163e-11 (×2),
  2.776e-11 (×2), 1.388e-11 (×3) — all FD residuals are ±(1.4–5.6)e-11 on arms that are analytically
  ≤1.4e-17, i.e. pure FD cancellation noise at ε=5e-7. **All 140 pass.**
- Recorded-packet consistency: recorded `fd_eps` = 1e-5 in every record; my FD at 1e-5 reproduces the
  recorded `finite_difference` values **bit-exactly** (max diff 0.0), and my analytic values match the
  recorded `analytic` values bit-exactly. The recorded 140 scoped `matched=True` records = my 140 finite
  pairs; 562 `matched=False` = the NaN pairs.

## 4. Declared-window audit — PASS (with coverage caveat)

Joint q-ranges: fitted `range` is **verbatim-carried** for all 14 arm-chain coordinates — parsed from
`source_xml/chimanoid.xml` and compared numerically (1e-12): shoulder_elv [0, 2.00713], shoulder_rot
[−0.785398, 0.785398], elv_angle [−1.5708, 1.5708], elbow_flexion(_l) [0, 2.26893], wrist_dev_r/l
[−0.436332, 0.610865], wrist_flex_r/l [−0.610864, 0.610864], wrist_3_r/l [−1.22173, 1.22173] — all match.

Muscle windows (`runs/actual_monkey_fit.json` `muscles`):

| tendon | status | L₀ (m) | lengthrange′ (m) | L₀ inside? | excursion margin (m) | force | timeconst | flag |
|---|---|---|---|---|---|---|---|---|
| BRD_tendon | derived | 0.088831037639 | [0.050260048960, 0.089817205597] | **YES** | **+9.862e-4** below hi′ (+3.857e-2 above lo′) | "261.33" | "0.01 0.04" | **requires_physiological_rerun** (`path:derived\|physiology:requires_physiological_rerun`) |
| BRD_l_tendon | derived | 0.088836364104 | [0.050256713452, 0.089811244879] | **YES** | **+9.749e-4** below hi′ (+3.858e-2 above lo′) | "261.33" | "0.01 0.04" | **requires_physiological_rerun** |
| BIClong(_l), BICshort(_l), ECRL(_l), ECRB(_l), ECU(_l), FCR(_l), FCU(_l), PT(_l) — 16 tendons | path_incomplete (unresolved thorax / hand_r+l / ulna+l sites) | **None** | **None** | n/a — no window exists | n/a | ingested_unchanged (verbatim strings) | ingested_unchanged | no lengthrange′ computed; physiology family remains requires_physiological_rerun by ledger |

- λ rebaseline law verified where applicable: λ = lengthrange′/lengthrange_src is a single constant per
  muscle to 1.2e-16 relative (BRD: λ=0.229183989785 at both ends; BRD_l: λ=0.229168779993) — consistent
  with DERIVATION §10 `homogeneous_path_scaling`.
- **Margins are tight:** L₀ sits 0.986 mm (BRD) / 0.975 mm (BRD_l) below the rebaselined upper bound
  (2.5%/2.5% of the window height 0.0396/0.0396 m) — inside, as predicted, but with ~1 mm of headroom.
- No forces computed anywhere (frozen boundary honored). Force/timeconst columns carry the recorded
  verbatim strings only, under `requires_physiological_rerun` — never treated as fitted.

## 5. Transmission statement (measured facts only) — PASS

**Grasp-relevant transmission set (coordinates with ANY nonzero finite arm from the 32-site tendons):
EMPTY.** At the static fitted pose, no wrist, elbow, or any other non-root coordinate receives a nonzero
finite moment arm from any of the 18 grasp tendons.

- **Dead set (arm = 0, computed):** 6 root pelvis coords (zero by definition, all 18 tendons); 16 resolved
  non-root coords per BRD/BRD_l (shoulder×3/side, lumbar_extension/bending, hip×3/side, knee×2 — exact
  structural zeros, no resolved boundary crossed). For the 16 incomplete tendons, only the root zeros exist.
- **UNDEFINED set (arm not computed — neither zero nor nonzero):** `elbow_flexion(_l)` (owner body ulna,
  unresolved) and `wrist_dev/flex/3_r` + `_l` (owner body hand_r/hand_l, unresolved). The paths demonstrably
  cross into the forearm (entry indices 1/5/8, entry bends 20–65°) — geometrically these crossings would
  produce nonzero elbow arms if the elbow axis were resolved — but the current fit does not claim that axis,
  and no arm is invented here.
- **Unresolved-hand limitation:** hand_r/hand_l are unresolved in the admission ledger (5 hand sites each,
  all NaN; wrist axes NaN). Therefore **no wrist or digit transmission claim is possible from this package
  at all** — tension→torque transmission for grasp is currently UNDEFINED at the elbow and both wrist
  coordinate triples, and zero (dead) only for shoulder/lumbar/leg/root coordinates. Grasp qualification
  cannot rest on the elbow/wrist arms until those bodies are resolved.
- Negative finding preserved: 16 of the 18 grasp tendons are path_incomplete (thorax origin sites of
  BIClong/BICshort; ulna sites of ECU/PT; hand insertion sites of ECRL/ECRB/FCR/FCU) — they have no L₀,
  no lengthrange′, and no non-root arms.

## 6. Baseline integrity — PASS

```
$ git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot
(empty output; exit 0)
```

sha256 of consumed artifacts vs `MANIFEST.json` (all match):
`actual_monkey_fit.json` a447555069748d7f… ✓ · `attachment_candidates.json` 854f70976deb1026… ✓ ·
`experiment_transverse_candidate.json` 3c13fca70c2a726e… ✓ · `chimanoid.xml` 675e00d0898cf7a1… ✓ ·
`compiler.py` 8a4ba07c033111730e… ✓ · `DERIVATION.md` cba8b8a1a35565eb… ✓ · mesh inputs
monkey_birth.bin 550a5b3e… / monkey_joints.bin 74b3ab04… ✓ (loader prints uppercase; case-insensitive match).

---

## FINDINGS (discrepancies — reported, not tuned)

- **A — code/derivation FD recipe mismatch.** `compiler.py` L46 `FD_EPS = 1e-5` and L528 threshold `5e-6`
  vs DERIVATION §8.3 "ε = 5e-7", "< 1e-9". The recorded packet used the CODE values (every `fd_eps` field
  = 1e-5). Recomputed at the DERIVATION recipe the packet still passes (max 5.551e-11), so no falsifier
  fires — but the doc and the code disagree, and the packet's `matched` flags were decided at the looser
  5e-6 threshold.
- **B — the recorded explanation of the zero-arm delta is imprecise.** Session report 05 §4-C: "the fitted
  forearm paths are straight (a straight tendon has zero moment arm about any joint, which the shift
  preserves)". Measured: the forearm runs ARE straight (0.000 mm deviation), but a straight path that
  CROSSES a joint boundary generally has a NONZERO arm (u·(ω̂×(p_entry−J))); straightness alone does not
  give zero. The recorded zero deltas hold because no finite chain crosses a RESOLVED boundary (the only
  crossings — elbow — are on unresolved coordinates → NaN) and root arms are zero by definition. The
  measured conclusion (max|Δ|≈0) is correct; the stated law is not the one that produces it.
- **C — coverage gap, not a zero.** 562/702 scoped arm pairs are NaN. The 8 grasp-relevant coordinates
  per the transmission statement (elbow_flexion_r/l, wrist_dev/flex/3_r/l) are UNDEFINED, not dead. Any
  downstream consumer reading "matched: false" rows as zero would be wrong; the ledger carries them as
  NaN with `matched: false`, which is honest, but the transmission set is empty *by absence of claims*,
  not by measured zero transmission at the joints that matter for grasp.
- **D — BRD window headroom ~1 mm.** L₀ sits 0.986/0.975 mm inside the rebaselined upper lengthrange′
  bound (criterion 4). Inside, as predicted; tight. Flag `requires_physiological_rerun` carried verbatim;
  forces not computed.

## UNCERTAINTY

- Candidate positions were reconstructed from recorded (db, dc) + a rebuilt envelope frame; agreement with
  the recorded per-site displacement magnitudes is 1.32e-10 m (the recorded 9dp rounding floor), which
  bounds any frame-reconstruction error. Residual risk: the recorded `per_site_displacement_m` magnitudes
  could in principle under-determine the frame direction — mitigated by the frame being rebuilt from the
  exact published recipe (`_side_frames`) and hash-verified mesh inputs.
- Arm values were recomputed from the fit packet's round-trip-exact floats (bit-exact match to recorded
  analytic values), so no serialization uncertainty enters criteria 1–3.
- Scope is the 18 tendons touching the 32 sites; the recorded `tendon_deltas` (all 120 tendons, max 0.0)
  are consistent with, but only 18 were independently recomputed here.
- Static pose only; the declared q-windows are tabulated, not sampled — no excursion integration was run
  (frozen boundary: static geometry only).

## RECEIPTS (exact commands + outputs, in `receipts/`)

- `a8_run_log.txt` — `PYTHONDONTWRITEBYTECODE=1 python a8_arms_audit.py` full stdout (all headline numbers).
- `a8_arms_results.json` — full machine-readable results: 702-record census, FD table, window rows,
  zero-law numbers, q-range verbatim checks, straightness/entry indices.
- `a8_fd_top.txt` — FD top-ratio listing (recomputed); recorded `fd_eps` = [1e-05]; matched counts
  True 1392 / False 3288 packet-wide, 140/562 scoped.
- `a8_straightness.txt` — per-tendon radius-run straightness + elbow-entry bend angles.
- `a8_envelope_frames.json` — rebuilt (b̂u, ĉu) frames per side.
- `scripts/a8_arms_audit.py`, `scripts/mesh_target_a8.py` — canonical audit code (work/ holds the run copies).
- Baseline integrity: command and hashes in §6 above; run 2026-09-24, repo HEAD at snapshot c70b7a6c per MANIFEST.

No baseline file was written, modified, or reverted; no dynamics, no MuJoCo, no force scaling, no
candidate re-run. Writes were confined to `forearm_package/audits/A8_arms/`.
