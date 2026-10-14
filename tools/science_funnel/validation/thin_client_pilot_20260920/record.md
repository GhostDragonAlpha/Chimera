# PREREGISTRATION — THE THIN-CLIENT CAMERA PILOT (lane/thin-client-pilot-20260920)

Banked at bd4bf630 (verified before worktree setup), BEFORE any thin-client code
was written. Astra round-5 Decision 2, camera-client clause: server-authoritative
sim with THIN CAMERA CLIENTS — timestamped snapshots -> interpolation -> local
camera/rendering; simulation, snapshot transmission, and rendering need not share
a frequency. Snapshot rate, deformation compression, visible-body count, and
interpolation measured TOGETHER. Teaching overlays synchronized to the
authoritative timestamps. The reported 50 ms corresponds to 15 physics ticks —
one policy period; RTT / one-way / jitter / tail qualified separately.

## THE SCENE (what exists today — the declared playable slice)

`tools/playable_slice/` at this commit: the slice server owns a free-port engine
(8127 refused by code), boots MOCK[mock_physics_body] (the bbox-derived stand-in
capsule, 314 verts / 624 tris) through the real `/mesh_import`, arms the real
root law, and the page streams `/api/verts` at a FIXED 10 Hz buffer-swap — no
timestamp, no interpolation. The motions that exist on this scene, all real:
LAUNCH (the gravity re-seat transient), DESCENT (terminal 0.2237 m/s, banked
constants), LANDING (the contact impact), CARRY (MOCK[mock_carry], the 0.4 m/s
XY slide), PRESS-RECOVERY (the tau dimple). These five phases ARE the
walk/playback material of this pilot; the gait skeleton is not importable here
(500k-tri cap, measured in the slice receipt) and is NOT claimed.

## THE ENGINE CONTRACT TODAY (measured from source before the build)

- `/verts` — `[u32 n][36 B/vert: pos3+normal3+color3 f32]`, serialized under the
  tick lock; `?delta=1` serves the C3 run-compressed chain framing
  `[0xD1][flags][rsvd][n][seq][runs]`, single-client, resync `?delta=key`.
  **NEITHER carries an authoritative timestamp in-band.** — ENGINE-SERVICE GAP
  E1 (recorded, not worked around silently; see E1 below).
- `/topology` — `[u32 tris][u32*3]`, one-time.
- `/tick_state` — JSON with the engine's OWN monotonic `ts_us`/`ts_ms`
  (steady clock, read under the same lock as the fields) + `ticks`, root_y,
  root_vy, cell pressures, dimple_m.
- `/frame` — pixel snapshot of the engine viewport: default full-res PNG;
  `?w=` box downscale; `?fmt=jpg&q=` WIC JPEG (F2 fast path). No timestamp
  in-band either (gap E1 applies to the pixel family).
- `/tick_touch` — the press (camera-ray form, force stated).

## RULE 0 — THE MEMBRANE

**STATEMENT.** A thin camera client on the EXISTING engine contract (no engine
edits; the slice server composes, the browser renders) — consuming timestamped
snapshots at a decoupled rate {60, 30, 15, 10} Hz and interpolating between them
at page framerate — sustains a visually faithful, timestamp-synchronized view of
the declared scene within these pre-named budgets:

- **BUDGET-BW** (bandwidth): compressed snapshot stream <= 1.25 MB/s (10 Mbps,
  home-uplink class; "Minecraft-class" connectivity) at the 30 Hz declared rate,
  while holding **BUDGET-VIS**. Derived from today's banked numbers, not taste:
  the web-kernel W4 record measured /verts at 664,528 B/pull (~2 MB/s at ~3 Hz,
  the 4-cell creature); the R6 bench measured the PNG-poll page at 105 MB/60 s
  (1.75 MB/s); the declared capsule derives 4 + 314*36 = 11,308 B/snapshot
  (339 KB/s at 30 Hz raw) — the budget binds the PIXEL family hard at every
  declared rate and binds the state family only at 60 Hz raw
  (11,308*60 = 678 KB/s ... with HTTP+framing overhead measured, not guessed).
- **BUDGET-VIS** (visual error): mean-absolute-difference <= 2.0 (on the 0-255
  scale) between the evaluated view and its reference — (a) compressed pixel
  formats vs the full-res PNG reference of the same instant; (b) interpolated
  client views vs the 60 Hz recorded truth at the same server render point.
  MAD 2/255 (~0.8%) is the standard "high-quality but lossy" band for smooth
  shaded renders; SSIM is reported secondarily, never as the gate.
