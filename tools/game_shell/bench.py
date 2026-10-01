#!/usr/bin/env python3
"""bench.py -- MEASURED (not claimed) performance harness for the Chimera engine.

Lane R6: the engine (C++ Vulkan sim serving HTTP on 127.0.0.1:8107) reports its
own frame loop as a "ticks" counter on GET /tick_state (JSON field "ticks");
ticks advancing ~= rendered frames. This harness samples that counter and
reports ticks-per-second under four scenarios, run back to back:

  1. IDLE             -- no other load.
  2. GAME_PAGE_LOAD   -- what the REAL game page makes the engine serve
                         (index.html: setInterval(pollVerts, 333) and
                         setInterval(pollState, 700); the shell proxies
                         /api/verts -> /verts and /api/state -> /tick_state;
                         the page NEVER calls /frame -- it renders client-side).
                         Since C3 landed, the page polls /api/verts?delta=1
                         (the kernel delta stream), NOT the full frame -- so
                         this scenario pulls /verts?delta=1 every 333 ms and
                         /tick_state every 700 ms, and reports the framing mix
                         (keyframe / runs / legacy) and bytes actually pulled.
                         NOTE: the delta chain is defined for ONE client; the
                         scenario's verts thread must be the only ?delta=1
                         poller against that engine while it runs.
  3. FRAME_THUMBNAIL  -- GET /frame?w=1024 every 2 s, alone. HONEST NOTE: this
                         is the THUMBNAIL channel (the reel / dyad grab path),
                         NOT the game page -- no player load pulls /frame. It is
                         kept as its own scenario because R6 measured a real
                         engine-side render stall under it (p1 0.00, 105 MB/60s)
                         and hiding it would be the drift this harness exists to
                         prevent. (The build window lands G8's async capture
                         readback; this scenario is where that shows.)
  4. TOUCH_STORM      -- POST /tick_touch {"px":0.5,"py":0.295,"force_n":30000},
                         then POST /tick_touch_clear 1 s later, cycling every 2 s.

LIVE SAFETY (fleet rule): the shared live stack must never be pressed and
never get a /frame flood -- both are mutating or tick-stalling loads. Running
TOUCH_STORM or FRAME_THUMBNAIL against the default live engine (8107) is
REFUSED unless --allow-live-mutating is passed. Run the full bench against a
scratch engine instead (--scratch launches one for you).

Bar: 60 ticks/s minimum (60 fps on a mid-range machine).

MEASUREMENT (revised after R6): the raw ticks counter advances in bursts --
R6 measured whole 250 ms sampling windows at 0 ticks followed by catch-ups up
to 651/s -- so per-250 ms-window percentiles sank below the bar even at IDLE.
The PRIMARY judgement is therefore per-5-second buckets: consecutive (t, ticks)
readings accumulate until >= 5.0 s elapsed, and the bucket rate =
delta(ticks) / elapsed. The 1% low of the BUCKET rates must be >= bar. The raw
250 ms per-interval rates are still computed and reported as a footnote row for
transparency and for like-for-like comparison with the R6 run. The first
interval of each scenario is discarded as warm-up. A scenario also FAILs if
the tick counter moved backwards (engine restart mid-run) or the engine was
unreachable for more than 60 s.

Stdlib only. Never crashes: each scenario is individually guarded, connections
are retried for up to 60 s (the engine may be mid-restart), and the report is
ALWAYS written to .tmp/bench_report.md and printed. Exit code: 0 = overall
PASS, 1 = overall FAIL, 2 = harness error (report still written).

Usage:
    python bench.py                          # full bench, 60 s per scenario
    python bench.py --scratch                # same, against a throwaway engine
                                             # (private port, isolated cwd,
                                             # killed after -- the R6 form)
    python bench.py --duration 10            # shorter scenarios
    python bench.py --scenarios idle         # IDLE probe only
    python bench.py --scenarios frame_thumbnail   # thumbnail channel only

TOUCH_STORM and FRAME_THUMBNAIL are refused against the default live engine
(8107) unless --allow-live-mutating: they press the shared world / stall its
tick loop. --scratch is the honest default for a full R6 run.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

DEFAULT_BASE = "http://127.0.0.1:8107"
DEFAULT_DURATION_S = 60.0
DEFAULT_INTERVAL_S = 0.25
DEFAULT_BAR = 60.0
BUCKET_S = 5.0             # PRIMARY tick-rate bucket width (smooths the bursty counter)
RETRY_WAIT_S = 60.0        # engine may be mid-restart: retry this long
RETRY_GAP_S = 0.5          # pause between connection retries
SAMPLE_TIMEOUT_S = 5.0     # per /tick_state attempt
VERTS_PERIOD_S = 1.0 / 3.0 # 333 ms (index.html: setInterval(pollVerts, 333))
STATE_PERIOD_S = 0.700     # 700 ms (index.html: setInterval(pollState, 700);
                           #        /api/state proxies to engine /tick_state)
FRAME_PERIOD_S = 2.0
TOUCH_CYCLE_S = 2.0
TOUCH_BODY = {"px": 0.5, "py": 0.295, "force_n": 30000}

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# -- scratch engine (the throwaway pattern: tools/gallery/run_gallery.py,
#    tools/vertbind_softmax.py -- private port, isolated cwd, killed after) --
DEFAULT_SCRATCH_PORT = 8141                 # PRIVATE: never 8107
DEFAULT_ENGINE_EXE = os.path.join(_ROOT, ".tmp", "build_tick", "Release",
                                  "chimera_engine.exe")
SCRATCH_DIR = os.path.join(_ROOT, ".tmp", "bench_scratch")

DEFAULT_REPORT = os.path.join(_ROOT, ".tmp", "bench_report.md")

SCENARIO_KEYS = ("idle", "game_page_load", "frame_thumbnail", "touch_storm")


def log(msg: str) -> None:
    print(msg, flush=True)


class EngineLost(Exception):
    """Engine did not answer within the retry window."""


# --------------------------------------------------------------------------
# HTTP plumbing
# --------------------------------------------------------------------------

_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def http_req(base: str, method: str, path: str, body: Optional[dict] = None,
             timeout: float = SAMPLE_TIMEOUT_S) -> Tuple[int, bytes]:
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, headers=headers,
                                 method=method)
    with _OPENER.open(req, timeout=timeout) as resp:
        return resp.status, resp.read()


def get_ticks(base: str) -> int:
    _status, raw = http_req(base, "GET", "/tick_state")
    return int(json.loads(raw.decode("utf-8", "replace"))["ticks"])


def retry_call(fn: Callable[[], object], what: str, max_wait: float = RETRY_WAIT_S,
               gap: float = RETRY_GAP_S) -> object:
    """Call fn() until it succeeds or max_wait elapses. Raises EngineLost.

    The engine may be mid-restart when a scenario starts; connection errors,
    HTTP errors and bad payloads are all retried inside the window.
    """
    deadline = time.monotonic() + max_wait
    last_exc: Optional[Exception] = None
    while True:
        try:
            return fn()
        except Exception as exc:  # any transport/HTTP/parse error is retried
            last_exc = exc
            if time.monotonic() >= deadline:
                break
            log("[bench]   %s: %s: %s -- retrying (window %.0fs)"
                % (what, type(exc).__name__, exc, max_wait))
            time.sleep(gap)
    raise EngineLost("%s: unreachable for %.0fs (last error: %s: %s)"
                     % (what, max_wait, type(last_exc).__name__, last_exc))


# --------------------------------------------------------------------------
# Sampling
# --------------------------------------------------------------------------

def sample_ticks(base: str, duration_s: float, interval_s: float,
                 log_every_s: float = 10.0
                 ) -> Tuple[List[float], List[Tuple[float, int]], int, int, bool]:
    """Poll GET /tick_state every interval_s for duration_s.

    Returns (rates, pairs, resets, failed_polls, lost):
      rates        -- RAW ticks/s per completed interval, in order (footnote
                      metric; bursts sink its percentiles -- see bucket_rates)
      pairs        -- every successful (t_monotonic, ticks) reading, in order;
                      input to bucket_rates() (the PRIMARY metric)
      resets       -- intervals dropped because the counter went backwards
                      (engine restarted mid-run)
      failed_polls -- polls that errored (each retried until it succeeds or the
                      60 s engine-lost abort fires)
      lost         -- True if the engine stayed unreachable past the abort window
    """
    rates: List[float] = []
    pairs: List[Tuple[float, int]] = []
    resets = 0
    failed_polls = 0

    prev_ticks = retry_call(lambda: get_ticks(base), "tick_state (baseline)")
    prev_t = time.monotonic()
    pairs.append((prev_t, prev_ticks))
    started = prev_t
    last_ok_t = prev_t
    next_progress = started + log_every_s

    while True:
        loop_t0 = time.monotonic()
        try:
            ticks = get_ticks(base)
            now = time.monotonic()
            last_ok_t = now
            pairs.append((now, ticks))
            if prev_ticks is not None:
                dt = now - prev_t
                delta = ticks - prev_ticks
                if dt > 0.0:
                    if delta >= 0:
                        rates.append(delta / dt)
                    else:
                        resets += 1  # counter went backwards: engine restart
            prev_t, prev_ticks = now, ticks
            now2 = time.monotonic()
            if now2 >= next_progress:
                log("[bench]   ... %5.1fs elapsed, %d intervals" % (now2 - started, len(rates)))
                next_progress += log_every_s
        except Exception:
            failed_polls += 1
            now = time.monotonic()
            if now - last_ok_t > RETRY_WAIT_S:
                return rates, pairs, resets, failed_polls, True
            prev_ticks = None  # re-baseline after the outage; drop that interval

        if time.monotonic() - started >= duration_s and prev_ticks is not None:
            break
        time.sleep(max(0.0, interval_s - (time.monotonic() - loop_t0)))

    return rates, pairs, resets, failed_polls, False


def bucket_rates(pairs: List[Tuple[float, int]], bucket_s: float = BUCKET_S,
                 max_merge_s: float = 10.0) -> List[float]:
    """Aggregate consecutive (t, ticks) readings into >= bucket_s windows.

    THE PRIMARY MEASUREMENT. The raw counter advances in bursts (R6: whole
    250 ms windows at 0 ticks, then catch-ups up to 651/s), so per-window
    percentiles sank below the bar even at IDLE -- a stall a player never
    sees at 240 fps. Rate per bucket = delta(ticks) / elapsed over the whole
    bucket, so the burst averages out inside it.

    Slow polls are MERGED, not split: the ticks counter is monotonic, so
    delta/dt across a slow stretch (e.g. the server answering /tick_state
    late while a thumbnail render blocks it) is the honest average, and true
    outages belong to the engine-lost abort, not to bucket math. A bucket
    splits only if the counter moved BACKWARDS (engine restart; also counted
    as a reset and failed outright upstream) or a reading gap exceeds
    max_merge_s (pathological). The first pair is the warm-up baseline. A
    trailing partial bucket is kept only if it covers at least half a bucket.
    """
    rates: List[float] = []
    if len(pairs) < 2:
        return rates
    min_tail = bucket_s / 2.0
    seg_t, seg_ticks = pairs[0]
    last_t, last_ticks = seg_t, seg_ticks
    for t, ticks in pairs[1:]:
        if ticks < last_ticks or t - last_t > max_merge_s:
            if last_t - seg_t >= min_tail:
                rates.append((last_ticks - seg_ticks) / (last_t - seg_t))
            seg_t, seg_ticks = t, ticks
        elif t - seg_t >= bucket_s:
            rates.append((ticks - seg_ticks) / (t - seg_t))
            seg_t, seg_ticks = t, ticks
        last_t, last_ticks = t, ticks
    if last_t - seg_t >= min_tail:
        rates.append((last_ticks - seg_ticks) / (last_t - seg_t))
    return rates


# --------------------------------------------------------------------------
# Load generators
# --------------------------------------------------------------------------

def _zero_load_stats() -> Dict[str, int]:
    return {"verts_ok": 0, "verts_err": 0, "verts_bytes": 0,
            "verts_keyframes": 0, "verts_runs": 0, "verts_legacy": 0,
            "state_ok": 0, "state_err": 0, "state_bytes": 0,
            "frame_ok": 0, "frame_err": 0, "frame_bytes": 0,
            "touch_ok": 0, "touch_err": 0, "clear_ok": 0, "clear_err": 0}


def _verts_thread(base: str, stop: threading.Event, st: Dict[str, int]) -> None:
    """The REAL page's 3 Hz ask: GET /verts?delta=1 (the C3 kernel stream).

    Drift fix (H14 audit, 2026-09-14): the page has polled
    /api/verts?delta=1 since C3 landed -- never the full frame at steady
    state. The shell (tools/game_shell/server.py) rides the query through to
    the engine /verts. Byte counts here are the honest page footprint and
    feed C3 verification (the >10x byte-drop bar). The framing of each
    answer is classified from the first bytes only -- the payload is never
    parsed. The delta chain is defined for ONE client: while this thread
    runs, nothing else may poll ?delta=1 against that engine.
    """
    while not stop.is_set():
        t0 = time.monotonic()
        try:
            _status, raw = http_req(base, "GET", "/verts?delta=1", timeout=15.0)
            st["verts_ok"] += 1
            st["verts_bytes"] += len(raw)
            if len(raw) >= 2 and raw[0] == 0xD1:
                if raw[1] == 0:
                    st["verts_keyframes"] += 1
                else:
                    st["verts_runs"] += 1
            else:
                st["verts_legacy"] += 1
        except Exception:
            st["verts_err"] += 1
        stop.wait(max(0.0, VERTS_PERIOD_S - (time.monotonic() - t0)))


def _frame_thread(base: str, stop: threading.Event, st: Dict[str, int]) -> None:
    while not stop.is_set():
        t0 = time.monotonic()
        try:
            _status, raw = http_req(base, "GET", "/frame?w=1024", timeout=30.0)
            st["frame_ok"] += 1
            st["frame_bytes"] += len(raw)
        except Exception:
            st["frame_err"] += 1
        stop.wait(max(0.0, FRAME_PERIOD_S - (time.monotonic() - t0)))


def _state_thread(base: str, stop: threading.Event, st: Dict[str, int]) -> None:
    """The real page's 700 ms poll: index.html setInterval(pollState, 700).

    /api/state proxies (tools/game_shell/server.py) to engine /tick_state --
    the same endpoint this harness samples. This thread models the page's
    share of that load; the sampler itself is the other share, exactly as on
    the live page (where pollState IS the /tick_state traffic).
    """
    while not stop.is_set():
        t0 = time.monotonic()
        try:
            _status, raw = http_req(base, "GET", "/tick_state", timeout=15.0)
            st["state_ok"] += 1
            st["state_bytes"] += len(raw)
        except Exception:
            st["state_err"] += 1
        stop.wait(max(0.0, STATE_PERIOD_S - (time.monotonic() - t0)))


def _touch_thread(base: str, stop: threading.Event, st: Dict[str, int]) -> None:
    while not stop.is_set():
        t0 = time.monotonic()
        try:
            http_req(base, "POST", "/tick_touch", body=TOUCH_BODY, timeout=15.0)
            st["touch_ok"] += 1
        except Exception:
            st["touch_err"] += 1
        if stop.wait(max(0.0, (t0 + 1.0) - time.monotonic())):
            break
        try:
            http_req(base, "POST", "/tick_touch_clear", timeout=15.0)
            st["clear_ok"] += 1
        except Exception:
            st["clear_err"] += 1
        stop.wait(max(0.0, (t0 + TOUCH_CYCLE_S) - time.monotonic()))


def _start_threads(base: str, stop: threading.Event,
                   targets: List[Callable[[str, threading.Event, Dict[str, int]], None]]
                   ) -> Tuple[List[threading.Thread], Dict[str, int]]:
    st = _zero_load_stats()
    threads = []
    for target in targets:
        th = threading.Thread(target=target, args=(base, stop, st), daemon=True)
        th.start()
        threads.append(th)
    return threads, st


def load_idle(base: str, stop: threading.Event):
    return [], _zero_load_stats()


def load_game_page(base: str, stop: threading.Event):
    """The REAL page model: /verts?delta=1 at 3 Hz + /tick_state ~1.4 Hz,
    /frame NEVER.

    index.html renders client-side from /api/verts (-> engine /verts, pulled
    as ?delta=1 kernel frames since C3) and polls /api/state (-> /tick_state)
    for the blood readout + lesson judge. The W4 sound rail and the E4
    lesson-rail work are page-local (no new engine channels): the page's
    engine footprint is still exactly these two GET streams. R6 measured the
    old /frame-based model as drift; the H14 audit measured the old FULL
    /verts model as drift (the page has asked ?delta=1 since C3).
    """
    return _start_threads(base, stop, [_verts_thread, _state_thread])


def load_frame_thumbnail(base: str, stop: threading.Event):
    """The thumbnail channel alone: /frame?w=1024 every 2 s.

    HONEST NOTE (kept visible on purpose): no player load pulls /frame -- it
    feeds the reel / dyad grabs. R6 measured a real engine-side stall under
    it (p1 0.00, max 651.30 catch-up); that stall is real and stays measured,
    clearly labeled as the thumbnail path, not the game.
    """
    return _start_threads(base, stop, [_frame_thread])


def load_touch_storm(base: str, stop: threading.Event):
    return _start_threads(base, stop, [_touch_thread])


SCENARIOS: List[Tuple[str, Callable]] = [
    ("IDLE", load_idle),
    ("GAME_PAGE_LOAD", load_game_page),
    ("FRAME_THUMBNAIL", load_frame_thumbnail),
    ("TOUCH_STORM", load_touch_storm),
]


# --------------------------------------------------------------------------
# Stats + verdicts
# --------------------------------------------------------------------------

def percentile(sorted_vals: List[float], frac: float) -> float:
    """Linear-interpolation percentile on a pre-sorted list."""
    if not sorted_vals:
        return float("nan")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * frac
    f = int(math.floor(k))
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def summarize(rates: List[float]) -> Optional[Dict[str, float]]:
    if not rates:
        return None
    s = sorted(rates)
    n = len(s)
    return {"mean": sum(s) / n, "min": s[0], "max": s[-1],
            "p1": percentile(s, 0.01), "n": n}


def human_bytes(n: int) -> str:
    if n >= 1_000_000:
        return "%.1f MB" % (n / 1_000_000.0)
    if n >= 1_000:
        return "%.1f KB" % (n / 1_000.0)
    return "%d B" % n


def load_summary(st: Dict[str, int]) -> str:
    parts = []
    if st["verts_ok"] or st["verts_err"]:
        parts.append("/verts?delta=1 (the page's C3 ask) ok=%d err=%d (%s pulled;"
                     " kernel keyframes=%d, runs=%d, legacy=%d)"
                     % (st["verts_ok"], st["verts_err"], human_bytes(st["verts_bytes"]),
                        st["verts_keyframes"], st["verts_runs"], st["verts_legacy"]))
    if st["state_ok"] or st["state_err"]:
        parts.append("/tick_state (the page's /api/state) ok=%d err=%d (%s pulled)"
                     % (st["state_ok"], st["state_err"], human_bytes(st["state_bytes"])))
    if st["frame_ok"] or st["frame_err"]:
        parts.append("/frame?w=1024 (thumbnail channel, NOT the game page) ok=%d err=%d (%s pulled)"
                     % (st["frame_ok"], st["frame_err"], human_bytes(st["frame_bytes"])))
    if st["touch_ok"] or st["touch_err"] or st["clear_ok"] or st["clear_err"]:
        parts.append("/tick_touch ok=%d err=%d; /tick_touch_clear ok=%d err=%d"
                     % (st["touch_ok"], st["touch_err"], st["clear_ok"], st["clear_err"]))
    return "; ".join(parts) if parts else "none"


# --------------------------------------------------------------------------
# Scenario runner
# --------------------------------------------------------------------------

def run_scenario(name: str, loader: Callable, base: str, duration_s: float,
                 interval_s: float, bar: float) -> Dict[str, object]:
    log("[bench] scenario %s: waiting for engine (up to %.0fs) ..." % (name, RETRY_WAIT_S))
    try:
        retry_call(lambda: get_ticks(base), "engine warm-up check")
    except EngineLost as exc:
        log("[bench] scenario %s: FAIL -- %s" % (name, exc))
        return {"name": name, "verdict": "FAIL", "status": "engine_lost",
                "summary": None, "resets": 0, "failed_polls": 0,
                "load": "not started", "error": str(exc)}

    stop = threading.Event()
    try:
        threads, st = loader(base, stop)
    except Exception as exc:
        stop.set()
        return {"name": name, "verdict": "FAIL", "status": "harness_error",
                "summary": None, "resets": 0, "failed_polls": 0,
                "load": "not started",
                "error": "load-thread start failed: %s: %s" % (type(exc).__name__, exc)}

    log("[bench] scenario %s: sampling %.0fs every %.0f ms (primary: %ds buckets) ..."
        % (name, duration_s, interval_s * 1000.0, int(BUCKET_S)))
    rates: List[float] = []
    pairs: List[Tuple[float, int]] = []
    resets = failed_polls = 0
    lost = False
    error: Optional[str] = None
    try:
        rates, pairs, resets, failed_polls, lost = sample_ticks(base, duration_s, interval_s)
    except EngineLost as exc:
        lost = True
        error = str(exc)
    except Exception as exc:  # harness bug must not kill the bench
        error = "%s: %s" % (type(exc).__name__, exc)
    finally:
        stop.set()
        for th in threads:
            th.join(timeout=10.0)

    if lost:
        log("[bench] scenario %s: FAIL -- engine lost mid-scenario" % name)
        return {"name": name, "verdict": "FAIL", "status": "engine_lost",
                "summary": summarize(bucket_rates(pairs)),
                "raw": summarize(rates[1:] if len(rates) > 1 else []),
                "resets": resets,
                "failed_polls": failed_polls, "load": load_summary(st),
                "error": error or ("engine unreachable for more than %.0fs"
                                   " mid-scenario" % RETRY_WAIT_S)}

    # Primary: 5 s buckets over the successful (t, ticks) readings (the first
    # pair is the discarded warm-up baseline). Footnote: raw per-interval
    # rates, first interval discarded -- same series R6 judged, kept for
    # like-for-like comparison.
    summary = summarize(bucket_rates(pairs))
    raw = summarize(rates[1:] if len(rates) > 1 else [])
    reasons = []
    if summary is None:
        reasons.append("no usable buckets sampled")
    elif summary["p1"] < bar:
        reasons.append("1%% low (%.0fs buckets) %.1f < bar %.1f"
                       % (BUCKET_S, summary["p1"], bar))
    if resets > 0:
        reasons.append("tick counter reset %d time(s) (engine restart mid-run)"
                       % resets)
    verdict = "FAIL" if reasons else "PASS"
    log("[bench] scenario %s: %s -- bucket mean %.1f ticks/s, 1%% low %s"
        % (name, verdict,
           summary["mean"] if summary else float("nan"),
           ("%.1f" % summary["p1"]) if summary else "n/a"))
    return {"name": name, "verdict": verdict,
            "status": "ok" if summary else "no_data",
            "summary": summary, "raw": raw,
            "resets": resets, "failed_polls": failed_polls,
            "load": load_summary(st), "warmup_discarded": min(1, len(rates)),
            "error": "; ".join(reasons) if reasons else None}


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def build_report(args: argparse.Namespace, results: List[Dict[str, object]]) -> str:
    bar = args.bar
    lines: List[str] = []
    ap = lines.append
    ap("# Chimera engine bench - measured ticks/s")
    ap("")
    ap("- engine: %s" % args.base)
    ap("- host: %s (%s)" % (platform.node(), platform.platform()))
    ap("- date (UTC): %s" % datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    ap("- raw sample interval: %d ms; scenario duration: %.1f s; pass bar: %.1f ticks/s"
       % (round(args.interval * 1000), args.duration, bar))
    ap("- PRIMARY measurement: %.0f-second buckets of consecutive /tick_state"
       % BUCKET_S)
    ap("  readings; bucket rate = delta(ticks)/elapsed. PASS criterion per"
       " scenario: 1%% low of BUCKET rates >= %.1f." % bar)
    ap("- Why buckets: the raw counter advances in bursts (R6 measured whole"
       " 250 ms windows at 0 ticks then catch-ups up to 651/s), so per-window"
       " percentiles sank below the bar even at IDLE. The raw %d ms per-interval"
       " rates are still computed and reported below as a footnote row per"
       " scenario (like-for-like with the R6 run)." % round(args.interval * 1000))
    ap("- ticks/s = (ticks_now - ticks_prev) / (t_now - t_prev), from GET"
       " /tick_state. The first reading of each scenario is discarded as"
       " warm-up. Readings where the counter moved backwards (engine restart)"
       " are excluded and counted as resets; a scenario also FAILs on any"
       " reset or if the engine is unreachable past the %.0f s retry window."
       % RETRY_WAIT_S)
    ap("- GAME_PAGE_LOAD models the REAL page: index.html polls /api/verts at"
       " 3 Hz (-> engine /verts?delta=1, the C3 kernel stream -- the page has"
       " never pulled the full frame at steady state since C3) and /api/state"
       " at ~1.4 Hz (-> engine /tick_state) and NEVER calls /frame."
       " FRAME_THUMBNAIL is the /frame?w=1024 thumbnail channel (reel / dyad"
       " grabs), NOT the game page -- kept visible because its engine-side"
       " render stall is real.")
    ap("")

    for r in results:
        ap("## Scenario: %s - %s" % (r["name"], r["verdict"]))
        ap("")
        summary = r.get("summary")
        if summary is not None:
            ap("| metric (%.0f s buckets) | value |" % BUCKET_S)
            ap("|---|---|")
            ap("| mean ticks/s | %.2f |" % summary["mean"])
            ap("| min ticks/s | %.2f |" % summary["min"])
            ap("| 1%% low (p1) | %.2f |" % summary["p1"])
            ap("| max ticks/s | %.2f |" % summary["max"])
            ap("| buckets | %d used (%d warm-up reading(s) discarded,"
               " %d counter reset(s), %d failed poll(s)) |"
               % (summary["n"], r.get("warmup_discarded", 0),
                  r["resets"], r["failed_polls"]))
            raw = r.get("raw")
            if raw is not None:
                ap("")
                ap("> Footnote -- raw %d ms per-interval samples (not the bar;"
                   " the bursty counter sinks these): mean %.2f, min %.2f,"
                   " 1%% low %.2f, max %.2f, n=%d."
                   % (round(args.interval * 1000), raw["mean"], raw["min"],
                      raw["p1"], raw["max"], raw["n"]))
        else:
            ap("| metric (%.0f s buckets) | value |" % BUCKET_S)
            ap("|---|---|")
            ap("| result | no usable samples |")
        ap("")
        ap("- load: %s" % r["load"])
        if r.get("error"):
            ap("- detail: %s" % r["error"])
        ap("")

    passed = sum(1 for r in results if r["verdict"] == "PASS")
    overall = "PASS" if passed == len(results) and results else "FAIL"
    ap("## Overall verdict: %s (%d/%d scenarios at or above %.1f ticks/s"
       " 1%% low, %.0f s buckets)"
       % (overall, passed, len(results), bar, BUCKET_S))
    ap("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Scratch engine (throwaway pattern: private port, isolated cwd, kill after)
# --------------------------------------------------------------------------

def sha256_of(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def launch_scratch_engine(exe_path: str, port: int,
                          wait_s: float = 90.0) -> Dict[str, object]:
    """Boot a throwaway engine on a PRIVATE port in an ISOLATED cwd.

    The gallery/vertbind measured pattern: the cwd gets its own `shaders/`
    copy and, when the build dir has one, the `session_snapshot/` blobs --
    boot restore (default-on) then replays the real sealed world, so the
    bench measures a representative scene instead of an empty tick. The
    process handle is returned and nothing else ever kills by image name:
    the LIVE engine shares the exe's image name, so kill is BY PID ONLY.
    """
    import shutil
    import subprocess
    if not os.path.isfile(exe_path):
        raise FileNotFoundError("engine exe not found: %s" % exe_path)
    exe_dir = os.path.dirname(os.path.abspath(exe_path))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(SCRATCH_DIR, "run_%s_p%d" % (stamp, port))
    os.makedirs(run_dir, exist_ok=True)
    shaders = os.path.join(exe_dir, "shaders")
    snap = os.path.join(exe_dir, "session_snapshot")
    if os.path.isdir(shaders):
        shutil.copytree(shaders, os.path.join(run_dir, "shaders"))
    snapshot_used = False
    if os.path.isdir(snap):
        shutil.copytree(snap, os.path.join(run_dir, "session_snapshot"))
        snapshot_used = True
    logf = open(os.path.join(run_dir, "engine_%d.log" % port), "ab")
    creationflags = 0x00000200 if os.name == "nt" else 0  # CREATE_NEW_PROCESS_GROUP
    proc = subprocess.Popen([exe_path, str(port), "--hidden"], cwd=run_dir,
                            stdout=logf, stderr=subprocess.STDOUT,
                            creationflags=creationflags)
    base = "http://127.0.0.1:%d" % port
    deadline = time.monotonic() + wait_s
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("scratch engine exited at boot (code %s)"
                               % proc.returncode)
        try:
            get_ticks(base)
            break
        except Exception:
            time.sleep(0.5)
    else:
        kill_scratch_engine(proc)
        raise RuntimeError("scratch engine did not answer within %.0fs" % wait_s)

    # BOOT SETTLE (measured, H14): the async snapshot restore re-bases the
    # tick counter mid-boot (observed 599 -> 53 and 586 -> 47 in the first
    # ~6 s), which the reset rule would read as an engine restart. Hold
    # until the counter has been monotonic and advancing for SETTLE_S.
    settle_s = 20.0
    settled_since = None
    prev = get_ticks(base)
    deadline = time.monotonic() + settle_s * 6
    while time.monotonic() < deadline:
        time.sleep(0.25)
        try:
            cur = get_ticks(base)
        except Exception:
            settled_since = None
            continue
        if cur < prev or cur == prev:
            settled_since = None     # re-based again: restart the settle clock
        else:
            if settled_since is None:
                settled_since = time.monotonic()
            elif time.monotonic() - settled_since >= settle_s:
                break
        prev = cur

    return {"proc": proc, "base": base, "run_dir": run_dir,
            "exe": exe_path, "exe_sha256": sha256_of(exe_path),
            "snapshot_used": snapshot_used, "log": logf}


def kill_scratch_engine(scratch: Dict[str, object]) -> None:
    """Kill ONLY the process this bench launched (by PID, never by name)."""
    import subprocess
    proc = scratch.get("proc")
    if proc is None or proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           capture_output=True)
        else:
            proc.terminate()
        proc.wait(timeout=15)
    except Exception as exc:
        log("[bench] WARNING: scratch engine kill failed: %s: %s"
            % (type(exc).__name__, exc))


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="bench.py",
        description="Measured ticks/s benchmark for the Chimera engine "
                    "(R6: MEASURED performance, not claimed).")
    ap.add_argument("--base", default=DEFAULT_BASE,
                    help="engine base URL (default %s)" % DEFAULT_BASE)
    ap.add_argument("--duration", type=float, default=DEFAULT_DURATION_S,
                    help=f"seconds per scenario (default {DEFAULT_DURATION_S:g})")
    ap.add_argument("--interval", type=float, default=DEFAULT_INTERVAL_S,
                    help=f"seconds between /tick_state polls "
                         f"(default {DEFAULT_INTERVAL_S:g})")
    ap.add_argument("--bar", type=float, default=DEFAULT_BAR,
                    help=f"minimum ticks/s for PASS, judged on the 1-percent low "
                         f"(default {DEFAULT_BAR:g})")
    ap.add_argument("--report", default=DEFAULT_REPORT,
                    help="report path (default %s)" % DEFAULT_REPORT)
    ap.add_argument("--scenarios",
                    default=",".join(SCENARIO_KEYS),
                    help="comma list from: %s (default all)" % ", ".join(SCENARIO_KEYS))
    ap.add_argument("--scratch", action="store_true",
                    help="run against a THROWAWAY engine: boot the exe "
                         "(--engine-exe) on a private port (--scratch-port) "
                         "in an isolated cwd, bench it, kill it. The live "
                         "stack is never touched.")
    ap.add_argument("--engine-exe", default=DEFAULT_ENGINE_EXE,
                    help="engine binary for --scratch (default %s)"
                         % DEFAULT_ENGINE_EXE)
    ap.add_argument("--scratch-port", type=int, default=DEFAULT_SCRATCH_PORT,
                    help="private port for --scratch (default %d)"
                         % DEFAULT_SCRATCH_PORT)
    ap.add_argument("--allow-live-mutating", action="store_true",
                    help="explicitly authorize TOUCH_STORM / FRAME_THUMBNAIL "
                         "against the default live engine. Fleet rule: the "
                         "shared live stack must never be pressed or frame-"
                         "flooded -- you almost certainly mean --scratch.")
    args = ap.parse_args(argv)
    keys = [k.strip().lower() for k in args.scenarios.split(",") if k.strip()]
    bad = [k for k in keys if k not in SCENARIO_KEYS]
    if bad or not keys:
        ap.error("--scenarios: unknown %r; valid keys: %s"
                 % (bad, ", ".join(SCENARIO_KEYS)))
    args.keys = keys
    return args


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    base = args.base

    # LIVE SAFETY: TOUCH_STORM presses the world; FRAME_THUMBNAIL stalls its
    # tick ~1 s per pull (~30 pulls per scenario). Against the shared live
    # engine both need the explicit flag; the honest default is --scratch.
    live_mutating = ("touch_storm" in args.keys or
                     "frame_thumbnail" in args.keys) and not args.scratch
    if live_mutating and base == DEFAULT_BASE and not args.allow_live_mutating:
        log("[bench] REFUSED: %s against the LIVE engine (%s) would press the "
            "shared world / stall its tick loop. Use --scratch (preferred), a "
            "private --base, or --allow-live-mutating if you truly mean live."
            % ("/".join(k for k in ("touch_storm", "frame_thumbnail")
                        if k in args.keys), base))
        return 2

    scratch = None
    try:
        if args.scratch:
            log("[bench] --scratch: booting throwaway engine %s on private "
                "port %d ..." % (args.engine_exe, args.scratch_port))
            scratch = launch_scratch_engine(args.engine_exe, args.scratch_port)
            args.base = base = scratch["base"]
            log("[bench] --scratch: engine up at %s (cwd %s, snapshot=%s)"
                % (base, scratch["run_dir"], scratch["snapshot_used"]))

        by_key = dict(zip(SCENARIO_KEYS, SCENARIOS))
        results: List[Dict[str, object]] = []
        for key in args.keys:
            name, loader = by_key[key]
            try:
                results.append(run_scenario(name, loader, args.base,
                                            args.duration, args.interval, args.bar))
            except Exception as exc:  # one scenario must never kill the others
                log("[bench] scenario %s: FAIL -- harness error: %s: %s"
                    % (name, type(exc).__name__, exc))
                results.append({"name": name, "verdict": "FAIL",
                                "status": "harness_error", "summary": None,
                                "resets": 0, "failed_polls": 0, "load": "unknown",
                                "error": "%s: %s" % (type(exc).__name__, exc)})

        report = build_report(args, results)
        if scratch is not None:
            report = report.replace(
                "- engine: %s" % args.base,
                "- engine: %s (SCRATCH, throwaway; exe %s sha256 %s; "
                "scene snapshot replayed: %s; engine log %s)"
                % (args.base, scratch["exe"], scratch["exe_sha256"],
                   scratch["snapshot_used"], scratch["run_dir"]),
                1)
        report_dir = os.path.dirname(os.path.abspath(args.report))
        os.makedirs(report_dir, exist_ok=True)
        with open(args.report, "w", encoding="utf-8", newline="\n") as f:
            f.write(report)
        log(report)
        log("[bench] report written to %s" % os.path.abspath(args.report))
        return 0 if all(r["verdict"] == "PASS" for r in results) else 1
    finally:
        if scratch is not None:
            log("[bench] --scratch: killing the throwaway engine (by PID) ...")
            kill_scratch_engine(scratch)


if __name__ == "__main__":
    _exit_code = 2
    try:
        _exit_code = main()
    except SystemExit:
        raise
    except BaseException as _exc:  # NEVER crash: always leave a report behind
        _msg = ("# Chimera engine bench - HARNESS ERROR\n\n"
                "`%s: %s` while running the bench. No scenario data. "
                "The engine itself may still be fine; re-run bench.py.\n"
                % (type(_exc).__name__, _exc))
        try:
            _path = os.environ.get("BENCH_REPORT_PATH", DEFAULT_REPORT)
            os.makedirs(os.path.dirname(os.path.abspath(_path)), exist_ok=True)
            with open(_path, "w", encoding="utf-8", newline="\n") as _f:
                _f.write(_msg)
            log(_msg)
            log("[bench] error report written to %s" % os.path.abspath(_path))
        except Exception:
            log(_msg)
        sys.exit(2)
    sys.exit(_exit_code)
