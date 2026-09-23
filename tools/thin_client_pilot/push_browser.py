"""push_browser.py -- THE F2/F4 BROWSER RUNS (lane/push-channel-20260920).

The F2 visual-error rerun through the PUSH channel: the push client PAGE
(bundled chromium; MACHINE_FINDINGS: installed Chrome cannot navigate on
this host) runs the FALL and CARRY scenarios while the TWIN slice records
60 Hz truth; the page's sampled rendered frames + rAF log are dumped in the
pilot's schema so tools/thin_client_pilot/analyze.py runs UNCHANGED (same
twin-shift estimator, same numpy raster, same frame-time table).

Rows (prereg minimum):
  PB1_fall_30_full  FALL  30 Hz FULL36  (the pilot's worst torn-frame fmt)
  PB2_fall_30_z12   FALL  30 Hz Z12
  PB3_carry_30_full CARRY 30 Hz FULL36

F5 gates recorded here: console ERRORS must be zero (warnings reported,
never gated); page __push_errs must be empty.

Usage: python push_browser.py --out-dir DIR [--rows PB1,PB2,PB3]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from push_stream import (http_get, http_post, wait_boot_settled,  # noqa: E402
                         wait_engine_alive, wait_health, wait_settled)

ENGINE_EXE = "E:/ChimeraWork/thincli-agent/.tmp/slice_build/Release/chimera_engine.exe"

# name, scenario, rate, fmt
ROWS = [
    ("PB1_fall_30_full",  "FALL",  30, "FULL36"),
    ("PB2_fall_30_z12",   "FALL",  30, "Z12"),
    ("PB3_carry_30_full", "CARRY", 30, "FULL36"),
]

BROWSER_ARGS = ["--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
                "--enable-gpu", "--enable-unsafe-swiftshader"]


def boot_slice(out: Path, tag: str) -> tuple:
    log = open(out / ("browser_slice_%s.log" % tag), "wb")
    p = subprocess.Popen(
        [sys.executable, "-u", str(HERE / "boot_slice.py"), "--port", "0",
         "--engine-exe", ENGINE_EXE],
        stdout=log, stderr=subprocess.STDOUT,
        cwd=str(HERE.parent.parent),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    port = None
    t0 = time.time()
    while time.time() - t0 < 90 and not port:
        try:
            for line in open(out / ("browser_slice_%s.log" % tag),
                             encoding="utf-8", errors="replace"):
                if line.startswith("slice: http://"):
                    port = int(line.strip().rsplit(":", 1)[1].split("/")[0])
        except OSError:
            pass
        time.sleep(0.5)
    assert port, "slice %s port not found" % tag
    return p, "http://127.0.0.1:%d" % port


def twin_gate(baseA: str, baseB: str, tries: float = 180.0) -> dict:
    """the pilot's twin bar: cross-boot fixed point differs <= 1e-6 m
    (byte-identity was falsified at one float ULP; recorded there).
    THE PILOT'S POLLING PATTERN: convergence stages differ per boot clock
    (and this box's GPU load makes the settle long) -- poll until identical,
    waiting the boot's own scene.settled between attempts; abort as an
    INSTRUMENT failure only if it never converges."""
    import time as _time
    def max_delta(xa: bytes, xb: bytes) -> float:
        if len(xa) != len(xb) or len(xa) < 4:
            return float("inf")
        n = struct.unpack_from("<I", xa, 0)[0]
        m = 0.0
        for v in range(n):
            o = 4 + v * 36
            fa = struct.unpack_from("<3f", xa, o)
            fb = struct.unpack_from("<3f", xb, o)
            m = max(m, max(abs(x - y) for x, y in zip(fa, fb)))
        return m
    t0 = _time.time()
    maxd = float("inf")
    va = vb = b""
    while _time.time() - t0 < tries:
        va, vb = http_get(baseA, "/api/verts"), http_get(baseB, "/api/verts")
        maxd = max_delta(va, vb)
        if maxd <= 1e-6:
            break
        wait_settled(baseA, timeout=20)
        wait_settled(baseB, timeout=20)
    return {"sha_A": hashlib.sha256(va).hexdigest()[:16],
            "sha_B": hashlib.sha256(vb).hexdigest()[:16],
            "max_pos_delta_m": maxd}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--rows", default=None)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    only = set(a.rows.split(",")) if a.rows else None

    pA, baseA = boot_slice(out, "A")
    pB, baseB = boot_slice(out, "B")
    wait_health(baseA)
    wait_health(baseB)
    wait_settled(baseA)
    wait_settled(baseB)
    gate = twin_gate(baseA, baseB)
    gate["gate"] = "max_pos_delta_m <= 1e-6 (cross-boot one-ULP finding)"
    print("twin gate:", gate, flush=True)
    if gate["max_pos_delta_m"] > 1e-6:
        (out / "suite_summary.json").write_text(json.dumps({"twin": gate}))
        raise RuntimeError("TWIN FAILURE")

    topo = http_get(baseA, "/api/topology")
    (out / "topology.bin").write_bytes(topo)

    summary: dict = {"twin": gate, "runs": {}}
    procs: list = []
    run_gate = {"max_pos_delta_m": gate["max_pos_delta_m"]}
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=BROWSER_ARGS)
        for (name, scen, rate, fmt) in ROWS:
            if only and name not in only:
                continue
            wait_engine_alive(baseA)
            wait_engine_alive(baseB)
            if scen == "FALL":
                # byte-clean world per FALL run; readiness = the slice's own
                # scene.settled (a trigger into a mid-swap world is swallowed:
                # the pilot's measured R06 lesson)
                http_post(baseA, "/api/restart")
                http_post(baseB, "/api/restart")
                wait_boot_settled(baseA)
                wait_boot_settled(baseB)
                run_gate = twin_gate(baseA, baseB, tries=60.0)
                print(name, "per-run twin gate:", run_gate["max_pos_delta_m"],
                      flush=True)
            wait_settled(baseA)
            wait_settled(baseB)

            truth_bin = out / ("truth_%s.bin" % name)
            tr = subprocess.Popen(
                [sys.executable, "-u", str(HERE / "truth_recorder.py"),
                 "--base", baseB, "--out", str(truth_bin), "--max-s", "150"],
                stdout=open(out / ("truth_%s.log" % name), "wb"),
                stderr=subprocess.STDOUT)
            procs.append(tr)
            time.sleep(0.8)

            page = browser.new_page(viewport={"width": 960, "height": 540})
            console: list = []
            page.on("console", lambda m: console.append(
                {"type": m.type, "text": m.text}))
            page.on("pageerror", lambda e: console.append(
                {"type": "pageerror", "text": str(e)}))
            url = "%s/push?fmt=%s&rate=%d&pilot=1" % (baseA, fmt, rate)
            page.goto(url, wait_until="commit", timeout=60000)
            page.wait_for_function("window.__push_state !== undefined",
                                   timeout=60000)
            page.wait_for_timeout(2500)
            st = page.evaluate("window.__push_state()")
            if st["achieved"] <= 0:
                page.wait_for_timeout(3000)
                st = page.evaluate("window.__push_state()")
            t_trigger = time.time()
            if scen == "FALL":
                http_post(baseA, "/api/drop_test")
                http_post(baseB, "/api/drop_test")
                fell = False
                for attempt in (1, 2):
                    if attempt == 2:
                        http_post(baseA, "/api/drop_test")
                        http_post(baseB, "/api/drop_test")
                    for _ in range(30):
                        time.sleep(0.5)
                        snap = json.loads(
                            http_get(baseA, "/api/status"))["engine_state"]
                        if "root_y" in snap and (
                                float(snap["root_y"]) > 0.4 or
                                float(snap["root_y"]) < 0.2):
                            fell = True
                            break
                    if fell:
                        break
                if not fell:
                    raise RuntimeError(name + ": the fall never started")
                page.wait_for_timeout(24000)
                while True:
                    ft = json.loads(
                        http_get(baseA, "/api/status"))["fall_test"]
                    if ft and ft.get("phase") == "done":
                        break
                    if time.time() - t_trigger > 90:
                        break
                    time.sleep(0.5)
            elif scen == "CARRY":
                http_post(baseA, "/api/carry_reset")
                http_post(baseB, "/api/carry_reset")
                time.sleep(0.3)
                http_post(baseA, "/api/send")
                http_post(baseB, "/api/send")
                page.wait_for_timeout(15000)
                http_post(baseA, "/api/stop")
                http_post(baseB, "/api/stop")

            dump = json.loads(page.evaluate("window.__push_dump()"))
            shot = page.screenshot(path=str(out / ("page_%s.png" % name)))
            del shot
            errs_console = [c for c in console if c["type"] == "error"]
            errs_page = [c for c in console if c["type"] == "pageerror"]
            page.close()
            tr.terminate()
            try:
                tr.wait(timeout=10)
            except subprocess.TimeoutExpired:
                tr.kill()

            (out / ("dump_%s.json" % name)).write_text(json.dumps(dump),
                                                       encoding="utf-8")
            snaps = dump["snaps"]
            if len(snaps) > 2:
                span_s = (snaps[-1]["arrival"] - snaps[0]["arrival"]) / 1000
                achieved = (len(snaps) - 1) / span_s
                ivs = sorted(snaps[i + 1]["arrival"] - snaps[i]["arrival"]
                             for i in range(len(snaps) - 1))
                med_iv, max_iv = ivs[len(ivs) // 2], ivs[-1]
            else:
                achieved, med_iv, max_iv = 0, None, None
            summary["runs"][name] = {
                "scenario": scen, "rate_nominal": rate, "fmt": fmt,
                "trace": "TRACE-CLEAN", "jhead_ms": 0,
                "transport": "PUSH",
                "twin_gate_max_pos_delta_m": (run_gate["max_pos_delta_m"]
                                              if scen == "FALL" else None),
                "valid": (run_gate["max_pos_delta_m"] <= 1e-6
                          if scen == "FALL" else True),
                "achieved_hz_dump": round(achieved, 2),
                "median_interval_ms": round(med_iv, 2) if med_iv else None,
                "max_interval_ms": round(max_iv, 1) if max_iv else None,
                "underruns": dump["underruns"],
                "underrun_ms": dump["underrun_ms"],
                "stream_errors": dump["streamErrs"],
                "reconnections": dump["reconnections"],
                "guard_rejects": dump["guard"]["rejects"],
                "guard_last_reason": dump["guard"]["last_reason"],
                "seq_gaps": dump["guard"]["seq_gaps"],
                "wire_bytes": dump["wire_bytes"],
                "console_errors": errs_console,
                "page_errors": errs_page,
                "held_samples": sum(1 for s in dump["samples"]
                                    if s.get("held"))}
            print("%s: achieved %.1f Hz, seq gaps %d, guard rejects %d, "
                  "held samples %d, console errors %d"
                  % (name, achieved, dump["guard"]["seq_gaps"],
                     dump["guard"]["rejects"],
                     summary["runs"][name]["held_samples"], len(errs_console)),
                  flush=True)
        browser.close()
    (out / "suite_summary.json").write_text(json.dumps(summary, indent=1))
    for p in procs:
        p.terminate()
    for p in (pA, pB):
        p.terminate()
    print("BROWSER-DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
