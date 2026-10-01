# ONE LIMB — STALE vs REAL (the brief's "reported context" audited)

Each claim in the brief's product/evidence list, checked against the
code and the live engine (GET-only on 8107) or a scratch this lane.

## REAL — verified in code and/or by measurement today

1. **Four sealed height-band regions** (feet/calves/thighs/torso). REAL:
   live /tick_state — 4 cells, y-bands [−0.020, 0.338], [3.415, 9.971],
   [1.903, 3.415], [0.338, 1.903]; v0 = 0.2879 / 12.5091 / 0.6930 /
   0.3346 m³; cuts sat exactly at the joint pins' heights.
2. **28 measured joint pins.** REAL: joints28.json, 28 entries with
   axes + ROM; loaded into the engine (pins 13–18 are the leg set).
3. **P = −(V−V0)/(κ·V0), κ = 4.6e-10 Pa⁻¹.** REAL: `kappa_` in
   membrane_tick; per-cell pressure computed live every tick.
4. **Mass 13,824.5 kg from the material inventory.** REAL in code
   (`mass_kg_`); measured V_whole 13.8246 m³ ⇒ 13,824.6 kg — the 1e-5
   relative gap is float-scale, not missing water.
5. **Press law delta = F/(4πσ), σ = 4000 N/m; recovery τ = 0.5 s.**
   REAL and now re-measured: 20 kN ⇒ dimple 0.397887 m; the law predicts
   20000/(4π·4000) = 0.397887 m — six-digit agreement (and it is still a
   QUALIFIED REDUCED MODEL: linear, and 40 cm deep at 20 kN).
6. **Ground contact spring 1.3562e7 N/m.** REAL (`k_ground_`, with the
   50·m·g force floor).
7. **Cut/split machinery with the 0.5% degenerate guard.** REAL
   (`SEAL_DEGENERATE_FRAC = 0.005`), guard kept ARMED by this lane.
8. **Gait transitions gated by measured quantities; no timers.** REAL in
   code (every phase transition reads measured depth/pressure/lean;
   RECOVER is the measured abort). The 15/15 gait_verify evidence is
   C1's; not re-run by this lane.
9. **Reflexes (breathing/flinch/startle) exist.** REAL — and this lane
   RE-MEASURED the causal core live: the nerve cut removes the active
   flinch while the passive response remains (`demo_nerve_cut_…json`).

## STALE — the claim no longer (or never did) describe the code

10. **"Joint actuators are force/torque-limited servos."** STALE as
    physics. The actuators are KINEMATIC pose writes (`joint_deg_`,
    ROM-capped ±90°, gait rate caps); no torque is computed anywhere in
    the actuation path. `intent_joint`'s force feeds the PRESS dimple
    distribution, not a servo limit. Consequence (named gap F-2):
    "obstruct an actuator and report the reaction load" has no
    implementation to test — obstruction of a pose write is the existing
    pin-ownership law; reaction loads require an actuator force state.
    The brief's own label ("servos, not contractile tissue") is the
    honest one and this lane keeps it.
11. **"Reflex plumbing … fails its controls."** STALE (pre-window-9
    state). Window-9 verified armed 15/15 fresh, and this lane's scratch
    demo re-verified the negative control live today (nerve cut ⇒ no
    active response, passive intact).
12. **"Three nearest pins with IDW squared … fold artifacts."** The
    ENGINE side is real (3 pins + weights per vertex are loaded and
    drive the blend); the IDW² PROVENANCE and the fold-artifact claim
    live in the graph lane's tools — reported-only here, not re-derived.

## REPORTED-ONLY — plausible, not re-verified by this lane

13. **"Coupled XPBD stack … bounded across tested substep counts;
    300 Hz, 2 GS iterations, n=4."** The membrane tick measured ~299–300
    fps (the live engine's own FPS log), but the XPBD solver wording
    describes a different module than the pressure law this lane reads;
    not re-verified. Fidelity caveat (1222.7 vs 1949 rad/s) — likewise
    reported-only; the ring prototype is not in this workspace.
14. **"Gait transitions … controller interruption produced abort/
    stumble."** Mechanism present; the recorded evidence was not re-run
    by this lane (out of slice).

## NEW findings this lane adds

15. **Scalar pressure cannot locate a touch within a cell** — confirmed
    by design reading: the C1 flinch used the touch POINT's x for the
    side (a hidden shortcut past the sensor), which is exactly the leak
    the patch layer closes: the controller now consumes only the
    patch-receptor field.
16. **The flinch's pin write mechanically re-stimulates its own
    detector while settling** (measured: after a 20 kN touch the
    envelope/pressure system needed a measured settle wait, not a fixed
    one — see an2_demo.py `wait_full_rest`). A real coupled-system
    behavior any future "recovery" claim must respect.
