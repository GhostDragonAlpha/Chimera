"""push_channel.py -- THE PUSH CHANNEL (lane/push-channel-20260920).

THE E2 FIX, Python-side: replaces client polling with server push. The
transport derivation is preregistered in
tools/science_funnel/validation/push_channel_20260920/record.md; in short:

  SSE's text envelope falsifies itself on the pilot's own numbers (base64
  4/3 inflation pushes the 1.0 MB/s pixel winner to 1.33 > 1.25 budget), and
  WebSocket has no stdlib server (hand-rolled RFC 6455 re-creates the exact
  framing-bug class the pilot measured on DELTA). CHOSEN: the SSE
  ARCHITECTURE over a binary HTTP body -- one long-lived GET whose response
  never ends, carrying server-paced length-prefixed records. Zero payload
  inflation, stdlib-only, proxy-transparent, and the framing IS the
  per-frame integrity instrument (the THS1 snapshot inside carries its own
  magic; the record envelope carries len+seq).

THE WEDGE LAWS (the pilot measured the ENGINE wedging on half-open
connections with no recv deadline; this server does not re-create the class):
  W1 every client write runs under a socket send timeout (SEND_TIMEOUT_S);
     a client that stops reading is DROPPED, its thread never blocks forever.
  W2 a slow/stalled client's mailbox is LATEST-WINS: the broadcaster
     OVERWRITES an undelivered frame instead of queueing -- graceful
     degradation is structural (drop toward the newest frame), never a
     bounded-queue flood.
  W3 HEARTBEAT records at HEARTBEAT_S keep idle links observed; a killed
     client surfaces as a write error within one heartbeat cycle.
  W4 TCP keepalive is armed so a silently-dead peer is reaped by the OS too.

THE ENGINE-LOAD LAW (P1): ONE broadcaster thread per stream PROFILE (fmt,
rate, pixel params) composes ONE snapshot per tick -- engine pulls scale with
PROFILES, not clients. Per-client cost is a socket write of the newest frame.

E3 boundary: DELTA is not offered (the engine's C3 chain is single-client);
the stream serves the stateless family + PIXEL. E1 note: ts is composed
exactly as /api/snapshot composes it (verts pull then state pull, gap_us in
the THS1 header); /frame has NO in-band ts (E1) so PIXEL records carry the
tick_state pulled right after the frame (gap named here, honest).

Wire format (per record, little-endian):
    u32 payload_len | u16 rtype | u16 flags | u32 seq | u64 ts_us | payload
    rtype 1 SNAPSHOT (payload byte-identical to /api/snapshot: THS1+verts)
          2 PIXEL    (payload = engine /frame bytes as served: JPEG/PNG)
          3 HEARTBEAT (payload = u64 server perf_counter us)
    flags bit0 = keyframe (every SNAPSHOT is one; the stream never needs
    a resync pull -- a mid-stream join just waits one tick).

Run:  python tools/playable_slice/slice_server.py [--port N]   (routes added:
      GET /api/stream?fmt=&rate= | ?pixel=1&w=&q=&pixel_rate= ; GET /api/channel)
"""
from __future__ import annotations

import struct
import sys
import threading
import time
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import scene_boot as sb  # noqa: E402

# ── the stated constants (each serves a named falsifier) ─────────────────
SEND_TIMEOUT_S = 2.0     # F3 WEDGE: a stopped reader is dropped <= 5 s
HEARTBEAT_S = 1.0        # F3 WEDGE: a killed client surfaces <= 2 s
IDLE_GRACE_S = 5.0       # broadcaster lingers this long after its last client
ENGINE_PULL_TIMEOUT_S = 4.0   # a hung engine pull must not wedge the
                         # broadcaster (the blocking routes keep their own)
