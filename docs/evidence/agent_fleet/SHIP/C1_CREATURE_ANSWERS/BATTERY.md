# C1 CREATURE ANSWERS — BATTERY DESIGN (window #8)

Scratch engine only (port 816x, snapshot-copied isolated cwd, killed by
PID); live 8107 GET-only; no /frame pulls; headless only. **Compact JSON
bodies — a space in `{"on": true}` parses as DISARM** (R4_GAIT_VERIFY/
PROTOCOL.md; the /tick_reflex route keeps the house law deliberately).

Every probe reads `/tick_state` (the `reflex_*` field set) and `/verts`
([u32 n][f32 x9]) — the page could render both; nothing here is engine-
internal. Stimulus generator: `POST /tick_touch {"hit":[x,y,z],"force_n":F}`
(world point; the belly hit (−0.000, 5.112, −4.288) is the measured
mid-radius torso vertex). Negative controls are B3, B5, B6, B8, B9.

| # | probe | body | PASS bar |
|---|-------|------|----------|
| B0 | DEFAULT OFF | fresh boot, GET /tick_state | `reflex_on:false`, breath fields 0/−1, no motion (the M5 reference: /verts drift exactly 0) |
| B1 | ARM | `{"on":true}` | `ok:true`, `reflex_on:true`, `reflex_block:""`, flinch pins **17/18** (the gait-resolved same-limb law), breath cell 1, period ≈ 13.38 s |
| B2 | breathing visible | poll /verts (torso-band min/max y) 30 s | oscillation at ≈ 13.4 s period, peak ≈ 1.5–3 mm; **max\|P\| over cells EXACTLY 0** (R1a); **\|conserve_pct\| ≤ 2e-4** (the measured noise; R1b) |
| B3 | **suspend the oscillator (negative control)** | `{"breathing":false}` | /verts drift returns to **exactly 0** within one poll (the M5 zero-motion reference); `{"breathing":true}` resumes (R1 falsifier b) |
| B4 | flinch positive | full rest (all rungs off), `{"hit":belly,"force_n":20000}` | touched side's `reflex_flinch_env_*` = 1 then decays to 0 in ≈ 2.5 s (5 tissue taus); the touched side's FOOT set shows the flex in /verts (≥ 5 mm max displacement vs its unarmed-press baseline) |
| B5 | flinch tolerance (negative control, level) | identical rest, 10000 N touch | env stays **exactly 0** (51 kPa < 100 kPa threshold — gentle handling tolerated) |
| B6 | **THE NERVE CUT (negative control)** | `{"pressure_coupling":false}`, then the IDENTICAL B4 touch | env stays **exactly 0**, foot motion == baseline ("a reflex that fires without its stimulus is an animation" — the cut proves the B4 motion was the pressure coupling and nothing else); `{"pressure_coupling":true}` restores; a post-restore touch fires again |
| B7 | startle positive | gravity+stance armed, settled (pressures exactly 0), sharp 2 kN touch | `reflex_startle_env` = 1 → decays ≈ 2.5 s; `stance_ankle_deg` shows the ≈ 2.03 deg bias pulse away from the touch; **\|stance_ankle_deg\| ≤ 5 deg at every poll** (inside the existing cap) |
| B8 | **the walker gate (negative control)** | gravity+stance+gait armed, walking; touches during the walk | flinch env AND startle env stay **exactly 0** while `gait_on:true`; strides continue (the walker is not fought); the walk's own 24 MPa pressures fire nothing |
| B9 | **post-cut quiet window (negative control)** | cut gait mid-stride (`{"on":false}` to /tick_gait) | for 1.0 s after the cut no flinch/startle trigger (the measured 583 MPa/s collapse rings nothing); envs stay 0 through the settle |
| B10 | gait 15/15 ARMED (the pre-built falsifier) | reflexes armed, then `python tools/gait_verify.py --base http://127.0.0.1:816x` | **all 15 bars PASS** — V1c/V10 (pressures exactly 0) prove the breath is pressure-blind through the harness's own gates; V8 proves conservation; V4/V5/V7/V9 prove the walker never fought |

Control leg (already run, current binary, reflexes absent — the behavior
reference the armed run must reproduce): 15/15 PASS
`gait_verify_control_scratch8164.json`.

## Reading the verdicts

- B2 fails with max|P| oscillating at the breath period (~14.9 MPa scale)
  → the breath leaked into the kappa inputs: R1's falsifier (a); the pass
  order is wrong — stop, fix, re-run (do not re-tune thresholds).
- B6 fires → the "reflex" is an animation; the coupling is not the driver.
- B8/B9 fire → the reflex fights the walker: the gate is broken.
- B10's V1c/V10 fail alone → the breath is pressure-visible only under the
  harness's exact sequencing; audit pass order, not amplitudes.
- Everything passing with the interim constants = the plumbing is proven;
  the CONSTANTS then go to Astra (PREREG: rate/amplitude, flinch
  threshold/amplitude, startle threshold/magnitude).
