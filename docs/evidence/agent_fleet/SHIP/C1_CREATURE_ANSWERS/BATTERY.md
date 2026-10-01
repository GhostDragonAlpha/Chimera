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
| B1 | ARM | `{"on":true}` | `ok:true`, `reflex_on:true`, flinch pins **17/18** once the gait machine has resolved on this body (adopted LIVE — window-9 fix; arming before gait is legal, the pins arrive when gait first enables and `reflex_block` clears itself), breath cell 1, period ≈ 13.38 s |
| B2 | breathing visible | poll /verts (torso-band min/max y) 30 s | oscillation at ≈ 13.4 s period, peak ≈ 1.5–3 mm; **max\|P\| over cells EXACTLY 0** (R1a); **\|conserve_pct\| ≤ 2e-4** (the measured noise; R1b) |
| B3 | **suspend the oscillator (negative control)** | `{"breathing":false}` | /verts drift returns to **exactly 0** within one poll (the M5 zero-motion reference); `{"breathing":true}` resumes (R1 falsifier b) |
| B4 | flinch positive | full rest (all rungs off), `{"hit":belly,"force_n":20000}` | touched side's `reflex_flinch_env_*` = 1 then decays to 0 in ≈ 2.5 s (5 tissue taus); the touched side's FOOT set shows the flex in /verts (≥ 5 mm max displacement vs its unarmed-press baseline) |
| B5 | flinch tolerance (negative control, level) | identical rest, 10000 N touch | env stays **exactly 0** (51 kPa < 100 kPa threshold — gentle handling tolerated) |
| B6 | **THE NERVE CUT (negative control)** | `{"pressure_coupling":false}`, then the IDENTICAL B4 touch | env stays **exactly 0**, foot motion == baseline ("a reflex that fires without its stimulus is an animation" — the cut proves the B4 motion was the pressure coupling and nothing else); `{"pressure_coupling":true}` restores; a post-restore touch fires again |
| B7 | startle positive | gravity+stance armed, settled (pressures exactly 0), sharp 2 kN touch | `reflex_startle_env` = 1 → decays ≈ 2.5 s; `stance_ankle_deg` shows the ≈ 2.03 deg bias pulse away from the touch; **\|stance_ankle_deg\| ≤ 5 deg at every poll** (inside the existing cap) |
| B8 | **the walker gate (negative control)** | gravity+stance+gait armed, walking; touches during the walk | flinch env AND startle env stay **exactly 0** while `gait_on:true`; strides continue (the walker is not fought); the walk's own 24 MPa pressures fire nothing |
| B9 | **post-cut quiet window (negative control)** | cut gait mid-stride (`{"on":false}` to /tick_gait) | for 1.0 s after the cut no flinch/startle trigger (the measured 583 MPa/s collapse rings nothing); envs stay 0 through the settle |
| B10 | gait 15/15 ARMED (the pre-built falsifier) | reflexes armed, world torn down to QUIET REST (gait off, stance off, settled, max\|P\| exactly 0) or a FRESH scratch, then `python tools/gait_verify.py --base http://127.0.0.1:816x` | **all 15 bars PASS** — V1c/V10 (pressures exactly 0) prove the breath is pressure-blind through the harness's own gates; V8 proves conservation; V4/V5/V7/V9 prove the walker never fought |

Control leg (current binary, reflexes absent): 15/15 PASS
`gait_verify_control_scratch8164.json`. Armed control (window-8 binary,
FRESH boot, reflexes armed, gait_verify first): 15/15 PASS —
`gait_verify_armed_fresh_scratch8167.json`; V10 root home +0.00950 exact.

## Reading the verdicts

- B2 fails with max|P| oscillating at the breath period (~14.9 MPa scale)
  → the breath leaked into the kappa inputs: R1's falsifier (a); the pass
  order is wrong — stop, fix, re-run (do not re-tune thresholds).
- B6 fires → the "reflex" is an animation; the coupling is not the driver.
- B8/B9 fire → the reflex fights the walker: the gate is broken.
- B10's V1b/V1c/V10 fail alone → CHECK THE WORLD, not the reflexes: the
  harness demands a fresh gravity-only settle. Window-8's armed run
  launched into B7–B9's live world (its own state0: gait_on=True,
  stance_on=True, root_vy=−0.175) and read the stance servo's transient
  as the reference; that run's final_state was the exact home
  (root +0.00950712, contact m·g, P 0, ankles 0).
- Everything passing with the interim constants = the plumbing is proven;
  the CONSTANTS then go to Astra (PREREG: rate/amplitude, flinch
  threshold/amplitude, startle threshold/magnitude).

## WINDOW-9 AMENDMENTS (after the window-8 run)

- **Canonical field names** (the lead's `flinch_env_l/r` guesses are
  retired): read `/tick_state` — `reflex_flinch_env_l`,
  `reflex_flinch_env_r`, `reflex_flinch_pin_l`, `reflex_flinch_pin_r`,
  `reflex_flinch_last_tick`, `reflex_flinch_last_cell`,
  `reflex_startle_env`, `reflex_startle_last_tick`,
  `reflex_startle_bias_deg`, `reflex_breath_disp_m`,
  `reflex_breath_phase_deg`, `reflex_breath_period_s`, `reflex_quiet_s`,
  `reflex_p_coupling`, `reflex_block`. The `/tick_reflex` echo now also
  exposes `flinch_env_l/r`, `startle_env`, `quiet_s` beside
  `flinch_pin_l/r`.
- **B7 note**: the startle requires the stance rung settled ≥ 1 s (the
  corollary-discharge gate — the window-8 binary fired the startle once
  on the stance-arm transient, tick 3273, with no stimulus: self-generated
  motion does not startle). Arm stance, wait > 1 s, then touch.
- **The breath pass now sits AFTER the FALL law's root read** — the root
  home is breath-blind by construction (the lead's option B, taken as
  hardening even though the measured V10 failure was the leftover-world
  artifact, not the breath).
- Reproduction record: `repro_window8_bugs.json`.
