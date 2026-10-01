# WINDOW #8 — VERIFICATION PROCEDURE (C1 CREATURE ANSWERS)

The lead's window. The plumbing is committed desk-checked but UNCOMPILED;
this window builds it, runs the battery, and decides the policy flip
(default OFF until this passes). Everything here is already staged in the
repo — copy/paste, no authoring.

## 1. Build

```bat
cmake --build ChimeraEngine\engine\build --config Release
```

If it fails, DESKCHECK.md's "known compile-risk residue" lists the suspects
in order (route-lambda static array; the std::string chains in set_reflex;
nothing else expected).

## 2. Boot a scratch (never the shared live world)

Isolated cwd, snapshot copy, port 816x, headless, kill by PID (the
`.c1r_scratch` pattern: chimera_engine.exe + shaders/ + session_snapshot/
copies; live 8107 stays GET-only; no /frame pulls):

```bat
mkdir .w8_scratch && xcopy .c1r_scratch\chimera_engine.exe .w8_scratch\
xcopy .c1r_scratch\shaders .w8_scratch\shaders\ /e /i
xcopy .c1r_scratch\session_snapshot .w8_scratch\session_snapshot\ /e /i
cd .w8_scratch && chimera_engine.exe 8165 --hidden
```

Confirm the world: `GET /tick_state` — 4 sealed cells, torso (cell 1,
v0 12.509) present, `reflex_on:false` (B0).

## 3. The battery (BATTERY.md, in order B0..B10)

Compact JSON only. Route summary for copy/paste:

```
POST /tick_reflex {"on":true}
POST /tick_reflex {"breathing":false}              (suspend oscillator)
POST /tick_reflex {"pressure_coupling":false}      (THE NERVE CUT)
POST /tick_reflex {"on":false}                     (deterministic full off)
POST /tick_touch   {"hit":[-0.0004,5.112,-4.288],"force_n":20000}
POST /tick_touch_clear {}
POST /tick_gravity {"on":true}      POST /tick_stance {"on":true}
POST /tick_gait     {"on":true}     POST /tick_gait {"on":false}
```

Bars: B2 breath period ≈ 13.4 s with max|P| EXACTLY 0 and conserve at
noise; B3 suspend → /verts drift exactly 0; B4 20 kN → flinch env 1→0 in
≈ 2.5 s + visible foot flex; B5 10 kN → nothing; B6 nerve cut → identical
touch → nothing (THE negative control); B7 startle ≈ 2 deg bias inside the
5 deg cap; B8 walking + touches → envs stay 0, strides continue; B9 the
1 s quiet window after the cut; B10 gait 15/15 ARMED.

## 4. THE PRE-BUILT FALSIFIER (run it)

```bash
python tools/gait_verify.py --base http://127.0.0.1:8165 \
    --json docs/evidence/agent_fleet/SHIP/C1_CREATURE_ANSWERS/gait_verify_armed_window8.json
```

with reflexes ARMED (B1 ran; /tick_reflex is not touched by the harness).
All 15 bars must PASS. Control reference (current binary, reflexes absent):
`gait_verify_control_scratch8164.json` — 15/15. Any armed-vs-control
divergence names the reflex pass that leaked (the battery's reading table
maps each divergence to its cause).

## 5. Register + verdict

- Record the battery transcript + the armed gait_verify JSON in
  `docs/evidence/agent_fleet/SHIP/C1_CREATURE_ANSWERS/`.
- On PASS: the plumbing is verified; the constants stay AWAITING ASTRA
  (rate/amplitude, flinch threshold/amplitude, startle threshold/magnitude
  — PREREG §"the honest interim values"). The DEFAULT REMAINS OFF on boot;
  enabling in the live world is a separate lead decision (the gravity
  precedent: the lead flips policy only after the bars pass).
- On FAIL: kill the scratch by PID, revert nothing automatically — the
  reading table in BATTERY.md names which pass to audit first (breath
  pass-order leak / a fired negative control / a broken gate). The reflex
  code is entirely additive (`if (reflex_.armed)`) — reverting the three
  step() hooks restores the pre-window behavior without touching the rest.
- Kill the scratch by PID. Commit evidence. No push.

---

# WINDOW #9 ADDENDUM (post window-8: two bugs + one interaction, all closed)

Window-8 verdict was 80% alive: compile (after the lead's get_bool-duplicate
fix — folded into the window-9 commit), B0/B1 clean, B2 breathing VISIBLE
(pressures blind), B10's V0–V9 all PASS. Three defects, all now fixed in
code with the reproductions on the window-8 binary
(`repro_window8_bugs.json`):

1. **Flinch pins never resolved** — two layers: (a) the reader resolved only
   at arm time (arming before gait's first enable froze the refusal) — the
   pins are now ADOPTED LIVE every tick; (b) worse, any re-arm killed BOTH
   triggers permanently (the `prev_p_valid` reseed deadlock — the reseed
   was gated by the size check alone). Fixed; the trigger loop now survives
   arm/disarm cycles and adopts the gait machine's persisted resolution
   (measured: re-arm after gait adopts 17/18).
2. **V10 root-home failure** — NOT the breath and NOT the reflexes: the
   armed run's own state0 shows B7–B9 left the world LIVE (gait on, stance
   holding, root_vy −0.175) and the harness read the stance transient as
   its reference; the run's final_state is the exact home
   (+0.00950712, contact m·g, P 0, ankles 0). Proven by
   `gait_verify_armed_fresh_scratch8167.json`: fresh boot, reflexes armed,
   gait_verify first — **15/15 PASS**. My B10 sequencing doc was the bug;
   BATTERY.md now demands the quiet-rest prelude. The lead's hardening
   option B is ALSO taken: the breath pass moved after the FALL law's root
   read (the root home is breath-blind by construction).
3. **A bonus catch while reproducing**: the startle had fired once (tick
   3273) on the stance-arm transient — self-generated motion. The startle
   now requires the stance rung settled ≥ 1 s (corollary-discharge gate).

**WINDOW #9 runs**: the full BATTERY.md B0–B10 as amended (canonical field
names listed there; B1's pins may arrive late-by-design; B7 waits > 1 s
after arming stance; B10 needs the quiet-rest prelude or a fresh scratch)
+ `gait_verify.py` ARMED expecting **15/15** (the fresh-boot armed control
already passed on the window-8 binary). Same constraints: engine files
only, no build by the fleet agent, scratch-only verification, live 8107
GET-only and running this code DARK (default OFF).
