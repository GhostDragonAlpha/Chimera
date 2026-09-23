"""push_wedge.py -- THE WEDGE TEST (lane/push-channel-20260920, falsifier F3).

The pilot's banked finding: a half-open connection wedged the ENGINE's
single HTTP worker (no recv deadline -- engine-side, recorded). This test
proves the push server does NOT re-create the class:

  t=0    3 harness clients subscribe Z12@30 (read normally)
  t=5    client W attaches and NEVER READS (socket open, GET sent) -- the
         stopped-reader shape; its send buffer fills, then the server's
         send timeout must drop it (W1) while the broadcaster OVERWRITES
         its mailbox (W2: skip-toward-newest, counted)
  t=10   client K connects then is KILLED with SO_LINGER(0) => real RST --
         must surface as a write error within one heartbeat cycle (W3)
  t=20   window closes

Verdict bars (prereg P4/F3):
  - every live client's post-wedge achieved rate >= 0.95 x 30 Hz
  - no live client's max inter-record gap (post-wedge) > 200 ms
  - server drops W within 5 s of attach, K within 2 s of the kill
All numbers reported; nothing tuned.

Usage: python push_wedge.py --out-dir DIR [--base http://...] [--quick 8]
"""
from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from push_stream import (StreamClient, host_port, http_get,  # noqa: E402
                         kill_rst, wait_health, wait_settled)

