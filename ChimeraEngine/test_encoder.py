"""test_encoder.py -- the async JPEG encoder, tested WITHOUT the render loop.

WHY NOT THROUGH THE VIEWER. The obvious test is "start the viewer, watch the stream advance", and
it was run first and answered nothing three times over: `aBlueWorld` publishes a byte-identical
frame under camera motion (pre-existing -- a git-stash control reproduced it exactly on the
committed code), `theMining` is a cone and genuinely renders the same picture under azimuthal
drift, and one process rendered 5 frames in 6 seconds for reasons that have nothing to do with
encoding. Three different confounds, none of them the thing under test.

    A TEST THAT CANNOT FAIL FOR ONLY ONE REASON IS NOT TESTING THAT REASON.

So this drives `_submit`/`_encode_loop`/`_publish` directly with synthetic frames, where "did the
newest frame reach `_latest`" has exactly one possible cause.

    python ChimeraEngine/test_encoder.py
"""
from __future__ import annotations

import hashlib
import io
import sys
import threading
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent)); sys.path.insert(0, str(_HERE))

OK, BAD = [], []


def check(name, cond, detail=""):
    (OK if cond else BAD).append(name)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))


def frame(seed, w=640, h=360):
    """A distinguishable frame. Deterministic, and JPEG-distinct from its neighbours."""
    rng = np.random.default_rng(seed)
    a = np.zeros((h, w, 3), dtype=np.uint8)
    a[:, :, 0] = seed % 251
    a[h // 4:3 * h // 4, w // 4:3 * w // 4] = rng.integers(0, 255, (h // 2, w // 2, 3), dtype=np.uint8)
    return a


class Harness:
    """The viewer's encoder machinery, lifted out of the viewer.

    It binds the REAL methods off LiveViewer rather than reimplementing them -- a copy would drift
    from the thing it claims to test the first time somebody edited one of them.
    """

    def __init__(self):
        import live_viewer as LV
        self._lock = threading.Lock()
        self._enc_cv = threading.Condition()
        self._enc_slot = None
        self._latest = None
        self._pub_hist = []
        self._err = None
        self._running = True
        self.n_encodes = 0
        cls = LV.LiveViewer
        self._submit = cls._submit.__get__(self)
        self._encode_loop = cls._encode_loop.__get__(self)
        _pub = cls._publish.__get__(self)

        def counting(img):
            self.n_encodes += 1
            return _pub(img)
        self._publish = counting
        self._t = threading.Thread(target=self._encode_loop, daemon=True)
        self._t.start()

    def latest_md5(self):
        with self._lock:
            return hashlib.md5(self._latest or b"").hexdigest()

    def stop(self):
        self._running = False
        with self._enc_cv:
            self._enc_cv.notify_all()
        self._t.join(timeout=2.0)


def md5_of_jpeg(img):
    from PIL import Image
    b = io.BytesIO(); Image.fromarray(img).save(b, "JPEG", quality=85)
    return hashlib.md5(b.getvalue()).hexdigest()


def wait_until(fn, timeout=5.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if fn():
            return True
        time.sleep(0.01)
    return False


def main() -> int:
    print("=" * 90)
    print("ASYNC JPEG ENCODER -- handoff, drop-newest, and the paused synchronous path")
    print("=" * 90)

    h = Harness()
    f1 = frame(1)
    h._submit(f1)
    check("a submitted frame reaches _latest", wait_until(lambda: h._latest is not None))
    check("and it is THAT frame, not some other", h.latest_md5() == md5_of_jpeg(f1))

    # EVERY frame must arrive when the encoder is not saturated. This is the property that fails
    # if the condition variable is notified without the slot being set, or vice versa.
    seen = set()
    for i in range(2, 12):
        f = frame(i)
        h._submit(f)
        wait_until(lambda: h.latest_md5() == md5_of_jpeg(f), timeout=2.0)
        seen.add(h.latest_md5())
    check("10 sequential frames each arrive distinctly", len(seen) == 10, f"{len(seen)}/10")

    # DROP, DON'T QUEUE. Submitting a burst faster than the encoder drains it must end on the
    # NEWEST frame -- and must not have encoded all of them, or it queued.
    n0 = h.n_encodes
    burst = [frame(100 + i) for i in range(40)]
    for f in burst:
        h._submit(f)
    last = md5_of_jpeg(burst[-1])
    arrived = wait_until(lambda: h.latest_md5() == last, timeout=5.0)
    encoded = h.n_encodes - n0
    check("a 40-frame burst settles on the NEWEST frame", arrived)
    check("and did NOT encode all 40 (it dropped, it did not queue)", encoded < 40,
          f"encoded {encoded} of 40")
    check("_pub_hist recorded a duration per encode", len(h._pub_hist) >= 1,
          f"{len(h._pub_hist)} entries, last {h._pub_hist[-1]:.2f} ms" if h._pub_hist else "empty")

    # THE ENCODER MUST NOT WEDGE ON A BAD FRAME. A malformed submit should be caught and reported,
    # and the thread must survive to encode the next good one.
    h._submit("not an image")
    time.sleep(0.3)
    good = frame(999)
    h._submit(good)
    check("survives a malformed frame and keeps encoding",
          wait_until(lambda: h.latest_md5() == md5_of_jpeg(good), timeout=3.0),
          f"err recorded: {(h._err or 'none')[:60]}")
    h.stop()
    check("the encoder thread exits when _running goes false", not h._t.is_alive())

    # THE SYNCHRONOUS PATH used while paused: _publish alone, no thread, must land immediately.
    h2 = Harness(); h2.stop()                      # kill the thread; use _publish directly
    f = frame(7)
    h2._publish(f)
    check("_publish alone lands the frame synchronously (the /step path)",
          h2.latest_md5() == md5_of_jpeg(f))

    print("=" * 90)
    print(f"  {len(OK)} passed, {len(BAD)} failed")
    for b in BAD:
        print(f"    FAILED: {b}")
    print("=" * 90)
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
