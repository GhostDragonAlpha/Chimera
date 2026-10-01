# WINDOW #10 — BUILD + VERIFY PROCEDURE (ONE LIMB, physics half)

The lead's window. The ONE-LIMB code (limb partition, oblique cut core,
sensor patches, routes, snapshot wiring) is desk-checked but UNCOMPILED;
this window builds it, runs the partition + patch demo, and decides the
policy flips. Everything is copy/paste.

## 1. Build

```bat
cmake --build ChimeraEngine\engine\build --config Release
```

If it fails, DESKCHECK.md lists the suspects in order. Note: the seal()
body was REFACTORED — the cut/weld/publish core moved verbatim into
`MembraneTick::seal_cut_core_` (one winding law for horizontal AND
oblique walls). The Y path is algebraically identical (pd = py − y);
if ANY pre-existing seal behavior changes, the refactor diff is the
first suspect.

## 2. Boot a scratch (never the live world)

Isolated cwd, snapshot copy, port 817x, headless, kill BY PID ONLY
(identify the PID from `netstat -ano | findstr :817x` — NEVER kill by
image name: this lane's blanket taskkill took down the shared live 8107
on 2026-09-15; it was restored from its own snapshot in
.tmp/build_tick/Release, but the standing rule is now: PID only):

```bat
mkdir .an2_win_scratch
copy .tmp\build_tick\Release\chimera_engine.exe .an2_win_scratch\
xcopy .tmp\build_tick\Release\shaders .an2_win_scratch\shaders\ /e /i
xcopy .tmp\build_tick\Release\session_snapshot .an2_win_scratch\session_snapshot\ /e /i
cd .an2_win_scratch && chimera_engine.exe 8172 --hidden
```

Confirm: GET /tick_state — 4 sealed cells, reflex_on:false, P all 0.

## 3. The partition

```
POST /tick_limb {"side":"L"}
```

POST **ONCE** per fresh scratch. The idempotency check (a second POST)
is only valid AFTER a passing first POST ("limb":"already"): if the
first POST failed validation, the tree is ALREADY partitioned and a
second POST refuses at identification with the NOTE naming that state —
that refusal is not a grouping bug; re-boot the scratch to retry.
(The window-11 lesson: the second POST's refusal masked POST 1's real
validation failure for a full round.)

Expect `{"ok":true,"limb":"executed","report":{...}}` with:
- `chain`: hip 13, knee 15, ankle 17; adj_hip_knee 112, adj_knee_ankle
  100, adj_hip_ankle 0 (must match derivation_table.json — P1)
- `segments`: thigh_L / shin_L / foot_L, each `"closed":true`,
  positive v0, mass_kg entries
- `seed_agreement`: the measured saddle split (knee ~42% expected —
  REPORTED DATA, not a pass bar; see the PREREG addendum)
- `validation`: coverage_pct within ±0.01, mass_total_kg within 1.38 kg
  of 13,824.5, genus_before == genus_after, piece_book_unique true,
  `pass:true`

Then `GET /tick_state` — `n_cells:7`, `limb_done:true`, the
`limb_segs` + `patches` arrays populated. A second identical POST must
answer `"limb":"already"` (idempotent replay).

## 4. The patch demo (the local, delayed, disconnectable path)

```
POST /tick_patch {"on":true}
POST /tick_touch {"hit":[0.752394,1.466624,0.041854],"force_n":20000}
```

With reflexes armed (run the /tick_gravity → /tick_stance → /tick_gait
on→off resolution prelude + the 1 s quiet window first — the BATTERY.md
discipline): the shin_L patch fires after its `delay_s` (≈30–40 ms,
distance/70 m/s) ± 1 tick, and env_l rises; `patch_events` carries the
sensor row (patch id, cell id, tick, t_us, out_m). Then:

```
POST /tick_patch {"path":"shin_L","connected":false}
```

The identical touch: NO sensor delivery, NO flinch; the cell pressure
and dimple match (passive remains). Reconnect (`"connected":true`) —
no stale spike. Full script: `an2_demo.py` (works against the new
binary unchanged; it exercises the nerve-cut demo which must still
pass, proving the patch layer is purely additive when disarmed).

