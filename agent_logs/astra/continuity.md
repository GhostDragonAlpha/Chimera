# ASTRA continuity handoff

Base master: f6ff0dbfb7064eafcc774bc34730dd6f43c264f1.
Branch: astra/gait-capture. Runtime implementation remains coordinator-owned.

1. Falsifier table:
   - Baseline diagnosis -> PASS: 1320 commanded-joint increments; max/RMS
     2.381311797/0.087412009 rad; one remote reseed, three virtual elbow sign
     changes. The largest jump rejects a local 0.010230781 wu error (inside
     the foot gate) solely because it is not accurate to 1e-10.
   - Persistent section and actual LBS -> PASS: one-stride foot max/RMS
     9.542360332e-5/5.643409958e-5 wu; bound 0.000250545733 < 0.028078200.
   - Continuous ROM -> PASS: strict annulus plus inverse-Jacobian interval
     certificate, 878 intervals; sampled minimum ROM margin 0.058289562 rad.
   - Actual 60 Hz jumps -> PASS against PROPOSED bound: max 0.095247312,
     RMS 0.024130364, limit 0.116378172 rad. Startup, off-grid exchanges and
     repeated stride included. Angle return 8.882e-16 rad.
   - Geometric interpolation -> PASS: certificate 0.019704563 wu < gate.
     Full-mesh chord control 0.020237887 wu is within its predicted bound.
     This is not a perceptual/triangle-strain certificate.
   - Nominal velocity match -> PASS: actual-LBS jump 6.875e-15 wu/s;
     joint velocity jump 3.775e-15 rad/s. Actual world foot speed at contact
     is 0.000138885 wu/s, not exactly zero: no no-slip certification.
   - Finite-force startup -> PASS: state closure 4.441e-16; independent RK4
     error 1.359e-13; required u=0.806343648 wu/s^2 for 1.831964036 s;
     integrated specific force 1.477192564 wu/s, work 1.739652480 wu^2/s^2.
     First-swing time deficit zero; pose/velocity joins ~1e-14 or better.
   - Preparation -> PASS geometrically: separate 1/60 s, max angle increment
     about 0.0715064 < 0.079066594 rad, continuous foot certificate 0.023010970.
   - Full physical integration -> CLOSED: missing budgets/contact/visual
     ratification, tiny proxy lift and unidentified active physical clock.

2. Files written:
   - docs/THE_CONTINUITY_LAW.md (derivation, numerical verdict, honesty ledger)
   - docs/THE_CAPTURE_LAW.md (pre-run membranes, refinements, result pointer)
   - docs/THE_CAPTURE_INTEGRATION.md (exact engine phase/angle/force law)
   - tools/gait_capture.py (baseline diagnosis, section, boundary laws, gates)
   - agent_logs/astra/continuity.txt (complete final real-blob output)
   - agent_logs/astra/continuity.md (this handoff)

3. Falsified/retracted:
   - Local-only and cyclic exact fitting did not solve continuity; the
     exact-fit cyclic result still jumped 2.496258 rad. Full failed-attempt
     ledger is in THE_CONTINUITY_LAW.md; none proves global impossibility.
   - Simple cubic low-lift swing still jumped 3.408222 rad at ROM; deriving
     the allowed overshoot and its endpoint turns removed that failure.
   - The initial successful T/2 startup candidate is superseded by finite
     forcing over T, so the recommendation starts at zero target velocity.
   - The old high-clearance passive swing is NOT preserved by this result.

4. Open items:
   - MOST FRAGILE: proxy lift is only 0.001928210330 wu. Whole-sole/terrain
     clearance is unproven. The tracked band itself is 0.206304 wu above the
     mesh-global ground proxy at its minimum; marker tracking is not contact.
   - Required swing acceleration bound 71.030061 wu/s^2 and startup contact
     friction lower bound 0.466411530 have no measured available budgets.
   - Physical mass/inertia/torque, finite-contact dynamics, nonzero hybrid
     reset impulses, lateral balance, triangle strain and movie judgment.
   - The 0.116378172 rad proposal needs coordinator ratification. Exact
     Rodrigues has no inherent 60 Hz stability cutoff. The bound concerns
     interpolation deviation, not maximum matter displacement or perception.
   - Active swing admits many clocks. The inherited conditional T is held
     fixed to isolate this task, not newly claimed as a unique physical clock.

5. Boundary hits:
   - None crossed. No edits to build/, blobs, mirror, engine or referee.
     No engine connection, runtime process operation, or live pose delivery.
     Branch-only fast-forward publication; no master or force-push.

Validation:
- OPENBLAS_NUM_THREADS=1 python tools/gait_capture.py --self-test -> exit 0.
- OPENBLAS_NUM_THREADS=1 python tools/gait_capture.py --require-ready -> exit 2
  intentionally for the full integration gate; all numerical assertions pass.
- The final run includes the preserved PR #6 baseline, not a cached result.
- git diff --check and protected-path/mirror/engine/referee diffs are clean.
