"""test_push_page_guard.py -- the push client PAGE's runtime guard test
(lane/push-channel-20260920). RUNS STANDALONE (its own process):

  python tools/thin_client_pilot/test_push_page_guard.py
     (env CHIMERA_TEST_SLICE=http://127.0.0.1:PORT reuses a running slice)

F2 runtime: an all-zero canned snapshot injected into the page is REJECTED
(guard_rejects increments, never rendered) and the good frame is HELD and
shown bound to its authoritative ts (the F3 law, inherited). Also asserts
the render loop SURVIVED the injection (zero new page errors after canned).

FINDING (recorded, 2026-09-22): this browser test verified standalone in
seconds twice, but HUNG twice (4-9 min, no CPU) when run inside the
same-process unittest-style suite (test_push_channel.py) after the stream
tests -- cause not isolated within the lane's budget; the test therefore
runs in its own process, which is the behavior the assertion needs anyway.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _free_port() -> int:
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p + 1 if p == 8127 else p


class LiveSlice:
    def __init__(self):
        self.port = _free_port()
        self.base = "http://127.0.0.1:%d" % self.port
        self.proc = subprocess.Popen(
            [sys.executable, "-u", str(HERE / "boot_slice.py"),
             "--port", str(self.port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            cwd=str(HERE.parent.parent),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        import urllib.request
        t0 = time.time()
        while time.time() - t0 < 120:
            try:
                with urllib.request.urlopen(self.base + "/api/health",
                                            timeout=10) as r:
                    j = json.loads(r.read())
                if j.get("ok") and j.get("world_booted"):
                    return
            except OSError:
                time.sleep(0.5)
        raise RuntimeError("slice never became healthy")

    def close(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def run_test(base: str) -> None:
    from playwright.sync_api import sync_playwright
    n = 314
    good = {"ts": 1111111111, "ticks": 1000, "root_y": 1.2345,
            "root_vy": -0.5, "P_l": 111.0, "P_u": 222.0, "dimple": 0.03,
            "pos": [0.1, 0.2, 0.3] * n}
    zero = {"ts": 2222222222, "ticks": 1001, "root_y": 0.0,
            "root_vy": 0.0, "P_l": 0.0, "P_u": 0.0, "dimple": 0.0,
            "pos": [0.0, 0.0, 0.0] * n}
    errs_before = None
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--disable-background-timer-throttling",
                  "--disable-renderer-backgrounding",
                  "--disable-backgrounding-occluded-windows",
                  "--enable-gpu", "--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport={"width": 960, "height": 540})
        page.set_default_timeout(20000)
        page.goto(base + "/push?fmt=FULL36&rate=30", wait_until="commit",
                  timeout=30000)
        page.wait_for_function("window.__push_state !== undefined",
                               timeout=20000)
        page.wait_for_timeout(2000)
        page.evaluate("(x) => window.__push_canned(JSON.parse(x))",
                      json.dumps([good, zero]))
        page.wait_for_timeout(700)
        st = page.evaluate("window.__push_state()")
        browser.close()
    errs_before = st["errs"]
    panel = st["panel"]["state"] + " | " + st["panel"]["sync"]
    assert "1.2345" in panel, "good canned frame not shown: " + panel
    assert "111.00" in panel and "222.00" in panel, \
        "canned pressures absent: " + panel
    assert "1111111111" in panel, "canned ts absent: " + panel
    assert "2222222222" not in panel, \
        "the REJECTED zero frame leaked into the overlay: " + panel
    assert "0.2553" not in st["panel"]["state"], \
        "a live world value leaked into the overlay after canned: " + panel
    assert st["guard_rejects"] >= 1, \
        "the zero frame was not counted as a guard reject"
    assert st["held"] and st["held"]["ts"] == 1111111111, \
        "held is not the last good frame: %r" % st["held"]
    frame_errs = [e for e in errs_before if e.startswith("frame:")]
    assert not frame_errs, "the render loop hit errors: %r" % frame_errs[:3]
    print("PASS test_push_page_guard_runtime "
          "(guard_rejects=%d held=%s)" % (st["guard_rejects"], st["held"]))


def main() -> int:
    base = os.environ.get("CHIMERA_TEST_SLICE")
    sl = None
    if not base:
        sl = LiveSlice()
        base = sl.base
    try:
        run_test(base)
        return 0
    finally:
        if sl is not None:
            sl.close()


if __name__ == "__main__":
    sys.exit(main())
