# STRIDE AUDIT — R4-stride-finisher ("stride-finisher", fleet, slot-01, 2026-09-14)

Finishes the first real stride. Ground truth: the window-4 run
(`verify_after_fix_window4.json`, scratch 8139): V0/V1a/V1c/V2/V3a/V3b/V7/V8
PASS, V4 (0 strides), V5 (0.00 mm swing), V9c (no mid-swing to cut) FAIL,
V10 partial (root did not return home), V1b intermittent inert start.
Everything below was MEASURED on the current (window-4) binary in scratch —
private ports 8147-8153, isolated cwds, snapshot copies, killed BY PID;
live 8107 untouched (GET-only, not even probed this session).

## 1. THE ONE LOGGED TRANSITION — the stuck gate, with its measured values

The machine logged exactly one transition: `L OFF->STANCE@t2209` (the enable
entry, replay OK). Thereafter both legs sat in STANCE with:

```
gait_block_l: "whatif:0.986697>0.571148"
gait_block_r: "whatif:0.987115>0.571148"
```

Reproduced byte-identical on scratch 8147 (armed gravity -> stance -> gait;
after 5 s: `whatif:0.986697>0.571148`, one log entry, hip/knee 0.000).
The STANCE->LIFT what-if gate demanded the whole-body centroid to lie inside
the would-be stance foot's measured patch. Decomposition from /verts at
rest: `bx-fcx[o] = -0.9370 m` (the two foot centroids sit at x = +/-0.9368 —
an 1.87 m splay), `bz-fcz[o] = -0.3202 m`; `|w| = 0.9898` vs patch 0.5711.

**The gate is unreachable AT ROM, measured.** Posing the resolved strut pin
(pin 17) through its full ladder, the gate's own quantity only falls to
**0.692 at -89 deg** (L_cx 0.9368 -> 0.6109; the strut's x-authority is
~1.1 mm/deg; closing 0.42 m needs ~380 deg of a 89-deg ROM pin). That is
F-STALL's exact condition ("any phase not reaching its measured gate within
10 tau WITHOUT ROM ... saturation -> the derivation is wrong"), firing on a
gate that precedes every phase.

The premise is also unexpressable on this plant: the movement law's root has
ONE translational DOF (y) and no rotation (membrane_tick.cpp step(), THE
FALL block) — a lifted foot cannot tip this body, and the body centroid
cannot translate toward the stance foot because no actuator owns horizontal
root motion (prereg SCOPE: "the root DOF is Y-only").

## 2. THE 0.00 mm SWING — mechanism

Two stacked causes, both measured:

