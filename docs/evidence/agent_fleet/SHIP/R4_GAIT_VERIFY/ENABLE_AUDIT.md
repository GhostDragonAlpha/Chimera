# ENABLE AUDIT — why /tick_gait refused to arm (V3a-block)

Agent R3-gait "gait-doctor", fleet, 2026-09-14. Lane: `membrane_tick.cpp/.hpp` ONLY.
Scratches: 8145 (restored snapshot) + 8146 (fresh classify), private cwds, killed by PID.
Live 8107 untouched. No builds (builds serialize through the lead — see FALSIFIER).

## 1. THE EXACT FAILING PRECONDITION (not the harness's paraphrase)

- `/tick_gait`'s RESPONSE body carries no rung name: `{"ok":false,"error":"refused:
  needs gravity, stance, classification, pins 13-18, and a sealed feet cell"}` (the
  route's static text). The engine console logs nothing for a refusal.
- The engine names the rung in `GET /tick_state` → **`gait_enable_block =
  "no_channel_hip_L0"`** (both worlds, byte-identical). Reading: the LEFT strut-slot
  arc channel measured **m = 0.000000 m per the +1 deg probe**, under
  `GAIT_MIN_CHANNEL = 1e-3` — the F1 no-channel refusal, hip slot, side L, value 0.
- The anomaly ("the harness sees a sealed feet cell, set_gait's discovery returns
  none") DISSOLVES: both readers agree — `/tick_state.cells[0]` IS `seal_cells_[0]`
  (ylo=-0.0195, yhi=0.338) and set_gait's min-yhi law finds the same feet cell 0.
  The harness's `feetCell=-1` in V3a is `gait_feet_cell_`, which stays -1 because
  the arm refused two rungs later, at the probe channels.

Repro (deployed binary, restored snapshot): V1 135,618 N at +0.00950712 m, V2
kp=3.53082, V3 refuse `no_channel_hip_L0` — `repro_restored_8145.json`.
Formal harness run (deployed binary, fresh world): V0-V2 PASS, V3a FAIL —
`verify_current_binary_V3a_fail_fresh8146.json`.

## 2. THE MECHANISM (measured, not argued)

The tick's travel law is PURE SKINNING (`apply_travel`): a vertex moves only by its
own 3-pin blend. The shipped W8 vertbind (same-limb law, G7-verified 2026-09-14,
hash-pinned `47368352d8c960eb51e4a3bf6c08c06d`) therefore gives the FOOT SETS zero
hip weight — measured directly from the shipped blob, per side (n=1290 verts below
y=0.338 each):

| foot set | blend weight per pin |
|---|---|
| L | ankle_L (17) = 1095.958, ankle_R fill (18) = 130.846, knee_L (15) = 63.196, **hip_L (13) = 0.000 exactly** |
| R | ankle_R (18) = 1095.958, ankle_L fill (17) = 130.846, knee_R (16) = 63.196, **hip_R (14) = 0.000 exactly** |

A +1 deg probe of pin 13 moves no foot vertex: dminy = dcz = 0.0 EXACTLY → mh = 0.0
→ `no_channel_hip_L0`. Replicating the engine's own arithmetic offline (float64 on
the same blobs) reproduces the engine's numbers at printed precision.

The binding is RIGHT: W8's same-limb law exists to kill shear seams, and a hip
weight inside the foot blend WOULD be that seam. Under pure skinning NO correct
binding ever gives a hip a foot channel. The G1 machine's enable derivation assumed
anatomy ("probe pins 13-16") instead of measuring the binding — the prereg's own
F-STALL clause names this outcome: "the derivation is wrong -> FAIL; amend with the
logged channel and deficit." The logged channel is 0.0; this is the amendment.

## 3. CONTROL — fresh vs restored (R2's territory exonerated)

Fresh world on 8146 (`POST /session clear` equivalent: born empty; then
`python tools/classify_run.py http://127.0.0.1:8146` + H8's three named cuts
`{"y":3.415}` → `{"y":1.903,"cell":0}` → `{"y":0.338,"cell":0}`) produces the
byte-equal 4-cell tree (y-bands -0.0195/0.338, 3.415/9.9712, 1.903/3.415,
0.338/1.903; V 0.287914/12.5091/0.693006/0.334578) and refuses IDENTICALLY:
`gait_enable_block = "no_channel_hip_L0"` after the same V1 (135,618 N, +9.51 mm)
→ V2 (kp 3.531) → V3 sequence. There is ONE refusal, not two: restore-state is
ruled out (fresh arms neither). The defect is the machine-vs-binding law mismatch,
present in every world this authoring line builds.

## 4. THE FIX (membrane_tick.cpp/.hpp only; syntax-checked, NOT compiled)

1. **DRIVE PINS RESOLVED FROM THE BINDING, NOT ASSUMED.** Per side, per-pin NET
   blend weight = own-side total minus opposite-side total (a pin belongs to the
   side it moves MORE — this rejects the contralateral fill ankle, whose net is
   negative). Each side's drive pair = its two highest-net pins; fewer than two →
   refuse `no_drive_pins_L/R`. Resolution on this body: L {17: +965.112, 15:
   +63.196}, R {18: +965.112, 16: +63.196}. NOTE: plain top-2 OWN weight would
   have handed each leg BOTH ankles (fill 130.846 > knee 63.196) — the net law is
   what rejects it.
