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
