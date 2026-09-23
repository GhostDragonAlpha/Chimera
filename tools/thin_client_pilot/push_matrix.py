"""push_matrix.py -- THE RATE/BANDWIDTH MATRIX (lane/push-channel-20260920).

The preregistered minimum set (push_channel_20260920/record.md):

  30 Hz x clients {1,2,4} x fmt {Z12, POS12, FULL36}
  60 Hz x clients {1}    x fmt {Z12, POS12, FULL36}   (P2's honest rows)
  pixel (jpg w=1280 q=85) at pixel_rate 30 x clients {1,4}, 60 x {1}

Per row: N concurrent StreamClients share ONE profile for `--seconds` (20 s
default, first 1 s discarded as ramp), the carry feeder keeps real motion in
the frames, and /api/channel before/after deltas give the SERVER truth
(composed Hz, engine pulls -- the P1 flatness check).

Verdict bars (from the prereg): per-client achieved >= 0.95 x declared
(F1 RATE), per-client wire <= 1.25 MB/s (F4 BW). Reported per row; NOTHING
is tuned.

Usage: python push_matrix.py --out-dir DIR [--seconds 20]
         [--base http://127.0.0.1:PORT] (reuse a running slice)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from push_stream import (StreamClient, http_get, http_post,  # noqa: E402
                         wait_health, wait_settled)

BUDGET_MBPS = 1.25
RATE_BAR = 0.95

# (name, query, clients)
ROWS = [
    ("Z12_30_c1",     "fmt=Z12&rate=30", 1),
    ("Z12_30_c2",     "fmt=Z12&rate=30", 2),
    ("Z12_30_c4",     "fmt=Z12&rate=30", 4),
    ("POS12_30_c1",   "fmt=POS12&rate=30", 1),
    ("POS12_30_c2",   "fmt=POS12&rate=30", 2),
    ("POS12_30_c4",   "fmt=POS12&rate=30", 4),
    ("FULL36_30_c1",  "fmt=FULL36&rate=30", 1),
    ("FULL36_30_c2",  "fmt=FULL36&rate=30", 2),
    ("FULL36_30_c4",  "fmt=FULL36&rate=30", 4),
    ("Z12_60_c1",     "fmt=Z12&rate=60", 1),
    ("POS12_60_c1",   "fmt=POS12&rate=60", 1),
    ("FULL36_60_c1",  "fmt=FULL36&rate=60", 1),
    ("PIXEL_30_c1",   "pixel=1&w=1280&q=85&pixel_rate=30", 1),
    ("PIXEL_30_c4",   "pixel=1&w=1280&q=85&pixel_rate=30", 4),
    ("PIXEL_60_c1",   "pixel=1&w=1280&q=85&pixel_rate=60", 1),
]


def host_port(base: str) -> tuple:
    rest = base.split("://", 1)[1]
    h, p = rest.split(":")
    return h, int(p.split("/")[0])


def channel_snapshot(base: str) -> dict:
    return json.loads(http_get(base, "/api/channel"))


def run_row(base: str, name: str, query: str, clients: int, seconds: float,
            stop_feed: threading.Event) -> dict:
    hp = host_port(base)
    before = channel_snapshot(base)
    cls = [StreamClient(*hp, query) for _ in range(clients)]
    for c in cls:
        c.connect()
    threads: list[threading.Thread] = []

    def run_one(c: StreamClient) -> None:
        try:
            c.pump(seconds)
        except (OSError, RuntimeError) as e:
            c.error = str(e)

    t0 = time.monotonic()
    for c in cls:
        th = threading.Thread(target=run_one, args=(c,))
        th.start()
        threads.append(th)
    for th in threads:
        th.join(timeout=seconds + 30)
    wall = time.monotonic() - t0
    after = channel_snapshot(base)

    # diff the channel's profiles to find THIS row's profile server truth
    def prof_delta(st_before, st_after):
        out = {}
        for k, p2 in st_after["profiles"].items():
            p1 = st_before["profiles"].get(k)
            if p1 is None and p2["clients"] == 0 and p2["composed"] == 0:
                continue
            d = composed = p2["composed"] - (p1["composed"] if p1 else 0)
            pulls = p2["engine_pulls"] - (p1["engine_pulls"] if p1 else 0)
            errs = p2["compose_errors"] - (p1["compose_errors"] if p1 else 0)
            if d > 0 or pulls > 0 or errs > 0:
                out[k] = {"composed_delta": d, "engine_pulls_delta": pulls,
                          "compose_errors_delta": errs,
                          "compose_us_median": p2["compose_us_median"],
                          "compose_us_p95": p2["compose_us_p95"],
                          "compose_us_max": p2["compose_us_max"]}
        return out

    row = {
        "row": name, "query": query, "clients": clients,
        "wall_s": round(wall, 2),
        "window_s": seconds,
        "server_profiles": prof_delta(before, after),
        "server_counters_delta": {
            k: after["counters"][k] - before["counters"][k]
            for k in after["counters"]},
        "clients": {},
        "budget_MBps": BUDGET_MBPS, "rate_bar": RATE_BAR,
    }
    for i, c in enumerate(cls):
        s = c.summary()
        s["holds_rate_bar"] = s["achieved_hz"] >= RATE_BAR * _declared(query)
        s["holds_budget"] = s["wire_MBps"] <= BUDGET_MBPS
        row["clients"]["c%d" % i] = s
    row["all_hold_rate"] = all(c["holds_rate_bar"]
                               for c in row["clients"].values())
    row["all_hold_budget"] = all(c["holds_budget"]
                                 for c in row["clients"].values())
    return row


def _declared(query: str) -> float:
    parts = dict(tok.split("=", 1) for tok in query.split("&"))
    if parts.get("pixel") == "1":
        return float(parts.get("pixel_rate", "30"))
    return float(parts.get("rate", "30"))


def carry_feeder(base: str, stop: threading.Event) -> None:
    """keep real motion in the frames: re-arm the carry every ~4.5 s."""
    while not stop.is_set():
        try:
            http_post(base, "/api/carry_reset")
            http_post(base, "/api/send")
        except OSError:
            pass
        stop.wait(4.5)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--base", default=None)
    ap.add_argument("--seconds", type=float, default=20.0)
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    procs = []
    if a.base:
        base = a.base.rstrip("/")
    else:
        log = open(out / "matrix_slice.log", "wb")
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
                for line in open(out / "matrix_slice.log", encoding="utf-8",
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
    print("matrix against", base, flush=True)

    rows_out: dict = {}
    stop_feed = threading.Event()
    feeder = threading.Thread(target=carry_feeder, args=(base, stop_feed),
                              daemon=True)
    feeder.start()
    try:
        only = set(a.only.split(",")) if a.only else None
        for name, query, clients in ROWS:
            if only and name not in only:
                continue
            print("ROW", name, "...", flush=True)
            row = run_row(base, name, query, clients, a.seconds, stop_feed)
            rows_out[name] = row
            c0 = row["clients"]["c0"]
            print("  c0 %.2f Hz (bar %s) %.3f MB/s (budget %s) gaps %d"
                  % (c0["achieved_hz"], c0["holds_rate_bar"],
                     c0["wire_MBps"], c0["holds_budget"], c0["seq_gaps"]),
                  flush=True)
            (out / "matrix.json").write_text(json.dumps(rows_out, indent=1))
    finally:
        stop_feed.set()
        for p in procs:
            p.terminate()
    (out / "matrix.json").write_text(json.dumps(rows_out, indent=1))
    print("MATRIX-DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
