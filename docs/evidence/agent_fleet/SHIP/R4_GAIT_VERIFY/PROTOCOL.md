# R4 GAIT VERIFY — the post-build protocol (agent H13 "gait-verify", fleet 2, 2026-09-14)

Verifies commit **20ecea08** (the G1 gait checkpoint machine,
`ChimeraEngine/engine/membrane_tick.cpp` / `.hpp`) against its prereg:
`docs/evidence/agent_fleet/MATTER_KERNEL/SEAL_PREREGISTRATION.md`,
section **"THE GAIT CHECKPOINT PREREGISTRATION"**, plus
`docs/THE_SHIP_GOAL.md` ("THE ROBOT STACK LAW", "THE MOVEMENT LAW").

The harness: **`tools/gait_verify.py`** — HTTP only, builds nothing, runs
nothing. Dry-run output (read-only, live 8107): `dryrun_8107.json` in
this directory.

---

## 1. DESK-CHECK — every prereg'd gate vs the landed code

Verdict legend: MEASURED = the gate reads a number the body reports this
tick; DERIVED = computed from measured channels at enable; WITNESS =
logged but explicitly not gating (the documented deviation).

| Prereg gate ("gated by a measured number") | Code location (membrane_tick.cpp) | Verdict |
|---|---|---|
| Rung-stack refusals at enable (gravity, stance, classification, pins 13-16, sealed feet cell) | 1467-1489 | MEASURED (state reads; refuses honestly) |
| Feet cell = the sealed cell with lowest `yhi` | 1482-1489 | MEASURED (seal-cell y-ranges) |
| Frozen per-side foot vertex sets (F1's 0.056-vs-0.283 self-cancel lesson) | 1496-1503; hpp 255-258 | MEASURED, frozen at enable from the rest blend |
| Support patch radius (RMS xz over the foot set); degenerate refuse < 1e-3 m | 1508-1519 | MEASURED |
| Rest lean reference (the tail is not "lean") | 1523-1528, 1603-1605 | MEASURED on the rest blend |
| Probe channels: SIGNED d(min y), d(centroid z) at +1 deg per pin; refuse channel < 1e-3 m/rad | 1530-1565 | MEASURED (the F1 probe precedent) |
| Rate caps: rate = (patch_r / tau) / \|arc channel\| — foot speed ≤ its own footprint per second | 1558-1567 | DERIVED from measured probes |
| LIFT combo nulls centroid-z drift: a_h = dcz_knee, a_k = −dcz_hip, ch = a_h·dminy_hip + a_k·dminy_knee; refuse \|ch\| < 1e-3 | 1570-1581 | DERIVED — **the documented deviation** ("null-z LIFT combo"), prereg DERIVATION + commit message |
| STANCE gates: other leg bearing (depth ≥ 0.8·sink), lean ≤ other patch, **WHAT-IF** (body centroid inside the would-be stance foot's patch) | 1741-1763 | MEASURED per tick (`gait_depth_[o]`, `lean`, `wx` vs `gait_patch_r_[o]`) |
| Schedule: the leg that stepped longer ago swings | 1764-1782 | DECISION, not a gate (prereg'd); blocker logged `schedule:turn` |
| LIFT: err = STANCE_BAND − world min-y; per-pin rate-bounded; **exit on wminy ≥ 0.05 m** | 1793-1832 | MEASURED (exit 1826) |
| LIFT support-lost abort (planted foot left the floor → other leg RECOVER, this leg LOAD) | 1797-1806 | MEASURED (`wminy[o] ≥ 0`) |
| REACH: knee holds clearance (measured kerr), hip zerr = stance centroid + own patch; **exit on fcz[s] − fcz[o] ≥ own patch** | 1834-1865 | MEASURED (exit 1860) |
| REACH touchdown abort (swing foot down mid-reach → RECOVER) | 1866-1873 | MEASURED (`wminy[s] < 0`) |
| LOAD/RECOVER: return-to-zero at measured caps; **exit on depth ≥ 0.8 × 0.01 m AND \|root_vy\| ≤ 1e-3** | 1876-1908 | MEASURED (exit 1883 / 1899) |
| Sealed-cell pressures at transitions | 1888-1891, 1902-1904 | **WITNESS ONLY** (`prelax` vs 50 kPa logged, NOT gating) — the documented deviation: F1's held ankle pitch keeps real pressure in leg cells between strides; depth+settle carry the transition |
| ACT: hip/knee pins 13-16 ONLY; ankles stay F1's (G1 block after the stance block) | 1913-1918; order at 659-691 | Verified (composition, not clobbering) |
| THE CUT: disarm logs `{"why":"cut", vy, dL, dR, knee, hip}` with the measured state; pins to exactly 0; legs to STANCE | `gait_off_locked_` 1430-1456 | MEASURED — this entry is P3/F-GLIDE's evidence |
| Disarm-hold if gravity/stance leave mid-run | 1644-1664 | MEASURED, logged once from a real hold |
| Bounded log: 16 entries (`GAIT_LOG_N`), every entry carries its gate values | 1416-1428; constant line 36 | Verified — exposed at `/tick_state` → `gait_log[]` |
| **NO TIMERS**: dt enters only via the clamped `dts` in the servo/rate caps; `ticks_` only stamps the log and the alternation memory | 1670, 1721-1737, 1813-1821 | Verified — no phase advances on elapsed time |

**Desk-check verdict: no gate is tasted, timed, or unwired.** Every
prereg'd transition gate reads a measured number, and the two deviations
from the posted plan (null-z LIFT combo; pressure as witness) are the
ones the commit message declares, both documented in the prereg itself.

### Desk-check findings (build-window items, none blocking the machine's law)

1. **ROUTE PARSE HAZARD** — `/tick_stance` and `/tick_gait` arm on the
   LITERAL substring `"on":true` (main.cpp 1285, 1292). A human curling
   `{"on": true}` (with a space) silently DISARMS; the route still
   answers `ok:true`. `/tick_gravity`'s parse (1300-1302) is
   space-tolerant. The harness posts compact JSON only. One-line lead fix
   if wanted; not a physics issue.
2. **200 "Not found"** — main.cpp 3341 answers ANY unknown route with
   HTTP 200 + body `Not found`. A 200 proves nothing by itself (the
   dry-run: `/health` does not exist and "200s"). Liveness = `/tick_state`
   parsing as JSON with `has_scene`. The harness body-classifies routes.
3. **SERVO SEMANTICS (disclosed, not a defect)** — `servo_dth` applies
   `err/(channel·tau)` per tick without dt scaling (deadbeat-exact at
   tau = 1); F1's stance servo scales its step by `dts`. The measured
   rate caps bound all travel, so convergence stays ~tau and stable; if
   F-STALL/P2 (cadence) misses, audit here FIRST (prereg gain-audit
   item 4).
4. **THE BINARY IS ALREADY BUILT** — the brief said "landed but
   uncompiled"; measured otherwise: the live 8107 exe
   (`.tmp/build_tick/Release/chimera_engine.exe`) was built 00:47:26,
   **50 seconds after** the 20ecea08 commit (00:46:36), and its
   `/tick_state` answers with the full gait field set (which exists only
   in that commit — the parent has zero matches). The routes landed even
   earlier (f1ac0b5f). The post-build run is therefore runnable NOW on a
   scratch port; nothing waits on a compile.
5. **SHARED-WORLD DRIFT** — on the live 8107, gravity was ON at first
   probe (g_contact_n = 135,618 N — m·g to the newton, the C2 fall bar
   visible live) and OFF minutes later (a co-tenant). The protocol runs
   on a SCRATCH port for this reason.

---

## 2. THE BARS — each derived, with the arithmetic

| Bar | Value | Derivation (source) |
|---|---|---|
| Mass | m = 13,824.5 kg | 13.824536 m³ sealed whole × 1000 kg/m³ (movement-law prereg DERIVATION; `mass_kg_` membrane_tick.cpp:227) |
| Weight | W = 135,618.3 N | m·g = 13,824.5 × 9.81 (movement-law prereg). Bar V1b/V10: \|g_contact_n − W\| ≤ 0.5%. Live-measured at rest: exactly 135,618 |
| Ground spring | k = 1.3562e7 N/m | k·s* = W at s* = 0.01 m → k = 135,618/0.01 (the 1-cm rest-sink bar). ω_n = √(k/m) = 31.32 rad/s, ζ = 0.7 → settle 0.18 s — the harness's 6 s settle window has ~30× headroom |
| Bearing (LOAD/RECOVER exit) | depth ≥ **0.008 m** | GAIT_BEARING_FRAC × GAIT_SINK_M = 0.8 × 0.01 (membrane_tick.cpp:30-31; prereg DERIVATION "bearing = depth ≥ 0.8 × the derived rest sink") |
| Swing depth in single support | < **0.002 m** | prereg P1: d_swing < 0.2 × sink |
| LIFT clearance | min-y ≥ **0.05 m** | STANCE_BAND_M (line 26; F1's sole + 5 cm band). Total rise from rest = sink + band = 0.01 + 0.05 = **0.06 m** (LIFT comment 1808-1811) |
| Settle | \|root_vy\| ≤ **1e-3 m/s** | GAIT_SETTLE_VY (line 32; the 0.1 mm press-cutoff scale) |
| Stride geometry | z ≥ **own patch radius** | REACH exit 1860; prereg: "the new footfall lands outside the old support patch — geometric necessity". Patches are MEASURED at enable (enable log entry `patchL/R`); the harness re-derives them from `/verts` (RMS xz radius, feet ≤ feet-cell yhi, split at x = 0) and demands ≤ 20% disagreement (V3b) |
| What-if envelope | body centroid inside the would-be stance foot's patch | STANCE gate 1752-1760; prereg rung 4. Every STANCE→LIFT entry must carry `whatif:true` (F-LIE) |
| Cadence | stride ≤ **10 τ = 10 s** (τ = 1 s) | F-STALL; P2 predicts ~8 τ. Read from the log's tick stamps |
| Pressure witness | ≤ **50 kPa**, logged not gating | GAIT_P_RELAX_PA (line 33; the repo's gentle-hand threshold, re-tuned to measurement per the R4 ledger) |
| Conservation | \|conserve_pct\| ≤ **0.01%** at every poll | P4; F1's S3 bar |
| The stumble | \|root_vy\| transient > 1e-3 m/s within 2 s of the cut | P3: "a root transient appears — the stumble number" |
| Teleport | commanded deg-rate ≤ measured caps × 1.10 | F-TELEPORT (coarse poll-grain version; caps from the enable entry `rateKL/KR/HL/HR`) |

---

## 3. THE POST-BUILD SEQUENCE (one script → the verdict)

```text
# 1. BOOT A SCRATCH (never the shared live world):
#    make a working dir with shaders/ + session_snapshot/ (copy both from
#    .tmp/build_tick/Release/, or any prior scratch), then from that dir:
#      E:\ChimeraWork\slot-01\.tmp\build_tick\Release\chimera_engine.exe 8139 --hidden
#    Boot restore replays mesh -> classify -> vertbind -> joints -> seals.
#    (If the scratch is EMPTY instead, the harness can import:
#     add --import-from <dir-containing-session_snapshot> -- it replays
#     the exact classify_run.py payload formats + the seal history.)

# 2. WAIT for the body (has_scene + sealed + feet cell):
curl -s http://127.0.0.1:8139/tick_state

# 3. RUN THE FALSIFIER (one command, ~2-3 min):
python tools/gait_verify.py --base http://127.0.0.1:8139 ^
       --json docs\evidence\agent_fleet\SHIP\R4_GAIT_VERIFY\gait_verify_result.json
```

The harness then arms gravity → stance → gait ITSELF (compact JSON —
see finding 1) and runs V0-V10. Expected gait_log lines while it runs:

```json
{"tick":T1,"leg":"OFF->STANCE","gates":{"why":"enable","patchL":...,"patchR":...,"homeL":...,"homeR":...,"chLiftL":...,"chLiftR":...,"dminyHL":...,"rateKL":...,"feetCell":0}}          <- enable: the frozen geometry
{"tick":T2,"leg":"L","from":"STANCE","to":"LIFT","gates":{...,"whatif":true,"patch":0.3..}}                    <- the what-if answered before acting
{"tick":T3,"leg":"L","from":"LIFT","to":"REACH","gates":{...,"miny":0.05..}}                                   <- measured clearance >= 0.05 m
{"tick":T4,"leg":"L","from":"REACH","to":"LOAD","gates":{...,"z":0.3..,"bar":0.3..}}                            <- stride z >= own patch
{"tick":T5,"leg":"L","from":"LOAD","to":"STANCE","gates":{...,"prelax":true,"stride":1}}                        <- depth >= 8 mm + settled; 50 kPa witness
{"tick":T6,"leg":"R","from":"LIFT","to":"STANCE","gates":{"why":"cut","vy":...,"dL":...,"dR":...,"knee":...,"hip":...}}  <- THE MEASURED ABORT (mid-swing cut)
```

(A RECOVER entry — `{"why":"support_lost"}` or `{"why":"touchdown"}` —
is also a PASS sight: the machine's own measured abort.)

### Pass/fail table (printed by the harness, exit 0 = PASS)

| Bar | PASS means | Source |
|---|---|---|
| V0 | sealed classified body with a feet cell (min yhi) | set_gait refusals 1467-1489 |
| V1a-c | gravity arms; settles; g_contact_n = m·g ± 0.5%; rest P exactly 0 | movement-law prereg F1/F2 |
| V2 | stance arms; kp = 1/(\|S\|·1 s), \|S\| ≈ 0.283 m/rad | stance prereg (audit reference) |
| V3a-b | gait arms; enable entry carries the frozen geometry; independent `/verts` patch audit ≤ 20% off | frozen-sets derivation |
| V4 | ≥ 3 strides; EVERY logged transition replays its own measured gate | P5 / F-LIE |
| V5 | swing < 2 mm; LOAD-exit depth in [8, 12] mm | P1 |
| V7 | commanded pose rate ≤ 1.10 × the measured caps | F-TELEPORT |
| V8 | \|conserve_pct\| ≤ 0.01 throughout | P4 |
| V9a-c | cut mid-swing → one poll: gait off, legs STANCE, pins 13-16 EXACTLY 0; the `why:"cut"` entry present; stride frozen; \|root_vy\| transient > 1e-3 | P3 / F-GLIDE / THE FALL LAW |
| V10 | settle back: contact = m·g, P exactly 0, ankles 0, root at baseline | S3 / F2 |

Any FAIL is a verdict, not an error: record it, and run the prereg's
gain audit in its stated order (logged gate values → enable channels vs
the /verts audit → rate caps → what-if envelope → the cut entry).

---

## 4. WHAT THE RUN NEEDS FROM THE WINDOW

1. A **scratch port booted with the session snapshot** (8139 default;
   `--base` overrides). The live 8107 stays read-only — the shared world
   drifts under co-tenants (measured: gravity flipped between probes).
2. **A quiet few minutes** — no other agent posting poses/touches to the
   scratch during the run (the machine composes over F1's ankles; a
   foreign `/tick_pose` on pins 13-18 would pollute the gates).
3. Nothing else. The routes are wired (f1ac0b5f), the machine is in the
   binary (finding 4), and the harness needs no build.

## EVIDENCE INDEX

- `tools/gait_verify.py` — the harness (this protocol, executable).
- `dryrun_8107.json` — the read-only dry-run against the live 8107:
  route inventory (with the 200-"Not found" fallback exposed), the
  /verts 36-B parse against the real payload, and the gait-field
  presence proving the G1 build is IN the live binary.
