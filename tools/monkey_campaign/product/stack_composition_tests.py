"""integrated_scenario.py -- R3's OWN integrated headless scenario.

Drives the STACK (X02 SessionFlow -> U03 FocusPolicy -> U01 InputMapper -> gate
-> sink) through: play -> hold key -> blur -> refocus -> pause -> resume ->
restart -> exit, plus the adversarial compositions. Asserts the cross-module
invariants. Everything is injected clocks + doubles; CPU-only, headless.

THE SHIM (declared review harness, NOT a fix): as committed, FocusPolicy lacks
`release_all`, so SessionFlow REJECTS it at construction (finding B1). The two
integration notes promise this composition works unchanged. To review the
STACK's SEMANTICS anyway, this harness adds the minimal 2-line passthrough in
the SUBCLASS ONLY -- no committed file is touched. A re-review after the real
fix should reproduce this file's numbers with `ComposedFocus` = FocusPolicy.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]  # adopted from R3's work/ copy (was parents[5] there)
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools" / "monkey_campaign" / "product"))

from tools.monkey_campaign.product.input_mapper import (  # noqa: E402
    InputMapper, MockSink, CommandRecord, V_MAX_IN_BAND_M_S, OMEGA_MAX_RAD_S,
    INTERVAL_MS, RELEASE_DECAY_MS, VALID_MS, SOURCE_ID)
from tools.monkey_campaign.product.focus_policy import FocusPolicy  # noqa: E402
from tools.monkey_campaign.product.session_flow import (  # noqa: E402
    SessionFlow, ATTRACT, PLAYING, PAUSED, EXITED)

FAILURES = []
CHECKS = [0]


def check(name, ok, detail=""):
    CHECKS[0] += 1
    tag = "PASS" if ok else "FAIL"
    if not ok:
        FAILURES.append((name, detail))
    print("  [%s] %s%s" % (tag, name, ("  -- " + str(detail)) if detail else ""))


# ── the shim ─────────────────────────────────────────────────────────────────
class ComposedFocus(FocusPolicy):
    """REVIEW-ONLY passthrough: the surface SessionFlow requires and
    FocusPolicy does not expose. Mirrors U03's own _release_everything body."""

    def release_all(self, now_ms):
        return self._mapper.release_all(int(now_ms))


class RecordingPolicy(ComposedFocus):
    """Logs every call the flow makes on the policy slot (for the
    [release_all, boot] ordering assert and the zero-calls-when-not-playing
    assert)."""

    def __init__(self, sink):
        super().__init__(sink)
        self.calls = []

    def _log(self, kind, now_ms):
        self.calls.append((kind, int(now_ms)))

    def press(self, name, now_ms):
        self._log("press", now_ms)
        return super().press(name, now_ms)

    def release(self, name, now_ms):
        self._log("release", now_ms)
        return super().release(name, now_ms)

    def mouse(self, dx_counts):
        self._log("mouse", dx_counts)
        return super().mouse(dx_counts)

    def tick(self, now_ms):
        self._log("tick", now_ms)
        return super().tick(now_ms)

    def release_all(self, now_ms):
        self._log("release_all", now_ms)
        return super().release_all(now_ms)


# ── the two consumer models (falsifier mining) ───────────────────────────────
class FaithfulConsumer:
    """The DECLARED consumer: honors U01's is_expired contract -- reverts to
    the seam's inert path when the held record ages past VALID_MS."""

    def __init__(self):
        self.records = []
        self._last = None

    def emit(self, r):
        self.records.append(r)
        self._last = r

    def demand_at(self, now_ms):
        if self._last is None:
            return None
        if InputMapper.is_expired(self._last, now_ms):
            self._last = None
            return None
        return self._last.v_forward


class NaiveHolder:
    """A ZOH consumer that NEVER applies expiry (holds the last record
    forever). What the stack looks like to it is falsifier-mining evidence."""

    def __init__(self):
        self.records = []
        self._last = None

    def emit(self, r):
        self.records.append(r)
        self._last = r

    def demand_at(self, now_ms):
        return None if self._last is None else self._last.v_forward


def bounds_violations(records):
    bad = []
    for r in records:
        if not isinstance(r, CommandRecord):
            bad.append(("type", r))
        elif r.source != SOURCE_ID:
            bad.append(("source", r.source))
        elif not (0.0 <= r.v_forward <= V_MAX_IN_BAND_M_S):
            bad.append(("v", r.v_forward))
        elif abs(r.yaw_rate) > OMEGA_MAX_RAD_S:
            bad.append(("yaw", r.yaw_rate))
    return bad


