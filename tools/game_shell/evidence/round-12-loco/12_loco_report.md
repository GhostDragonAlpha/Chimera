# Round 12 — Locomotion R&D spike (Tiel, chimera-worker)

Date: 2026-10-11. Tree: HEAD `16097866` + the uncommitted working tree (no
commits made by me). Engine built from this tree into
`E:/PythonChimera/.tmp/loco-engine/Release/chimera_engine.exe` (MSBuild,
exit 0, re-verified at teardown). All numbers below come from MY runs in
this session; the loco-bank engine edits were inherited from the earlier
interrupted dispatch of this same assignment and are re-verified by my own
build, my own :8119 runs, and my own no-flag refusal test (disclosed in §F).

Scratch port: 8119 only. Ports 8110/8210/8117 untouched. Every process I
started is dead (teardown evidence §G).

Evidence directory: `E:/PythonChimera/tools/game_shell/evidence/round-12-loco/`

---

## A. Actuation map (what exists today)

### A.1 Joint hierarchy and DOFs

- Binding format `JNT3_hierarchical`: 28 joints, 18,459 vertices, per-vertex
  primary + secondary LBS owners with parents (`joint_binding.hpp:50,61,83-84`;
  parse of pivots/axes/limits `joint_binding.hpp:81-82`). Asset:
  `Saved/meshes/monkey_birth.bin` + `monkey_joints.bin`, pinned in
  `tools/creature_graph/data/creature_graph.json`; scene compile + load in
  `tools/science_funnel/creature_scene.py:12-73` (scene declares
  `"model":"JNT3_hierarchical","actuation":"kinematic"` line 45).
- Full joint table dumped to `joint_table.txt` (28 names, pivots, axes,
  admitted limits).
- The only joint state is `joint_deg_` — 28 angles. It is a POSE channel:
  every writer computes an angle and `apply_travel`/`pose_binding` turns it
  into per-vertex geometry (`membrane_tick.cpp:390-420`; JNT3 path
  `pose_binding` at `membrane_tick.cpp:392-395`). No joint-level force or
  inertia exists in the body: nothing integrates torque into `joint_deg_`
  except the tendon drive, which integrates internally and writes the
  result as a pose.
- Anatomical pin atlas: HIP 13/14, KNEE 15/16 (`membrane_tick.hpp:560-561`),
  ANKLE 17/18 (`membrane_tick.hpp:548`).
- Root DOF: exactly one — `root_y_, root_vy_` (`membrane_tick.hpp:536`).
  `/tick_state` exposes only `root_y`, `root_vy`, `g_contact_n`
  (`membrane_tick.cpp:5035-5037`). There is no root_x/root_z and no
  rotation; the render root is `set_sim_root(0.f, root_y, 0.f)`
  (`main.cpp:4540`). My probe confirms: `root_keys=["root_vy","root_y"]`,
  `xz_fields=[]` (`probe_ground_contact.json`, step `root_dof_fields`).

### A.2 THE FALL — the movement law (`membrane_tick.cpp:870-903`)

`y'' = -g + F_contact/m`, one rigid Y DOF. Penalty contact read ONLY at the
body's lowest vertex against floor y=0:
`F = k_ground*depth + c_ground*max(0,-vy)` (`membrane_tick.cpp:887`), capped
at `50*m*g` (`:888`). Constants: `mass_kg_=13824.5` (`membrane_tick.hpp:533`),
`k_ground_=1.3562e7 N/m` (= mg/0.01, `:534`), `c_ground_=6.062e5 N·s/m`
(`:535`), `G_EARTH=9.81` (`membrane_tick.cpp:71`). Semi-implicit integration
`:895-897`, root clamped ±3 m (`:899-900`), uniform Y translation of all
verts applied LAST (`:901-902`) so no volume/pressure leak.

Measured (my probe, `probe_ground_contact.json` / `...2.json`):
- Settled rest: `root_y=0.00950712 m` (the derived 1 cm sink),
  `g_contact_n=135,618 N` = m·g exactly, `root_vy≈-1e-8`.