REC_HDR = "<IHHIQ"       # u32 len | u16 rtype | u16 flags | u32 seq | u64 ts
REC_HDR_SIZE = struct.calcsize(REC_HDR)          # 20
RT_SNAPSHOT = 1
RT_PIXEL = 2
RT_HEARTBEAT = 3
FLAG_KEYFRAME = 1
MAX_RECORD_B = 64 * 1024 * 1024   # framing sanity bar (client-side guard too)

STATE_FMTS = ("FULL36", "POS12", "POS16", "Z12")   # DELTA excluded: E3


def pack_record(rtype: int, flags: int, seq: int, ts_us: int,
                payload: bytes) -> bytes:
    return struct.pack(REC_HDR, len(payload), rtype, flags, seq, ts_us) + payload


class Subscriber:
    """One client connection's mailbox (W2: latest-wins, never a queue)."""

    def __init__(self) -> None:
        self.mu = threading.Lock()
        self.slot: bytes | None = None
        self.pending = False
        self.ev = threading.Event()
        self.skipped = 0          # frames overwritten before delivery
        self.delivered = 0
        self.opened = time.time()

    def offer(self, rec: bytes) -> None:
        with self.mu:
            if self.pending:
                self.skipped += 1     # the newest frame wins; the displaced
                                      # one is counted, never queued (W2)
            self.slot = rec
            self.pending = True
            self.ev.set()

    def take(self, timeout: float) -> bytes | None:
        got = self.ev.wait(timeout)
        with self.mu:
            rec, self.slot, self.pending = self.slot, None, False
            self.ev.clear()
        return rec if (got and rec is not None) else None


class Profile:
    """One (kind, fmt, rate, w, q, pixel_rate) composition + its fan-out."""

    def __init__(self, key: tuple, world) -> None:
        self.key = key                 # (kind, fmt, rate, w, q, pixel_rate)
        self.kind = key[0]             # 'state' | 'pixel'
        self.world = world
        self.mu = threading.Lock()
        self.subs: list[Subscriber] = []
        self.seq = 0
        self.composed = 0
        self.engine_pulls = 0
        self.compose_errors = 0
        self.last_compose_us = 0
        self.compose_us_hist: deque = deque(maxlen=512)
        self.started = time.time()
        self.last_client_seen = time.time()
        self.stop = threading.Event()
        self.thread: threading.Thread | None = None

    # ── fan-out (W2) ─────────────────────────────────────────────────────
    def subscribe(self) -> Subscriber:
        sub = Subscriber()
        with self.mu:
            self.subs.append(sub)
            self.last_client_seen = time.time()
            if self.thread is None or not self.thread.is_alive():
                self.stop.clear()
                self.thread = threading.Thread(
                    target=self._run, daemon=True,
                    name="push-bcast-%s" % "_".join(map(str, self.key)))
                self.thread.start()
        return sub

    def unsubscribe(self, sub: Subscriber) -> None:
        with self.mu:
            if sub in self.subs:
                self.subs.remove(sub)
            self.last_client_seen = time.time()

    def _broadcast(self, rec: bytes) -> None:
        with self.mu:
            subs = list(self.subs)
        for s in subs:
            s.offer(rec)

    # ── composition (ONE per tick for EVERY client of this profile) ──────
    def _compose(self) -> bytes | None:
        w = self.world
        t0 = time.perf_counter()
        try:
            if self.kind == "state":
                snap, _fmt, _n = w.snapshot(self.key[1],
                                            timeout=ENGINE_PULL_TIMEOUT_S)
                self.engine_pulls += 2
                ts_us = struct.unpack_from("<Q", snap, 4)[0]
                rec = pack_record(RT_SNAPSHOT, FLAG_KEYFRAME, 0, ts_us, snap)
            else:
                _kind, _fmt, _rate, width, qual, _prate = self.key
                raw = sb.http_get_raw(
                    w.url, "/frame?w=%d&fmt=jpg&q=%d" % (width, qual),
                    timeout=ENGINE_PULL_TIMEOUT_S)
                self.engine_pulls += 1
                st = w.tick_state(timeout=ENGINE_PULL_TIMEOUT_S)
                self.engine_pulls += 1
                ts_us = int(st.get("ts_us", 0))
                # E1 honesty: /frame carries no in-band ts; this ts postdates
                # the frame by the pull gap -- named in the prereg.
                rec = pack_record(RT_PIXEL, FLAG_KEYFRAME, 0, ts_us, raw)
        except OSError:
            self.compose_errors += 1
            return None
        self.last_compose_us = int((time.perf_counter() - t0) * 1e6)
        self.compose_us_hist.append(self.last_compose_us)
        with self.mu:
            self.seq += 1
            self.composed += 1
            seq = self.seq
        return rec[:8] + struct.pack("<I", seq) + rec[12:]   # stamp the seq

    def _run(self) -> None:
        kind, _fmt, rate, _w, _q, prate = self.key
        hz = rate if self.kind == "state" else prate
        period = 1.0 / hz if hz > 0 else 1.0
        next_t = time.perf_counter()
        while not self.stop.is_set():
            with self.mu:
                alive = len(self.subs)
            if alive == 0 and \
                    time.time() - self.last_client_seen > IDLE_GRACE_S:
                break
            now = time.perf_counter()
            if now < next_t:
                time.sleep(min(next_t - now, 0.002))
                continue
            next_t = max(next_t + period, now + 0.001)
            rec = self._compose()
            if rec is not None:
                self._broadcast(rec)
        with self.mu:
            self.thread = None


