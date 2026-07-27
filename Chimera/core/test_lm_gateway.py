"""Tests for core.lm_gateway — run: python core/test_lm_gateway.py"""

import sys
import shutil
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PASS = TOTAL = 0


def check(name, cond):
    global PASS, TOTAL
    TOTAL += 1
    print(("  ok  " if cond else "FAIL  ") + name)
    PASS += cond


def main():
    tmp = Path(tempfile.mkdtemp(prefix="lmgw_test_"))
    import core.lm_gateway as gw
    gw.QUEUE_DIR = tmp / "lm_queue"
    gw.COUNTER = gw.QUEUE_DIR / ".counter"
    gw.LOCK_PATH = gw.QUEUE_DIR / ".lock"
    gw.QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    gw.MAX_CONCURRENT = 1
    gw.STALE_TTL = 2.0
    gw.HEARTBEAT_S = 0.4
    gw.POLL_S = 0.05

    # 1: monotonic unique sequence
    seqs = [gw._next_seq() for _ in range(5)]
    check("sequence is monotonic + unique", seqs == sorted(seqs) and len(set(seqs)) == 5)

    # 2: FIFO clearance under concurrency=1
    t1 = gw._Ticket(gw._next_seq(), "a")
    t2 = gw._Ticket(gw._next_seq(), "b")
    check("first ticket cleared, second blocked (concurrency=1)",
          t1.cleared() and not t2.cleared())
    t1.release()
    check("second clears once first releases", t2.cleared())
    t2.release()

    # 3: stale reclamation — a dead holder's ticket is removed by mtime
    dead = gw.QUEUE_DIR / "t_999_12345.json"
    dead.write_text("{}")
    import os
    old = time.time() - 10
    os.utime(dead, (old, old))
    live = gw._live_tickets()
    check("stale ticket reclaimed", not dead.exists()
          and 999 not in [s for s, _ in live])

    # 4: _BufferedResponse surface (read + context manager)
    br = gw._BufferedResponse(b'{"x":1}', 200)
    with br as r:
        data = r.read()
    check("buffered response reads once, context-manages", data == b'{"x":1}'
          and br.getcode() == 200)

    # 5: INTEGRATION — two concurrent callers serialize, neither is dropped.
    # Fake urlopen records each call's held window; with concurrency=1 the
    # windows must not overlap (the whole point: no dogpile, no timeout).
    windows, wlock = [], threading.Lock()

    def fake_urlopen(req, timeout=None):
        start = time.time()
        time.sleep(0.3)                       # simulate generation
        class _R:
            status = 200
            def read(self_inner):
                with wlock:
                    windows.append((start, time.time()))
                return b'{"ok":1}'
        return _R()

    orig = urllib.request.urlopen
    urllib.request.urlopen = fake_urlopen
    try:
        results = []
        def worker(tag):
            with gw.lm_urlopen(object(), timeout=5, agent=tag) as r:
                results.append(r.read())
        threads = [threading.Thread(target=worker, args=(f"w{i}",)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
    finally:
        urllib.request.urlopen = orig

    check("all three concurrent callers completed (none dropped)", len(results) == 3)
    windows.sort()
    overlap = any(windows[i][1] > windows[i + 1][0] + 0.02
                  for i in range(len(windows) - 1))
    check("held windows do NOT overlap (fair serialization, concurrency=1)",
          len(windows) == 3 and not overlap)
    check("queue fully drained after all calls", gw.queue_depth() == 0)

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{PASS}/{TOTAL} tests passed")
    return 0 if PASS == TOTAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
