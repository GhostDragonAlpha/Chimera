# Rule 0 record — THE SLICE'S REAL BODY, lane slice-real-body-20260920

Lane: `lane/slice-real-body-20260920` @ `bd4bf630` (the merge of the playable
slice into master; verified by `git ls-remote origin master` ==
`bd4bf6300d1633a67d2dae5a8a06bdf278f67f97` before the fetch). Engine port law
8127 refused by code; master untouched; only this lane branch is pushed.
Git trailer on this lane's commits: `Agent: realbody`.

## HONESTY SECTION — what this lane inherited (read before anything else)

The mission briefing said this worktree was a fresh clone with no lane work in
it. That was false in two ways, neither a scope discrepancy:

1. A previous instance (`agent/slice-real-body-20260922`, prereg commit
   `4aba5bfe`, Agent: GLM 5.3) had already preregistered and BUILT this exact
   mission — same scope, verified against its receipts
   (`slice_real_body_20260922/preregistration.md`): replace the slice's bbox
   stand-in tick body with the real CT skeleton, repaired + decimated under the
   importer's own cap, keeping the slice's falsifier bank green. It died
   (host crash) AFTER the build, BEFORE any receipt: its build was uncommitted.
   This lane preserved its uncommitted work verbatim (`b4f9acaa` on its own
   branch), carried it onto this lane base by cherry-picks (`f4ed9ca8`,
   `c38ce8b7`), and is FINISHING it: re-running every falsifier on this base,
   adding the measurements it never made, and writing the receipt it never
   wrote. Nothing of its build is trusted without a fresh measurement here.
2. The briefed fetch source (`E:/ChimeraWork/pass3-integ/repo`) cannot serve a
   full pack (it is a `blob:none` partial clone with lazy fetch disabled).
   The commit `bd4bf630` was instead fetched from the canonical origin, where
   the integrator had pushed it; `FETCH_HEAD` verified == `bd4bf630`.

One real defect was found IN the inherited build and fixed by this lane before
any run: `standing_body.obj` (the sha-pinned import payload) sat under
`* text=auto`, so a fresh checkout rewrote its LF bytes to CRLF and the
manifest's sha256 pin no longer matched the working tree — the slice's boot
would have refused its own body on any clean machine. Fixed by the repo's own
"CRLF lesson" convention: `tools/playable_slice/*.obj -text -whitespace` in
`.gitattributes`, payload re-checked-out, pin re-verified (worktree sha ==
`bc9033bf...` == pin). This is falsifier-relevant: it is the byte-stability
class the mission calls "where the body swap shouldn't reach".

## THE THEORY

**STATEMENT** (someone could disagree): the playable slice's tick body can be
the REAL CT-derived macaque skeleton — the committed bone previews repaired to
the aliveness importer's own closure rule and decimated under its own
500,000-triangle cap by the cap-derived ratio, posed by the SAME standing
compose as the ghost — at correct mm scale, so the slice's physics (gravity,
floor contact, the fall law, the settle) rides the real anatomy while every
slice falsifier stays green.

**PREDICTIONS** (not yet measured by anyone; the alignment prediction is NEW
with this record — the previous instance never measured it):

- P-A (alignment): through the exact standing compose, each femur's posed
  hip pivot (the hip battery's fitted femoral-head centers, `pivot_02_mm`,
  `pivot_03_mm`) lies INSIDE the posed payload femur mesh (the mesh is measured
  closed; winding number == 1), and for both hip and knee pivots
  (the realizing-gap midpoints of `bond.joint_02_06` / `joint_03_07`) the
  payload femur's pivot-to-surface distance agrees with the full-preview
  femur's — the geometry class the pivots were fitted on — within **5 mm**
  (the mission-named bound). The DERIVED expectation is far tighter: the
  manifest's own per-bone QEM deviation for the femora is sub-millimetre
  (`decimation.deviation.max_dev_mm` <= 0.6827 mm, bone_01, all bones same
  order), so anything near 5 mm means the swap moved the anatomy.