- **BUDGET-RT** (client render): p95 requestAnimationFrame delta <= 16.7 ms
  (the 60 fps ordinary-machine bar, R6's own bar) on every network trace.

**PREDICTIONS (pre-named, not yet measured).**
- P1: JPEG q80 at w=960 cuts the full-res PNG's bytes by >= 2x while holding
  BUDGET-VIS against the PNG reference (the engine's PNG is stored-deflate over
  a smooth shaded viewport; JPEG at q80 on such content typically wins far more
  than 2x — 2x is the conservative floor).
- P2: 30 Hz snapshots + interpolation hold BUDGET-VIS on DESCENT and CARRY;
  15 Hz lands within 2x the 30 Hz error; 10 Hz (the declared minimum) holds or
  F2 fires; the worst phase at EVERY rate is LANDING (the contact impact is the
  scene's fastest motion — the swing-analog stress case).
- P3: interpolation keeps p95 frame <= 16.7 ms on every trace; the 200 ms tail
  stalls cause at most 2 playout underruns per 20 s run and the client recovers
  within 2 snapshot intervals (freeze on the older bracket, never extrapolate).
- P4: the engine's tick rate with a 60 Hz thin client subscribed stays in the
  R6 band (>= 295 ticks/s) — poll-servicing cost measured via the snapshot
  headers' own `ticks` field, because bandwidth is not the only server cost.

**FALSIFIERS (named before the run; all four may fire honestly).**
- **F1 BANDWIDTH-FAIL**: no measured format family holds BUDGET-VIS (MAD <= 2.0)
  while serving <= 1.25 MB/s at 30 Hz on the declared scene. The projection to
  the real creature (664,528 B/pull at 30 Hz = 19.9 MB/s raw; the reduction
  factor each surviving format achieves, measured on the declared scene, applied
  as a DERIVED statement) is recorded in the receipt — labeled DERIVED, never
  counted as a measurement.
- **F2 VISUAL-ERROR-FAIL**: the interpolated view at any declared rate exceeds
  MAD 2.0 vs the 60 Hz truth at that render point, on any phase — worst phase
  named with its number.
- **F3 SYNC-FAIL**: any teaching-overlay value rendered from a client clock when
  an authoritative snapshot timestamp was available. Enforced twice: (a) code
  review of the extended page — overlay VALUE code paths read the snapshot
  buffer only (client clocks may drive measurement instrumentation and playout
  arithmetic only); (b) a runtime test feeds the page canned snapshots with
  known ts and values and asserts the overlay displays those values bound to
  that ts.
- **F4 LATENCY-FAIL**: p95 client render frame time > 16.7 ms under the
  +50 ms one-way, ±20 ms jitter trace (F4's named trace; all traces reported).
- **F5 DETERMINISM-FAIL**: the offline metric path is non-deterministic — the
  same recorded bytes must yield the same MAD (bit-stable), and the replay
  renderer must produce the same pixel hash for the same inputs across two runs
  (network and scene timing vary; the METRIC must not).

## THE TRACES (named before the run)

1. TRACE-CLEAN — localhost, no added delay.
2. TRACE-50 — +50 ms one-way, each direction, deterministic per chunk.
3. TRACE-50J — +50 ms one-way with ±20 ms uniform jitter, drawn independently
   per chunk per direction.
4. TRACE-TAIL — TRACE-50J plus a 200 ms stall (the tail case) on one downstream
   chunk every 5 s.

The proxy is a lane-owned TCP forwarder (asyncio, chunk-preserving); the browser
client and the harness both go THROUGH it for trace runs. Never port 8127.

## THE INSTRUMENT (derived, so no step is a taste call)

1. **Snapshot transport** (slice server, lane code): `/api/snapshot` composes,
   per pull, engine `/verts` then engine `/tick_state`, returning ONE framed
   binary: `[u32 magic 'THS1'][u64 ts_us][u64 ticks][f32 root_y][f32 root_vy]
   [f32 P_lower][f32 P_upper][f32 dimple_m][u32 n][36 B * n]`. The ts postdates
   the verts by the inter-request gap delta — the ambiguity is MEASURED (its
   distribution reported; predicted sub-millisecond on localhost, i.e. <= 6% of
   one 60 Hz frame). Transforms behind `fmt=`: `full36` (today+ts),
   `pos12` (positions only; normals recomputed client-side from topology),
   `pos16` (f16 positions+normals, 12 B/vert), `z12` (zlib-9 of pos12),
   `delta` (the engine's own C3 chain, measured as-is).
2. **Interpolation** (page, extended from the existing viewer — no parallel UI):
   client maintains per-snapshot (server ts, client arrival); the playout clock
   is `r(t) = ts_latest + (t - arrival_latest) - D` with pre-named playout
   delay `D = 1.5 * snapshot_interval` (+ measured jitter headroom; named per
   run); the render point is bracketed by the two newest snapshots (older =
   snapA, newer = snapB); positions lerped per-vertex, alpha in SERVER time;
   normals and colors taken from snapB (lerped normals are measured as a
   non-gate ablation). Underrun freezes on snapA — never extrapolates.
3. **Truth** (harness): a 60 Hz `/api/snapshot` recorder runs alongside every
   client run — the ground truth at the client's own render points.
4. **Visual metric** (offline, scripted): for sampled render points, the client's
   interpolated buffer is recomputed offline from its recorded snapshot stream
   (same formula; unit-tested against the page's own math on canned pairs), the
   truth buffer is linearly interpolated at the same render point from the 60 Hz
   truth, and BOTH are drawn through the page's REAL WebGL program (same
   shaders, same camera) in a replay page; pixels read back; MAD + SSIM
   computed in numpy; side-by-side stills saved (worst sample + phase
   representatives). Camera fixed at the viewer default (yaw 0.7, pit 0.42,
   dist 2.2, target 0, 0.25, 0), viewport 960x540, for every measured run.
5. **Bandwidth** (harness): median + p95 payload bytes per snapshot per
   format x rate (n >= 50), plus wire bytes counted by the proxy for the live
   client runs. HTTP+framing overhead reported separately, never hidden.
6. **Perceived latency** (offline): a scripted press event; the truth stream's
   dimple_m crosses a threshold at ts_e (server clock); the client's rendered
   dimple crosses it at render point r_e; the event-visible latency is the wall
   time between them through the client's own offset estimate. Reported for
   every trace alongside the playout delay D (the designed latency).
7. **Frame time** (page instrumentation): per-rAF deltas logged client-side
   (client clocks drive INSTRUMENTATION — F3 governs overlay VALUES, not the
   stopwatch).

## ENGINE-SERVICE GAPS (recorded, engine untouched — the frozen core)

- **E1 — NO IN-BAND TIMESTAMP**: neither `/verts` (legacy or C3 delta framing)
  nor `/frame` carries the engine's authoritative `ts_us`. The thin client needs
  a paired `/tick_state` pull; the slice server composes it (`/api/snapshot`),
  and the pairing ambiguity is measured and bounded in the receipt. The named
  successor: extend the legacy framing with a `ts_us` field (engine-side work,
  out of this lane's boundary).
- **E2 — POLL-ONLY TRANSPORT**: the engine has no push channel (WS/SSE); every
  snapshot is an HTTP request. At 60 Hz this is measured (P4) but the successor
  shape (one push stream, many camera clients) is named, not built here.
- **E3 — NO MULTI-CLIENT SNAPSHOT CHAIN**: the C3 delta chain is single-client
  by design (route-local cache, one chain). A second camera would break it.
  The pilot's declared scope is one camera; E3 is recorded at the C3 site.

## SCOPE / BOUNDARIES

No C++ engine edits (HTTP contract only; gaps recorded above). No edits to
gait_* validation, first_skill_prestage_20260922/, master, shared tooling; port
8127 never touched; CPU-side work only (no 4090 contention). The lane extends
`tools/playable_slice/` (the existing viewer page + its server) and adds
`tools/thin_client_pilot/` (harness + proxy + replay + tests) and this
validation folder. Keyboard-first interaction: the extended page is fully
operable from the keyboard (orbit, zoom, press, rate, mode, slice actions).
The engine binary: the prebuilt `chimera_engine.exe` from the merged
playable-slice lane (e96eb943) is byte-equivalent for the chimera_engine target
— `git diff e96eb943 bd4bf630 -- ChimeraEngine/engine/` touches only
gait_controller.hpp (included by NO chimera_engine target file) and
tests_coupled_arm; provenance recorded here before use. If boot or any probed
route misbehaves, the engine is rebuilt from this worktree's source instead.
