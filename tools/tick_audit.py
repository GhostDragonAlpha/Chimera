#!/usr/bin/env python3
"""tick_audit.py -- G8 tick-counter audit: profile the bursty tick counter.

Samples GET /tick_state every --interval seconds (default 0.25) for
--duration seconds, with an optional background /frame load:

  idle       no /frame traffic at all
  frame512   GET /frame?w=512 every --frame-every seconds (default 5)
  framefull  GET /frame (full resolution) every --frame-every seconds

Per-interval ticks/s = (ticks_now - ticks_prev) / (t_now - t_prev), both
sides measured around the poll itself. The first interval is discarded as
warm-up. Intervals where the counter moved backwards are counted as engine
resets (and excluded from the rate series).

Stall windows: intervals with zero tick advance. Consecutive zero windows
are merged into stalls; a stall's duration is reported as the merged span
between the last advancing sample and the next advancing sample (exact,
from the sample timestamps, not n * interval).

Burst windows: intervals above --burst-thresh t/s (default 450 = 1.5x the
300 fps frame cap) -- the catch-up signature.

Raw samples land in .tmp/tick_audit/<scenario>.json next to the analysis,
so the next agent inherits the pathway instead of re-paying for it.

Run:
  python tools/tick_audit.py idle
  python tools/tick_audit.py frame512
  python tools/tick_audit.py framefull
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / ".tmp" / "tick_audit"


def http_get(url: str, timeout: float = 5.0) -> tuple[int, bytes]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def poll_ticks(engine: str) -> tuple[float, int | None]:
    """One /tick_state poll -> (monotonic_end, ticks) or (end, None) on error."""
    t0 = time.perf_counter()
    try:
        status, body = http_get(engine + "/tick_state", timeout=5.0)
    except Exception:
        return time.perf_counter(), None
    t1 = time.perf_counter()
    if status != 200:
        return t1, None
    try:
        return t1, json.loads(body)["ticks"]
    except Exception:
        return t1, None


def frame_puller(engine: str, path: str, every: float, stop: threading.Event,
                 log: list[dict]) -> None:
    """Background /frame traffic; every request logged with timing."""
    # small offset so the first pull does not collide with the warm-up discard
    time.sleep(1.0)
    while not stop.is_set():
        t0 = time.perf_counter()
        try:
            status, body = http_get(engine + path, timeout=10.0)
            size = len(body)
        except Exception as e:
            status, size = 0, 0
            err = repr(e)
        else:
            err = ""
        t1 = time.perf_counter()
        log.append({"t": t0, "dur_s": t1 - t0, "status": status,
                    "bytes": size, "err": err})
        stop.wait(every)


def analyze(samples: list[dict], burst_thresh: float) -> dict:
    """samples: [{t, ticks}] chronological, ticks not None."""
    ivals = []          # per-interval rates
    events = []         # resets
    for prev, cur in zip(samples, samples[1:]):
        dt = cur["t"] - prev["t"]
        dticks = cur["ticks"] - prev["ticks"]
        if dticks < 0:
            events.append({"t": cur["t"], "from": prev["ticks"], "to": cur["ticks"]})
            continue
        ivals.append({"t0": prev["t"], "t1": cur["t"], "dt": dt,
                      "dticks": dticks, "rate": dticks / dt if dt > 0 else 0.0})
    used = ivals[1:]    # discard warm-up
    rates = [i["rate"] for i in used]
    if not rates:
        return {"used": 0}

    # merge consecutive zero-advance intervals into stalls; duration from
    # the last sample inside to the first sample after (exact timestamps)
    stalls = []
    i = 0
    while i < len(used):
        if used[i]["dticks"] == 0:
            j = i
            while j + 1 < len(used) and used[j + 1]["dticks"] == 0:
                j += 1
            # interval i starts at sample[i]'s t0 and the tick that ends the
            # stall lands at used[j+1].t1... conservatively t1 of interval j
            stalls.append({"start": used[i]["t0"], "end": used[j]["t1"],
                           "dur_s": used[j]["t1"] - used[i]["t0"],
                           "windows": j - i + 1})
            i = j + 1
        else:
            i += 1
    bursts = [i for i in used if i["rate"] > burst_thresh]
    rates_sorted = sorted(rates)
    p1 = rates_sorted[max(0, int(round(0.01 * len(rates_sorted))) - 1)]
    return {
        "used": len(used),
        "mean": statistics.mean(rates),
        "median": statistics.median(rates),
        "p1": p1,
        "min": min(rates),
        "max": max(rates),
        "zero_windows": sum(1 for r in rates if r == 0.0),
        "zero_frac": sum(1 for r in rates if r == 0.0) / len(rates),
        "stalls": stalls,
        "stall_total_s": sum(s["dur_s"] for s in stalls),
        "bursts": bursts,
        "burst_windows": len(bursts),
        "resets": events,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="G8 tick counter audit")
    ap.add_argument("scenario", choices=["idle", "frame512", "framefull"])
    ap.add_argument("--engine", default="http://127.0.0.1:8107")
    ap.add_argument("--duration", type=float, default=120.0)
    ap.add_argument("--interval", type=float, default=0.25)
    ap.add_argument("--frame-every", type=float, default=5.0)
    ap.add_argument("--burst-thresh", type=float, default=450.0)
    args = ap.parse_args(argv)

    load_path = {"idle": None,
                 "frame512": "/frame?w=512",
                 "framefull": "/frame"}[args.scenario]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.perf_counter()

    pulls: list[dict] = []
    stop = threading.Event()
    worker = None
    if load_path:
        worker = threading.Thread(target=frame_puller,
                                  args=(args.engine, load_path, args.frame_every,
                                        stop, pulls),
                                  daemon=True)
        worker.start()

    samples: list[dict] = []
    next_t = t_start
    n_err = 0
    while time.perf_counter() - t_start < args.duration:
        t, ticks = poll_ticks(args.engine)
        if ticks is None:
            n_err += 1
        else:
            samples.append({"t": t, "ticks": ticks})
        next_t += args.interval
        rest = next_t - time.perf_counter()
        if rest > 0:
            time.sleep(rest)
    stop.set()
    if worker:
        worker.join(timeout=15)

    res = analyze(samples, args.burst_thresh)
    out = {
        "scenario": args.scenario,
        "engine": args.engine,
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "duration_s": args.duration,
        "interval_s": args.interval,
        "frame_path": load_path,
        "frame_every_s": args.frame_every if load_path else None,
        "poll_errors": n_err,
        "summary": res,
        "frame_pulls": pulls,
        "samples": samples,
    }
    fp = OUT_DIR / f"tick_audit_{args.scenario}.json"
    fp.write_text(json.dumps(out, indent=1), encoding="utf-8")

    # console summary
    print(f"== {args.scenario} == ({args.duration:.0f}s, {args.interval*1000:.0f} ms"
          f" polling, load={load_path or 'none'})")
    print(f"raw: {fp}")
    if res.get("used", 0) == 0:
        print("no usable intervals")
        return 1
    print(f"mean {res['mean']:.2f} t/s | median {res['median']:.2f} | p1 {res['p1']:.2f}"
          f" | min {res['min']:.2f} | max {res['max']:.2f}")
    print(f"zero-tick windows: {res['zero_windows']}/{res['used']}"
          f" ({res['zero_frac']*100:.1f}%) | burst(>{args.burst_thresh:.0f}) windows:"
          f" {res['burst_windows']} | resets: {len(res['resets'])}"
          f" | poll errors: {n_err}")
    print(f"stalls (merged 0-advance spans): {len(res['stalls'])}"
          f", total {res['stall_total_s']:.2f} s")
    for s in res["stalls"]:
        print(f"  stall {s['dur_s']*1000:.0f} ms ({s['windows']} windows) at +{s['start']-t_start:.1f}s")
    if pulls:
        ok = [p for p in pulls if p["status"] == 200]
        durs = sorted(p["dur_s"] for p in ok)
        print(f"/frame pulls: {len(ok)}/{len(pulls)} ok"
              + (f" | dur min {durs[0]*1000:.0f} ms, median {durs[len(durs)//2]*1000:.0f} ms,"
                 f" max {durs[-1]*1000:.0f} ms, total {sum(durs):.2f} s" if durs else ""))
        # overlap: stall spans containing a pull
        for s in res["stalls"]:
            inside = [p for p in pulls
                      if p["t"] >= s["start"] - 0.3 and p["t"] <= s["end"] + 0.3]
            if inside:
                print(f"  stall at +{s['start']-t_start:.1f}s overlaps"
                      f" {len(inside)} pull(s):"
                      + ", ".join(f"{p['dur_s']*1000:.0f} ms/{p['status']}" for p in inside))
    return 0


if __name__ == "__main__":
    sys.exit(main())