def run_spine(ScenarioLog):
    """S1: play -> hold -> blur -> refocus -> pause -> resume -> restart ->
    exit, with the cross-module invariant asserts."""
    print("S1 SPINE: play -> hold W -> blur -> refocus -> pause -> resume -> "
          "restart -> exit")
    sink = FaithfulConsumer()
    pol = RecordingPolicy(sink)
    world_log = []
    flow = SessionFlow(pol,
                       restart_scene=lambda: (world_log.append("boot"),
                                              {"booted": True})[1],
                       teardown=lambda: world_log.append("teardown"))
    recs = sink.records
    n_at = lambda: len(recs)  # noqa: E731

    # -- attract: nothing plays ------------------------------------------------
    for t in range(100, 301, 10):
        flow.tick(t)
    flow.key("W", 1, 200)          # gameplay key in attract: named drop
    check("S1 attract: zero records before play", n_at() == 0)
    check("S1 attract: gameplay key dropped (named)", flow.state == ATTRACT
          and any(d["kind"] == "key_press" for d in flow.last_trace["dropped"]))
    check("S1 attract: the policy slot received NOTHING",
          not any(c[0] in ("press", "mouse", "tick", "release_all")
                  for c in pol.calls), pol.calls)

    # -- play ------------------------------------------------------------------
    flow.key("Return", 1, 310)
    check("S1 Return starts play", flow.state == PLAYING)
    flow.key("W", 1, 320)
    t = 320
    while t <= 600:
        flow.tick(t)
        if t == 400:
            flow.mouse(50)         # a steer nudge mid-run
        t += 10
    v_hold = [r.v_forward for r in recs]
    check("S1 holding W emits bounded records at the 50 ms grid",
          len(v_hold) >= 5 and all(v == V_MAX_IN_BAND_M_S for v in v_hold),
          "%d records" % len(v_hold))
    check("S1 all records inside U01's frozen bounds",
          not bounds_violations(recs))
    check("S1 steer nudge carried (|yaw|>0 once)", any(abs(r.yaw_rate) > 0
          for r in recs))

    # -- blur (alt-tab) mid-run -------------------------------------------------
    blur_at = 610
    last_before_blur = n_at()
    flow.mouse(500)                # mouse during blur: dropped by policy
    pol.on_blur(blur_at)
    flow.key("W", 1, 700)          # physical typing while alt-tabbed
    t = 610
    post_blur = []
    while t <= 800:
        for r in flow.tick(t):
            post_blur.append((t, r.v_forward))
        t += 10
    check("S1 blur: decay runs to EXACT 0.0 then silence",
          any(v == 0.0 for _, v in post_blur)
          and post_blur[-1][1] == 0.0, post_blur)
    check("S1 blur: no v>0 later than blur+100 ms",
          all(v <= 0.0 or tt <= blur_at + RELEASE_DECAY_MS
              for tt, v in post_blur), post_blur)
    check("S1 blur: press while blurred DROPPED by name (policy layer)",
          "dropped_blurred" in pol.last_trace
          and ("W", 700) in pol.last_trace["dropped_blurred"],
          pol.last_trace.get("dropped_blurred"))
    check("S1 blur: no press reached the MAPPER (the policy held the gate)",
          not any(n == "W" and 610 <= ts < 800
                  for n, ts in pol._mapper.last_trace.get("pressed", [])))
    check("S1 blur: the mapper is key-free", len(pol.held) == 0)

    # -- refocus ----------------------------------------------------------------
    pol.on_focus(800)
    check("S1 refocus: clean re-arm (held empty)", len(pol.held) == 0)
    silence = n_at()
    t = 810
    while t <= 850:
        flow.tick(t)
        t += 10
    check("S1 refocus: still silent with no key (no tail resurrection)",
          n_at() == silence)

    # -- pause mid-run (the quiesce) ---------------------------------------------
    flow.key("W", 1, 860)
    t = 860
    while t <= 910:
        flow.tick(t)
        t += 10
    n_pre_pause = n_at()
    pre_pause_speed = recs[-1].v_forward
    check("S1 pre-pause demand live", pre_pause_speed == V_MAX_IN_BAND_M_S,
          pre_pause_speed)
    pol.calls.clear()
    pause_at = 920
    flow.key("Escape", 1, pause_at)
    check("S1 pause transition fired", flow.state == PAUSED)
    check("S1 quiesce: the flow's world contact is release_all-then-nothing",
          [c[0] for c in pol.calls] == ["release_all"], pol.calls)
    calls_at_pause = list(pol.calls)
    n_at_pause = n_at()
    paused_ticks = 0
    t = 930
    while t <= 1300:
        flow.tick(t)
        paused_ticks += 1
        flow.key("W", 1, t)        # mashing keys into the menu
        flow.mouse(30)
        t += 10
    check("S1 pause: ZERO records while paused (%d ticks)" % paused_ticks,
          n_at() == n_at_pause)
    check("S1 pause: the policy slot received NOTHING while suspended",
          pol.calls == calls_at_pause, pol.calls)
    check("S1 pause: menu mashing named-dropped by the FLOW (40+ drops)",
          len([d for d in flow.last_trace["dropped"]
               if d["kind"] in ("key_press", "mouse", "decision_tick")]) >= 100)

    # -- resume: the bounded tail -------------------------------------------------
    flow.key("Return", 1, 1310)
    check("S1 resume -> playing", flow.state == PLAYING)
    t = 1310
    tail = []
    while t <= 1500:
        got = flow.tick(t)
        tail.extend(got)
        t += 10
    vals = [r.v_forward for r in tail]
    check("S1 resume tail bounded <= 2 records", len(vals) <= 2, vals)
    check("S1 resume tail: every record <= pre-pause speed",
          all(v <= pre_pause_speed for v in vals), vals)
    check("S1 resume tail lands EXACTLY 0.0 then silence",
          vals and vals[-1] == 0.0 and all(v <= 0.0 for v in vals[1:]), vals)
    check("S1 after the tail: total silence, grid dissolved",
          n_at() == n_at_pause + len(vals))
    check("S1 faithful consumer: demand inert again 200 ms after resume",
          sink.demand_at(1510) is None, sink.demand_at(1510))

    # -- restart through pause ------------------------------------------------------
    flow.key("W", 1, 1510)
    t = 1510
    while t <= 1610:
        flow.tick(t)
        t += 10
    n_pre2 = n_at()
    flow.key("Escape", 1, 1620)
    check("S1 second pause", flow.state == PAUSED)
    boot_tick = 2000                  # well past the decay window
    flow.key("R", 1, boot_tick)
    check("S1 restart via pause: state playing again", flow.state == PLAYING)
    check("S1 restart: exactly ONE boot call", world_log == ["boot"], world_log)
    t = 2010
    post_boot = []
    while t <= 2200:
        post_boot.extend(flow.tick(t))
        t += 10
    check("S1 post-restart, no key: only the stale tail's exact-0.0 landing",
          [r.v_forward for r in post_boot] == [0.0],
          [r.v_forward for r in post_boot])
    check("S1 no positive speed after pause_at+100 ms across the restart",
          all(r.v_forward == 0.0 for r in recs[n_pre2:]))
    check("S1 the post-restart mapper holds NO stale key", len(pol.held) == 0)

    # -- exit ------------------------------------------------------------------------
    flow.key("Q", 1, 2210)
    check("S1 exit -> terminal", flow.state == EXITED)
    check("S1 teardown exactly once", world_log == ["boot", "teardown"],
          world_log)
    n_exit = n_at()
    pol.calls.clear()
    flow.key("Q", 1, 2220)
    flow.key("Return", 1, 2230)
    flow.key("W", 1, 2240)
    flow.tick(2250)
    check("S1 after exit: zero mapper/policy contacts, zero records",
          pol.calls == [] and n_at() == n_exit)
    check("S1 second Q is a named drop, no second teardown",
          world_log == ["boot", "teardown"])
    check("S1 whole run inside U01's bounds", not bounds_violations(recs))
    return sink


