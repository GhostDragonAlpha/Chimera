# U02 integration notes — for U07 (measure during actual play) and W10 (walking in the scene)

Author: M-U02. Date: 2026-09-24. Module:
`tools/monkey_campaign/product/follow_camera.py` (stdlib-only). Tests:
`tools/monkey_campaign/product/follow_camera_tests.py` (24/24 green,
`receipts/test_run.txt`; latency record `receipts/latency_run.json`).
Contract citations: `discovery_note.md` (re-verified at HEAD `8550b634`).

## 1. Minimum live wiring (no new machinery needed)

```python
from tools.monkey_campaign.product.follow_camera import (
    FollowCamera, EngineRigProvider, Cylinder, RecordingClient)
from tools.product_viewer.server import EngineClient      # existing client

engine = RecordingClient(EngineClient("http://127.0.0.1:PORT"))
provider = EngineRigProvider(engine)            # anchor = rig envelope center
fcam = FollowCamera(engine, provider,
                    obstacles=[Cylinder(cx, cz, r, top), ...],   # declared model
                    tick_period=0.05, tau=0.30)
fcam.bind()
while playing:                                  # a 20 Hz loop thread
    rep = fcam.tick()          # one POST /camera max, all 8 fields, pan=0
# off the tick path:
fcam.verify_apply()            # POST /project cam echo vs last command (FG)
engine.allowlist_violations()  # must stay [] for the whole session (FA)
```

The client only needs `get(path)` / `post_json(path, payload)` with the
EngineClient signatures — RecordingClient wraps it and IS the invariant
evidence (keep its `log` for the session receipt).

## 2. For U07 (C12 + C23 measurement during actual play)

- **Anchor source upgrade**: the current lineage exposes no root-motion route
  (discovery note §3/§6). When the walker state is served (P02P03 pinned the
  walker lineage; U01 landed the `CommandRecord v1` input seam with
  `yaw_rate` still unrouted), replace `EngineRigProvider` with a
  `CallableAnchorProvider(fn)` returning `(world_point, heading_or_None)`.
  Heading `(hx, hz)` engages the derived behind-the-animal law
  (`theta_des = atan2(-hx, hz)`); without it the azimuth holds — measured as
  designed.
- **Latency chain** (already instrumented per tick in `TickReport`):
  `t_state → t_anchor → t_solution → t_acked`; presentation =
  `(first GET /frame whose capture armed >= t_acked) − t_state` (the G8
  freshness contract makes "bytes postdate the command" checkable; the
  headless harness proved the protocol against the mock — receipts). Report
  the tick setpoint (50 ms) SEPARATELY from measured latencies (C12's own
  warning). Compare against P06 limits once P06 freezes them; the frozen
  budgets used here (50 ms Python chain, 200 ms presentation with the
  engine's F2 law) are TEST budgets, not product limits.
- **Feel vs numbers** are separate acceptance fields (U07's row): re-derive
  `tau` (default 0.30 s) and the deadbands ONLY from human-acceptance runs;
  they are constructor parameters, frozen defaults, not laws of nature.
- **Session receipt**: keep `RecordingClient.log` — the never-moves-the-animal
  invariant (`allowlist_violations() == []`, `forbidden_hits() == []`, pan 0
  on every write) should be asserted over the WHOLE play session, not just
  the unit scenarios.

## 3. For W10 (walking in the actual scene)

- Obstacles: feed the REAL geometry — F03's trunk (the designation law takes
  cylinders with r >= 0.25 m) and F07's obstacles when placed
  (`Cylinder(cx, cz, r, top)`, base on y=0). F02's terrain query
  (`tools/monkey_campaign/data/monkey_clearing/terrain_query.py`) can derive
  per-obstacle `top` from the heightfield. The module does NOT discover
  obstacles; an unmodeled obstacle can still occlude (declared limitation).
- The module issues ONLY `GET /joints`, `GET /scene`, `POST /camera` on the
  tick path — stride/hinge packs (`/hinge_bin`, `/stride_bin`, `/stride`) and
  the U01 command seam are never touched; camera activity cannot disturb
  walking by construction (engine-side receipt: main.cpp:4190-4204, camera
  writes never reach `load_membrane`).
- Camera-side rate: the deadbands keep idle ticks commandless (the observer
  must not starve the observed); avoidance responses may move radius/phi in
  one tick — expected, and bounded by the pull-in floor (`R >= R_ground`),
  the elevation cap (67.5 deg), and the orbit sweep (±90 deg).
- If the playable pin exposes a root position via a new route, wire it
  through `CallableAnchorProvider` and re-run the suite: the speed clamp
  (camera <= 2x measured animal speed) and the cut policy (snap only on
  teleport-scale jumps) are already proven against anchor streams.
