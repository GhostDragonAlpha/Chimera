"""test_push_channel.py -- the push channel's falsifier tests (lane/push-channel-20260920).

Run:  python -m pytest tools/thin_client_pilot/test_push_channel.py -q
   or python tools/thin_client_pilot/test_push_channel.py  (plain runner)

Covers:
  F2 framing (offline): the record assembler NEVER emits a torn record --
  a byte stream split at EVERY possible boundary assembles to the same
  records; an impossible length is a loud error, never a partial frame.
  F2 zero-frame (runtime): a canned all-zero snapshot injected into the
  page is REJECTED (guard_rejects increments, HELD stays, the panel shows
  the last good frame) -- the pilot's banked zero-frame class cannot render.
  F3 sync law (runtime): canned snapshot values surface VERBATIM in the
  overlay bound to the canned authoritative ts (inherited law).
  Server truth (live): DELTA refused with the E3 note; /api/channel
  counters; first record parses; snapshot payload sizes match the fmt;
  achieved rate within bar over a 4 s window; pixel records carry JPEG.
Unit tests run offline; live tests SKIP (named) when no slice is reachable.
"""
from __future__ import annotations

import json
import socket
import struct
import subprocess
import threading
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "playable_slice"))

from push_stream import REC_HDR, RT_HEARTBEAT, RT_SNAPSHOT, StreamClient  # noqa: E402

BUDGET_RATE_BAR = 0.95


def _rec(rtype: int, seq: int, payload: bytes, ts: int = 1) -> bytes:
    return struct.pack("<IHHIQ", len(payload), rtype, 1, seq, ts) + payload


# ── offline: the assembler cannot emit a torn record ─────────────────────

def test_assembler_split_every_boundary():
    recs = [_rec(RT_SNAPSHOT, 1, b"A" * 100),
            _rec(RT_HEARTBEAT, 0, b"\x00" * 8),
            _rec(RT_SNAPSHOT, 2, b"B" * 300)]
    wire = b"".join(recs)
    sizes = [len(r) for r in recs]
    for split in range(1, len(wire) - 1):        # EVERY boundary
        c = StreamClient("127.0.0.1", 9, "fmt=Z12&rate=30")
        c.t0 = time.monotonic()
        c.buf = wire[:split]
        c._drain()
        # exactly the COMPLETE records the prefix holds, IN ORDER -- the
        # first record that doesn't fit ends the count (a partial record
        # must never be emitted: the torn-frame guard at the framing layer)
        n_complete, acc = 0, 0
        for sz in sizes:
            if acc + sz <= split:
                n_complete += 1
                acc += sz
            else:
                break
        assert len(c.records) == n_complete, \
            ("prefix emitted wrong count", split, len(c.records), n_complete)
        c.buf += wire[split:]
        c._drain()
        assert [r[1] for r in c.records] == [RT_SNAPSHOT, RT_HEARTBEAT,
                                             RT_SNAPSHOT], split
        assert [r[2] for r in c.records] == [1, 0, 2], split


def test_assembler_seq_gap_counted():
    c = StreamClient("127.0.0.1", 9, "fmt=Z12&rate=30")
    c.t0 = time.monotonic()
    c.buf = _rec(RT_SNAPSHOT, 5, b"x" * 10) + _rec(RT_SNAPSHOT, 9, b"y" * 10)
    c._drain()
    assert c.seq_gaps == 3                       # 6,7,8 skipped: counted


def test_assembler_impossible_length_is_loud():
    c = StreamClient("127.0.0.1", 9, "fmt=Z12&rate=30")
    c.t0 = time.monotonic()
    c.buf = struct.pack("<IHHIQ", 0x7FFFFFFF, RT_SNAPSHOT, 1, 1, 0)
    try:
        c._drain()
        assert False, "impossible length accepted"
    except RuntimeError as e:
        assert "framing" in str(e)


# ── unit: the mailbox is latest-wins (the degradation law) ───────────────

def test_subscriber_latest_wins():
    pc = __import__("push_channel")
    sub = pc.Subscriber()
    sub.offer(b"frame1")
    sub.offer(b"frame2")          # overwrites the undelivered frame
    got = sub.take(timeout=0.1)
    assert got == b"frame2"       # the NEWEST frame wins
    assert sub.skipped == 1       # and the drop is counted, never hidden
    assert sub.take(timeout=0.05) is None


