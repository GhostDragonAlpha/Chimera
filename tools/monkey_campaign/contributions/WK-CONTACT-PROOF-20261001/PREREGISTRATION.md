# PREREGISTRATION (DRAFT v1) — contact-proof: fingertip–cylinder fixture proof

Status: **DRAFT** — submitted to the Lieutenant for a separate-first commit.
No implementation of this card executes until the Lieutenant commits this file
and hands back the pin SHA; the Phase B package is pinned to that commit.
Frozen BEFORE implementation and before any experiment run.
Composed 2026-09-29 by `wk-proof-contact` (Phase A, tasking "bounded contact
proof, PREREG-FIRST"). Checkout identity: `E:/PythonChimera` branch
`WK-ENGINE-PATHS-20260929-PR` HEAD `7222729eca6e9f97f25061c8b1dc3d229bb703d8`
(dirty work preserved; this card lives in the lane dir
`E:\ChimeraWork\monkey-coordination\contact-proof\`, outside the repo).

## 0. What this card is

A bounded proof that the certified G04 grasp-contact fixture line, extended
with a declared torsion channel, measures all four assigned quantities against
a rigid fingertip pad pressed on the trunk cylinder:

1. **normal force** (N),
2. **resisting torque** (N·m) about the cylinder axis,
3. **sliding displacement** (m),
4. **release** (clean separation: zero retained force + free-fall + gap growth).

The reference evaluation (REFERENCE_EVAL.md, this lane) is the recorded basis
for the reference choice. No solver swap occurs: the M06 module is imported
byte-identical, never forked.

## 1. Established interface (imported, hash-asserted, never forked)

- Solver: `chimera.local_contact.v1`, file
  `local_contact.py`, sha256
  `1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc`
  (certified MAT2-M06 pin; byte-identical copy verified in the MAT2-G04 review
  workspace and the sealed evidence store). Imported at run time after sha256
  assertion; refusals `interface_pin_missing` / `interface_pin_drift`.
- This card adds no bond, weld, or sticky constraint; no `lambda_min`; no
  penalty stiffness; the only pinned body is the trunk (literal lint scan).
- The solver has **translation-only** rigid kinematics (declared in the
  module). Rotation is therefore NOT simulated; the resisting torque is a
  MEASURED DERIVED quantity computed from the recorded contact impulse vectors
  and contact points per tick — the same epistemic status as the recorded
  trunk anchor reaction. No rotational DOF is invented anywhere.

## 2. Frozen fixture (fingertip–cylinder, G04-line reuse)

Frame: `m06_experiment_z_up` (trunk axis = z through origin; gravity −z).
Geometry transform is the sealed asset's own `frame_transform_to_m06`
(`m06 = (x − bx, −(z − bz), y − by)`, `(bx, by, bz) = (11.976783, 0.0, 2.471766)`);
no other transform is composed.

- Trunk: pinned body `trunk_01.lateral` built from the pinned asset
  `trunk_01_mesh.json` (sha256
  `3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7`),
  partitioned by the F03 per-triangle rule (vertex 128 → base_cap, 129 →
  top_cap, else lateral; exactly 64 lateral facets), material layer
  `wood_trunk_01`, mu_s = mu_k = 0.6 (F03 declared placeholders), thickness 0.
- Fingertip pad: ONE tetra pad body (n = 1) on the sealed S1 lateral facet
  (triangle 0; centroid m06 `[0.036763, −0.002406, 0.386]`, outward normal
  `[0.9951835289511874, −0.09802930023345664, 0.0]`), pad start = facet
  centroid offset outward along the normal by `PAD_OFFSET_M = 0.9e-5` m,
  contact face parallel to the facet plane, `ex = n`, `(ey, ez) = _orthobasis(n)`
  (F03 heritage), thickness 0, mu_s = 0.6 / mu_k = 0.4 (NAMED placeholders;
  FRICTION_SOURCES verdict GAP stands — acquisition remains the recorded debt).
- Multi-channel refinement arms (R3) reuse the G04 channel selection rule
  verbatim (channel k at azimuth `az0 + 360·k/n`, same z band, ties to lowest
  triangle index) with `n ∈ {2, 3}`; reading share = reading/n.
- Declared external channels (ALL recorded per tick; full-tick ledger identity
  asserted every tick): press `P_n = 0.30 N·s` inward along −n (the sealed F03
  S1 operating point); anti-gravity `+m·g·dt` along +z (Arm T only, so the
  torsion demand is the only tangential input); twist `P_az` azimuthal
  (Arm T only) along `t_az = (−cy, cx, 0)/ρ_c` at the pad centroid
  (`t_az = [0.06530652537080572, 0.9978652502938421, 0.0]`); gravity always.
  Every channel is a fixture input applied to pad velocity before
  `lc.solve_tick`, exactly the G04 press pattern. Pressing stops ⇒ nothing
  holds: there is no mechanism that can retain a force after channels go to 0.

Constants: `G = 9.81`, `DT = 0.005 s` (M06 frozen declarations; never changed).

## 3. Frozen scenario battery (the declared sweep)

30 deterministic ticks per scenario (HOLD ticks 1–20 channels on; RELEASE
ticks 21–30 channels off). CPU-only, no RNG, no wall clock.

- **Arm V (vertical; G04 heritage)**: press + gravity. Readings
  {band_lo 5.4, band_mid 6.15, band_hi 6.9, scene 10.037998} kg x
  n ∈ {1, 2, 3} — the full 12-row certified sweep — plus the zero-mu control
  (band_mid, n = 3, mu_s = mu_k = 0.0, trace key `...|mu=0`).
  Measures: normal force, sliding displacement, release.
- **Arm T (torsion; NEW)**: press + anti-gravity + twist; reading band_mid,
  n = 1 (share 6.15 kg). `P_az ∈ {0.10, 0.17, 0.19}` N·s.
  Stick condition (closed form): `P_az ≤ mu_s · P_n = 0.18 N·s` (mass-free;
  jt_req = m·(P_az/m) = P_az). Rows: 0.10 STICK, 0.17 STICK, 0.19 SLIP.
  No row sits at the exact equality (float-flip hygiene); the equality case is
  declared untested. Measures: resisting torque, torsional stick/slip boundary,
  release.

Controls: zero-mu control (Arm V); release phase in every scenario; full-tick
ledger identity in every scenario.

## 4. Preregistered predictions and tolerances (four measured quantities)

Values below are computed from the pinned inputs only (facet geometry:
`ρ_hi = 0.03700000000000081` m = facet-vertex radius;
`ρ_lo = 0.03682179057119474` m = perpendicular foot of the S1 facet plane from
the trunk axis, verified inside the facet triangle — the honest lever-arm band
because the facet chords inside the cylinder surface). The harness recomputes
ρ_lo/ρ_hi from the pinned mesh at run time and refuses on mismatch
(`geometry_drift`).

**(1) Normal force.** Per pad per hold tick `jn = P_n = 0.30 N·s` within 1e-9;
`F_n = jn/DT = 60.0 N` within 1e-6 N. Trunk-side normal reaction per loaded
channel = 60.0 N (equal and opposite through the contact records).

**(2) Resisting torque** about the trunk axis (z through origin), per tick:
`τ_z = Σ_channels (jt_vec × lever)·ẑ` computed from recorded impulses with
`lever = (point_b_x, point_b_y, 0)` (the recorded trunk-side contact point).
- Arm T stick rows (P_az = 0.10, 0.17): jt = P_az within 1e-9, so
  `τ_z ∈ P_az·[ρ_lo, ρ_hi]/DT`: P_az=0.10 → [0.7364358114238948,
  0.7400000000000163] N·m; P_az=0.17 → [1.2519408794206213,
  1.2580000000000275] N·m. Band membership ± 1e-9 N·m; the per-tick recorded
  ρ is written to the ledger.
- Arm T slip row (P_az = 0.19): jt = mu_k·P_n = 0.12 N·s,
  `τ_z ∈ [0.8837229737086737, 0.8880000000000193]` N·m ± 1e-9.
- Arm V (vertical friction): `τ_z = 0` within 1e-9 N·m — a vertical friction
  force has a zero moment about the vertical axis; this is the torque
  channel's specificity check.

**(3) Sliding displacement.** Arm V stick rows: hold-phase downward
displacement ≤ 1e-9 m after tick 1; slip rows follow the exact recursion
`v(k) = v(k−1) + g·DT − mu_k·P_n/m_share`, displacement accumulates `v(k)·DT`
(windows 1e-9 m/s and 1e-9 m after the first recorded tick — G04 heritage).
Arm T azimuthal displacement: stick rows ≤ 1e-9 m; slip row
`v(k) = v(k−1) + (P_az − 0.12)/6.15` per tick (windows as above).

**(4) Release (clean separation).** Every release tick: per pad
`(jn, jt) = 0` within `share_kg·1e-10 N·s` (G04 amendment a2 bar);
velocity follows free fall `v(k) = v(k−1) + g·DT` within 1e-9 m/s; displacement
within 1e-9 m; and the pad–facet separation gap (measured per tick with the
pinned module's own `tri_tri_closest` between the pad contact face and the S1
facet — a read-only geometry query, not a solve) exceeds `1e-3 m` by the end
of release and grows monotonically within 1e-9 m per tick. Nothing retains a
force after the channels stop.

**Boundary agreement.** Arm V solver stick/slip MUST equal the certified G04
12-row table (G01 feasibility heritage): n=1 SLIP at every lawful reading;
multi-channel closes at n ≥ 2 (band rows) and n = 3 (scene). Arm T rows equal
the Section 3 stick/slip table. No g-convention flip (record-g vs standard-g
arithmetic checked per row, G04 heritage).

## 5. Reference comparison (the deliverable comparison, not a solver swap)

- External reference: **Drake hydroelastic contact** per REFERENCE_EVAL.md §4
  (BSD-3-Clause; no native Windows package — WSL2 route is the named gap).
  The external arm EXECUTES ONLY after the Lieutenant adopts the WSL2 bridge;
  its protocol is declared now: identical scenario inputs (60 N steady normal
  press of a fingertip proxy on the cylinder lateral; torsion about the axis
  below and above the friction bound; release), exchange by deterministic
  JSON. Draft comparison tolerances (to be committed by the Lieutenant before
  any external run): F_n within ±5% of 60 N at steady state; resisting torque
  within the Coulomb band ±5%; stick displacement ≤ `2·g·dt²`; release
  free-fall displacement within ±2%; hydroelastic mesh refinement ×2 moves
  F_n by ≤ 2% (refinement law of the external model itself).
- Fallback external reference if WSL2 is refused: **IPC toolkit source build**
  (MIT; named gap: MSVC Build Tools). Same scenario and tolerance skeleton.
- Internal references that run inside the sealed battery regardless:
  (a) the closed forms above; (b) M06 `solve_tick(..., exhaustive=True)`
  all-pairs broad-phase — per-pair contact records agree with the
  sweep-and-prune run within 1e-9 on jn/jt and 1e-9 m on displacement
  (candidate ordering can reorder float sums; byte identity is NOT claimed);
  (c) certified G04 receipt rows as regression anchors (band_mid|n=3 stick
  rows). It is recorded honestly: (a)–(c) verify the fixture against its own
  law and certified heritage; they are NOT independent-solver comparisons.

## 6. Refinement checks (declared before execution)

- **R1 offset**: `PAD_OFFSET_M` halved (0.45e-5 m) — every hold-phase
  prediction unchanged within its windows (both variants stay on the
  persistent-contact branch; Baumgarte bias 0 in both).
- **R2 press scale**: `P_n` doubled (0.60 N·s) with Arm T rows scaled to
  {0.20, 0.34, 0.38} — F_n = 120.0 N ± 1e-6; stick threshold 0.36; τ bands
  scale exactly (law-linearity check, not a number check).
- **R3 channels**: n = 3 band_mid — per-channel jt identical across channels
  within 1e-9 (azimuthal symmetry); τ_z = 3 x per-channel band sum.
- **R4 tick scale**: `DT/2 = 0.0025 s` with `P_n`/`P_az` halved per tick —
  F_n and τ_z invariant within windows (impulse-law invariance).
- **R5 torque specificity**: the Section 4 Arm V `τ_z = 0` check.

A refinement check that fails is a recorded result (Section 7); it does not
trigger re-tuning.

## 7. Failure preservation (a failing comparison is a recorded result, never a retry-until-pass)

- Every scenario runs ONCE against the sealed candidate; the receipt records
  every check pass/fail with full per-tick traces. Failures stand in the
  receipt and EVIDENCE.md; no silent re-run, no tolerance edits after a run.
- Prereg amendments, if any, are committed to this file BEFORE the receipt run
  (G04 amendment law); after receipt runs begin, only additive amendments that
  do not touch predictions, constants, windows, or falsifier designs are
  lawful, and each states what changed and why.
- Named refusal codes (nothing silently repaired): `input_pin_missing`,
  `input_pin_drift`, `interface_pin_missing`, `interface_pin_drift`,
  `channel_band_mismatch`, `geometry_drift`, `ledger_imbalance:full_tick`,
  `reaction_concealed`, `nonfinite_state`, `vacuous_comparison_refused`,
  `tamper_site_missing`, `scenario_refusal:*`.

**Falsifier arms (every arm runs its clean control FIRST; a non-biting arm
fails the build):**
- **FB1 release_hidden_sticky** (G04 heritage): tamper = re-apply the last
  hold friction impulse after channels stop; discriminator = X4 passes clean,
  fails tampered.
- **FB2 zero_mu_adhesion** (heritage): tamper = pair mu ignores the declared
  zero; discriminator = zero-mu control slides clean, holds tampered.
- **FB3 ledger_concealment** (heritage): tamper = unrecorded `0.02 N·s`
  per-tick pad impulse; discriminator = full-tick identity fires (~2e-2).
- **FB4 boundary_flip** (heritage, Arm T site): tamper = one recorded
  expectation row flipped (P_az = 0.17 STICK → SLIP); discriminator =
  `verdict_row_disagrees` fires.
- **FB5 torque_axis_offset** (NEW): tamper = lever computed about an axis
  offset `+1e-3 m` in x; discriminator = the Arm T stick τ_z shifts by
  ~`P_az/DT·1e-3 ≈ 0.034 N·m`, outside the declared band + 1e-9 window; the
  torque check must fail on the tampered build (proves the torque measurement
  discriminates its own lever arm).

## 8. Named checks (test_contact_proof.py; executed, none skipped)

X1 attachment_through_solver (press channel recorded; jn = P_n ± 1e-9;
no-bond/weld/sticky literal lint); X2 friction_law (Arm V + Arm T stick
arrest 1e-12-class bars and slip recursions 1e-9); X3 reaction_loads (anchor =
−contact ± 1e-12 every tick; 60 N per-channel reaction); X4 release_opens
((jn, jt) zero bars, free-fall, gap growth); X5 boundary_agreement (Arm V 12
rows == certified table; Arm T 3 rows == closed form; g-convention no-flip);
X6 ledger_identity (full-tick residual ≤ 1e-12 including every declared
channel); X7 determinism (two independent main runs byte-identical trace);
X8 torque_measurement (bands of Section 4(2), recorded per-tick lever arm,
Arm V zero-torque specificity). P-class: input pins verified at run time;
named-variable law (the ten G04 named absent variables carried verbatim —
x_press, x_share, x_aperture, x_reach, x_com, x_inertia, x_trajectory,
x_sequence, x_losses, x_trunk_strength — status ABSENT, no synthetic value);
placeholder naming (mu provenance strings); `lambda_min`/`penalty stiffness`
literals absent from all card sources; vacuous-comparison guard self-test.

## 9. Input pins (verified at run time; drift refuses the run)

| pin | source path (verified copy) | sha256 |
|---|---|---|
| local_contact_py | `E:/ChimeraWork/monkey-coordination/kanban-reviews/MAT2-G04/sgt-pr298-18e931a5/scratch/contrib/MAT2-M06/local_contact.py` (byte-identical to `evidence-store/MAT2-M06/source/local_contact.py`) | 1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc |
| trunk_mesh_json | `.../sgt-pr298-18e931a5/scratch/contrib/MAT2-F03/assets/trunk_01_mesh.json` | 3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7 |
| trunk_material_state | `.../sgt-pr298-18e931a5/scratch/contrib/MAT2-F03/assets/trunk_01_material_state.json` | 91c17a5c59ce79af3dc0e8a6dadb00c92a039075775a0a1de618da12dfca61bd |
| g04_experiment_receipt (regression anchors) | `E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/numerical/experiment_receipt.json` | (recorded in EVIDENCE.md; the G04 receipt references its own source copy) |
| friction_sources_md | `E:/ChimeraWork/monkey-coordination/g04-friction/FRICTION_SOURCES.md` | 336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b |

The Phase B sealed package vendors byte-identical copies of the pinned files
and asserts every hash at run time inside the sealed run (G04 pattern); no
path outside the sealed package is read at run time.

## 10. Explicitly not yet done (honest inventory)

- No implementation of this card exists yet; no sealed (gated) run has
  executed; every prediction above is untested by this card.
- Neither external reference is installed; the external comparison cannot
  start before the Lieutenant's adoption decision (REFERENCE_EVAL.md §4).
- The Lieutenant's prereg commit and pin SHA do not exist yet; this draft is
  the first deliverable.
- Development (non-gated) shakedown runs in Phase B may surface float-noise
  facts; any window rescale follows the amendment law (Section 7) BEFORE the
  receipt run, disclosed like G04's a1/a2.