class Channel:
    """The profile registry + channel-wide counters (the /api/channel truth)."""

    def __init__(self, world) -> None:
        self.world = world
        self.mu = threading.Lock()
        self.profiles: dict[tuple, Profile] = {}
        self.drops: list[dict] = []          # the timeline (wedge evidence)
        self.counters = {"connections": 0, "drops_send_timeout": 0,
                         "drops_broken": 0, "bytes_sent": 0,
                         "records_sent": 0, "heartbeat_sent": 0}

    def profile(self, key: tuple) -> Profile:
        with self.mu:
            p = self.profiles.get(key)
            if p is None:
                p = Profile(key, self.world)
                self.profiles[key] = p
            return p

    def gc_profiles(self) -> None:
        with self.mu:
            dead = [k for k, p in self.profiles.items()
                    if (p.thread is None or not p.thread.is_alive())
                    and not p.subs]
            for k in dead:
                del self.profiles[k]

    def note_drop(self, reason: str, sub: Subscriber, profile_key: tuple) -> None:
        with self.mu:
            self.drops.append({
                "t": time.time(), "reason": reason,
                "profile": "_".join(map(str, profile_key)),
                "delivered": sub.delivered, "skipped": sub.skipped,
                "open_s": round(time.time() - sub.opened, 3)})
            if len(self.drops) > 256:
                del self.drops[:len(self.drops) - 256]

    def note(self, counter: str, n: int = 1) -> None:
        with self.mu:
            self.counters[counter] = self.counters.get(counter, 0) + n

    def stats(self) -> dict:
        with self.mu:
            out = {"counters": dict(self.counters),
                   "drops_tail": list(self.drops[-32:]), "profiles": {}}
            profiles = list(self.profiles.items())
        for key, p in profiles:
            h = sorted(p.compose_us_hist) if p.compose_us_hist else [0]
            with p.mu:
                n_subs = len(p.subs)
            out["profiles"]["_".join(map(str, key))] = {
                "kind": p.kind, "fmt": key[1], "rate": key[2],
                "clients": n_subs, "seq": p.seq,
                "composed": p.composed,
                "engine_pulls": p.engine_pulls,
                "compose_errors": p.compose_errors,
                "compose_us_median": h[len(h) // 2],
                "compose_us_p95": h[min(len(h) - 1, int(0.95 * len(h)))],
                "compose_us_max": h[-1],
                "age_s": round(time.time() - p.started, 1)}
        return out


# ── the stream endpooint (runs INSIDE the client's own handler thread) ───
def parse_stream_query(query: str):
    """-> (key, error_json_or_None). key = (kind, fmt, rate, w, q, pixel_rate)."""
    params: dict[str, str] = {}
    for tok in query.split("&"):
        if "=" in tok:
            k, v = tok.split("=", 1)
            params[k.lower()] = v
    if params.get("pixel") in ("1", "true"):
        w = int(params.get("w", "1280"))
        q = int(params.get("q", "85"))
        prate = int(params.get("pixel_rate", "30"))
        if prate <= 0 or prate > 240 or w <= 0 or not (1 <= q <= 100):
            return None, {"error": "bad pixel params"}
        return ("pixel", "NONE", 0, w, q, prate), None
    fmt = params.get("fmt", "FULL36").upper()
    if fmt not in STATE_FMTS:
        return None, {"error": "fmt not offered on the stream (DELTA is "
                               "single-client by engine design: gap E3)"}
    try:
        rate = int(params.get("rate", "30"))
    except ValueError:
        return None, {"error": "bad rate"}
    if rate <= 0 or rate > 240:
        return None, {"error": "bad rate"}
    return ("state", fmt, rate, 0, 0, 0), None


def serve_stream(handler, world, channel: Channel, query: str) -> None:
    """The long-lived GET. Runs in the client's OWN thread (the slice server
    is a ThreadingHTTPServer): parse -> subscribe -> write loop -> drop."""
    import socket as _socket
    key, err = parse_stream_query(query)
    if err is not None:
        body = repr(err).encode()
        handler.send_response(400)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
        return
    prof = channel.profile(key)
    sub = prof.subscribe()
    channel.note("connections")
    drop_reason = "client_close"
    try:
        handler.send_response(200)
        handler.send_header("Content-Type", "application/octet-stream")
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Connection", "close")
        handler.end_headers()
        sock = handler.connection
        sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_KEEPALIVE, 1)   # W4
        # W1 (the wedge deadline math): a stopped reader is detected only
        # once the send buffer FILLS (fill_s = buf/wire) plus SEND_TIMEOUT_S.
        # The default ~64-256 KB of OS buffering at the slowest stream's
        # wire (Z12 ~37 KB/s) puts that past the prereg's 5 s deadline
        # (measured 6.8 s). Bounding SNDBUF to 64 KB makes fill <= 1.8 s at
        # ANY state-format wire, so drop <= ~3.8 s. This is per-connection
        # memory too: a slow client can hold at most one buffer + one frame.
        sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_SNDBUF, 65536)
        try:
            sock.ioctl(_socket.SIO_KEEPALIVE_VALS, (1, 2000, 1000))
        except (OSError, AttributeError, ValueError):
            pass                        # non-Windows / unsupported: W1+W3 cover
        sock.settimeout(SEND_TIMEOUT_S)                                  # W1
        last_write = time.time()
        while True:
            rec = sub.take(timeout=HEARTBEAT_S)
            if rec is None:
                now = time.time()
                if now - last_write >= HEARTBEAT_S:                    # W3
                    payload = struct.pack(
                        "<Q", int(time.perf_counter() * 1e6))
                    rec = pack_record(RT_HEARTBEAT, 0, 0, 0, payload)
                    handler.wfile.write(rec)
                    channel.note("heartbeat_sent")
                    channel.note("bytes_sent", len(rec))
                    last_write = now
                continue
            handler.wfile.write(rec)
            sub.delivered += 1
            channel.note("records_sent")
            channel.note("bytes_sent", len(rec))
            last_write = time.time()
    except TimeoutError:                                            # W1
        drop_reason = "send_timeout"
        channel.note("drops_send_timeout")
    except (ConnectionError, BrokenPipeError, OSError):
        drop_reason = "broken"
        channel.note("drops_broken")
    finally:
        try:
            handler.wfile.flush()
        except OSError:
            pass
        channel.note_drop(drop_reason, sub, key)
        prof.unsubscribe(sub)
        channel.gc_profiles()
