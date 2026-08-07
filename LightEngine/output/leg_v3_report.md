# theLeg v3 Report

## 1. Theory (RULE 0)

**STATEMENT:** A captured muscle-bone machine can be made stable by routing the
muscle pull through a *rope* tendon (single-file chain) from the anchored
droplet apex to the arm-tip underside.  A rope pulls but cannot push, so when
slack it must crumple into the well rather than prop the lever.  Stability is
governed by a **full-arc gate** that requires the kernel static torque ratio
`R_true(theta) >= 1` on the whole reachable interval
`[-theta_load, +theta_muscle]`, making the muscle-side stop the unique
attractor.

**PREDICTION:** With the full-arc gate satisfied, the main run settles
muscle-side-down, the load end lifts, and the rope never sustains compression.
With the slack gate satisfied (`R_slack(0)` in [0.5, 1.0] and `max R_slack <= 1`
on the full arc), the control run settles load-side-down and the load end does
not lift.

**FALSIFIERS:**
- (a) LIFT   — main: load end rises >= 0.10 absolute z.
- (b) HOLD   — control: load end rises <= 0.05 all run.
- (c) BALANCE — settled lever-angle sign matches `sign(R_true - 1)`.
- (d) INTEGRITY — all five bodies remain one cluster each; pins hold.
- (e) SAG    — main settles muscle-down but load end does not lift.
- (f) SLACK  — main: sustained rope compression (> 20% of samples) = FAIL.

## 2. Build

- **Builder:** `LightEngine/seed_structures.py:leg()` (v3)
- **Driver:** `LightEngine/demo_seed.py:leg_main()` (v3)
- **Muscle:** anchored `4^3` droplet pinned to the well floor
- **Tendon:** single-file rope chain from droplet apex (`+d_eq`) to arm-tip
  underside (`-d_eq`)
- **Gate:** full-arc scan over 201 `contact_x` samples; droplet-size knob
  `{4,5,6}`; honest best-effort fallback if strict gate fails
- **Run:** 8000 ticks, dt = 0.0005, seed = 20260806
- **Tests:** `python -m pytest LightEngine/tests/test_structures.py -q` —
  **95 passed** (includes 14 leg-specific tests)

## 3. Gate Result

The strict full-arc gate did **not** pass for any contact or any droplet size in
`{4,5,6}`.  The builder recorded this honestly and fell back to the
least-bad contact.

| | main | control |
|---|---|---|
| route | best-effort | best-effort |
| gate_passed | False | False |
| droplet side | 4 | 4 |
| `contact_x` | +0.00662 | -0.06563 |
| `a_m` / `a_l` | 0.30630 / 0.29321 | 0.23405 / 0.36546 |
| cold `R_true` | 0.399 | 0.573 |
| `theta_stop_muscle` | 18.54° | 24.12° |
| `theta_stop_load` | -120.00° | -120.00° |
| `n_rope` | 2 | 2 |
| `well_floor_z` | -0.10000 | -0.10000 |

The rope is only two grains long (`n_rope = 2`), i.e. one link.  It can pull
but cannot crumple into a useful slack phase; the single-link geometry is a
consequence of the frozen v2 well depth and the 0.05 lattice step.

## 4. Dynamics Result

Logs:
- `LightEngine/output/print_leg_v3_log.txt`
- `LightEngine/output/print_leg_v3_control_log.txt`

Begin/end frames were rendered to:
- `LightEngine/output/v3_begin.png`, `v3_end.png`
- `LightEngine/output/v3_control_begin.png`, `v3_control_end.png`

The default camera distance makes the frames a single blob; they are present
for the record but do not resolve the rope.

### Main run

- Settled lever angle: **+48.66°** (muscle-side-down)
- Max |theta|: **49.22°**, exceeding `theta_stop_muscle` (18.54°)
- Load gain: **-0.2444** (load end dropped, did not lift)
- Rope state: slack 95% of samples, tension 5%, compression 0%
- Final rope mean link force: +0.402
- Min arm-tip-to-droplet distance: 0.0281
- Droplet apex z held at 0.0995 (anchor held)

### Control run

- Settled lever angle: **+8.93°** (muscle-side-down, not load-side-down)
- Max |theta|: **17.07°**, within stops
- Load gain: **-0.2761** (load end dropped, held)
- Rope state: slack 95% of samples, tension 5%, compression 0%
- Final rope mean link force: +0.442
- Min arm-tip-to-droplet distance: 0.0251
- Droplet apex z held at 0.0995

## 5. Verdict

### Main

- (a) LIFT      : **FAIL** — load end dropped; max load_gain = 0.0000
- (c) BALANCE   : **FAIL** — `R_true = 0.399` predicts load-side-down, but the
  machine settled muscle-side-down (+48.66°)
- (d) INTEGRITY : **PASS** — all bodies one cluster; plate pins held
- (e) SAG       : **DETECTED** — muscle-down settle with no load lift
- (f) SLACK     : **PASS** — rope compression fraction = 0.00 (the rope went
  slack rather than compressed)

### Control

- (b) HOLD      : **PASS** — max load_gain = 0.0000 <= 0.05
- (c) BALANCE   : **FAIL** — `R_true = 0.573` predicts load-side-down, but the
  machine settled muscle-side-down (+8.93°)
- (d) INTEGRITY : **PASS** — all bodies one cluster; plate pins held

## 6. Conclusion

The strict full-arc gate did not yield a buildable machine with the frozen v2
well and the 0.05 lattice step: no contact in the scanned bracket satisfied
`min R_taut >= 1` on `[-theta_load, theta_muscle]`, and the droplet-size knob
`{4,5,6}` did not rescue it.  The best-effort dynamics confirm the gate's
judgement rather than contradict it: both main and control runs settled
muscle-side-down, the load end never lifted, and the lever rotated past the
derived muscle-side stop in the main run.

The rope did avoid compression (SLACK pass), but with only two grains it could
not crumple out of the way; it simply went slack and the lever fell through the
unpriced arc.  The v2 relaxation-lurch pattern repeats in sign-reversed form:
a load-favoring `R_true` at print is overcome by the initial dynamics, and the
machine lives on the side of the arc where the gate said it should not.

**Verdict:** theLeg v3 theory is **falsified as implemented**.  The falsifier
prescribed by `docs/THE_CATEGORIES.md:1042-1046` fired: the rope-tendon +
full-arc-gated machine settled muscle-down in both runs, past the muscle-side
stop in main, with the load end dropping rather than lifting.  The next level
is the skeleton's geometry — the well depth, lever length, or lattice spacing
must carry the stability, not a contact hunted after the fact.
