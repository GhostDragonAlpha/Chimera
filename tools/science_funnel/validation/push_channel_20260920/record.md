# PREREGISTRATION — THE PUSH CHANNEL (lane/push-channel-20260920)

Banked at d0a2ff28 (the thin-client pilot's landed tip), BEFORE any push-channel
code was written. The pilot's own receipt named the one measured blocker this
lane fixes: **E2 — POLL-ONLY TRANSPORT**. The measured facts this lane fixes:

- The engine serves ~15 ms/request on ONE HTTP worker: a poll client's snapshot
  costs 2 engine pulls (/verts + /tick_state), so ONE client at 60 Hz demands
  ~120 pulls/s from an engine that serves ~66/s — measured consequence: R04
  collapsed to 17.64 Hz achieved. Engine load also SCALES WITH CLIENT COUNT
  under polling (N clients x rate x 2 pulls) — multi-client 30 Hz is
  arithmetically impossible on poll (4 x 30 x 2 = 240 pulls/s).
- Under transport stalls the client rendered torn ALL-ZERO frames: F2's
  transient MAD 13.33 (median 0.0 everywhere). Mechanism banked: "a rare
  page-side edge case (torn/empty work buffer at sample time)".
- The engine's worker wedges on half-open connections (no recv deadline) —
  ENGINE-side, recorded (below), and the SAME failure class must not be
  rebuilt Python-side: this lane's server needs recv/send deadlines of its own.

## THE TRANSPORT DERIVATION (before any build; each constraint measured, not tasted)

The channel must carry BINARY payloads (36 B/vert state frames; JPEG pixels)
at a per-client steady cadence WITHOUT request-per-frame, to MULTIPLE
concurrent clients, from the existing stdlib `ThreadingHTTPServer`, through
the lane's chunk-preserving TCP trace proxy.

- **C1 — binary budget**: the pilot's winning pixel family (jpg w1280 q85)
  measured 1.0 MB/s at 30 Hz. SSE's text/event-stream envelope carries base64:
  1.0 x 4/3 = **1.33 MB/s > the 1.25 MB/s budget** — the envelope ALONE
  falsifies SSE for the winning pixel family before anything else is measured.
  (State family would fit: FULL36 0.34 -> 0.46 MB/s base64 — but the transport
  must serve both families.)
- **C2 — stdlib server**: the slice server is `BaseHTTPRequestHandler`-shaped.
  WebSocket has NO stdlib server; hand-rolling RFC 6455 (handshake, masking,
  fragmentation, close) re-creates the exact framing-bug class the pilot
  MEASURED in its DELTA transport ("DELTA transport framing bug found+fixed").
- **C3 — cadence without request-per-frame**: both SSE and WS satisfy this in
  architecture; the differentiator is C1/C2.
- **C4 — proxy/host**: the trace proxy is a plain TCP forwarder; any HTTP body
  streams through it unchanged. The host's browser stack requires Playwright's
  BUNDLED chromium (MACHINE_FINDINGS.md) — a client-side constraint only.

**CHOSEN: the SSE architecture over a binary HTTP body.** One long-lived
`GET /api/stream` whose response NEVER ends: `Content-Type:
application/octet-stream`, server-paced length-prefixed records — the SSE
shape (push events on one GET) without the text envelope (C1) and without a
frame protocol rewrite (C2). Zero payload inflation; HTTP-native (no upgrade,
curl-able, proxy-transparent); reconnect = the client re-GETs (EventSource's
auto-reconnect semantics, ~6 lines, since the browser's EventSource cannot
carry binary). Per-record framing IS the integrity instrument:

```
record  = u32 payload_len | u16 type | u16 flags | u32 seq | u64 ts_us | payload
type    = 1 SNAPSHOT (payload byte-identical to /api/snapshot: THS1 hdr+verts)
          2 PIXEL    (payload = engine /frame bytes as served: JPEG/PNG)
          3 HEARTBEAT (payload = u64 server monotonic us; 1 Hz on idle)
flags   = bit0 keyframe
seq     = per-connection monotonic; a skip = dropped frame, counted, never hidden
```

Server architecture (the E2 fix, stated so it can be falsified): ONE
broadcaster thread per stream PROFILE (fmt, rate, pixel params) composes ONE
snapshot per tick — engine pulls scale with PROFILES, not clients — and each
client connection thread copies from its own latest-wins mailbox (a slow or
stalled client overwrites frames instead of queueing: graceful degradation is
structural, never a bounded-queue flood). Every client write runs under a
socket send timeout; a client that stops reading is dropped at the deadline,
not allowed to wedge its thread forever. HEARTBEAT records keep idle links
observed at 1 Hz.

**E3 boundary: DELTA is NOT offered on the stream.** The engine's C3 chain is
single-client by design (route-local cache, one chain) — a push broadcaster
fanning one chain to many clients would corrupt it. Recorded, not worked
around silently; the stream serves the stateless family (FULL36/POS12/POS16/
Z12) + PIXEL.

## RULE 0 — THE MEMBRANE

**STATEMENT.** A Python-side push transport (the slice server composes and
pushes; clients hold one long-lived GET) serves MULTI-client timestamped
snapshots at the declared rates within the per-client bandwidth budget, keeps
engine load independent of client count, and KILLS the torn-frame class —
no client ever renders an all-zero or partial frame; a bad frame is held as
the visibly-labeled last good frame.

**BUDGETS (inherited from the pilot, same numbers):**
- BUDGET-BW: per-client wire <= 1.25 MB/s (1,250,000 B/s decimal) at the
  declared rate, wire truth measured client-side AND server-side, framing and
  HTTP overhead reported separately, never hidden.
- BUDGET-VIS: MAD <= 2.0 (0-255) vs the 60 Hz twin truth at the same render
  point — now on MEDIAN *and* MAX over valid rows (the pilot recorded a FAIL
  on max; this lane's bar is that the class is GONE, not merely rare).
- BUDGET-RT: p95 rAF delta <= 16.7 ms.

**PREDICTIONS (pre-named, not yet measured):**
- P1 (multi-client rate): 30 Hz holds to 4 concurrent clients, each >= 28.5 Hz
  achieved (0.95 x declared) on TRACE-CLEAN, because composition is per-PROFILE:
  engine pulls/s measured via the channel's own counters must be EQUAL (within
  noise) at 1 and 4 clients — the property poll arithmetic cannot have.
- P2 (60 Hz honest): predicted FAIL for the state family: one composed snapshot
  costs 2 engine pulls at ~15 ms each, capping composition near ~33 Hz < the
  57 Hz bar. Measured pass-or-fail; if it passes, the ~15 ms/request model was
  wrong for this composition and the receipt names the corrected mechanism.
  NOTHING is tuned to rescue this row (no pull-skipping, no state-caching).
- P3 (torn class dead): the F2 rerun on the same FALL scene through the SAME
  metric shows max MAD <= 2.0 on every valid row (pilot max: 13.33). The guard
  (magic + declared-length + n>0 + seq) rejects bad frames; the client HOLDS
  the last good frame with a visible HELD label. If any valid row shows an
  all-zero rendered sample, F2 fires against this lane too.
- P4 (wedge): a client that stops reading mid-stream does NOT move any other
  client's achieved rate below 0.95 x declared in the post-wedge window, causes
  no other-client delivery gap > 200 ms, and is dropped by the server within
  5 s (send timeout). An abruptly-killed client (RST) is dropped within one
  heartbeat cycle (<= 2 s). Measured with real sockets, not mocked alone.
- P5 (bandwidth): per-client wire at 30 Hz predicted: Z12 ~0.04 MB/s,
  POS12 ~0.12 MB/s, FULL36 ~0.36 MB/s (pilot payload numbers + 20 B/record
  framing), pixel jpg w1280 q85 at 30 Hz pixel cadence ~1.0 MB/s — all within
  BUDGET-BW; the pixel row has the least headroom and is measured honestly.

**FALSIFIERS (named before the run; all may fire honestly):**
- **F1 RATE-FAIL**: any valid row (see validity below) with achieved_hz
  < 0.95 x declared, client-side, on TRACE-CLEAN. Reported per client id,
  fmt, rate, client-count. The 60 Hz rows are EXPECTED candidates (P2) — if
  they fail, they fail WITH numbers and the lane does not hide them.
- **F2 TORN-FAIL**: any all-zero/partial frame RENDERED by the push client
  (runtime evidence: a sampled rendered frame that is all-zero while a good
  frame was available to hold), or any valid row with MAD > 2.0 (median OR max).
- **F3 WEDGE-FAIL**: a stopped-reading or killed client moves any other
  client's achieved rate below 0.95 x declared post-wedge, or causes any
  other-client delivery gap > 200 ms, or survives unwedged on the server past
  its named deadline (5 s stopped-reader / 2 s killed).
- **F4 BW-FAIL**: any valid row with per-client wire > 1.25 MB/s.
- **F5 DET-FAIL**: the raster metric non-deterministic on identical bytes
  (double-run), or any browser console error on the push client page during
  a measured run.

**Row validity** (declared before the runs, the pilot's pattern): a row is
VALID if its window completed with the client connected >= 90% of the window
on TRACE-CLEAN; environment storms invalidate a row only with the reason
written next to it. No row is deleted; invalid rows stay with reasons.

## THE MEASUREMENT MATRIX (pre-named minimum set)

- Bandwidth/rate matrix (harness stream clients, TRACE-CLEAN, 20 s windows):
  - 30 Hz x clients {1, 2, 4} x fmt {Z12, POS12, FULL36}
  - 60 Hz x clients {1} x fmt {Z12, POS12, FULL36} (P2's honest rows)
  - 30 Hz x clients {1, 4}: pixel stream jpg w=1280 q=85 (state Z12 rides the
    same stream at 30 Hz; pixel cadence 30 Hz; the pilot's 1.0 MB/s number
    re-measured through the push wire)
  - per client: achieved_hz (records/s), wire B/s (received), frame-size
    median/p95, seq gaps; per profile server-side: composed Hz, engine pulls/s
- Wedge test (F3): 3 harness clients at 30 Hz Z12; at t=5 s client W stops
  reading (socket open, reads nothing); at t=10 s client K is killed (RST);
  window to t=20 s. Verdicts: others' post-wedge rate, max others' gap,
  server drop times for W and K (from the channel's own counters).
- F2/F4 browser runs (bundled chromium; Machine findings honored):
  FALL @30 Hz FULL36, FALL @30 Hz Z12, CARRY @30 Hz FULL36 — each with the
  twin-engine truth recorder; page dumps sampled rendered frames + rAF log;
  offline numpy raster (the pilot's instrument) computes MAD vs twin truth;
  frame-time p95 from the rAF log; console errors collected via Playwright.
- F5: raster double-run on identical bytes; console-error count must be 0.

## ENGINE-SERVICE GAPS (recorded — engine untouched, the frozen core)

- **E1 — NO IN-BAND TIMESTAMP** (engine /verts, /frame): UNCHANGED by this
  lane. The push composes ts the same way /api/snapshot does (verts pull then
  state pull; gap_us rides every THS1 header). Engine-side fix (a ts_us field
  in the legacy framing) remains named, out of this lane's boundary.
- **E2 — POLL-ONLY TRANSPORT**: this lane's subject. The PYTHON side gains a
  push channel; the ENGINE remains pull-only behind it (the slice server's
  broadcaster is the engine's ONE well-behaved poller per profile). E2 is
  closed at the service boundary this lane owns and NOWHERE else; the engine
  itself still has no native push — recorded honestly as a residual.
- **E3 — NO MULTI-CLIENT SNAPSHOT CHAIN**: UNCHANGED (engine-side). The push
  channel respects it by NOT offering DELTA (above); a per-connection chain
  would require engine work. Status: recorded.

## SCOPE / BOUNDARIES

No engine or ChimeraEngine/ edits; no gait_controller.hpp; port 8127 never
touched; no 4090; the shared desktop never touched (boot_slice.py stubs the
browser pop; browser work is Playwright BUNDLED chromium only, per
MACHINE_FINDINGS.md). NO edits to tools/playable_slice/index.html (the
rendertruth lane owns the page) — the push client is a NEW page
(tools/thin_client_pilot/push_client.html) served by a new route. slice_server.py
gains ADDITIVE routes + one import; every existing route byte-unchanged.
New harness lives in tools/thin_client_pilot/ (push_* prefixed) reusing the
pilot's trace_proxy / raster / truth_recorder / boot_slice as-is. Engine
binary: the pilot's prebuilt chimera_engine.exe (thincli worktree .tmp,
provenance + byte-equivalence recorded in thin_client_pilot_20260920/) is
reused unchanged; any misbehavior reboots from this worktree's source instead.
PowerShell-only for .ps1 (-File, never inline -Command with $); long runs as
background processes with redirected logs; no block-waiting.