- **Ungated dashpot**: the `c_ground*max(0,-vy)` term at `:887` is applied
  regardless of depth. Measured: body at `root_y` 2.60→1.81 m (airborne)
  descends at constant `root_vy=-0.223719 m/s` with `g_contact_n` pinned at
  135,618 N — the terminal velocity `m·g/c_ground = 0.2237 m/s` at any
  altitude. Any bounce/step dynamics are masked by this until fixed.

### A.3 Tendon drive — the only force-level actuator

Module `ChimeraEngine/engine/tendon_drive.hpp` (laws A7/A8/A5/A1):
- A7 muscle: `F = a·Fmax + F_passive`, `Fmax=150 N` (`:45`), fL=fV=1.
- A8 tendon: tension-only spring `F=(EA/L0t)·max(0,L−L0t)`, `EA=2000`
  (`:37`), `L0t=0.09` (`:41`); sever falsifier zeroes F and tau in one step.
- A5 capsule: `tau = −k(q−theta_rest)`, `k_capsule=2.0` (`:57`),
  `theta_rest=0` (`:60`); ROM stops `rom_lo=−2.29`, `rom_hi=2.56 rad`
  (`:63,:66`).
- Dynamics: `I·qdd = tau_muscle·r + tau_capsule + tau_ext`, `I=0.02` (`:23`),
  `r=0.03` (`:27`), semi-implicit Euler at `dt_internal=1/300 s` (`:84`).
- A1 ledger: battery drain = work + heat + dE booked exactly per substep,
  `battery_J0=1000` (`:79`), `heat_rate=2.0` (`:75`).
- All parameters are declared synthetic monkey-scale in the header comments.
  Max actuation torque = r·Fmax = **4.5 N·m**.

Wiring: `/tick_effort` (`main.cpp:1259`) → `tendon_effort()`
(`membrane_tick.cpp:1149-1163`): single pin ownership `tendon_pin_=15`
(knee_L, `membrane_tick.hpp:390`; refusal `:1151`), `u<0` disarms
(`:1153-1157`), arm re-inits the drive (`:1159`). Tick block
`membrane_tick.cpp:850-859`: `tendon_drive_step` then
`joint_deg_[tendon_pin_] = q` — the drive OWNS the pin; `/tick_pose` on an
owned pin is refused (my probe: `pose_refusal_owned_pin ok:false`).
Per-frame ledger guard tol 1e-6 J (`membrane_tick.cpp:1121-1147`); my run:
max err 2.7e-12 J, 0 violations (`engine_8119_stderr.txt`).
`/tick_sever` → `tendon_sever()` (`membrane_tick.cpp:1165-1169`).

Unit tests of the real module re-run by me (5/5 PASS,
`tendon_drive_test_head.txt`): LEDGER 2.5e-12 J, SEVER, STALL, REST,
MONOTONIC.

### A.4 Ground interaction and stance/gait rungs

- Ground: THE FALL only (§A.2). Single lowest vertex; no per-foot contact
  sets; no tangential force; no friction.
- F1 stance servo (ankle lean integral): hook `membrane_tick.cpp:799-814`,
  `set_stance` refuses on JNT3: `if (body_active() && on) return false;`
  (`membrane_tick.cpp:3571-3572`). Route `main.cpp:1588-1594` (on parsed as
  literal substring `"on":true`, `:1590`).
- G1 gait checkpoint machine (STANCE→LIFT→REACH→LOAD, measured gates): hook
  `membrane_tick.cpp:838`, `set_gait` refuses on JNT3 identically
  (`membrane_tick.cpp:3712-3713`). Route `main.cpp:1581-1587` (substring
  parse `:1584`). My probe with the correct compact payload: both refuse,
  `stance_on/gait_on` stay false (`probe_ground_contact2.json`,
  `stance_gait_jnt3`).
- Reflex/touch pathway: `/tick_touch` (`main.cpp:1507`) →
  `touch_press`/`touch_press_at` (`membrane_tick.cpp:1442/1432`) →
  `reflex_detect_locked_` (`:776,:4675`) → `reflex_compose_locked_`
  (`:821,:4867`) which WRITES BOTH ANKLE PINS (`:4881-4882`). This is a
  second pose-writer contending for leg pins (last-write-wins, see the
  ownership comment `membrane_tick.cpp:845-849`).

### A.5 What is MISSING for walking (explicit)