2. **ROLES SLOTTED BY MEASURED z-AUTHORITY** (never by anatomy): the STRUT (REACH
   z-servo, the old "hip" slot) = larger |dcz| probe → ankles 17/18; the CLEAR
   (LIFT/REACH clearance hold, the old "knee" slot) → knees 15/16. Channels:
   strut m=0.015346, clear m=0.002913 — both pass the unchanged F1 bar (1e-3) at
   15x / 2.9x. Refusal names carry the resolved pin id (`no_channel_pin17_L_...`).
3. **ACT COMPOSES OVER STANCE** (the prereg's own words made literal):
   `joint_deg_[strut_pin] = stance_th_ + machine strut component` — the balance
   servo's lean term survives while the machine strides; knee pins as before; hip
   pins 13/14 retire to authored bearing (zero footprint — writing them would be
   motion without a channel: animation).
4. **DISARM/CUT/BALANCE-LOSS** restore the composed ankles to stance's OWN
   component (`stance_th_` if stance on, else 0) instead of stomping raw 0.
5. **`no_lift_channel` ENABLE GATE REMOVED**, per the prereg's own law for that
   number: "the linear-channel estimate only sizes the step, and the measured
   error closes the rest." Measured null-z rise channel = 1.663e-5 (the drive
   channels are nearly collinear), while the REAL lift is 4.61 deg of strut within
   the 89-deg ROM; the LIFT gate (min-y >= STANCE_BAND_M) is measured and rate
   caps bound dparam (well-defined as ch -> 0: mx clamp; +inf handled by
   min/max; NaN only at err==0 where the gate fires anyway). Falsifier = F-STALL.
6. **FEASIBILITY AT ROM (measured, not linear-extrapolated):** strut-only at 89
   deg gives |d(centroid z)| = 0.6511 m > the REACH gate (patch_r 0.5711 m) — the
   walk gates are reachable. LIFT needs 4.61 deg. New fields: `/tick_state`
   gains `gait_strut_pin_l/r`, `gait_clear_pin_l/r`; the enable log entry gains
   `strutPinL/R`, `clearPinL/R` (the harness's enable replay checks a key SUBSET —
   extra keys are harmless).

Syntax: `g++ -std=c++17 -fsyntax-only -Wall -Wextra` clean (exit 0); every warning
is pre-existing (`touch_press` :931, R2's `load_seal_state` :1496-1507).

## 5. NAMED NEXT DEFICITS (walk-window owner — NOT touched here)

- **THE HARNESS MIRRORS THE REMOVED GATE** (one line, NOT committed — tools/ is
  outside this lane's commit scope): `tools/gait_verify.py` `replay_gate`, the
  `frm == "OFF"` branch requires `all(abs(g[k]) >= MIN_CHANNEL for k in
  ("chLiftL", "chLiftR"))`. With the measured chLift = 1.663e-5 the fixed engine
  ARMS but V4's log replay would count the enable entry not-OK. EXACT amendment:
  replace that clause with `all(g[k] != 0.0 for k in ("chLiftL", "chLiftR"))`
  (measured, signed, NONZERO — presence is P5's law; the magnitude bar was the
  removed engine refusal mirrored into the reader).
- **SERVO FRAME OBSERVATION** (shipped, unchanged): probe channels are stored per
  1-deg probe but consumed as per-radian by servo and rate caps — a 57.3x gain the
  ROM clamp and caps absorb (every transition stays measured-gate-owned). Window
  #4 should read cadence against P2's "~8 tau" and V7's teleport bar with this in
  mind. Changing it rewrites the machine's speed law — the lead's call, not a
  refusal audit's.

## 6. FALSIFIER (Rule 0)

- **BEFORE (measured this audit, both arms):** deployed binary, restored 8145 AND
  fresh 8146 — V3a refuses; `gait_enable_block = "no_channel_hip_L0"`; the failing
  precondition's measured value is m = 0.0 (hip-pin foot weight 0.000 exactly).
- **AFTER (desk-checked only):** the same gravity → stance → gait sequence arms —
  drives resolve to {17,15}/{18,16}, probes pass (0.015346 / 0.002913 >= 1e-3),
  `gait_on=true`, `gait_feet_cell=0`, `gait_strut_pin_l=17`, `gait_clear_pin_l=15`
  (r: 18/16) in `/tick_state`, and with the Section-5 harness line applied the
  run proceeds into V4-V10. The falsifier AGAINST this fix: if window #4 still
  shows a nonempty `gait_enable_block` with gravity+stance armed on a built
  binary, the fix is wrong and this audit reopens.

## 7. WINDOW #4 VERIFICATION (one command, after the lead builds)

Boot the new binary in a scratch cwd with its `session_snapshot/` (the harness
arms gravity and stance itself), then:

    python tools/gait_verify.py --base http://127.0.0.1:8139 --json docs/evidence/agent_fleet/SHIP/R4_GAIT_VERIFY/verify_after_fix_window4.json

(port = the lead's scratch; 8139 is the harness's documented default. Apply the
Section-5 one-line harness amendment first, or V4's replay will false-fail on
chLiftL/R. Empty-world alternative: boot empty, `classify_run.py <base>` + the
three cuts from Section 3, then the same command.)

Artifacts: `repro_restored_8145.json`, `verify_current_binary_V3a_fail_fresh8146.json`,
`fresh_8146_state_capture.json`, `drive_resolution_prediction.json` (this directory).
Raw scratch trees: `.tmp/gait_doctor/`, `.tmp/gait_doctor_ctl/` (killed by PID).