## 5. Persistence (acceptance 10)

- POST /session {"op":"restore"} on the same scratch: the partition and
  patch states come back from tick_limb_state.blob + tick_patch_state.blob
  (executed seals and partition answer "already"; failed == 0).
- Kill the scratch; reboot from the same snapshot dir: limb_done true,
  patches present (restored registry), patches DISARMED unless the blob
  said armed.
- A mesh swap must visibly stale the registry: /tick_limb_state refuses
  (the blob validation) — the staleness is a visible failure, not a
  silent reset.

## 6. Registers + verdict

- Record the partition report JSON and the demo transcript in
  docs/evidence/agent_fleet/SHIP/ONE_LIMB/.
- On PASS: the partition is a verified build; arming patches in the live
  world is a separate lead decision (the gravity/reflex precedent:
  default OFF on boot; the route is the operator's).
- On FAIL: kill the scratch BY PID; the reading table: (a) chain
  refusal ⇒ connectivity differs from the blobs (run derive_limb.py
  against the live snapshot); (b) closure/coverage failure ⇒ the merge
  or the core refactor (diff first); (c) patch silent when connected ⇒
  the delay-line clock (patch_step_locked_); (d) any seal behavior
  change ⇒ the seal_cut_core_ refactor diff. Reverting = drop the new
  routes from main.cpp + the step()/detect hooks; everything else is
  additive.

## 7. Cleanup

Kill the scratch BY PID. Live 8107: GET-only, untouched. No push.

---

# WINDOW #10 OUTCOME + WINDOW #11 ADDENDUM

**Window #10 verdict**: compile clean (seal refactor included); chain
derivation CORRECT (13→15→17, 112/100/0, pops 243/256/1477); the
in-code validation gate REFUSED the partition correctly — thigh_L
v0 = -nan (806 pieces, closed:true). The gate firing IS the honest-
failure path working; the NaN was Bug A below. The lead also fixed a
state_json defect live (the patch block emitted without its key —
invalid JSON that took the telemetry down) and set the standing JSON
law. Both fixes folded into the AN2 fix commit.

**Bug A — the NaN (fixed at the mechanism)**: the validation volumes
read the geometry cache built at route ENTRY; the oblique cuts append
wall slots to cut_src_ afterwards, so every wall slot indexed PAST the
end of the stale cutrest vector (operator[] does not bound-check) —
heap garbage as floats. Proof the geometry itself was sound: the LIVE
per-tick volumes of the same cells were finite (0.2725 / 0.1674 /
0.0104 m³, conserve −0.00011%). Fix: rest_geometry_locked_ re-run
after the cuts, before validation. LAW: a geometry cache is valid only
until the next cut mutates cut_src_.

**Bug B — multi-component bands (deeper, found in the same repro)**:
the bands are bilayer/multi-sheet (measured census in DESKCHECK.md) —
the old code merged ONE component per band and left stray sealed
shells. Fix: resolve_band groups ALL cells by containment in the
band's y-window, splits any multi-surface member, and the segment
merges ALL side components (per-component centroid-x sign).

**The JSON law (standing, encoded as jf())**: no float reaches JSON
unguarded — NaN/Inf serialize as null, never nan/-inf. Every float
emitter this lane added goes through it.

## Window #11 expectations (per this procedure, end to end)

1. POST /tick_limb {"side":"L"} → ok:true, limb:executed, pass:true:
   all three segments positive v0 (multi-sheet closed cells — chi may
   exceed 2 per cell, the SUM over sheets is what the report carries),
   mass_total_kg within 1.38 kg of 13,824.5, coverage_pct |<0.01|,
   genus before == after, piece_book_unique true, n_cells ≈
   4 + splits − merges + 2 cuts (report carries it).
2. Idempotency: second POST → "limb":"already".
3. GET /tick_state → VALID JSON (jf-guarded), limb_done true, the
   limb_segs + patches arrays keyed (`"patches":` — the lead's fix).
4. The patch demo + nerve-cut demo (an2_demo.py) green.
5. Persistence: restore → partition + patch states back, failed == 0.
6. Then the live-world limb build is the lead's policy call.