def main():
    print("== R3 INTEGRATED SCENARIO (stack: X02 flow -> U03 policy -> "
          "U01 mapper -> gate -> sink) ==")
    print("-- B1 first: the composition AS COMMITTED --")
    sink = MockSink()
    fp = FocusPolicy(sink)
    missing = [n for n in ("press", "release", "mouse", "tick", "release_all",
                           "held") if not hasattr(fp, n)]
    check("B1 FocusPolicy surface: complete post-fix", missing == [],
          "missing=%r" % missing)
    try:
        SessionFlow(fp, restart_scene=lambda: None, teardown=lambda: None)
        check("B1 SessionFlow(FocusPolicy) constructs post-fix", True,
              "constructed?! review harness assumption wrong")
    except Exception as exc:
        check("B1 SessionFlow(FocusPolicy) REJECTED at construction "
              "(the documented composition does not exist)",
              type(exc).__name__ == "FlowError", repr(exc))

    sink = run_spine(None)

    # ── S2 ADVERSARIAL COMPOSITIONS ─────────────────────────────────────────
    print("S2a blur DURING the resume tail")
    s = FaithfulConsumer()
    p = RecordingPolicy(s)
    w = []
    f = SessionFlow(p, restart_scene=lambda: (w.append("boot"), 1)[1],
                    teardown=lambda: w.append("teardown"))
    f.key("Return", 1, 0)
    f.key("W", 1, 10)
    for t in range(10, 111, 10):
        f.tick(t)
    f.key("Escape", 1, 120)           # quiesce mid-run: tail armed [V_MAX,120,0]
    f.key("Return", 1, 140)           # resume inside the decay window
    got = f.tick(150)                 # boundary 1 of the tail (a positive sample)
    p.on_blur(160)                    # BLUR DURING THE TAIL
    t, tail = 160, list(got)
    while t <= 400:
        tail.extend(f.tick(t))
        t += 10
    vals = [r.v_forward for r in tail]
    check("S2a tail <= 2 records despite the blur", len(tail) <= 2, vals)
    check("S2a blur did not RESTART the tail (idempotent release_all)",
          len(vals) == 2 and vals[-1] == 0.0, vals)
    check("S2a positive sample <= pre-pause V_MAX", all(v <= V_MAX_IN_BAND_M_S
          for v in vals), vals)
    f.key("W", 1, 300)                # still blurred: must drop
    check("S2a press while blurred (tail era) dropped",
          "dropped_blurred" in p.last_trace and len(p.held) == 0)
    p.on_focus(410)
    f.key("W", 1, 420)
    got = f.tick(420)
    check("S2a after focus a fresh press arms a FRESH grid",
          len(got) == 1 and got[0].v_forward == V_MAX_IN_BAND_M_S, got)
    check("S2a no stuck movement: all bounded", not bounds_violations(s.records))

    print("S2b restart DURING the decay window (does a stale tail cross the boot?)")
    s = FaithfulConsumer()
    p = RecordingPolicy(s)
    w = []
    f = SessionFlow(p, restart_scene=lambda: (w.append("boot"), 1)[1],
                    teardown=lambda: w.append("teardown"))
    f.key("Return", 1, 0)
    f.key("W", 1, 10)
    for t in range(10, 111, 10):
        f.tick(t)
    f.key("Escape", 1, 120)           # tail armed at 120
    f.key("R", 1, 150)                # restart 30 ms INTO the 100 ms decay window
    check("S2b restart inside the decay window boots once",
          f.state == PLAYING and w == ["boot"], w)
    t, post = 160, []
    while t <= 400:
        post.extend(f.tick(t))
        t += 10
    vals = [r.v_forward for r in post]
    check("S2b THE STALE TAIL CROSSES THE BOOT: a positive record reaches "
          "the FRESH scene", any(v > 0.0 for v in vals), vals)
    check("S2b but it is bounded: <= 2 records, lands exact 0.0",
          len(post) <= 2 and vals[-1] == 0.0, vals)
    check("S2b no positive record past 120+100 ms (the frozen deadline holds "
          "across the boot)", all(v == 0.0 for v in vals[1:]), vals)
    check("S2b bounds held", not bounds_violations(s.records))

    print("S2c disconnect + pause race, both orders")
    for order in ("disconnect-first", "pause-first"):
        s = FaithfulConsumer()
        p = RecordingPolicy(s)
        f = SessionFlow(p, restart_scene=lambda: 1, teardown=lambda: 1)
        f.key("Return", 1, 0)
        f.key("W", 1, 10)
        for t in range(10, 111, 10):
            f.tick(t)
        n0 = len(s.records)
        if order == "disconnect-first":
            p.on_disconnect(120)
            check("S2c/%s disconnect releases and names the state"
                  % order, p.state == "disconnected" and len(p.held) == 0)
            for t in range(120, 221, 10):
                f.tick(t)             # flow still playing: decay reaches sink
            f.key("Escape", 1, 230)   # pause while disconnected
            check("S2c/%s pause during disconnect is legal" % order,
                  f.state == PAUSED)
        else:
            f.key("Escape", 1, 120)   # pause first: tail SUSPENDED mid-decay
            p.on_disconnect(130)      # device dies while the menu is up
            check("S2c/%s disconnect while paused names itself" % order,
                  p.state == "disconnected")
        for t in range(240, 400, 10):
            f.tick(t)                 # suspended: nothing flows
        n_susp = len(s.records)
        f.key("Return", 1, 410)       # resume while STILL disconnected
        check("S2c/%s resume while disconnected -> playing (flow) + dropped "
              "intent (policy)" % order, f.state == PLAYING
              and p.state == "disconnected")
        f.key("W", 1, 420)
        t, tail = 410, []
        while t <= 600:
            tail.extend(f.tick(t))
            t += 10
        vals = [r.v_forward for r in tail]
        check("S2c/%s tail bounded on resume (silence if the decay already "
              "completed pre-pause; else <= 2 records landing exact 0.0)"
              % order, len(vals) <= 2 and (not vals or vals[-1] == 0.0)
              and all(0.0 <= v <= V_MAX_IN_BAND_M_S for v in vals), vals)
        check("S2c/%s no NEW walk demand while disconnected (press dropped)"
              % order, not any(v > 0.0 for v in vals), vals)
        p.on_reconnect(610)
        f.key("W", 1, 620)
        got = f.tick(620)
        check("S2c/%s after reconnect a fresh press walks again" % order,
              len(got) == 1 and got[0].v_forward == V_MAX_IN_BAND_M_S, got)
        check("S2c/%s bounds held" % order, not bounds_violations(s.records))

    print("S2d a key held across the ENTIRE restart (stale held key?)")
    s = FaithfulConsumer()
    p = RecordingPolicy(s)
    f = SessionFlow(p, restart_scene=lambda: w.append("boot"),
                    teardown=lambda: w.append("teardown"))
    f.key("Return", 1, 0)
    f.key("W", 1, 10)
    for t in range(10, 111, 10):
        f.tick(t)
    f.key("Escape", 1, 120)           # the PHYSICAL W is still down...
    f.key("R", 1, 300)                # ...across the whole restart (OUTSIDE the
                                      # 100 ms decay window: 300 > 120+100)...
    check("S2d no new keydown is synthesized after the restart",
          f.state == PLAYING)
    t, post = 310, []
    while t <= 600:                   # ...and the finger stays on W
        post.extend(f.tick(t))
        t += 10
    vals = [r.v_forward for r in post]
    check("S2d the post-restart mapper sees NO stale held key: "
          "only the tail's exact-0.0 landing, zero movement, no fresh press",
          len(p.held) == 0 and vals == [0.0], (len(p.held), vals))
    f.key("W", 1, 610)                # the operator genuinely re-presses
    got = f.tick(610)
    check("S2d a fresh press walks again after the restart",
          len(got) == 1 and got[0].v_forward == V_MAX_IN_BAND_M_S, got)
    # corroboration (S2b's finding, second measurement): restart INSIDE the
    # decay window imports a POSITIVE stale sample into the fresh scene
    s = FaithfulConsumer()
    p = RecordingPolicy(s)
    w = []
    f = SessionFlow(p, restart_scene=lambda: w.append("boot"),
                    teardown=lambda: w.append("teardown"))
    f.key("Return", 1, 0)
    f.key("W", 1, 10)
    for t in range(10, 111, 10):
        f.tick(t)
    f.key("Escape", 1, 120)
    f.key("R", 1, 200)                # 200 < 120+100: inside the window
    t, post = 210, []
    while t <= 600:
        post.extend(f.tick(t))
        t += 10
    vals = [r.v_forward for r in post]
    check("S2d-corroborates-B2 restart inside the decay window imports the "
          "stale positive sample [~0.1*V_MAX, 0.0] into the fresh scene",
          len(vals) == 2 and 0.0 < vals[0] < 0.15 * V_MAX_IN_BAND_M_S
          and vals[1] == 0.0, vals)

    print("S2e R pressed DURING PLAY must never boot (the deliberate absence)")
    s = FaithfulConsumer()
    p = RecordingPolicy(s)
    w = []
    f = SessionFlow(p, restart_scene=lambda: w.append("boot"),
                    teardown=lambda: w.append("teardown"))
    f.key("Return", 1, 0)
    f.key("W", 1, 10)
    f.tick(20)
    f.key("R", 1, 30)
    check("S2e mid-play R is a named no-op, zero boots",
          f.state == PLAYING and w == [] and "R" not in p.held
          and any(d["kind"] == "flow_action" for d in f.last_trace["dropped"]))

    print("S2f the expiry floor INSIDE the composition (stalled physics clock)")
    class Stalled:
        """A tick_source frozen at boot: every record carries issued_tick 100."""
        def __call__(self):
            return 100
    sink2 = MockSink()
    pol2 = ComposedFocus(sink2, mapper_factory=lambda gate: InputMapper(
        gate, tick_source=Stalled()))
    f = SessionFlow(pol2, restart_scene=lambda: 1, teardown=lambda: 1)
    f.key("Return", 1, 0)
    f.key("W", 1, 10)
    for t in range(10, 601, 10):
        f.tick(t)
    # Boundaries 10..410 (9 of them) carry age <= 30 ticks at delivery -> the
    # belt passes them (genuinely fresh); boundaries 460,510,560 exceed the
    # floor -> dropped, named. ZERO stale records may reach the sink.
    stale_in_sink = [r for r in sink2.records
                     if InputMapper.is_expired(r, 434)]
    check("S2f the belt: fresh-at-delivery records pass (9), stale ones are "
          "dropped and named (3), and NOTHING expired-at-delivery is in the "
          "sink", pol2.gate_stats["passed"] == 9
          and pol2.gate_stats["expired_at_gate"] == 3
          and len(sink2.records) == 9 and not stale_in_sink,
          (pol2.gate_stats, len(sink2.records), len(stale_in_sink)))
    check("S2f drops are named in the policy trace",
          "expired_at_gate" in pol2.last_trace)

    print("S3 falsifier mining: the pause leans on a consumer OUTSIDE the stack")
    s = NaiveHolder()
    p = RecordingPolicy(s)
    f = SessionFlow(p, restart_scene=lambda: 1, teardown=lambda: 1)
    f.key("Return", 1, 0)
    f.key("W", 1, 10)
    for t in range(10, 111, 10):
        f.tick(t)
    f.key("Escape", 1, 120)
    naive = [s.demand_at(t) for t in range(130, 3000, 100)]
    check("S3 a naive ZOH consumer sees FULL-SPEED demand for the WHOLE pause "
          "(the stack alone cannot stop the animal)",
          all(v == V_MAX_IN_BAND_M_S for v in naive), naive[:3])
    s2 = FaithfulConsumer()
    p2 = RecordingPolicy(s2)
    f2 = SessionFlow(p2, restart_scene=lambda: 1, teardown=lambda: 1)
    f2.key("Return", 1, 0)
    f2.key("W", 1, 10)
    for t in range(10, 111, 10):
        f2.tick(t)
    f2.key("Escape", 1, 120)
    faithful = [s2.demand_at(t) for t in range(130, 3000, 100)]
    check("S3 the DECLARED consumer (is_expired honored) coasts <= 100 ms "
          "then goes inert", faithful[0] == V_MAX_IN_BAND_M_S
          and all(v is None for v in faithful[2:]), faithful[:4])

    print("S4 note-probe: exit does NOT quiesce the mapper (terminal object "
          "keeps its held set)")
    s = FaithfulConsumer()
    p = RecordingPolicy(s)
    f = SessionFlow(p, restart_scene=lambda: 1, teardown=lambda: 1)
    f.key("Return", 1, 0)
    f.key("W", 1, 10)
    f.key("Q", 1, 30)
    check("S4 exit keeps W in the mapper's held set (harmless while terminal; "
          "a hazard only if the object were resurrected)",
          f.state == EXITED and "W" in p.held, (f.state, sorted(p.held)))

    print("== RESULT: %d checks, %d FAILED ==" % (CHECKS[0], len(FAILURES)))
    for name, detail in FAILURES:
        print("  FAILED: %s -- %s" % (name, detail))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