1. No horizontal root DOF: no root_x/root_z, no velocity, no state field,
   no integration (`membrane_tick.hpp:536`, `membrane_tick.cpp:895-902`,
   `main.cpp:4540`). Limb forces can only bob the body vertically.
2. No tangential contact force (no friction): `:887` is purely normal.
3. Contact is the single lowest vertex — only one foot can ever load; the
   gait machine's measured foot vertex sets (`gait_foot_verts_`,
   `membrane_tick.cpp:301-302`) are measurement-only.
4. F1 stance and G1 gait both refuse on JNT3 (`:3572`, `:3713`) — their
   derived gains belong to the legacy independent-pin travel law.
5. One shipped drive (pin 15). Legs need ≥6 (pins 13–18). The multi-drive
   bank exists but is scratch-gated (§F) and LOCO_MAX=4 (`hpp:414`).
6. Actuator/mass scale mismatch: 4.5 N·m max muscle torque vs a 13,824.5 kg
   body (a knee supporting half the body at ~1 m lever needs ~68 kN·m —
   ~15,000× more). The only channel by which muscles move the body today is
   pose→penetration→stiff-ground-spring, which converts cm of penetration
   into multiples of body weight (measured §D).
7. Dashpot not depth-gated (`:887`): terminal fall 0.2237 m/s at any
   altitude; contact transients are unobservable.
8. No attitude DOF (no pitch/roll): the body cannot tip, cannot balance;
   the support polygon is not enforced anywhere.

---

## B. Candidate architectures (≥3)

### Arch 1 — Per-limb tendon drives + CPG-like coupled phase oscillators

u_i(t) for pins 13–18 from coupled oscillators (the engine already contains
a phase-oscillator network concept for the legacy particle world:
`gait_controller.hpp`, `/gait_bin`). Drive law unchanged (A7/A8/A5/A1).
- Engine changes: promote the loco bank to a game feature (drop the
  `--loco-spike` gate, `main.cpp:657-663`), LOCO_MAX 4→8
  (`membrane_tick.hpp:414`), add a `/loco_cpg` route (pattern:
  `/loco_script` `main.cpp:1293-1305`) or run the CPG in the game layer.
- Physical plausibility: the drive is a single agonist (extension is
  capsule recoil, not muscle) — a 6-drive CPG needs antagonistic pairs or
  pose-assisted extension. Fatal issue: with no X/Z root DOF, alternating
  torques cannot produce horizontal reaction force on the single-Y root;
  they only modulate normal contact. Measured: grounded anti-phase bank
  LAUNCHED the body (+8.79 m/s, §D) instead of translating it.
- Cost: LOW-MED (bank exists, ledger guard exists). Risk: HIGH — no
  propulsion channel; launch instability from the stiff ground spring.

### Arch 2 — Kinematic `/tick_pose` swing + tendon stance lock

Swing leg follows a scripted/rate-limited pose trajectory; stance leg holds
a tendon drive at high u (capsule + ROM stiffness ≈ joint lock). This is
exactly the shape of G1 (measured gates + pose actuation), so the rung is:
port F1/G1 to JNT3 — re-derive their gains for `pose_binding` travel (the
derivations at `membrane_tick.cpp:3568-3570, 3709-3711` are explicitly
"this engine's own arithmetic" for the legacy law; the 1°/20° derivation
probes assume independent-pin travel arithmetic).
- Engine changes: HIGH — re-derive stance/gait laws for JNT3, plus pin
  ownership arbitration with reflex compose (`:4881-4882`).
- Physical plausibility: pose is an infinite-impedance kinematic channel —
  energetically free, outside the A1 ledger. Acceptable only if declared a
  "neural kinematic assist", not muscle. Still no X/Z DOF → stepping in
  place.
- Cost: HIGH. Risk: HIGH (re-derivation touches sealed F1/G1 laws).

### Arch 3 — Hybrid: root XZ DOF + tangential contact + Arch-1 drive

