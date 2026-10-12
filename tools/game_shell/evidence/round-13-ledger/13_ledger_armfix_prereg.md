# Round-13 pre-registration: ledger continuity across tendon arm (rule §15)

Written BEFORE any source edit. Worker: TIEL. Branch:
WK-ENGINE-PATHS-20260929-PR. Repro evidence being fixed:
`tools/game_shell/evidence/round-12/12_ledger_repro.txt` (constant
1.1111111111 J guard error, violations == frames, on every arm from a
limp/severed state; arm-from-rest clean at ~1e-12).

## Diagnosis (verified against the code, correcting the assignment's attribution)

The guard invariant (membrane_tick.cpp `ledger_guard_frame_`):

    battery0 - battery == work + heat + (elastic - elastic0)   [tol 1e-6 J]

Two defects in the arm/re-init path combine:

1. **Stale `severed` flag inside `tendon_drive_init`**
   (`ChimeraEngine/engine/tendon_drive.hpp`, lines 178-185). The init
   computes `s.elastic_J = elastic_energy_j(p, s)` on line 183 BEFORE
   clearing `s.severed = false` on line 184. `elastic_energy_j` returns
   capsule-only energy when `severed` is true. So arming from a state whose
   previous session ended severed books the baseline as
   `0.5*k_capsule*(0-theta_rest)^2 = 0` (theta_rest = 0.0), while the first
   `step_internal` computes `e_old` UNSEVERED and therefore includes the
   tendon pretension. The guard then sees a constant offset equal to the
   tendon pretension energy at q = 0:

       0.5 * (EA/L0t) * (L0m - L0t)^2
     = 0.5 * (2000/0.09) * (0.10 - 0.09)^2
     = 10/9 = 1.1111111111111112 J

   matching the observed 1.1111111111114969 to float64 round-off. NOTE: the
   assignment attributed the 1.1111 J to the capsule at q_rest ~ 1.0541 rad
   (`0.5*2.0*1.0541^2 = 1.11112681`); that value differs from the observed
   constant at the 5th decimal, while the tendon-pretension value matches to
   16 digits, and the code has `theta_rest = 0.0` with no override anywhere
   (grep: `theta_rest` appears only in tendon_drive.hpp). The mechanism
   (unbooked elastic appearance at arm time) is as the assignment stated;
   the spring is the tendon, not the capsule.

2. **Arm re-initializes the drive to the fixed rest q = 0** regardless of
   where the joint actually is (`s.q = 0.0` in `tendon_drive_init`, called
   by `MembraneTick::tendon_reset_`). The limb teleports to q = 0 on the
   first armed frame (the drive owns the pin and writes `joint_deg_`), and
   the drive's elastic baseline reflects a pose the limb was not in. This
   does not by itself break the guard (elastic0 is captured after init at
   the same q = 0), but it is the physical discontinuity Qwen's fix
   direction removes.

## Fix (Qwen-approved direction, implemented as)

- `tendon_drive.hpp`: add `tendon_drive_init_at(p, s, q0)` which clears
  `s.severed = false` BEFORE computing the elastic baseline, and initializes
  `s.q = q0`. `tendon_drive_init(p, s)` becomes a wrapper calling
  `tendon_drive_init_at(p, s, 0.0)` — byte-identical for every existing
  caller whose state is unsevered (all of them except the arm-from-severed
  path, which is the bug).
- `membrane_tick.cpp` `tendon_reset_()`: arm at the CURRENT joint angle,
  `q0 = joint_deg_[tendon_pin_]` when the pin exists, via
  `tendon_drive_init_at`; `tendon_battery0_J_` / `tendon_elastic0_J_`
  snapshots stay AFTER the re-init (guard captures elastic0 from the drive's
  reported `elastic_J` after re-init).
- No A1-A8 constants, force laws, or the fall/contact block
  (membrane_tick.cpp ~860-905) are touched. The loco bank (scratch,
  default-off) keeps its existing arm-at-0 semantics; it is unaffected by
  the init ordering fix because it re-inits from a fresh `LocoDrive{}`
  (`severed == false` already).

## Prediction

After the fix:

- Arm-from-limp and arm-from-severed sessions show **0 ledger violations**
  (max err < 1e-6 J; expected ~1e-12 like arm-from-rest). The battery drain
  of the first armed frame includes/conserves the previously-unbooked
  baseline: `elastic0` equals the drive's full tendon+capsule energy at the
  actual arm-time joint angle, so no constant offset appears in
  `drain - (work + heat + elastic - elastic0)`.
- Offline test (`ChimeraEngine/engine/tests/tendon_arm_ledger_test.cpp`,
  g++ -std=c++17 -O2 -I ChimeraEngine/engine): every armed frame of every
  arm transition (from rest, from limp with zero activation, from severed,
  disarm+re-arm) satisfies drain == work + heat + (elastic - elastic0)
  within 1e-6 J; 0 violations per session.

## Falsifier

- ANY armed session (from rest, limp, or severed) shows violations > 0; OR
- the arm-from-rest session numbers CHANGE from the pre-fix clean values.
  They must stay byte-identical: from the authored rest pose the current
  joint q == rest q == 0 (fresh `load_body_binding` zeroes `joint_deg_`;
  `theta_rest = 0`), so `tendon_drive_init_at(p, s, 0)` must reproduce the
  old `tendon_drive_init` state exactly (q=0, qd=0, a=0, battery=1000,
  work=heat=0, elastic=10/9 J, severed=false, accumulator=0), and the live
  arm-from-rest `tendon_elastic0_J` must remain 1.1111111111111132-style
  (10/9 J) with max err ~1e-12 and 0 violations, as in round-12
  `A_after_arm_from_rest`.

## Verification plan

(a) Offline unit test above (engine/tests convention, standalone g++).
(b) Live: Release build (cmake -S ChimeraEngine/engine -B scratch dir;
    cmake --build --config Release --parallel 2), own engine on scratch
    port >= 8119, `--hidden 1600 900 --no-restore`, creature scene via
    `python -B -m tools.science_funnel.creature_scene`, then the round-12
    sequence against the engine routes directly (/tick_effort, /tick_sever,
    /tick_state): arm from rest (fresh scene, joint q = 0; expect clean,
    elastic0 = 10/9 J, max err ~1e-12), sever, limp, re-arm from limp
    (expect 0 violations now), disarm+re-arm. Snapshots written to
    `13_ledger_armfix_repro.txt` in the round-12 format. Frame-count
    dependent totals (work/heat/battery) depend on wall-clock frames and are
    compared as invariants (per-frame ledger err), not byte totals; the
    deterministic arm-time fields (elastic0, q at arm, severed) are compared
    to ~1e-9.