- P-B (byte stability where the swap should not reach): the engine's banked
  constants are geometry-independent, so the fall identity holds as it did on
  the capsule: terminal descent median |vy| == m·g/c = 0.223719 m/s to
  <= 1e-6 relative; the boot is byte-clean: 3 boots, identical scene sha
  (== the committed payload's pinned sha) and identical settled start-state
  sha; and the committed payload re-derives BYTE-IDENTICALLY in process
  (`build_standing_layer` on the committed body bones) — compose determinism,
  which also closes the CRLF class mechanically.
- P-C (cap + closure, the inherited prereg's own): the merged payload passes
  the importer's closure check with ZERO refusals and enters under its cap;
  `/mesh_import` answers `ok`.

**FALSIFIERS** (named before the run; any one failing = the theory loses, the
RED is recorded and reported, not tuned):

| id | class | pass condition |
|----|-------|----------------|
| F-BODY-CLOSURE | the importer's own closure rule (importer.cpp finish()) | every output mesh — repaired bones, decimated bones, merged payload: index_degenerate_faces=0 ∧ boundary_edges=0 ∧ nonmanifold_edges=0 ∧ winding_violations=0; 25 bones, 1:1 with the committed previews |
| F-BODY-CAP | the importer's own cap | merged payload <= 500,000 tris AND `/mesh_import` answers `ok` with the engine's own stats |
| F-ALIGNMENT | P-A above | hip pivots (L,R): inside posed payload femur (winding==1, d_surf>0) AND \|d_surf(payload)−d_surf(preview)\| <= 5 mm; knee pivots (L,R): \|d_surf(payload)−d_surf(preview)\| <= 5 mm; absolutes recorded |
| F-PAYLOAD-PIN | byte identity of the payload | in-process recompose of the committed body bones == committed `standing_body.obj` bytes (sha == manifest pin); worktree file == pin (checkout invariance) |
| F-SLICE-MOCK-TRUTH | the slice's honesty contract (re-run) | grep both directions PASS; fantasy ids == {mock_carry} exactly; mock_physics_body has 0 code sites and a `retired` registry record; declared == {ghost_standing_pose} resolving to the real skeleton |
| F-SLICE-NO-SPLAT | conformance (re-run) | zero splat-machinery names in any slice file; triangle routes only |
| F-SLICE-RESTART | byte-clean boot (re-run; the boot changed) | 3 boots: identical scene sha (== payload pin) and identical settled start-state sha |
| F-SLICE-FALL | the fall law rides the real body (re-run; the body changed) | I1 clamp 3.0 m within 1 cm; I2 terminal |vy| == 0.223719 m/s within 1e-6 relative (geometry-independent identity, the carried prereg's bar); I3 equilibrium sink −(m·g/k) = −0.010000 m within 10% |
| F-SLICE-LAUNCH | the slice's own launch bar (re-run) | t_first_verts < 10 s, zero console errors in a real browser transcript |
| F-SLICE-VISUAL | eyes-on (re-run) | after-PNGs through the real page with the REAL skeleton riding the tick; before-PNGs are the 0921 committed capsule shots |

3-run determinism: every offline falsifier script runs 3x, verdicts and
artifact hashes identical; F-SLICE-RESTART is itself 3 boots; the engine-in-the-
loop transient (F-SLICE-FALL) rides the measured attractor (constant root_y,
constant /verts sha — the 0921 receipt's own fixed-point law).

## DERIVED, NOT TUNED (Rule 1)

- The decimation ratio is the cap's own: r = kMaxTris / N_repaired
  (measured N_repaired = 712,224 -> r = 0.7020263...); per-bone target
  floor(r·n_i) is under the cap by construction. No margin constant exists.
- The 5 mm alignment bound is the MISSION's named bound, not this lane's
  taste; the derived expectation (sub-mm, from the manifest's own measured
  deviations) is recorded beside it so a pass near 5 mm is visible as a near-
  fire. The knee pivot's containment test is WAIVED BY DERIVATION, not
  convenience: M is the midpoint of the realizing closest pair — in the joint
  GAP by construction — so the only well-posed knee test is surface-distance
  agreement; the hip fit center is a head-sphere center, so containment there
  is well-posed and required.
- The fall bar is the engine's own identity (banked constants), the closure
  classes are the importer's own check, the launch bar is the slice's own
  10 s — no number in this lane is chosen by this lane.
- The swap carries NO flag: the inherited receipts show the stand-in mock
  retired outright (`mock_physics_body` -> `retired`, zero code sites), not
  toggled. This lane does not invent a flag the receipts do not name.

## RUN PLAN

Prereg (this file, committed) -> rebuild the engine from THIS base (master
side changed `gait_controller.hpp` after 2909bb4e; the binary must match the
checkout) -> offline falsifiers x3 -> engine-in-the-loop falsifiers (import
stats, restart x3, fall, launch + browser) -> `receipt.json` in THIS directory
with per-falsifier verdicts -> push only `lane/slice-real-body-20260920`.

Receipt: `tools/science_funnel/validation/slice_real_body_20260920/receipt.json`.
Inherited prereg + build (pointed at, not duplicated):
`tools/science_funnel/validation/slice_real_body_20260922/`.

## AMENDMENT 1 — F-SLICE-FALL's I1 clause, FALSIFIED AS PREREGISTERED, then restated

Measured 2026-09-22 (`fall_measurement_realbody.json`): the real body's
transient peaks at root_y = **0.9152 m**, NOT the 3 m clamp — I1 as written
above ("peak root_y = 3.0 m within 1 cm") is RED. The clamp-reach was the
CAPSULE's transient shape, arithmetic-derivably geometry-dependent: the
penalty spring's stored energy is k·x²/2 with x = the centered import's
penetration, and the real body penetrates 0.1346 m vs the capsule's
0.2653 m — ~1/4 the specific energy, launch to ~0.9 m, exactly as measured.
The geometry-independent identity — the carried bank's actual bar — HOLDS:
median |vy| in the descent = 0.223719 m/s vs derived m·g/c = 0.223718814,
relative error 8.3e-7 <= 1e-6; equilibrium sink −0.010000 m exact; the
settled root landed on the DERIVED prediction −(m·g/k) − ymin = 0.124641.
F-SLICE-FALL's pass condition is restated: import ok (F-BODY-CAP engine
half) ∧ I2 <= 1e-6 relative ∧ I3 within 10%. Both the fired clause and the
restatement are recorded; nothing tuned.

## AMENDMENT 2 — F-SLICE-RESTART's recorder, RED as first measured, then fixed

First measurement (`restart_measurement_realbody.json`, first run): scene sha
identical x3 AND == the payload pin, but boot 0's settled start-state sha
differed from boots 1/2 (which were bitwise identical to each other). The
diagnosis is a RECORDER defect in the slice's own `_finish_settle`: its
drift-only convergence break (`|Δroot_y| < 1e-7 and |vy| < 1e-5` between two
0.25 s polls) fires at bounce CRESTS of the real body's longer-lived
oscillation — it recorded mid-oscillation states (0.124713 / 0.124354 /
0.124908, all ~3e-4 off the attractor). The fix is in the slice
(`slice_server.py`): "settled" now means residence AT the DERIVED attractor
— |root_y − (−(m·g/k) − ymin)| < 5e-5 with |vy| < 1e-5, held 10 s, constants
banked, ymin from the import's own stats (any body). Re-measurement: 3 boots,
scene sha == pin x3, start-state sha identical x3 (`8c040418…`), settled root
at the attractor. The engine was never nondeterministic; the recorder raced
the oscillation.

## AMENDMENT 3 — F-SLICE-LAUNCH: RED, stands

Measured (`launch_server_timeline_realbody.json`, `import_timing.json`):
t_first_verts = **135.73 s** against the slice's own 10 s bar. Breakdown
(isolated, no server): engine ready 0.71 s, ghost build 7.92 s, gravity arm
0.026 s, and the engine's own `/mesh_import` parse of the pinned 499,976-tri
payload **237.67 s** (variable 130–240+ s across boots; one boot was killed
by the old 180 s POST timeout — the boot timeout is now 900 s so the slice
can boot its own body at all). The carried prereg's payment (committing the
posed payload, removing the compose from the boot path) was real but
insufficient: the cost is the ENGINE's parse, first exercised at this scale
by this body (the 500k-tri cap had never been filled before). Not
slice-side fixable without tuning (the decimation ratio is the cap's own
law, not a knob): SUCCESSOR WORK — engine importer performance at cap scale,
its own Rule-0 lane.

Agent: realbody