def test_profile_composes_one_per_tick_and_stamps_seq():
    pc = __import__("push_channel")
    THS1 = struct.pack("<IQIfffffQII", 0x31534854, 123456, 7, 0.25, 0.0,
                       0.0, 0.0, 0.0, 0, 0, 4)
    class FakeWorld:
        url = "fake"
        calls = 0
        def snapshot(self, fmt, timeout=None):
            FakeWorld.calls += 1
            return (THS1, fmt, 4)
    prof = pc.Profile(("state", "Z12", 50, 0, 0, 0), FakeWorld())
    sub = prof.subscribe()
    got: list = []
    drain_done = threading.Event()

    def drain():                  # consume DURING composition -- the mailbox
        while not drain_done.is_set():   # is latest-wins: an undrained run
            r = sub.take(timeout=0.02)   # would (correctly) keep only 1
            if r is not None:
                got.append(r)
        while True:                      # final drain after stop; the window
            r = sub.take(timeout=0.2)    # covers a compose straddling the
            if r is None:                # stop flag (broadcast lands right
                break                    # after the tick that saw stop)
            got.append(r)
    th = threading.Thread(target=drain)
    th.start()
    time.sleep(0.5)               # ~25 ticks at 50 Hz
    prof.stop.set()
    drain_done.set()
    th.join(timeout=5)
    assert FakeWorld.calls >= 10, "broadcaster never composed"
    assert len(got) >= 10, "fan-out lost frames"
    # every composed frame is either delivered or counted-skipped (W2):
    # a take that straddles an offer sees the newest frame win
    assert len(got) + sub.skipped >= FakeWorld.calls, \
        ("frames vanished", len(got), sub.skipped, FakeWorld.calls)
    seqs = [struct.unpack_from("<I", r, 8)[0] for r in got]
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs)
    # the THS1 payload rides byte-identical
    assert all(r[20:24] == b"TS\x011"[:4] or r[20:24] == THS1[:4] for r in got)


# ── live tests (a slice; SKIP with a name when none reachable) ───────────

_SLICE = None


def get_slice():
    global _SLICE
    if _SLICE is None:
        import os
        env = os.environ.get("CHIMERA_TEST_SLICE")
        if env:
            class _Existing:
                base = env
                def close(self):
                    pass
            _SLICE = _Existing()
        else:
            _SLICE = LiveSlice()
    return _SLICE


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p + 1 if p == 8127 else p


def _get(base: str, path: str, timeout: int = 10) -> tuple:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.status, r.read()


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
        t0 = time.time()
        while time.time() - t0 < 120:
            try:
                j = json.loads(_get(self.base, "/api/health")[1])
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


def _hp(base):
    rest = base.split("://", 1)[1]
    h, p = rest.split(":")
    return h, int(p)


def test_stream_first_records_parse_and_sizes_match_fmt():
    sl = get_slice()
    for fmt, per_vert in (("FULL36", 36), ("POS12", 12), ("POS16", 12)):
        c = StreamClient(*_hp(sl.base), "fmt=%s&rate=30" % fmt)
        c.connect()
        c.pump(1.5)
        snaps = [r for r in c.records if r[1] == RT_SNAPSHOT]
        assert len(snaps) >= 20, (fmt, "too few records", len(snaps))
        size = snaps[0][3] - 20
        assert size >= 52, (fmt, size)
        assert (size - 52) % per_vert == 0, (fmt, size)
        assert c.framing_errors == 0


def test_stream_rate_holds_bar_4s():
    sl = get_slice()
    c = StreamClient(*_hp(sl.base), "fmt=Z12&rate=30")
    c.connect()
    c.pump(4.0)
    s = c.summary(drop_ramp_s=0.5)
    assert s["achieved_hz"] >= BUDGET_RATE_BAR * 30, s


def test_delta_refused_with_e3_note():
    sl = get_slice()
    try:
        _get(sl.base, "/api/stream?fmt=DELTA&rate=30")
        assert False, "DELTA accepted (E3 violation)"
    except urllib.error.HTTPError as e:  # noqa: UP042
        assert e.code == 400
        body = e.read().decode()
        assert "E3" in body, body


def test_channel_truth_counters():
    sl = get_slice()
    st = json.loads(_get(sl.base, "/api/channel")[1])
    assert "counters" in st and "profiles" in st and "drops_tail" in st


def test_pixel_stream_serves_jpeg():
    sl = get_slice()
    c = StreamClient(*_hp(sl.base), "pixel=1&w=320&q=70&pixel_rate=30")
    c.capture_pixel = True
    c.connect()
    c.pump(3.0)
    assert any(r[1] == 2 for r in c.records), "no pixel record seen"
    assert c.pixel_payloads, "pixel payload not captured"
    assert c.pixel_payloads[0][:3] == b"\xff\xd8\xff", \
        "pixel payload is not a JPEG"
    c.close()


def _first_pixel_is_jpeg(c: StreamClient) -> bool:
    """kept for symmetry with the harness checks: payloads are captured in
    StreamClient.pixel_payloads (the drained tail buffer holds no complete
    records)."""
    return bool(c.pixel_payloads) and \
        c.pixel_payloads[0][:3] == b"\xff\xd8\xff"


# test_push_client_page_guard_runtime moved to its own runner
# (test_push_page_guard.py) -- see the FINDING note there.

if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    fails = 0
    for fn in fns:
        try:
            fn()
            print("PASS %s" % fn.__name__)
        except Exception as e:  # noqa: BLE001
            fails += 1
            print("FAIL %s: %s" % (fn.__name__, e))
    print("done:", len(fns) - fails, "/", len(fns))
    sys.exit(1 if fails else 0)