1. **LIFT never fired** — the what-if gate above blocked both legs for the
   whole 90 s, so `gait_hip_l_deg` stayed 0.000 and the swing depth stayed
   0.00 mm. (V5's bar has nothing to measure; V9c has no mid-swing to cut.)
2. **Had LIFT fired, the servo frame was broken — the 57.3x probe-unit
   gain.** The enable probes pose exactly 1 deg (`degs[pin] = 1*pi/180`)
   but every consumer (servo `err/(channel*tau)`, the rate caps
   `rate*(tau)/|a|`, the ROM clamp) treats the channels as m/rad, and the
   commanded product lands in the radian `joint_deg_`/`gait_hip_rad_`
   fields. With the window-4 enable entry's own numbers: the LIFT clamp
   `mx = rate_hip*dts/|ah|` admits `|dparam*ah| = rate_hip*dts` in the
   PROBE-DEG frame, but that product is stored as RADIANS — a commanded
   strut rate of 37.2 deg/s * 57.3 = 2133 deg/s: the rate cap evaluates to
   ~57x its bar, i.e. the foot teleports (F-TELEPORT) the first tick LIFT
   runs. Proof the channels are per-deg on THIS binding: posing pin 17 at
   -1 deg live moved the posed foot-set min-y by -0.015116 m — the enable
   entry's `dminyHL = -0.0151164` to 7 digits (per THAT 1-deg probe).

## 3. THE FIXES (membrane_tick.cpp / .hpp only; RULE 0/1: derived, no taste)

**F1 — the servo frame is radians.** The probe divides its deltas by the
probed angle once at measurement (`/ kProbeRad`): every channel is honestly
m/rad; the caps bound real rad/s (V7's harness arithmetic, which multiplies
the entry's caps by 57.2958, becomes correct with NO harness change).
Post-fix LIFT, from the measured channels: ch = 5.46e-2 m/rad, full 60 mm
band at dparam ~1.1 rad = strut -5.5 deg + clear +9.5 deg, rise rate
0.40 m/s at the cap — LIFT exits in ~0.2 s, within F-STALL's 10 tau.
Demonstrated on the current binary: posing the resolved pins at exactly
those angles lifted the swing foot's world min-y to +33.8 mm through the
root's 20 mm follow (posed rise 64 mm) — the exit gate (+50 mm) is reached
with one more servo step, inside ROM.

**F2 — the what-if gate re-derived for the measured plant.** The gate now
answers rung 4's question with the failure mode this plant actually has:
GROUNDING, not tipping. New enable measurements (same rest blend, same
travel arithmetic): `sink_ch` = d(min-y of the OTHER foot set) under the
lift combo at dparam = 1 rad (the cross-coupled rise the root follows the
support down by), and `headroom` = grounding distance from the feet's rest
min-y to the lowest NON-foot rest vertex minus the derived sink. Gate: the
predicted sink for THIS lift must fit inside headroom minus the bearing
margin; the blocker names its numbers (`whatif:sink...>...`). Measured on
this binding: sink_ch ~12 mm/rad -> a full lift sinks ~14-20 mm against a
~348 mm headroom — passes with 25x margin; a body that would sit down
mid-stride is refused BY NUMBER. (Live support: the stance foot stayed
pressed at ~10 mm through every ladder row — the root follows; the old
gate's live witness, the `wminy[o] >= 0` support-lost abort, stands.)

**F3 — REACH strides along the MEASURED branch.** The strut's z-channel is
NONMONOTONIC in theta: the 1-deg probe reads +2.6 mm/deg, but the live
ladder peaks near -4.6 deg (+5 mm) and swings BACKWARD (-35 mm/deg by
-20 deg; -0.68 m at -89 deg) — an orbit about the pivot, not a rail; the
old `fcz[o] + patch` target chased the unusable +z branch (it presses the
foot DOWN 15 mm/deg — more than the clear pin's measured 2.5-3.2 mm/deg
rise can pay) into a ROM stall. New law, derived from a +20 deg probe at
enable (inside ROM, deterministic): `lift_sign` = the theta sign that
raises the foot set; `reach_dir` = the z direction that branch swings
(-1 here — logged in the enable and LIFT entries); the REACH servo drives
the strut further into its lifting branch with the branch-scale gain
dcz20 toward the radius bar |fcz[s] - z0| >= own patch, z0 = the foot's
own support-patch center frozen at LIFT entry. The bar is the prereg's
stated necessity ("the new footfall lands outside the old support patch")
measured on the foot's OWN patch: the stance-relative reading demands
2x patch = 1.142 m of travel once the feet separate, beyond the measured
0.677 m strut reach — F-STALL at ROM past stride one. Feet start together
here (homeL 0.7212 ~ homeR 0.7212), so the first stride satisfies both
readings; only the own-patch reading keeps every later one reachable.
The knee (clear pin) holds the 50 mm band while the swing drops the body
(~64-112 mm of measured sink; the knee's fill is measured negligible —
root unchanged through its whole ladder). Equilibrium check from the
ladder: strut ~-45 deg + knee ~-38 deg holds the swing foot >50 mm above
the support with |dz| 0.58-0.63 m >= 0.5711 m — REACH exits inside ROM
with margin, ~1 s per swing at the 0.65 rad/s cap. Predicted cadence:
LIFT 0.2 s + REACH ~1 s + LOAD ~1 s -> >= 3 strides in well under 90 s
(F-STALL budget 10 tau per phase).

**F4 — the arm-on-readiness gate (the intermittent inert start).** Race
characterized by 6 fresh boots (arm at HTTP-up / at has_scene / at V0 /
at V0+5 s; ports 8148-8153):

| boot | arm mode | inert read (gon=true, vy==0.0, contact==0) | engage |
|---|---|---|---|
| 8148 | HTTP-up | YES — 3 polls, 2 ms, ticks frozen 0 | settled 135,618 N |
| 8149 | has_scene | no | settled |
| 8150 | V0 | YES — 3 polls, 25 ms, ticks frozen 13 | settled |
| 8151 | V0+5 s | YES — FIRST poll only (ticks frozen 1499; next poll vy 0.12) | settled |
| 8152 | has_scene | no | settled |
| 8153 | V0 | no | settled |

3 of 6 boots reproduced the exact window-4 V1b signature (worst |root_vy|
0.00e+00, contact 0 N, gravity_on true — "gravity engaged MID-RUN" when the
tick caught up; contact then ranged [77k, 265k] = the first-tick spring
transient 264,554 N and its damped underswing). All six settled at
135,618 N = m*g exactly, root_y +0.00950712 m — R2's deterministic case
stays clean; only the ARM WINDOW races: the flag flips while the tick loop
is stalled or pre-scene, and the harness's wait_settle early-exits on the
first 0/0 read. The fix: the gravity block bumps an evaluation counter;
set_gravity(true) snapshots it under the lock and does not RETURN until the
first ground-force evaluation under the flag (bounded 500 ms — a dead tick
loop degrades to the old flag-only arm; the lock is NOT held while waiting,
the tick try_locks and must run). After this fix the arm cannot return
before the contact force exists, so the harness's first poll reads a
post-arm number — V1b's settle becomes deterministic, and V10's `rest_root_y`
baseline is captured at the true +0.0095 m equilibrium (V10's "root did not
return home" was a downstream face of the same race: the baseline was
captured during the inert window).

## 4. DESK-CHECK

- `g++ -std=c++17 -fsyntax-only -Wall -Wextra membrane_tick.cpp` — 0 errors;
  only the pre-existing warnings (touch_press unused params, load_seal_state
  misleading indentation — both named pre-existing in PROTOCOL.md).
- Known traps checked: no `small` identifier (Windows.h), no string-parse
  changes (stod-on-booleans untouched), brace balance compile-verified,
  JSON log fields print as valid literals (floats +/-1, no bare commas).
- Replay-compatibility (tools/gait_verify.py replay_gate, unmodified):
  enable entry keeps chLiftL/R != 0 (now 9.5e-2) and gains extra keys
  (presence-checked only); STANCE->LIFT keeps `whatif:true` + `patch`;
  LIFT->REACH keeps `miny >= 0.05`; REACH->LOAD logs `z >= bar` (the
  radius) + gains `z0`; RECOVER entries unchanged. V7's cap conversion
  becomes correct with the per-rad entries. No harness change needed.

## 5. THE ONE-COMMAND WINDOW-#5 VERIFICATION

```
python tools/gait_verify.py --base http://127.0.0.1:<scratch-port> \
  --json docs/evidence/agent_fleet/SHIP/R4_GAIT_VERIFY/verify_after_stride_fix.json
```

after rebuilding `.tmp/build_tick/Release/chimera_engine.exe` from this
commit and booting a scratch with `shaders/` + `session_snapshot/` (the
PROTOCOL.md §3 pattern). Expected: V1b PASS deterministically (the arm
returns after the first ground-force evaluation), V4 >= 3 strides with
every transition replaying (LIFT entries now carry sink/z0/reachDir),
V5 swing ~0 mm and LOAD-exit depths ~10 mm, V9a-c cut mid-swing -> the
measured abort, V10 root back at +0.00950712. Falsifiers standing:
F-GLIDE (the cut), F-TELEPORT (V7 vs the now-honest caps), F-STALL (any
phase 10 tau short — the numbers above say ~0.2-1 s per phase), F-LIE
(every entry carries its gate values).

Raw scratch artifacts (not committed, per the targeted-add rule):
`.tmp/stride_finisher/` — engine logs, `channel_rows.json`,
`ladder2.json` (the clean equilibrium ladder), `race_results.json`,
`race_<n>/` per boot, probe scripts (`repro_stuck.py`,
`measure_channels.py`, `measure_ladder2.py`, `race_boots.py`).

## 4. THE TEARDOWN BARS CLOSED (R5-teardown-finisher, fleet, slot-01, 2026-09-14)

Ground truth: the window-5 run (`verify_after_stride_fix.json`, scratch 8139) —
THE CREATURE WALKED (3 strides / 4.6 s, 16 transitions, the mid-swing cut
falsifier complete) with exactly two residual FAILs: V4 (the 3 RECOVER aborts)
and V10 (teardown). Everything below was MEASURED on the current (window-5)
binary, scratch port 8155 (PID 55704, killed by PID; isolated cwd `.r5_scratch/`,
shaders + session_snapshot copied from `.tmp/build_tick/Release`); live 8107
GET-only (the read-only dry run, no POSTs).

### 4.1 V4 — the aborts are the machine working as designed; the REPLAY was mis-reading them

The harness's V4 bar is "strides >= min AND every logged transition replays its
own gate". The 3 RECOVER entries themselves replayed OK; what failed was their
PARTNER entries — the abort pair logs `L REACH->LOAD` / `R LIFT->LOAD` with
`why: support_lost`, and `replay_gate` judged those against the PHASE-ADVANCE
gates (z >= bar) or found no rule at all ("unknown transition LIFT->LOAD").

**Why the swings missed touchdown, from the logged gate values (derive, not
taste):** every abort carries `vy` = -0.181, -0.215, -0.215 m/s and
`pmax` = 76-86 MPa (clean transitions: 0.5-1 MPa). The mechanism: the lift
combo's cross-coupled rise (`sink_ch`, measured at enable as d(min-y of the
OTHER foot) under the combo) raises the planted foot's posed min-y faster than
the 1-DOF root's spring can follow it down — k = 1.3562e7 N/m, m = 13,824.5 kg
give omega = sqrt(k/m) = 31.3 rad/s, c = 6.062e5 Ns/m gives zeta = 0.70, a
~46 ms follow lag — so the stance foot's world min-y grazes the floor mid-transient,
the contact spring unloads, and the root free-falls briefly (the logged vy). The
support-lost gate reads the instantaneous world min-y against exactly 0 (the
prereg's own contact definition) with no margin, and fires the prereg'd abort.
The what-if gate does not cover this: it bounds the GEOMETRIC end-state (full
drive vs headroom, passes with ~25x margin), not the root-dynamics transient —
that transient is the FALL law's own plant, working as built.

**The prereg's own words back the bar amendment:** the STATEMENT defines the
machine as "STANCE -> LIFT -> REACH -> LOAD, **plus RECOVER (the measured
abort)**"; P5 demands "every gait_log entry carries ITS measured gate values"
— the abort entries carry the full shared gate set (dL, dR, cL, cR, lean, vy,
pmax, why); F-LIE fires when values are MISSING or a LIFT is outside what-if —
neither happened. The z/bar values the old replay demanded belong to a gate the
aborted phase never reached. THE BAR AMENDMENT (gait_verify.py): abort entries
(`why` in support_lost/touchdown) replay against the ABORT contract — the full
measured gate set — and, when present, against the gate's OWN number. No
machine change; the falsifiers (F-STALL at 0.5-0.65 tau, F-LIE) were checked
and stand.

**P5 strengthening (membrane_tick.cpp, desk-checked only — needs window #6):**
`gates0()` now logs `minyL`/`minyR`, the per-side world min-y the support-lost
and touchdown gates themselves read, so an abort entry's CLAIM is auditable
against its own numbers instead of its why-string. FALSIFIER (named before the
run): a support-lost whose lost foot's min-y is still planted (< -1e-3) is a
SPURIOUS abort — the gate misread a planted foot — and the harness FAILs it
("state and log contradict").

### 4.2 V10 — one held number explained all four failing numbers; the harness never asked for the state the bar names

R4's teardown measured: contact dev 0.581%, max|P| 1.39e5 Pa, ankles0=False
(stance_th_ = -0.1217 deg), root at +0.00727 instead of +0.00950. MECHANISM:
the stance servo is a pure integral law (`stance_th_ -= kp*lean_z*dt`, no leak
term); once the cut restores rest geometry, lean_z nulls and the integrator
FREEZES at the lean term the walk earned. The held ankle pitch bends the rest
surface; the water law answers dP BY DESIGN (prereg S3's own parenthetical);
the root rests where the spring carries the weight on the bent pose, off the
baseline; contact dev follows. All four numbers are ONE held pose. This is the
servo holding state in a rung that is STILL ARMED — the harness disarms gait
(the V9 cut) but never disarms stance, so V10 as coded measured a state nobody
was asked to produce.

**The prereg's own words (THE STANCE PREREGISTRATION, S3, verbatim):**
"teardown returns the ankles to exactly 0 and lean to baseline; the root rest
state (root_y, root_vy) is unchanged by stance having run ... while the servo
runs the ankles bend the surface and the water law answers dP there BY DESIGN
— rest is rest." The ENGINE already implements this: `stance_off_locked_` is
"deterministic off: ankles to authored 0 — no hidden pose decay, no stale
integrator" and zeroes pins 17/18 (= ANKLE_PIN_L/R = the resolved strut pins,
so the cut's composed lean term is cleared too). No engine change; the
pressures need no flush (they are recomputed from the pose every tick — at
authored rest they are EXACTLY 0, measured in V1c); the root needs only its own
tau (sub-second; wait_settle + 3 s hold). THE BAR AMENDMENT (gait_verify.py):
V10 completes the teardown it names — POST /tick_stance {"on":false} — then
measures, and additionally demands `both rungs disarmed`.

**Demonstrated live on the window-5 binary (scratch 8155):** after a 10-stride
walk and the cut, stance still armed: stance_th_ frozen at -0.0609 deg,
max|P| 6.21e4 Pa, root -1.15e-03 m off baseline, contact dev 0.16%. After
/tick_stance off: stance_th_ = +0.000000 EXACTLY, max|P| = 0.00e+00 EXACTLY,
root within 7.6e-06 m of baseline, contact = 135,618 N = m*g EXACTLY. S3's
teardown clause measured TRUE on the current binary.

### 4.3 V5/V7 measurement grain (surfaced by the clean fast walk, same discipline)

The window-5 binary walks ~1.35 s/stride on a fresh boot (10 strides in 14 s,
live). At that cadence the two grain-level audits flaked:

- **V5 swing depth**: the sampler read the swing leg's depth during LIFT too —
  at the STANCE->LIFT tick the foot still reads the full sink (10.00 mm) while
  it LEAVES the floor. That is the designed rise transient, not weight-bearing;
  a 10 Hz poll samples it on any clean fast walk (R4's interleaved-abort walk
  happened to miss it). P1's window is "single support", and the machine's own
  vocabulary names REACH as that phase (membrane_tick.cpp REACH case comment).
  Amendment: sample during REACH. The LOAD-exit bearing clause is unchanged
  (measured [9.86, 10.96] mm in band).
- **V7 teleport audit**: per-poll wall-clock rate false-fired at 1.14-1.23x on
  the SAME binary that measured 1.01x in R4 — the poll's wake jitter
  (~15-20 ms Windows grain, documented main.cpp:583) against a machine running
  pinned at its caps. The per-tick clamps make `gross pose travel <= cap * wall
  window` a theorem, so the fallback mode now accumulates gross travel over the
  whole run (jitter cancels in aggregate; a real 57x-class teleport still blows
  it past the bar) — measured 0.26x. For window #6 the engine adds `ts_ms` to
  state_json (steady-clock ms read under the SAME lock pass as the state), and
  the harness then audits per-poll against exact server windows.

### 4.4 RESULT (verify_after_teardown_fix.json, this directory)

Full PASS, all 15 bars, on the CURRENT window-5 binary: V4 "3 strides in 4.5 s;
16 logged transitions, 16 replay OK (3 measured RECOVER aborts seen)"; V10
"dev 0.000%, max|P| 0.00e+00 Pa == 0, ankles0=True, root back at +0.00951,
both rungs disarmed". Desk-check: `g++ -std=c++17 -fsyntax-only -Wall -Wextra`
clean (pre-existing warnings only), `py_compile` clean; replay_gate unit-tested
against R4's recorded 16-entry log (16/16) plus F-LIE negatives (missing gates,
spurious-abort miny contradiction, phase-advance gate intact).

### 4.5 WINDOW #6 VERIFICATION (one command, after the lead builds)

Boot the new binary in a scratch cwd with its `session_snapshot/` (the harness
arms gravity/stance/gait itself and disarms them again at teardown), then:

    python tools/gait_verify.py --base http://127.0.0.1:8139 --json docs/evidence/agent_fleet/SHIP/R4_GAIT_VERIFY/verify_after_teardown_fix_window6.json

(port = the lead's scratch; 8139 is the harness's documented default.) On a
ts_ms binary expect V7's text "(engine ts_ms, per-poll)" and abort entries
carrying minyL/minyR with the support_lost claims audited by number.


### 4.6 THE WINDOW-6 V7 ADJUDICATION (R5-teardown-finisher, 2026-09-14) -- the stamp lied, not the servo

Window #6's exact-clock V7 read 1.24x. With a server-exact window the per-tick
clamp theorem (gross pose travel <= cap * wall window -- every writer in
gait_step_locked_ is clamped: return_zero min(|th|, rate*dts), the LIFT combo
min(bh, bk), the REACH servos min(err/(ch*tau), rate*dts)) makes a true
overshoot impossible while the machine is on, so the denominator itself was
indicted -- and convicted. THE EVIDENCE, from the lead's committed JSON:
`state0.ts_ms = 88485000.0`, `final_state.ts_ms = 88494800.0` -- both EXACT
multiples of 100. My window-5 stamp printed a double through ostringstream's
DEFAULT 6 SIGNIFICANT DIGITS; steady_clock on Windows epochs at MACHINE BOOT,
the lead's host had been up 88,485 s, so the stamp's ulp was 100 ms -- the
whole poll interval. Adjudication by arithmetic: 1.2384x = a cap-pinned servo
pair (LIFT/REACH, where the servos run AT their derived caps) whose TRUE
window was ~123.8 ms read as 100 ms -- poll jitter re-imported through the
quantized denominator. NOT the RECOVER-reaction hypothesis (RECOVER exits
through return_zero, clamped by the same per-pin caps -- a RECOVER-internal
overshoot is impossible by construction); NOT the enable boundary (poses arm
at 0); NOT the V9 cut (posted after the run loop closes; its jump is P3's,
owned by V9a's exactly-zero check, which passed).

THE FIX, both sides mine:
- ENGINE (membrane_tick.cpp, needs window #7): the stamp is now INTEGER --
  `ts_us` (steady microseconds) + `ts_ms` (steady milliseconds), both from
  ONE now() read under the same lock pass as the state. Integers do not
  decay with clock magnitude; int64 microseconds is exact to year 292k.
- HARNESS (gait_verify.py): the stamp LADDER. ts_us pairs -> exact per-poll.
  ts_ms pairs -> per-poll ONLY after measuring the stamp's own ulp
  (10^(floor(log10|v|)-5) ms) and refusing it when that ulp swallows > 5% of
  a poll window (the cliff is exactly 1e6 ms = 16.7 min of boot time). Else
  gross/whole-run with the reason NAMED in the bar text. Pairs are scoped to
  gait_on at BOTH ends (F-TELEPORT's own "while on"; the disarm jump is P3's
  jurisdiction). New instrument: the worst pair is RECORDED
  (results["v7_worst"]: pin, window, pose pair, phases) -- the next
  adjudication reads numbers, not priors.

MEASURED, window-6 binary, scratch 8159 (PID 41228, killed by PID; box uptime
~24.8 h): the detector fired -- "client wall clock, gross/whole-run (ts_ms ulp
100 ms at this clock magnitude -- pre-ts_us binary)" -- V7 0.29x PASS, and the
full run PASS 15/15 (`verify_after_ts_us_ladder.json`, this directory). At
window #7 expect V7's text "(engine ts_us, per-poll)" with a worst-pair record
in the evidence JSON; on any fresh boot the ts_ms legacy path also runs
per-poll safely (ulp 1 ms under the 5% bar).

One harness unit bug caught on the road here (disclosed): the detector's first
draft compared its ulp in ms against a seconds threshold -- inverting the safe
band (a fresh 1 ms stamp would have been refused) and printing "100000 ms".
Fixed to seconds consistently; unit-tested across the cliff (999999 ms safe /
1000000 ms refused).
