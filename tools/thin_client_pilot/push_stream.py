"""push_stream.py -- THE HARNESS STREAM CLIENT (lane/push-channel-20260920).

A real TCP client of the push channel: opens GET /api/stream, reads with
incremental recv (chunk-as-arrived -- never a blocking full-buffer read,
which would mis-measure cadence), assembles length-prefixed records, and
accounts per-second cadence, wire bytes (INCLUDING the HTTP response
header, never hidden), seq gaps, and framing errors.

Used by push_matrix.py (the rate/bandwidth matrix), push_wedge.py (the
wedge falsifier), and the tests. The wedge kill helper uses SO_LINGER(0)
so close() sends a real RST (the abrupt-kill shape).
"""
from __future__ import annotations

import http.client
import json
import socket
import struct
import time

REC_HDR = struct.Struct("<IHHIQ")
RT_SNAPSHOT = 1
RT_PIXEL = 2
RT_HEARTBEAT = 3
MAXREC = 64 * 1024 * 1024


class StreamClient:
    def __init__(self, host: str, port: int, query: str):
        self.host, self.port, self.query = host, port, query
        self.records: list[tuple] = []   # (t_monotonic, rtype, seq, size, ts_us)
        self.wire_bytes = 0              # every byte off the socket
        self.http_header_b = 0
        self.framing_errors = 0
        self.heartbeats = 0
        self.seq_gaps = 0
        self.last_seq = None
        self.sock: socket.socket | None = None
        self.raw_sock: socket.socket | None = None
        self.fp = None
        self.resp = None
        self.buf = b""
        self.t0 = None
        self.error: str | None = None
        self.ended = False
        self.capture_pixel = False       # tests: keep the first JPEG payload
        self.pixel_payloads: list[bytes] = []

    # ── connection ───────────────────────────────────────────────────────
    def connect(self, timeout: float = 10.0) -> None:
        c = http.client.HTTPConnection(self.host, self.port, timeout=timeout)
        c.request("GET", "/api/stream?" + self.query)
        # hold the raw socket BEFORE getresponse(): a Connection: close
        # response (what the stream sends) makes http.client drop its own
        # reference, and the raw socket is what close()/timeout control.
        self.raw_sock = c.sock
        r = c.getresponse()
        if r.status != 200:
            raise RuntimeError("stream HTTP %d" % r.status)
        ctype = r.getheader("Content-Type")
        assert ctype == "application/octet-stream", ctype
        # HOLD the response object: nothing else references it, and when
        # connect() returns the refcount would destroy it -- closing fp
        # underneath the client ("read of closed file", measured).
        self.resp = r
        # incremental reads through the response's buffered reader; read1
        # returns whatever arrived (never block-accumulates a full buffer --
        # that would mis-measure cadence, measured in this lane's smoke)
        self.fp = r.fp
        self._c = c
        self.raw_sock.settimeout(2.0)
        hdr = b"HTTP/1.1 200 OK\r\n"     # wire accounting: header bytes
        for k, v in r.getheaders():
            hdr += ("%s: %s\r\n" % (k, v)).encode()
        self.http_header_b = len(hdr) + 4
        self.wire_bytes += self.http_header_b
        self.t0 = time.monotonic()

    # ── reading ──────────────────────────────────────────────────────────
    def pump(self, seconds: float, stop: "callable | None" = None) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if stop is not None and stop():
                break
            try:
                chunk = self.fp.read1(262144)
            except (TimeoutError, socket.timeout):
                continue
            except ValueError:
                # fp closed under us: the stream end surfaced late
                self.error = "stream fp closed"
                self.ended = True
                break
            except OSError as e:
                self.error = str(e)
                self.ended = True
                break
            if not chunk:
                self.ended = True
                break
            self.wire_bytes += len(chunk)
            self.buf += chunk
            self._drain()
        self.close()

    def _drain(self) -> None:
        buf = self.buf
        pos = 0
        n = len(buf)
        while n - pos >= 20:
            ln, rt, _fl, sq, ts = REC_HDR.unpack_from(buf, pos)
            if ln > MAXREC:
                self.framing_errors += 1
                raise RuntimeError("framing insane: %d" % ln)
            if n - pos < 20 + ln:
                break                    # partial record: wait (never torn)
            self.records.append((time.monotonic(), rt, sq, 20 + ln, ts))
            if rt == RT_HEARTBEAT:
                self.heartbeats += 1
            if rt == RT_PIXEL and self.capture_pixel and \
                    len(self.pixel_payloads) < 4:
                self.pixel_payloads.append(bytes(buf[pos + 20:pos + 20 + ln]))
            if self.last_seq is not None and rt == RT_SNAPSHOT:
                if sq > self.last_seq + 1:
                    self.seq_gaps += sq - self.last_seq - 1
            if rt == RT_SNAPSHOT:
                self.last_seq = sq
            pos += 20 + ln
        self.buf = buf[pos:]

    def close(self) -> None:
        if self.raw_sock is not None:
            try:
                self.raw_sock.close()
            except OSError:
                pass
            self.raw_sock = None
        try:
            if self.fp is not None:
                self.fp.close()
        except OSError:
            pass
        self.fp = None

    # ── accounting ───────────────────────────────────────────────────────
    def summary(self, drop_ramp_s: float = 1.0) -> dict:
        """cadence/wire over the window, discarding the first `drop_ramp_s`
        (connection ramp); per-second buckets keep the full timeline."""
        recs = [r for r in self.records
                if r[0] >= self.t0 + drop_ramp_s]
        snaps = [r for r in recs if r[1] == RT_SNAPSHOT]
        if len(recs) >= 2:
            span = recs[-1][0] - recs[0][0]
            hz = (len(recs) - 1) / span if span > 0 else 0.0
            shz = (len(snaps) - 1) / span if span > 0 else 0.0
        else:
            span, hz, shz = 0.0, 0.0, 0.0
        ivs = sorted(recs[i + 1][0] - recs[i][0]
                     for i in range(len(recs) - 1))
        wire = self.wire_bytes - self.http_header_b
        window = max(0.001, span)
        return {
            "records": len(recs), "snapshots": len(snaps),
            "achieved_hz": round(hz, 3), "snapshot_hz": round(shz, 3),
            "heartbeats": self.heartbeats,
            "median_interval_ms": round(1000 * ivs[len(ivs) // 2], 2) if ivs else None,
            "max_interval_ms": round(1000 * ivs[-1], 2) if ivs else None,
            "seq_gaps": self.seq_gaps,
            "framing_errors": self.framing_errors,
            "wire_bytes_total": self.wire_bytes,
            "wire_payload_Bps": round(wire / window),
            "wire_MBps": round(wire / window / 1e6, 4),
            "http_header_bytes": self.http_header_b,
            "record_median_B": sorted(r[3] for r in recs)[len(recs) // 2] if recs else 0,
            "ended_early": self.ended, "error": self.error,
            "per_second": self._per_second(),
        }

    def _per_second(self) -> dict:
        out: dict[int, int] = {}
        for t, _rt, _sq, _sz, _ts in self.records:
            if self.t0 is None:
                continue
            s = int(t - self.t0)
            out[s] = out.get(s, 0) + 1
        return out


def max_gap_ms(cl: StreamClient, after_s: float = 0.0) -> float:
    """max inter-record gap after `after_s` (the wedge-falsifier's bar)."""
    recs = [r for r in cl.records if r[1] != RT_HEARTBEAT
            and r[0] >= cl.t0 + after_s]
    if len(recs) < 2:
        return 0.0
    return 1000 * max(recs[i + 1][0] - recs[i][0]
                      for i in range(len(recs) - 1))


def kill_rst(sock: socket.socket) -> None:
    """close with SO_LINGER 0 => a real RST (the abrupt-kill wedge shape)."""
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                    struct.pack("ii", 1, 0))
    sock.close()


# ── slice orchestration helpers (shared by matrix/wedge/browser) ─────────
def wait_health(base: str, timeout: float = 90.0) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib_urlopen(base + "/api/health") as r:
                j = json.loads(r.read())
            if j.get("ok") and j.get("world_booted"):
                return
        except OSError:
            pass
        time.sleep(0.5)
    raise RuntimeError("no health at " + base)


def urllib_urlopen(path: str, timeout: int = 15):
    import urllib.request
    return urllib.request.urlopen(path, timeout=timeout)


def http_get(base: str, path: str, timeout: int = 15) -> bytes:
    with urllib_urlopen(base + path, timeout=timeout) as r:
        return r.read()


def http_post(base: str, path: str, body: bytes = b"{}") -> dict:
    import urllib.request
    req = urllib.request.Request(base + path, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def wait_settled(base: str, timeout: float = 120.0) -> dict:
    t0 = time.time()
    last = None
    st: dict = {}
    while time.time() - t0 < timeout:
        st = json.loads(http_get(base, "/api/status"))["engine_state"]
        if "root_vy" not in st:
            last = None
            time.sleep(0.5)
            continue
        vy, y = abs(float(st["root_vy"])), float(st["root_y"])
        if vy < 1e-5 and last is not None and abs(y - last) < 1e-9:
            return st
        last = y
        time.sleep(0.4)
    return st


def wait_boot_settled(base: str, timeout: float = 240.0) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            st = json.loads(http_get(base, "/api/status"))
            if st.get("scene") and st["scene"].get("settled"):
                return
        except (OSError, KeyError):
            pass
        time.sleep(0.5)
    raise RuntimeError("boot at %s never reached scene.settled" % base)


def wait_engine_alive(base: str, timeout: float = 90.0) -> None:
    """the ENGINE-side wedge gap (recorded, engine untouched): its single
    worker can stall seconds on a half-open connection. Gate every run on a
    live engine state first (the pilot's own pattern)."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            st = json.loads(http_get(base, "/api/status"))["engine_state"]
            if "root_vy" in st:
                return
        except (OSError, KeyError):
            pass
        time.sleep(0.5)
    raise RuntimeError("engine at %s never came back to life" % base)