RATE = 30.0
RATE_BAR = 0.95
GAP_BAR_MS = 200.0
W_DEADLINE_S = 5.0
K_DEADLINE_S = 2.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--base", default=None)
    ap.add_argument("--window", type=float, default=20.0)
    ap.add_argument("--wedge-at", type=float, default=5.0)
    ap.add_argument("--kill-at", type=float, default=10.0)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    procs = []
    if a.base:
        base = a.base.rstrip("/")
    else:
        log = open(out / "wedge_slice.log", "wb")
        p = subprocess.Popen(
            [sys.executable, "-u", str(HERE / "boot_slice.py"), "--port", "0",
             "--engine-exe",
             "E:/ChimeraWork/thincli-agent/.tmp/slice_build/Release/chimera_engine.exe"],
            stdout=log, stderr=subprocess.STDOUT,
            cwd=str(HERE.parent.parent),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        procs.append(p)
        port = None
        t0 = time.time()
        while time.time() - t0 < 90 and not port:
            try:
                for line in open(out / "wedge_slice.log", encoding="utf-8",
                                 errors="replace"):
                    if line.startswith("slice: http://"):
                        port = int(line.strip().rsplit(":", 1)[1].split("/")[0])
            except OSError:
                pass
            time.sleep(0.5)
        assert port, "slice port not found"
        base = "http://127.0.0.1:%d" % port
    wait_health(base)
    wait_settled(base)
    hp = host_port(base)
    print("wedge against", base, flush=True)

    result: dict = {"window_s": a.window, "wedge_at": a.wedge_at,
                    "kill_at": a.kill_at, "rate": RATE,
                    "rate_bar": RATE_BAR, "gap_bar_ms": GAP_BAR_MS}
    readers = {n: StreamClient(*hp, "fmt=Z12&rate=%d" % int(RATE))
               for n in ("C1", "C2", "C3")}
    for c in readers.values():
        c.connect()
    threads: list[threading.Thread] = []
    for c in readers.values():
        th = threading.Thread(target=c.pump, args=(a.window,))
        th.start()
        threads.append(th)

    t_start = time.monotonic()
    wedge_sock: socket.socket | None = None
    kill_sock: socket.socket | None = None
    t_wedge = t_kill = None            # WALL clocks (server drops carry
    t_wedge_wall = t_kill_wall = None  # time.time(); same host, comparable)
    try:
        while time.monotonic() - t_start < a.window:
            now = time.monotonic() - t_start
            if now >= a.wedge_at and wedge_sock is None:
                # THE STOPPED READER: GET sent, then reads nothing, ever.
                s = socket.create_connection(hp, timeout=10)
                s.sendall(("GET /api/stream?fmt=Z12&rate=%d HTTP/1.1\r\n"
                           "Host: wedge\r\n\r\n" % int(RATE)).encode())
                wedge_sock = s
                t_wedge = time.monotonic()
                t_wedge_wall = time.time()
                print("W attached (never reads)", flush=True)
            if now >= a.kill_at and kill_sock is None:
                k = socket.create_connection(hp, timeout=10)
                k.sendall(("GET /api/stream?fmt=Z12&rate=%d HTTP/1.1\r\n"
                           "Host: kill\r\n\r\n" % int(RATE)).encode())
                time.sleep(0.5)         # let it subscribe+receive first
                kill_rst(k)             # the abrupt kill (real RST)
                t_kill = time.monotonic()
                t_kill_wall = time.time()
                kill_sock = k
                print("K killed (RST)", flush=True)
            time.sleep(0.05)
    finally:
        for th in threads:
            th.join(timeout=a.window + 30)
        if wedge_sock:
            try:
                wedge_sock.close()
            except OSError:
                pass

    # ── verdicts ─────────────────────────────────────────────────────────
    clients = {}
    for n, c in readers.items():
        s = c.summary(drop_ramp_s=1.0)
        post = [r for r in c.records if r[0] >= c.t0 + a.wedge_at + 1.0]
        span = post[-1][0] - post[0][0] if len(post) >= 2 else 0.0
        post_hz = (len(post) - 1) / span if span > 0 else 0.0
        gaps = [1000 * (post[i + 1][0] - post[i][0])
                for i in range(len(post) - 1)]
        s["post_wedge_hz"] = round(post_hz, 3)
        s["post_wedge_holds_bar"] = post_hz >= RATE_BAR * RATE
        s["post_wedge_max_gap_ms"] = round(max(gaps), 2) if gaps else 0.0
        s["post_wedge_gap_ok"] = (s["post_wedge_max_gap_ms"] <= GAP_BAR_MS)
        clients[n] = s
        print("%s post-wedge %.2f Hz (bar %s) max gap %.1f ms (ok %s)"
              % (n, post_hz, s["post_wedge_holds_bar"],
                 s["post_wedge_max_gap_ms"], s["post_wedge_gap_ok"]),
              flush=True)

    ch = json.loads(http_get(base, "/api/channel"))
    drops = ch["drops_tail"]
    # correlate by WALL time: server drop t (time.time) vs local markers.
    # W: first Z12-profile drop after the wedge attach. K: first drop after
    # the kill whose open_s <= 2 s (the killed client lived ~0.5 s; W lives
    # much longer and is excluded by that bar).
    w_drop = next((d for d in drops if t_wedge_wall and
                   d["profile"].startswith("state_Z12") and
                   d["t"] >= t_wedge_wall - 0.5), None)
    k_drop = next((d for d in drops if t_kill_wall and
                   d["profile"].startswith("state_Z12") and
                   d["t"] >= t_kill_wall - 0.5 and
                   d["open_s"] <= 2.0), None)
    result["wedge_drop"] = {
        "found": w_drop is not None,
        "reason": w_drop["reason"] if w_drop else None,
        "dropped_after_s": round(w_drop["t"] - t_wedge_wall, 3)
                           if w_drop and t_wedge_wall else None,
        "skipped_frames": w_drop["skipped"] if w_drop else None,
        "deadline_s": W_DEADLINE_S,
        "holds": bool(w_drop and t_wedge_wall and
                      w_drop["t"] - t_wedge_wall <= W_DEADLINE_S),
    } if t_wedge_wall else {"found": False, "holds": False}
    result["kill_drop"] = {
        "found": k_drop is not None,
        "reason": k_drop["reason"] if k_drop else None,
        "dropped_after_s": round(k_drop["t"] - t_kill_wall, 3)
                           if k_drop and t_kill_wall else None,
        "deadline_s": K_DEADLINE_S,
        "holds": bool(k_drop and t_kill_wall and
                      k_drop["t"] - t_kill_wall <= K_DEADLINE_S),
    } if t_kill_wall else {"found": False, "holds": False}
    result["clients"] = clients
    result["drops_timeline"] = drops
    result["F3_verdict"] = {
        "rate_holds": all(c["post_wedge_holds_bar"] for c in clients.values()),
        "gaps_hold": all(c["post_wedge_gap_ok"] for c in clients.values()),
        "wedge_dropped_in_time": result["wedge_drop"]["holds"],
        "kill_dropped_in_time": result["kill_drop"]["holds"],
    }
    result["F3_verdict"]["no_wedge_fail"] = all(
        result["F3_verdict"].values())
    (out / "wedge.json").write_text(json.dumps(result, indent=1))
    print("F3 verdict:", json.dumps(result["F3_verdict"]), flush=True)
    for p in procs:
        p.terminate()
    print("WEDGE-DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
