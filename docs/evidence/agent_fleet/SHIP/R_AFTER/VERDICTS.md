# R_AFTER — the three after-run verdicts (agent R-after "window-verifier", 2026-09-14)

Binary under test (provenance for every verdict below):
`.tmp/build_tick/Release/chimera_engine.exe`
sha256 `a62c6b467f1a860cad96faae9da47fd5e56553076aaa04b10454de73d137238e`
(the lead's rebuild: sealed-cell degenerate guard + two-phase capture readback).

Isolation: live 8107 read-only throughout (GET only; still PID 43248 at the
end, never posted to, never /frame'd). Each protocol ran on a scratch engine
on its private port (8139 / 8140 / 8141) in an isolated cwd, one at a time,
each killed BY PID (netstat-sourced or harness-tracked). Headless only.
All scratch ports confirmed freed after each run.

---

## RUN 1 — GAIT FALSIFIER (R4 protocol, scratch 8139 + session snapshot): **FAIL**

Harness: `tools/gait_verify.py --base http://127.0.0.1:8139` (console:
`run1_gait_console.txt`; raw bars: `gait_verify_result.json`).

| Bar | Result | Measured |
|---|---|---|
| V0 body live | PASS | has_scene=True sealed=True feetCell=0 (yhi=0.338) n_cells=4, conserve −0.000117% |
| V1a gravity arms | PASS | gravity_on=True after POST (compact JSON) |
| **V1b contact = m·g ± 0.5%** | **FAIL** | settled=True with worst \|root_vy\| **0.00e+00**; g_contact_n **0 N** vs m·g 135,618 N (dev 100.000%) |
| V1c rest P = 0 | PASS | max P 0.00e+00 Pa |
| V2 stance arms | PASS | kp=3.531 → \|S\| ≈ 0.283 m/rad (prereg match) |
| **V3a gait arms** | **FAIL** | gait_on=False, feetCell=−1 — set_gait refused (gravity rung dead downstream of V1b) |
| V4–V10 | NOT REACHED | the run aborts after V3 |

V0–V10 summary: V0 ✓ V1a ✓ **V1b ✗** V1c ✓ V2 ✓ **V3a ✗**, V4–V10 unexercised.
Exit 0 was NOT earned (harness printed `VERDICT: FAIL`).

Root-cause evidence (all recorded, nothing fixed, per mission):
- Scratch engine log (`run1_gait/engine_run1.log`): boot restore answers
  `"ok":false,"replayed":7,"failed":60` — after `mesh_bin/joints/classify/
  vertbind:ok` and exactly THREE `seal:ok`, a wall of 57+ `seal:FAIL`.
  Boot restore ran three cycles (initial + retries); each cycle the fail
  count grew **60 → 63 → 66** and re-saved `tick_seal_history +1` ×3.
- The seal history (`run1_gait/tick_seal_history_after_amplification.log`,
  69 lines) is ~20 repeats of the same three seal heights
  (`{"y":3.415}`, `{"y":1.903,"cell":0}`, `{"y":0.338,"cell":0}`) —
  redundant re-seals the OLD binary re-applied silently and the NEW GUARD
  now refuses on replay. State carries `seal_refusal: "degenerate_split"`.
- The restored 4-cell body is INERT: gravity flag on, contact exactly 0 N,
  root_vy exactly 0.0 for the whole settle window (perfectly frozen, not
  oscillating), all cell pressures 0. The gait enable's gravity rung then
  refuses → V3a. **The walking was never exercised; this is not a verdict
  on the gait machine.**
- DISCRIMINATOR PROBE (`run1_gait/gravity_probe_fresh_body.json` + `.py`):
  same binary, fresh-classified blob via the H15 bring-alive path (NO
  session restore), gravity armed compact → the body FALLS (root_vy up to
  11.38 m/s, root_y 1.99 and dropping) and contact force is LIVE (sampled
  135,618 N mid-fall/impact; probe window closed before settle — the
  discriminator is motion vs frozen, and it is unambiguous). **Gravity
  works on this binary; the run-1 failure is restore-state-specific.**

## RUN 2 — ALIVENESS GALLERY (H15 protocol, throwaways on 8140): **PASS 5/5 ALIVE**

Driver: `docs/evidence/agent_fleet/SHIP/H15_GALLERY/h15_gallery.py --port
8140` (console: `run2_gallery_console.txt`; artifacts:
`run2_gallery/gallery_results_20260914_092945.json` + 5 portraits).
Exit code 0. Guard-string scan: **CLEAN** (zero degenerate/refus/guard
strings on any shape on any endpoint).

| creature | verts | tris | cells | V_whole | cons% | loops | dimple m | joint → maxdisp | 10 kN dP Pa | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| blob     | 1,986 | 3,968 | 2 | 8.33391 | 0.000 | 1 | 0.198944 | j1 → 0.1562 | +13,136,100 | ALIVE |
| torus    | 2,048 | 4,096 | 2 | 7.34284 | 0.000 | **2** | 0.198944 | j2 → 0.0958 | +2,249,130 | ALIVE |
| capsule  | 1,346 | 2,688 | 2 | 1.69175 | 0.000 | 1 | 0.198944 | j0 → 0.1031 | +2,371,300 | ALIVE |
| peanut   | 1,986 | 3,968 | 2 | 0.90617 | 0.000 | 1 | 0.198944 | j1 → 0.0860 | +30,212,600 | ALIVE |
| rbox     | 1,986 | 3,968 | 2 | 8.47347 | 0.000 | 1 | 0.198944 | j0 → 0.1632 | +36,092,500 | ALIVE |

Every pinned channel matches the baseline table bit-for-bit (same joint
routing, same displacements, same dimple, torus loops=2). **Both sentinels
(torus, capsule) sealed `ok:true` — the degenerate guard did NOT refuse any
legitimate 50% daughter. NO guard regression.** (Note: the sentinels were
exercised on the FRESH-seal path, which is exactly where the gallery runs;
the guard's refusal behavior did surface — on the RESTORE replay path, see
Run 1 / classification.)

## RUN 3 — R6 BENCH (H14 protocol, own scratch on 8141): **PASS 4/4 — beat or match baseline 4/4**

Harness: `python tools/game_shell/bench.py --scratch --report
bench_after_build.md` (console: `run3_bench_console.txt`). Exit 0. The
report header carries the exe sha256 and `scene snapshot replayed: True`.
Engine killed by PID by the harness.

| scenario | 1% low this run (t/s) | pre-build baseline | delta | 60 t/s bar | verdict |
|---|---:|---:|---:|---|---|
| IDLE | 299.22 | 298.99 | +0.08% | clear | PASS, above baseline |
| GAME_PAGE_LOAD | 299.04 | 298.44 | +0.20% | clear | PASS, above baseline |
| FRAME_THUMBNAIL | 140.72 | 134.14 | **+4.90%** | clear | PASS, ABOVE baseline |
| TOUCH_STORM | 298.99 | 298.42 | +0.19% | clear | PASS, above baseline |

- **FRAME_THUMBNAIL moved UP** (+4.9%) — the capture-readback win is real
  even with the known stall still in flight.
- **IDLE / TOUCH_STORM did NOT regress** → no measurable gait-machine tick
  cost on the no-frame scenarios (the mission's judge-these-two rule).
- KNOWN-DEFECT CAVEAT (recorded, not guessed): the in-flight /frame stall
  is visible in FRAME_THUMBNAIL's raw 250 ms footnote — per-interval rates
  swing min 0.00 → max 764 t/s (the ~950 ms stall + catch-up signature).
  The 5 s bucket metric absorbs it; the scenario still beat baseline. The
  other three scenarios pull no frames and show clean ~299 t/s throughout.

---

## CLASSIFICATION — known in-flight defect vs NEW defect (the deliverable)

**The known /frame stall is NOT the cause of any failure today.** It shows
up only as the FRAME_THUMBNAIL raw-sample burst signature; that scenario
still finished +4.9% ABOVE baseline, and the two scenarios that judge the
gait machine question (IDLE, TOUCH_STORM — zero frame pulls) are at full
rate, above baseline.

**NEW DEFECT (blocking Run 1): boot-restore of the session snapshot vs the
degenerate-split guard, with two observable faces.**
1. *Guard refuses the recorded seal history on replay.* The snapshot's
   `tick_seal_history.log` holds ~60+ entries, mostly redundant re-seals at
   three already-sealed heights — re-applied silently by the pre-guard
   binary, REFUSED by the new guard (`seal:FAIL` ×60-66, restore answers
   `ok:false`, state `seal_refusal: "degenerate_split"`). The 4-cell geometry
   itself still restores (first 3 entries apply; V0 passes), but…
2. *The restored body is inert under gravity.* Gravity flag arms, contact
   stays exactly 0 N and root_vy exactly 0.0 (frozen solid), so the gait
   enable's gravity rung refuses (V3a) and the falsifier dies before the
   machine can be judged. Same binary on a fresh-classified body engages
   gravity normally (probe) — restore-state-specific, not binary-wide.
3. *Amplification sub-defect:* each boot-restore cycle re-appends the 3
   replayed seals to the history (measured 60 → 63 → 66 fails over three
   cycles) — the restore/save loop grows the very file it cannot replay.

**LIVE-WORLD IMPLICATION (flag, do not panic):** the live 8107 (same binary,
relaunched by the lead through the same snapshot) carries the same
`seal_refusal: "degenerate_split"` marker in `/tick_state` (read-only GET).
Its gravity was OFF at check time (co-tenant drift is documented), so live
gravity engagement is UNTESTED — if the restored-live body is inert the same
way run 1's scratch was, arming gravity on live will do nothing. I armed
nothing on live. Recommend the engine owner verifies gravity on a scratch
restored from the same snapshot before trusting the live fall, and makes
boot restore idempotent (skip already-satisfied seals; stop re-appending
replayed seals). THEN re-run the R4 falsifier — the gait machine itself
remains untested, not exonerated.

Per Rule 0: the R4 prereg's prediction ("every logged transition replays
against its own measured gate values; cut-mid-swing produces the measured
abort") was NOT tested — the run legitimately died at V3a, and that death,
with its evidence chain, is the recorded result. Nothing was fixed; every
log is in this directory.

## EVIDENCE INDEX

- `PROVENANCE.md` — binary sha256 + isolation rules + run index
- `run1_gait_console.txt`, `gait_verify_result.json` — Run 1 harness output
- `run1_gait/engine_run1.log` — boot-restore seal:FAIL wall, 3 cycles
- `run1_gait/tick_seal_history_after_amplification.log` — the refused history
- `run1_gait/tick_state_boot.json` — restored state (seal_refusal present)
- `run1_gait/gravity_probe_fresh_body.json` / `.py` — the discriminator probe
- `run2_gallery_console.txt`, `run2_gallery/` — Run 2 artifacts (5 portraits + JSON)
- `run3_bench_console.txt`, `bench_after_build.md` — Run 3 harness output
