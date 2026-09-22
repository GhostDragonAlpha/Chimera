"""run_suite.py -- THE COUPLED MEASUREMENT SUITE (lane/thin-client-pilot-20260920).

Boots the declared slice (A, the client's world) and a byte-identical TWIN
(B, the truth recorder's world), then runs the preregistered matrix:

  bandwidth: harness-paced pulls per fmt x rate while the carry moves
  visual:    browser client runs (rates x formats x traces) over the fall,
             the carry, and the press, each with a twin-truth recording
  latency:   press-event visible latency + render frame time per trace
  F5:        the replay pipeline run twice on identical bytes

Everything lands in --out-dir as JSON + PNG stills. No eyeballs anywhere.

Usage: python run_suite.py --out-dir E:/ChimeraWork/thincli-agent/.tmp/suite [--only name,name]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable

TRACES = {
    "TRACE-CLEAN": {"delay": 0, "jitter": 0, "tail": 0},
    "TRACE-50": {"delay": 50, "jitter": 0, "tail": 0},
    "TRACE-50J": {"delay": 50, "jitter": 20, "tail": 0},
    "TRACE-TAIL": {"delay": 50, "jitter": 20, "tail": 200},
}

# name, scenario, rate, fmt, trace, jhead_ms
RUNS = [
    ("R01_fall_30_full",     "FALL",  30, "FULL36", "TRACE-CLEAN", 0),
    ("R02_fall_15_full",     "FALL",  15, "FULL36", "TRACE-CLEAN", 0),
    ("R03_fall_10_full",     "FALL",  10, "FULL36", "TRACE-CLEAN", 0),
    ("R04_fall_60_full",     "FALL",  60, "FULL36", "TRACE-CLEAN", 0),
    ("R05_fall_30_tr50",     "FALL",  30, "FULL36", "TRACE-50",    0),
    ("R06_fall_30_tr50j",    "FALL",  30, "FULL36", "TRACE-50J",  25),
    ("R07_fall_30_tail",     "FALL",  30, "FULL36", "TRACE-TAIL", 25),
    ("R08_fall_30_pos12",    "FALL",  30, "POS12",  "TRACE-CLEAN", 0),
    ("R09_fall_30_pos16",    "FALL",  30, "POS16",  "TRACE-CLEAN", 0),
    ("R10_fall_30_z12",      "FALL",  30, "Z12",    "TRACE-CLEAN", 0),
    ("R11_fall_30_delta",    "FALL",  30, "DELTA",  "TRACE-CLEAN", 0),
    ("R12_carry_30_full",    "CARRY", 30, "FULL36", "TRACE-CLEAN", 0),
    ("R13_press_30_full",    "PRESS", 30, "FULL36", "TRACE-CLEAN", 0),
]

BANDWIDTH_FMTS = ["FULL36", "POS12", "POS16", "Z12", "DELTA"]
BANDWIDTH_RATES = [60, 30, 15, 10]


def http_get(base: str, path: str, timeout: int = 15) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


def http_post(base: str, path: str, body: bytes = b"{}") -> dict:
    req = urllib.request.Request(base + path, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def wait_health(base: str, timeout: float = 90.0) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            j = json.loads(http_get(base, "/api/health"))
            if j.get("ok") and j.get("world_booted"):
                return
        except OSError:
            pass
        time.sleep(1.0)
    raise RuntimeError(f"no health at {base}")


def wait_settled(base: str, timeout: float = 120.0) -> dict:
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        st = json.loads(http_get(base, "/api/status"))["engine_state"]
        vy, y = abs(float(st["root_vy"])), float(st["root_y"])
        if vy < 1e-5 and last is not None and abs(y - last) < 1e-9:
            return st
        last = y
        time.sleep(0.4)
    return st


def paced_puller(base: str, fmt: str, rate: float, seconds: float,
                 stop: threading.Event, sink: list) -> None:
    """the thin client's transport, harness-paced: one pull each 1/rate."""
    interval = 1.0 / rate
    next_t = time.perf_counter()
    n = 0
    while not stop.is_set():
        now = time.perf_counter()
        if now < next_t:
            time.sleep(min(next_t - now, 0.002))
            continue
        next_t = max(next_t + interval, now + 0.001)
        if next_t < now:            # fell behind: skip ahead (achieved<rate)
            next_t = now + interval
        t0 = time.perf_counter()
        try:
            b = http_get(base, f"/api/snapshot?fmt={fmt}")
            sink.append((n, time.perf_counter() - t0, len(b)))
            n += 1
        except OSError:
            sink.append((n, -1, 0))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--only", default=None)
    ap.add_argument("--keep-worlds", action="store_true")
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    only = set(a.only.split(",")) if a.only else None
    summary: dict = {"runs": {}, "twin": {}}

    # ── boot both worlds ──────────────────────────────────────────────
    procs: list = []
    logA = out / "sliceA_stdout.log"
    pA = subprocess.Popen([PY, "-u", str(HERE / "boot_slice.py"), "--port", "0"],
                          stdout=open(logA, "wb"), stderr=subprocess.STDOUT,
                          cwd=str(HERE.parent.parent),
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    procs.append(pA)
    portA = None
    t0 = time.time()
    while time.time() - t0 < 90:
        try:
            for line in open(logA, encoding="utf-8", errors="replace"):
                if line.startswith("slice: http://"):
                    portA = int(line.strip().rsplit(":", 1)[1].split("/")[0])
        except OSError:
            pass
        if portA:
            break
        time.sleep(0.5)
    assert portA, "slice A port not found"
    baseA = f"http://127.0.0.1:{portA}"

    logB = out / "sliceB_stdout.log"
    pB = subprocess.Popen([PY, "-u", str(HERE / "boot_slice.py"), "--port", "0"],
                          stdout=open(logB, "wb"), stderr=subprocess.STDOUT,
                          cwd=str(HERE.parent.parent),
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    procs.append(pB)
    portB = None
    t0 = time.time()
    while time.time() - t0 < 90:
        try:
            for line in open(logB, encoding="utf-8", errors="replace"):
                if line.startswith("slice: http://"):
                    portB = int(line.strip().rsplit(":", 1)[1].split("/")[0])
        except OSError:
            pass
        if portB:
            break
        time.sleep(0.5)
    assert portB, "slice B port not found"
    baseB = f"http://127.0.0.1:{portB}"
    print(f"slices: A={baseA} B={baseB}", flush=True)

    wait_health(baseA)
    wait_health(baseB)
    print("waiting settled both worlds...", flush=True)
    wait_settled(baseA)
    wait_settled(baseB)

    # ── twin certification: fixed-point verts must be byte-identical ──
    # the receipt bar: the fixed point is BIT-STABLE once root_y stops; two
    # fresh boots reach the same bytes. Poll until identical (convergence
    # stages differ per boot clock), abort as an instrument failure if never.
    # MEASURED FINDING (recorded in the receipt): the fixed point is
    # bit-stable WITHIN a boot but cross-boot /verts differs by exactly ONE
    # float ULP in the Y component on a subset of vertices (max |delta|
    # 2.98e-8 m -- landing-depth rounding at one ulp). The twin gate is
    # therefore max|delta pos| <= 1e-6 m (33 ulps = 1 micrometre, ~2e-5 px at
    # 960x540), not byte identity. Byte identity was the start hypothesis; it
    # was falsified and recorded, not tuned away.
    import struct as _st
    def max_delta(xa: bytes, xb: bytes) -> float:
        if len(xa) != len(xb) or len(xa) < 4:
            return float("inf")
        n = _st.unpack_from("<I", xa, 0)[0]
        m = 0.0
        for v in range(n):
            o = 4 + v * 36
            fa = _st.unpack_from("<3f", xa, o)
            fb = _st.unpack_from("<3f", xb, o)
            for x, y in zip(fa, fb):
                m = max(m, abs(x - y))
        return m
    maxd = float("inf")
    sha_a = sha_b = None
    t_sha = time.time()
    while time.time() - t_sha < 180:
        va, vb = http_get(baseA, "/api/verts"), http_get(baseB, "/api/verts")
        sha_a = hashlib.sha256(va).hexdigest()
        sha_b = hashlib.sha256(vb).hexdigest()
        maxd = max_delta(va, vb)
        if maxd <= 1e-6:
            break
        wait_settled(baseA, timeout=20)
        wait_settled(baseB, timeout=20)
    summary["twin"] = {"verts_sha_A": sha_a, "verts_sha_B": sha_b,
                       "identical_at_rest": sha_a == sha_b,
                       "max_pos_delta_m": maxd,
                       "gate": "max_pos_delta_m <= 1e-6",
                       "finding": "cross-boot one-ULP Y divergence (2.98e-8 m) "
                                  "falsified byte-identity; per-boot stability intact"}
    print("twin gate: max|dpos| =", maxd, "m", flush=True)
    if maxd > 1e-6:
        (out / "suite_summary.json").write_text(json.dumps(summary, indent=1))
        raise RuntimeError(f"TWIN FAILURE: max pos delta {maxd} m > 1e-6")
    topo = http_get(baseA, "/api/topology")
    (out / "topology.bin").write_bytes(topo)

    try:
        # ── BANDWIDTH matrix (harness-paced pulls, carry moving) ──────
        if only is None or "bandwidth" in only:
            http_post(baseA, "/api/send")
            http_post(baseB, "/api/send")
            time.sleep(1.0)
            bw: dict = {}
            for fmt in BANDWIDTH_FMTS:
                for rate in BANDWIDTH_RATES:
                    stop = threading.Event()
                    sink: list = []
                    th = threading.Thread(target=paced_puller,
                                          args=(baseA, fmt, float(rate), 0, stop, sink))
                    th.start()
                    time.sleep(10.0)
                    stop.set()
                    th.join(timeout=15)
                    ok = [(rt, sz) for (_, rt, sz) in sink if rt >= 0]
                    sizes = sorted(sz for _, sz in ok)
                    achieved = len(ok) / 10.0
                    med = sizes[len(sizes) // 2] if sizes else 0
                    p95 = sizes[int(0.95 * len(sizes))] if sizes else 0
                    bw[f"{fmt}@{rate}"] = {
                        "achieved_hz": round(achieved, 2),
                        "median_payload_B": med, "p95_payload_B": p95,
                        "bytes_per_s_median_x_rate": int(med * rate),
                        "bytes_per_s_achieved": int(med * achieved),
                        "MB_per_s_achieved": round(med * achieved / 1e6, 3)}
                    print(f"bw {fmt}@{rate}: {bw[f'{fmt}@{rate}']}", flush=True)
            summary["bandwidth"] = bw
            (out / "bandwidth.json").write_text(json.dumps(summary["bandwidth"], indent=1))
            http_post(baseA, "/api/stop")
            http_post(baseB, "/api/stop")

        # ── BROWSER RUNS ──────────────────────────────────────────────
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="chrome", headless=True)
            for (name, scen, rate, fmt, trace, jhead) in RUNS:
                if only is not None and name not in only and "browser" not in only:
                    continue
                wait_settled(baseA)
                wait_settled(baseB)
                # trace proxy in front of A (the page's whole origin rides it)
                if TRACES[trace]["delay"] or TRACES[trace]["jitter"]:
                    logp = out / f"proxy_{name}.log"
                    proc_args = [PY, "-u", str(HERE / "trace_proxy.py"),
                                 "--listen", "0", "--target-host", "127.0.0.1",
                                 "--target-port", str(portA),
                                 "--delay-ms", str(TRACES[trace]["delay"]),
                                 "--jitter-ms", str(TRACES[trace]["jitter"])]
                    if TRACES[trace]["tail"]:
                        proc_args += ["--tail-ms", str(TRACES[trace]["tail"]),
                                      "--tail-every-s", "5"]
                    pr = subprocess.Popen(proc_args, stdout=open(logp, "wb"),
                                          stderr=subprocess.STDOUT)
                    pport = None
                    t0 = time.time()
                    while time.time() - t0 < 20 and not pport:
                        try:
                            for line in open(logp, "rb"):
                                if line.startswith(b"PROXY_PORT="):
                                    pport = int(line.split(b"=")[1])
                        except OSError:
                            pass
                        time.sleep(0.1)
                    procs.append(pr)
                    base_page = f"http://127.0.0.1:{pport}"
                else:
                    pr = None
                    base_page = baseA

                # truth recorder on the twin (direct, never through the trace)
                truth_bin = out / f"truth_{name}.bin"
                tr = subprocess.Popen([PY, "-u", str(HERE / "truth_recorder.py"),
                                       "--base", baseB, "--out", str(truth_bin),
                                       "--max-s", "150"],
                                      stdout=open(out / f"truth_{name}.log", "wb"),
                                      stderr=subprocess.STDOUT)
                procs.append(tr)
                time.sleep(0.8)   # recorder spinning before the motion starts

                page = browser.new_page(viewport={"width": 960, "height": 540})
                url = (f"{base_page}/?thin=1&rate={rate}&fmt={fmt}"
                       f"&pilot=1&jhead={jhead}")
                page.goto(url)
                page.wait_for_timeout(2500)
                st = page.evaluate("window.__thin_state()")
                if st["achieved"] <= 0:
                    page.wait_for_timeout(3000)
                    st = page.evaluate("window.__thin_state()")
                t_trigger = time.time()
                trigger_page_t = page.evaluate("performance.now()")
                press_info = None
                if scen == "FALL":
                    http_post(baseA, "/api/drop_test")
                    http_post(baseB, "/api/drop_test")
                    page.wait_for_timeout(24000)     # launch+descent+landing
                    while True:
                        ft = json.loads(http_get(baseA, "/api/status"))["fall_test"]
                        if ft and ft.get("phase") == "done":
                            break
                        if time.time() - t_trigger > 90:
                            break
                        time.sleep(0.5)
                elif scen == "CARRY":
                    http_post(baseA, "/api/carry_reset")   # arrival parks the
                    http_post(baseB, "/api/carry_reset")   # mock; reset first
                    time.sleep(0.3)
                    http_post(baseA, "/api/send")
                    http_post(baseB, "/api/send")
                    page.wait_for_timeout(15000)
                    http_post(baseA, "/api/stop")
                    http_post(baseB, "/api/stop")
                elif scen == "PRESS":
                    page.wait_for_timeout(2000)
                    page.keyboard.press(" ")
                    press_info = {"pressed_wall": time.time()}
                    page.wait_for_timeout(6000)
                dump = json.loads(page.evaluate("window.__pilot_dump()"))
                shot = page.screenshot(path=str(out / f"page_{name}.png"))
                del shot
                page.close()
                tr.terminate()
                try:
                    tr.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    tr.kill()
                if pr is not None:
                    pr.terminate()
                    try:
                        pr.wait(timeout=5)
                        procs.remove(pr)
                    except (subprocess.TimeoutExpired, ValueError):
                        pass
                (out / f"dump_{name}.json").write_text(
                    json.dumps(dump), encoding="utf-8")
                snaps = dump["snaps"]
                if len(snaps) > 2:
                    span_s = (snaps[-1]["arrival"] - snaps[0]["arrival"]) / 1000
                    achieved_dump = (len(snaps) - 1) / span_s
                    ivs = [(snaps[i + 1]["arrival"] - snaps[i]["arrival"])
                           for i in range(len(snaps) - 1)]
                    ivs.sort()
                    med_iv = ivs[len(ivs) // 2]
                    max_iv = ivs[-1]
                else:
                    achieved_dump, med_iv, max_iv = 0, None, None
                summary["runs"][name] = {
                    "scenario": scen, "rate_nominal": rate, "fmt": fmt,
                    "trace": trace, "jhead_ms": jhead,
                    "achieved_hz_dump": round(achieved_dump, 2),
                    "median_interval_ms": round(med_iv, 2) if med_iv else None,
                    "max_interval_ms": round(max_iv, 1) if max_iv else None,
                    "trigger_page_t_ms": trigger_page_t,
                    "underruns": dump["underruns"],
                    "underrun_ms": dump["underrun_ms"],
                    "pull_errors": dump["pullErrs"],
                    "press": press_info}
                print(f"run {name}: achieved(dump) {achieved_dump:.1f} Hz, "
                      f"med_iv {med_iv:.1f} ms, max_iv {max_iv:.1f} ms, "
                      f"underruns {dump['underruns']}", flush=True)
            browser.close()

        # ── twin curve check per run happens in analyze.py (root_y curves)
        (out / "suite_summary.json").write_text(json.dumps(summary, indent=1))
    finally:
        if not a.keep_worlds:
            for p in procs[2:]:
                try:
                    p.terminate()
                except Exception:
                    pass
            for p in (procs[0], procs[1]):
                try:
                    p.terminate()
                except Exception:
                    pass
    print("SUITE-DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
