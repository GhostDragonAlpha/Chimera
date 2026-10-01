#!/usr/bin/env python3
"""verify_g8_capture.py -- G8 arm/collect readback: the AFTER verification bar.

Measures, against a LIVE engine, the two numbers the G8 fix is judged by:

  1. ticks/min  -- the membrane tick counter (GET /tick_state, field "ticks"),
                   sampled as a TRUE mean (last ticks - first ticks) / wall time,
                   in a QUIET window (no /frame traffic) and under a /frame BURST.
                   BAR: burst ticks/min >= quiet ticks/min / 2 (within 2x).
  2. max tick-loop stall during the burst -- the longest span between
                   consecutive /tick_state polls (20 ms cadence) that gained no
                   ticks. BAR: <= 200 ms.

Run it BEFORE the fix (it also documents the BEFORE numbers: the same script
against the synchronous engine reports multi-hundred-ms stalls) and AFTER the
lead's build window. On the pre-G8 binary `?async=1` is an unknown query param
and is ignored, so the script is byte-faithful on both sides of the fix.

Usage:
  python verify_g8_capture.py                 # quiet window + ?async=1 burst
  python verify_g8_capture.py --pull /frame   # burst with the default route
  python verify_g8_capture.py --quiet-only    # just the quiet baseline

Exit code 0 = both bars met, 1 = a bar missed (or --pull burst on the pre-G8
engine, where stalls of ~900 ms per pull are the expected BEFORE evidence).
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def http_get(url: str, timeout: float = 5.0) -> tuple[int, bytes]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


class TickPoller:
    """Samples /tick_state on a fixed cadence; records (t_end, ticks) pairs."""

    def __init__(self, engine: str, interval: float = 0.02) -> None:
        self.engine = engine
        self.interval = interval
        self.samples: list[dict] = []
        self.stop = threading.Event()
        self.thread: threading.Thread | None = None

    def _poll_loop(self) -> None:
        next_t = time.perf_counter()
        while not self.stop.is_set():
            t0 = time.perf_counter()
            try:
                status, body = http_get(self.engine + "/tick_state", timeout=5.0)
                ticks = json.loads(body)["ticks"] if status == 200 else None
            except Exception:
                ticks = None
            t1 = time.perf_counter()
            if ticks is not None:
                self.samples.append({"t": t1, "ticks": ticks})
            next_t += self.interval
            rest = next_t - time.perf_counter()
            if rest > 0:
                time.sleep(rest)

    def start(self) -> None:
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()

    def stop_and_join(self) -> None:
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=5)


def true_ticks_per_min(samples: list[dict]) -> float | None:
    """TRUE mean: total ticks gained / wall time, immune to poll classification."""
    if len(samples) < 2:
        return None
    wall = samples[-1]["t"] - samples[0]["t"]
    gained = samples[-1]["ticks"] - samples[0]["ticks"]
    return (gained / wall * 60.0) if wall > 0 else None


def max_zero_stall_ms(samples: list[dict]) -> float:
    """Longest span between consecutive polls that under-ran the nominal rate.

    Deficit, not zero-delta: a tick-loop freeze makes /tick_state polls QUEUE
    behind a blocking capture on the single-worker HTTP server, so a poll pair
    spanning a 900 ms freeze often GAINS ticks (those the loop made before and
    after the freeze) — a zero-delta check would miss it entirely (measured,
    see verify_g8_before_*.json). The honest stall of a span is
    max(0, dt - dticks/300): every ms the loop under-ran 300 t/s, whatever
    swallowed it (render-thread freeze, or the queue delay a freeze causes).
    """
    nominal = 300.0
    worst = 0.0
    for prev, cur in zip(samples, samples[1:]):
        dt = cur["t"] - prev["t"]
        dticks = cur["ticks"] - prev["ticks"]
        if dticks < 0:
            continue   # counter reset, not a stall
        deficit = dt - dticks / nominal
        if deficit > worst:
            worst = deficit
    return worst * 1000.0


def burst(engine: str, pull_path: str, n_pulls: int, gap_s: float,
          log: list[dict]) -> None:
    """Back-to-back /frame pulls; each request logged with its duration."""
    for i in range(n_pulls):
        t0 = time.perf_counter()
        try:
            status, body = http_get(engine + pull_path, timeout=10.0)
            size = len(body)
        except Exception as e:
            status, size = 0, 0
        t1 = time.perf_counter()
        log.append({"i": i, "t": t0, "dur_s": t1 - t0, "status": status,
                    "bytes": size})
        if gap_s > 0:
            time.sleep(gap_s)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="G8 capture readback verifier")
    ap.add_argument("--engine", default="http://127.0.0.1:8107")
    ap.add_argument("--quiet-s", type=float, default=15.0)
    ap.add_argument("--pull", default="/frame?async=1",
                    help="burst pull path (default: the two-phase route)")
    ap.add_argument("--pulls", type=int, default=10)
    ap.add_argument("--pull-gap", type=float, default=0.0,
                    help="seconds between burst pulls (0 = back-to-back)")
    ap.add_argument("--burst-s", type=float, default=20.0,
                    help="burst-phase wall budget (polling continues this long)")
    ap.add_argument("--quiet-only", action="store_true")
    ap.add_argument("--tag", default="run",
                    help="filename tag for the raw JSON record")
    args = ap.parse_args(argv)

    # Recover the route from MSYS/Git-Bash path conversion: an argv of
    # "C:/Program Files/Git/frame" is the mangled form of "/frame" — keep from
    # the last '/' onward (query string survives), then guarantee one leading '/'.
    raw = args.pull
    if raw.count("/") > 1 or ":\\" in raw:
        raw = raw[raw.rfind("/"):]
    pull_path = raw if raw.startswith("/") else "/" + raw
    args.pull = pull_path

    out: dict = {
        "engine": args.engine,
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "pull_path": None if args.quiet_only else args.pull,
        "bars": {"burst_within_2x_quiet": None, "max_stall_ms_le_200": None},
    }

    # ── phase 1: quiet window ────────────────────────────────────────────────
    poller = TickPoller(args.engine)
    poller.start()
    time.sleep(args.quiet_s)
    poller.stop_and_join()
    quiet = poller.samples
    quiet_tpm = true_ticks_per_min(quiet)
    quiet_stall = max_zero_stall_ms(quiet)
    out["quiet"] = {"samples": len(quiet), "ticks_per_min": quiet_tpm,
                    "max_zero_stall_ms": quiet_stall}
    print(f"quiet: {len(quiet)} polls | ticks/min {quiet_tpm:.0f}"
          if quiet_tpm else "quiet: no usable samples")
    if args.quiet_only:
        fp = Path(__file__).resolve().parent / f"verify_g8_{args.tag}.json"
        fp.write_text(json.dumps(out, indent=1), encoding="utf-8")
        print(f"raw: {fp}")
        return 0 if quiet_tpm else 1

    # ── phase 2: capture burst (poller keeps running through it) ─────────────
    poller = TickPoller(args.engine)
    poller.start()
    time.sleep(1.0)   # warm-up polls so the burst phase has a baseline
    pulls: list[dict] = []
    worker = threading.Thread(target=burst, daemon=True,
                              args=(args.engine, args.pull, args.pulls,
                                    args.pull_gap, pulls))
    t_b0 = time.perf_counter()
    worker.start()
    remaining = args.burst_s - (time.perf_counter() - t_b0)
    if remaining > 0:
        time.sleep(remaining)
    worker.join(timeout=15)
    poller.stop_and_join()
    burst_samples = poller.samples

    burst_tpm = true_ticks_per_min(burst_samples)
    burst_stall = max_zero_stall_ms(burst_samples)
    ok_pulls = [p for p in pulls if p["status"] == 200]
    out["burst"] = {
        "samples": len(burst_samples), "ticks_per_min": burst_tpm,
        "max_zero_stall_ms": burst_stall,
        "pulls": len(pulls), "pulls_ok": len(ok_pulls),
        "pull_durs_ms": [round(p["dur_s"] * 1000) for p in pulls],
    }
    durs = ", ".join(f"{p['dur_s']*1000:.0f}ms/{p['status']}"
                     for p in pulls)
    print(f"burst({args.pull}): {len(ok_pulls)}/{len(pulls)} pulls ok"
          f" | ticks/min {burst_tpm:.0f}" if burst_tpm else
          f"burst: no usable samples | pulls {durs}")
    print(f"pull durations: {durs}")

    # ── the two bars ─────────────────────────────────────────────────────────
    bar_rate = (burst_tpm is not None and quiet_tpm is not None
                and burst_tpm >= quiet_tpm / 2.0)
    bar_stall = burst_stall <= 200.0
    out["bars"] = {"burst_within_2x_quiet": bar_rate,
                   "max_stall_ms_le_200": bar_stall}
    print(f"BAR burst within 2x of quiet: "
          f"{'PASS' if bar_rate else 'FAIL'} "
          f"({burst_tpm:.0f} vs {quiet_tpm:.0f} ticks/min)" if bar_rate else
          f"BAR burst within 2x of quiet: FAIL (no usable samples)")
    print(f"BAR max tick stall <= 200 ms: {'PASS' if bar_stall else 'FAIL'}"
          f" (worst zero-tick poll gap {burst_stall:.0f} ms)")

    fp = Path(__file__).resolve().parent / f"verify_g8_{args.tag}.json"
    fp.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"raw: {fp}")
    return 0 if (bar_rate and bar_stall) else 1


if __name__ == "__main__":
    sys.exit(main())