Extend THE FALL to three translational DOFs with a Coulomb-bounded
tangential force at the contact vertex:
`F_t = −min(μ·F_n, k_t·Δx + c_t·v_t)` opposing slip. Stance drive stiffens
the planted leg (Arch 2's lock, no kinematic swing), swing is drive+capsule
(Arch 1). The body becomes a point-mass + sliding-contact model: feet
cannot tip it (no attitude DOF), friction translates it — crude, but real
horizontal locomotion with the tendon drive as the sole force source (A1
ledger intact; the contact law is a new pre-registration item).
- Engine changes: MEDIUM — one block (`membrane_tick.cpp:870-903`), state
  fields (`hpp:536`), `state_json` (`:5035-5037`), `set_sim_root`
  (`main.cpp:4540`), bank promotion (§F). Default-OFF flag-gated.
- Physical plausibility: standard simplified locomotion model; consistent
  with A7/A8/A5/A5 unchanged. The scale mismatch (§A.5.6) still dominates
  and must be reconciled (pre-reg decision).
- Cost: MEDIUM. Risk: MEDIUM — contact-vertex switching between feet gives
  force spikes; control stability without attitude needs the friction cone
  to do all the "balancing".

---

## C. Offline prototype (deliverable C) — DONE

`E:/PythonChimera/tools/loco_proto/loco_proto.cpp` — standalone C++17,
instantiates **3 real `chimera::tendon::TendonDrive` units** (knee_L,
knee_R, hip_L) from the shipped header, anti-phase controller
`u_i(t)=0.05+0.90·0.5·(1+sin(2π·1.2·t+i·π))`, 10 s at dt=1/240 s.
Build: `g++ -std=c++17 -O2 -I ChimeraEngine/engine
tools/loco_proto/loco_proto.cpp -o .tmp/loco_proto.exe`. Full output:
`loco_proto_output.txt`. Results (my run):

- LEDGER per unit (tol 1e-6 J): knee_L max 5.002e-12 J, knee_R 4.206e-12 J,
  hip_L 1.471e-12 J — 0 violations. Drains 280.7/274.1/259.5 J booked as
  work+heat+dE.
- Alternating trajectories: knee_L q ∈ [−35.7°, +147.0°], knee_R
  [−37.4°, +147.0°] (ROM-clamped), torques 0→4.153 N·m (r·Fmax ceiling);
  corr(q_kneeL, q_kneeR) = **−0.9409** (anti-phase confirmed).
- Crude stance/swing body-displacement estimate (DECLARED SYNTHETIC strut
  model, L=0.35 m, no-slip planted foot — NOT engine geometry): knee arcs
  9.26 m / 8.87 m over 24 half-cycles → mean advance ≈0.378 m per
  half-cycle ≈ **0.91 m/s** at 1.2 Hz. Assumptions printed in the output.
  This is an order-of-magnitude feasibility figure, not an engine result.

---

## D. Ground-contact verdict (deliverable D)

### VERDICT: **NEEDS_ENGINE_WORK**

Ground contact exists and is stable under gravity, but it cannot support
walking: there is no horizontal force channel at all, the contact set is a
single vertex, the balance/gait rungs refuse on this body, and the measured
response to limb actuation is a body launch, not a step. Numbers (my runs,
:8119, creature loaded via `creature_scene.py` path):

1. Stable normal contact at rest (`probe_ground_contact.json`):
   `root_y 0→0.00950712 m`, `g_contact_n 0→135,618 N` (= m·g),
   `root_vy −1.2e-8`. Contact law works for standing.
2. No propulsion channel: `/tick_state` root fields are `root_y, root_vy`
   only; `xz_fields=[]`. `set_sim_root(0, y, 0)` (`main.cpp:4540`) hardcodes
   x=z=0. Nothing in the tick integrates a horizontal force.
3. Dashpot ungated (`membrane_tick.cpp:887`): airborne body at
   root_y 2.60→1.81 m falls at constant `root_vy=−0.223719 m/s` with
   `g_contact_n` constant 135,618 N — matches `m·g/c_ground=0.2237 m/s`.
   Contact transients cannot be observed at any altitude.
4. Pose→contact coupling is a launcher, not a stepper
   (`probe_ground_contact.json` pose_probe): flexion `knee_L=−60°` while
   grounded changed nothing (`root_y` 0.00950712, `g_contact` 135,618 flat
   for 2 s, `probe_ground_contact2.json` launch_event); returning
   `knee_L=0°` drove the lowest vertex below the floor and jumped
   `root_y 0.0095→2.98554 m` between samples.
5. Grounded multi-drive bank (3 drives pins 15/16/13, scripted anti-phase
   1.2 Hz, u∈[0.05,0.95], from settled rest,
   `probe_ground_contact2.json` bank_grounded): at t=0
   `g_contact_n=455,377 N = 3.36×mg` (penetration ≈3.4 cm on the k_ground
   spring), then `root_vy=+8.79 m/s` at t=100 ms, `root_y` ≥2.92 m,
   `g_contact_n→0` (airborne). The body is launched, not walked. Ledger
   stayed honest throughout: loco bank max err 1.876e-12 J, 0 violations
   (`engine_8119_stderr.txt`).
6. Balance/gait rungs unavailable on this body (compact payloads,
   `probe_ground_contact2.json`): `/tick_stance` →
   `refused: the body must be classified and a support band must exist`;
   `/tick_gait` → `refused: needs gravity, stance, classification, pins
   13-18, and a sealed feet cell`; both flags stay false. Code:
   `membrane_tick.cpp:3572, 3713`.

Why not GROUND_CONTACT_USABLE: items 2–5 — no horizontal DOF/force, single
vertex, launcher response, unobservable transients. Why not merely
INSUFFICIENT: the gaps are missing engine mechanisms (root DOF, tangential
force, JNT3 stance/gait), i.e. engine work, not tuning.

---

## E. Recommendation (deliverable E)

**Adopt Arch 3 (hybrid root-XZ DOF + friction + promoted tendon bank),
staged.** It is the only candidate that creates a propulsion channel while
keeping the tendon drive as the sole force source and the A1 ledger intact;
Arch 1 without it is provably a vertical bobber (measured §D.5), Arch 2
re-derives sealed laws for a kinematic channel and still cannot translate.

Stages and concrete engine changes (file:line granularity):

- Stage 0 (pre-reg, behavior change): depth-gate the dashpot —
  `membrane_tick.cpp:887` `c_ground_*max(0,−vy)` → apply only when
  `depth>0`. Until then every contact transient is masked (§D.3). This
  changes shipped behavior → needs lead pre-registration, not a silent fix.
- Stage 1: root XZ DOF + tangential contact, default-OFF flag
  (`--loco-root` or `/tick_loco_root`):
  - `membrane_tick.hpp:536` — add `root_x_, root_z_, root_vx_, root_vz_`
    (+ contact-vertex x/z anchor for the spring term).
  - `membrane_tick.cpp:880-903` — track lowest vertex x/z; add
    `F_t = −min(μ·F_n, k_t·Δx + c_t·v_t)`; integrate x/z beside y; extend
    the uniform translation at `:901-902` to x/z.
  - `membrane_tick.cpp:5035-5037` — emit `root_x/z/vx/vz`, `F_tangent_n`.
  - `main.cpp:4540` — `set_sim_root(root_x_, root_y_, root_z_)`.
- Stage 2: promote the loco bank to a game feature: drop the argv gate
  (`main.cpp:657-663`), `LOCO_MAX` 4→8 (`membrane_tick.hpp:414`) to cover
  pins 13–18; per-instance ledger guard already in place. Lead's call on
  making it shippable.
- Stage 3: CPG controller as an engine route `/loco_cpg` (pattern
  `main.cpp:1293-1305`) for determinism; game-layer HTTP per-frame
  `/loco_arm` is the fallback.
- Stage 4: scale reconciliation (pre-reg decision, not mine): either the
  creature mass (`membrane_tick.hpp:533`) or the drive scale
  (`tendon_drive.hpp:23-84`) must move; today max torque 4.5 N·m vs ~68
  kN·m needed at the knee, and the k_ground spring converts cm of
  penetration into multiples of body weight (§D.5).
- Stage 5 (later): port F1/G1 to JNT3 for measured checkpoint gait; promote
  `gait_foot_verts_` to per-foot contact sets; attitude DOF only if
  tipping/balance becomes a goal.

Top risks:
1. Scale mismatch dominates everything: any pre-reconciliation walking
   controller sees launches (measured 455,377 N spike, +8.79 m/s).
2. Single-vertex contact switching between feet = discontinuous force;
   expect spikes until per-foot contact sets exist.
3. Ungated dashpot (Stage 0) must land first or measurements stay
   meaningless.
4. Pin-ownership contention: pose, reflex compose (`:4881-4882`), stance,
   gait and N drives all write `joint_deg_` (last-write-wins,
   `membrane_tick.cpp:845-849`); arbitration must be explicit before 6
   drives ship.
5. No attitude DOF: "walking" is sliding; do not claim balance.

---

## F. Engine source edits disclosure

Loco-bank edits inherited from the earlier interrupted dispatch of THIS
assignment (same worker scope), re-verified by me (build + live runs +
no-flag refusal test). All additive + default-OFF:

- `ChimeraEngine/engine/membrane_tick.hpp:87-112` — loco bank API
  (`loco_allow_scratch`, `loco_arm/disarm`, `loco_script`,
  `loco_state_json`, ledger getters); `:414-415` — `LOCO_MAX=4`,
  `loco_[]` slots; scratch flag member.
- `ChimeraEngine/engine/membrane_tick.cpp:861-868` — tick hook
  (`if (loco_scratch_allowed_) loco_step_locked_(dt)`); `:1221-1330` —
  `loco_arm` (`:1221`), `loco_disarm` (`:1248`), `loco_script` (`:1251`),
  `loco_step_locked_` (`:1291`), `loco_state_json` (`:1322`).
- `ChimeraEngine/engine/main.cpp:657-663` — `--loco-spike` argv gate;
  `:1282-1307` — `/loco_arm`, `/loco_script`, `/loco_state` routes.

Zero-behavior-change verified live by me: engine launched WITHOUT the flag
on :8119 → `/loco_arm` returns
`{"ok":false,"error":"refused: loco scratch flag off, bad pin, or u outside [0,1]"}`,
`/loco_state` returns `loco_scratch:false`, `/loco_script` returns
`loco_scratch_flag_off` (`engine_8119_noflag_stdout.txt` + this report).
With the flag: bank armed pins 15/16/13, scripted anti-phase ran, per-frame
ledger guard held at ≤2.2e-12 J (`engine_8119_stderr.txt`).

Not mine, untouched: `ui.cpp` CHIMERA_GRID_DIAG removal, `engine.cpp` depth
LESS_OR_EQUAL fix. No commits, branches, stashes by me.

---

## G. Acceptance checks

1. Build from current tree succeeds — **PASS**. `cmake --build
   .tmp/loco-engine --config Release` exit 0 at teardown (incremental over
   the full build earlier this session); exe
   `.tmp/loco-engine/Release/chimera_engine.exe`.
2. Prototype compiles and runs, output in evidence — **PASS**.
   `tools/loco_proto/loco_proto.cpp` → `loco_proto_output.txt`, 0 failures,
   ledger ≤5.0e-12 J/unit (tol 1e-6).
3. Deliverable D backed by numbers — **PASS**.
   `probe_ground_contact.json`, `probe_ground_contact2.json`,
   `engine_8119_stderr.txt`; verdict NEEDS_ENGINE_WORK.
4. This report complete with file:line citations — **PASS**.
5. Nothing listening on 8119 at teardown — **PASS**. Both engines killed by
   PID (last: PID 94008); final `netstat` shows no LISTENING on 8119 (only
   TIME_WAIT residue, no process).
6. No new commits by me — **PASS**. `git log -1` = `16097866` (pre-existing
   HEAD); no git write operations performed.

Scope note: project-checks (physics/gameplay) were NOT run — this spike
made no behavior-affecting engine change beyond the default-OFF scratch
bank, and the acceptance list does not include them. The tendon-drive unit
suite (the module the spike reuses) was re-run directly: 5/5 PASS.

## Evidence files

- `joint_table.txt` — 28-joint atlas dump
- `loco_proto_output.txt` — prototype run (deliverable C)
- `tendon_drive_test_head.txt` — real drive module unit tests (5/5)
- `probe_ground_contact.py/.json` — probe 1 (settle, pose, drive, bank, root DOF fields)
- `probe_ground_contact2.py/.json` — probe 2 (stance/gait refusals, launch event, grounded bank launch)
- `engine_8119_stdout.txt`, `engine_8119_stderr.txt` — flagged engine session (ledger guards)
- `engine_8119_noflag_stdout.txt` — no-flag refusal witness
