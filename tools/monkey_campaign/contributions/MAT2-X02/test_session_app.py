"""test_session_app.py -- MAT2-X02 falsifier probe (prereg P1/P2, F1).

CPU-only. Qualifies the app-level session wiring (session_app.py) against the
frozen prereg:

  P1 clauses (the done_when over the wiring, strict doubles):
    key-only start; Escape pause with quiesce + ZERO mapper events while
    paused; Q exit with ordered teardown exactly once to terminal EXITED;
    R restart ONLY from paused with EXACTLY ONE world boot; R-while-playing
    is a named no-op with zero world calls; resume via Return accepts fresh
    keys.
  P2 clauses (additive-route law):
    the wired routes are only the declared ones; the pinned page bytes get
    exactly one disclosed additive script tag and nothing else; legacy
    dispatch reaches the base handler unchanged for every legacy path.

Falsifier F1: removing or altering any guarantee above makes this file exit
nonzero with the named clause id (demonstrated failing-first before the
implementation existed).

The doubles are session_flow's own (StrictWorld, CountingMapper) -- imported,
never redeclared. The real World/HTTP stack is exercised by the integrated
probe, not here.
"""
from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF = HERE / "reference"
for p in (str(REF), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

# session_flow's own doubles: imported, never redeclared (U03's P2 law).
from tools.monkey_campaign.product.session_flow import (  # noqa: E402
    ATTRACT, EXITED, PAUSED, PLAYING,
    CountingMapper, StrictWorld, TeardownDouble,
)

SESSION_APP_LOADED = False
import session_app  # noqa: E402

SESSION_APP_LOADED = True


class SeqClock:
    """An injected integer-millisecond clock (no wall time anywhere)."""

    def __init__(self):
        self.now = 1000

    def __call__(self) -> int:
        self.now += 10
        return self.now


class StrictSessionWorld:
    """Both declared flow referents, nothing else (the archived prereg's
    StrictBootWorld + StrictTeardownWorld shape). Any other attribute the
    wiring ever touches is recorded, then raised -- an undeclared world
    contact cannot happen silently."""

    def __init__(self):
        self.boot_calls = 0
        self.shutdown_calls = 0
        self.attempts = []

    def boot(self):
        self.boot_calls += 1
        return {"booted": True}

    def shutdown_engine(self):
        self.shutdown_calls += 1
        return True

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        self.attempts.append(name)      # recorded BEFORE the raise: evidence
        raise AttributeError(
            "StrictSessionWorld: %r is not a declared flow surface "
            "(only boot/shutdown_engine)" % name)


def make_session(world=None, mapper=None):
    clock = SeqClock()
    s = session_app.SliceSession(
        world if world is not None else StrictSessionWorld(),
        mapper=mapper,
        clock=clock,
    )
    return s, clock


# ── P1: the done_when clause set over the wiring ─────────────────────────────
class TestSessionWiringClauses(unittest.TestCase):
    def test_01_start_is_key_only_from_attract(self):
        s, _ = make_session()
        self.assertEqual(s.flow.state, ATTRACT)
        dest = s.key("Return", down=1)
        self.assertEqual(dest, PLAYING)
        self.assertEqual(s.flow.state, PLAYING)

    def test_02_pause_quiesces_and_leaks_zero(self):
        rec = CountingMapper()
        s, _ = make_session(mapper=rec)
        s.key("Return", down=1)
        n0 = len(rec.calls)
        s.key("Escape", down=1)                      # pause: quiesce, gate shut
        self.assertEqual(s.flow.state, PAUSED)
        self.assertIn("release_all", [c[0] for c in rec.calls[n0:]])
        frozen = len(rec.calls)
        for _ in range(25):                          # dense suspended probes
            self.assertEqual(s.tick(), [])
            s.key("W", down=1)
            s.key("W", down=0)
            s.mouse(12)
        self.assertEqual(len(rec.calls), frozen)     # ZERO mapper events
        self.assertEqual(s.flow.state, PAUSED)

    def test_03_resume_via_return_accepts_fresh_keys(self):
        rec = CountingMapper()
        s, _ = make_session(mapper=rec)
        s.key("Return", down=1)
        s.key("Escape", down=1)
        dest = s.key("Return", down=1)               # resume
        self.assertEqual(dest, PLAYING)
        self.assertEqual(s.key("W", down=1), None)   # reaches the mapper again
        self.assertIn(("press", "W", rec.calls[-1][2]), rec.calls)

    def test_04_restart_only_from_paused_exactly_one_boot(self):
        w = StrictSessionWorld()
        s, _ = make_session(world=w)
        s.key("Return", down=1)
        self.assertEqual(s.key("R", down=1), None)   # playing: named no-op
        self.assertEqual(w.boot_calls, 0)            # ZERO world calls
        self.assertEqual(s.flow.state, PLAYING)
        s.key("Escape", down=1)
        dest = s.key("R", down=1)                    # paused: the only path
        self.assertEqual(dest, PLAYING)
        self.assertEqual(w.boot_calls, 1)            # EXACTLY ONE boot
        self.assertEqual(w.attempts, [])             # no undeclared contact

    def test_05_exit_teardown_once_terminal(self):
        td = TeardownDouble()
        s, _ = make_session()
        s.flow._teardown = td.shutdown_engine        # the declared referent
        s.key("Return", down=1)
        s.key("Q", down=1)
        self.assertEqual(td.calls, ["terminate", "wait", "kill"])
        self.assertEqual(s.flow.state, EXITED)
        frozen = len(td.calls)
        for _ in range(20):
            s.key("Q", down=1)
            s.tick()
            s.key("Return", down=1)
        self.assertEqual(len(td.calls), frozen)      # teardown never re-runs
        self.assertEqual(s.flow.state, EXITED)       # terminal holds

    def test_06_exit_from_any_nonexited_state(self):
        for prep in ((), ("Return",), ("Return", "Escape")):
            td = TeardownDouble()
            s, _ = make_session()
            s.flow._teardown = td.shutdown_engine
            for k in prep:
                s.key(k, down=1)
            s.key("Q", down=1)
            self.assertEqual(td.calls, ["terminate", "wait", "kill"])
            self.assertEqual(s.flow.state, EXITED)

    def test_07_session_snapshot_names_state(self):
        s, _ = make_session()
        snap = s.snapshot()
        self.assertEqual(snap["state"], ATTRACT)
        self.assertEqual(snap["records"], 0)
        s.key("Return", down=1)
        self.assertEqual(s.snapshot()["state"], PLAYING)


# ── P2: the additive-route law over HTTP-shaped doubles ──────────────────────
class _FakeHeaders:
    def get(self, name, default=None):
        body = getattr(_FakeHeaders, "_current_body", b"")
        return str(len(body)) if name == "Content-Length" else default


class FakeBaseHandler:
    """Records every legacy dispatch the wired handler forwards."""

    def __init__(self):
        self.legacy = []
        self.sent = []
        self.headers = _FakeHeaders()
        self.rfile = io.BytesIO(b"{}")

    def do_GET(self):
        self.legacy.append(("GET", self.path))

    def do_POST(self):
        self.legacy.append(("POST", self.path, getattr(self, "body", b"{}")))

    def _send(self, code, body, ctype):
        self.sent.append((code, body, ctype))

    def _json(self, obj, code=200):
        self.sent.append((code, obj, "application/json"))


def make_request(handler, path, body=None):
    handler.path = path
    raw = b"{}" if body is None else json.dumps(body).encode("utf-8")
    _FakeHeaders._current_body = raw
    handler.rfile = io.BytesIO(raw)
    return handler


class TestAdditiveRouteLaw(unittest.TestCase):
    def _wired(self):
        s, _ = make_session()
        base = FakeBaseHandler
        wired_cls = session_app.make_wired_handler(base, s)
        h = wired_cls.__new__(wired_cls)             # no HTTP stack in unit law
        FakeBaseHandler.__init__(h)
        h.session = s
        return h, s

    def test_08_declared_new_routes_only(self):
        h, s = self._wired()
        make_request(h, "/api/session").do_GET()
        make_request(h, "/session_overlay.js").do_GET()
        make_request(h, "/api/session/key", {"key": "Return", "down": 1}).do_POST()
        make_request(h, "/api/session/tick", {}).do_POST()
        _c, key_payload, _t = h.sent[-2]
        self.assertEqual(key_payload["transition"], PLAYING)
        code, payload, _ = h.sent[-1]
        self.assertEqual(code, 200)
        self.assertEqual(payload["state"], PLAYING)  # the key above started it
        self.assertEqual(payload["emitted"], 0)      # no demand held after start

    def test_09_legacy_routes_forward_unchanged(self):
        h, _ = self._wired()
        pinned = (REF / "tools/playable_slice/index.html").read_bytes()
        for path in ("/", "/index.html", "/api/status", "/api/health",
                     "/api/verts", "/api/stats", "/ghost.obj"):
            make_request(h, path).do_GET()
        for path in ("/api/press", "/api/restart", "/api/send", "/api/save"):
            make_request(h, path, {"x": 1}).do_POST()
        legacy_paths = [l[1] for l in h.legacy]
        # "/" and "/index.html" are the ONE disclosed page delta (served with
        # the injected tag); every other legacy route forwards unchanged.
        for path in ("/api/status", "/api/health", "/api/verts",
                     "/api/stats", "/ghost.obj"):
            self.assertIn(path, legacy_paths)
        for path in ("/api/press", "/api/restart", "/api/send", "/api/save"):
            self.assertIn(("POST", path, json.dumps({"x": 1}).encode("utf-8")),
                          h.legacy)
        self.assertNotIn("/", legacy_paths)
        self.assertNotIn("/index.html", legacy_paths)
        served = [s for s in h.sent if isinstance(s[1], bytes)]
        self.assertEqual(len(served), 2)             # "/" + "/index.html"
        tag = session_app.OVERLAY_TAG.encode("ascii")
        for _code, body, ctype in served:
            self.assertEqual(ctype, "text/html")
            self.assertEqual(body.replace(tag, b"", 1), pinned)

    def test_10_unknown_route_still_404s_via_base(self):
        h, _ = self._wired()
        make_request(h, "/api/definitely_not_a_route").do_GET()
        self.assertEqual(h.legacy[-1][1], "/api/definitely_not_a_route")

    def test_11_page_injection_is_exactly_one_disclosed_tag(self):
        tag = session_app.OVERLAY_TAG.encode("ascii")
        pinned = (REF / "tools/playable_slice/index.html").read_bytes()
        served = session_app.inject_overlay(pinned)
        self.assertNotEqual(served, pinned)          # the wiring is visible
        # removing the tag restores the pinned bytes byte-exactly
        once = served.replace(tag, b"", 1)
        self.assertEqual(once, pinned)
        self.assertNotIn(tag, once)
        self.assertEqual(served.count(tag), 1)
        # idempotence of the law: no other byte differs
        self.assertEqual(len(served), len(pinned) + len(tag))

    def test_12_overlay_names_all_player_controls(self):
        js = session_app.overlay_js().decode("utf-8")
        for token in ("Return", "Escape", "Q", "R", "api/session/key",
                      "api/session/tick", "api/session"):
            self.assertIn(token, js)
        self.assertNotIn("/api/restart", js)         # legacy path is NOT re-owned


def main() -> int:
    print("test_session_app -- MAT2-X02 falsifier probe (prereg P1/P2/F1)")
    print("  session_app import loaded:", SESSION_APP_LOADED)
    rc = unittest.main(module=sys.modules[__name__], exit=False,
                       verbosity=2).result
    bad = len(rc.failures) + len(rc.errors)
    print("RESULT: %s (%d tests, %d failures, %d errors)" % (
        "ALL CHECKS PASS" if bad == 0 else "CHECKS FAILED",
        rc.testsRun, len(rc.failures), len(rc.errors)))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
