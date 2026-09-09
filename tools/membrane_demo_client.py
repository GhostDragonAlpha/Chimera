#!/usr/bin/env python3
"""membrane_demo_client.py -- GLM-GPU-DEMO-01 runtime gate driver.

One request at a time against the engine's opt-in /membrane_demo_* API, so a
crash is attributed to the exact request that triggered it. Serves the
RUNTIME-HANDOFF reproducibility law: launch mode records the executable, PID,
cwd, port and stdout/stderr files; it terminates ONLY the process it launched
and refuses to run if the port is already occupied (never touches a live
engine it did not start).

Upload law: the FROZEN B2 fixture (docs/evidence/gpu_fixtures/b2) supplies
positions, indices and CSR; gamma comes from the fixture's per-face gamma
arrays; the engine computes on the declared B2 z-up coordinates and applies
the rigid presentation lift at the PRESENT stage (physics never sees it).

Usage:
  python tools/membrane_demo_client.py gate --launch <exe> [--port 8091]
  python tools/membrane_demo_client.py <init|status|step|run|gamma|reset|reject|capture> ... --base http://localhost:8091

Exit codes: 0 all checks PASS; 1 any FAIL/CRASH; 2 usage/environment blocker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "docs" / "evidence" / "gpu_fixtures" / "b2"
EVID = ROOT / "docs" / "evidence" / "membrane_gpu_demo_runtime"
MAGIC = 0x3130444D  # "MD01"
CENTRE_INDEX = 6
LIFT_M = 0.5  # presentation only (GLM-DYAD-02); engine present-stage applies it

results: list[dict] = []


def log(msg: str) -> None:
    print(msg, flush=True)


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def record(name: str, verdict: str, detail: dict) -> None:
    results.append({"name": name, "verdict": verdict, "detail": detail, "utc": utc()})
    log(f"  [{verdict}] {name}: {json.dumps(detail, default=str)[:300]}")


# ── frozen fixture ───────────────────────────────────────────────────────────

def load_b2(gamma_case: str = "case_gamma1") -> dict:
    geom = FIX / "geometry"
    pos = np.load(geom / "positions_f32.npy").astype("<f4")
    idx = np.load(geom / "indices_u32.npy").astype("<u4").reshape(-1)
    off = np.load(FIX / "adjacency" / "csr_offsets_i64.npy").astype("<u4")
    cor = np.load(FIX / "adjacency" / "csr_corner_idx_i64.npy").astype("<u4")
    case = FIX / gamma_case
    return {
        "pos": pos.reshape(-1), "idx": idx,
        "csr_off": off.reshape(-1), "csr_cor": cor.reshape(-1),
        "gamma_face": np.load(geom / f"gamma{gamma_case[-1]}_f32.npy").astype("<f4").reshape(-1),
        "E_ref": float(np.load(case / "energy_f64.npy").reshape(-1)[0]),
        "vf_ref": np.load(case / "vertex_forces_f64.npy").astype(np.float64).reshape(-1),
        "case": gamma_case,
    }


def md01_packet(b2: dict, gamma_admitted: float) -> bytes:
    pos, idx = b2["pos"], b2["idx"]
    nv, nf = len(pos) // 3, len(idx) // 3
    assert len(b2["csr_off"]) == nv + 1 and len(b2["csr_cor"]) == nf * 3
    assert len(b2["gamma_face"]) == nf
    header = struct.pack("<IIII df I".replace(" ", ""), MAGIC, nv, nf,
                         CENTRE_INDEX, gamma_admitted, LIFT_M, 0)
    return (header + pos.tobytes() + idx.tobytes()
            + b2["csr_off"].tobytes() + b2["csr_cor"].tobytes()
            + b2["gamma_face"].tobytes())


# ── HTTP ─────────────────────────────────────────────────────────────────────

class Crash(Exception):
    def __init__(self, request: str, cause: str):
        super().__init__(f"CRASH at {request}: {cause}")
        self.request, self.cause = request, cause


def http_req(base: str, method: str, path: str, body: bytes | None = None,
             ctype: str = "application/json", timeout: float = 45.0):
    url = base + path
    req = urllib.request.Request(url, data=body, method=method)
    if body is not None:
        req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except (urllib.error.URLError, ConnectionResetError, TimeoutError,
            OSError) as e:  # connection death == engine crash
        raise Crash(method + " " + path, repr(e)) from e


def jget(base: str, path: str) -> dict:
    st, body = http_req(base, "GET", path)
    return json.loads(body.decode("utf-8", "replace"))


def demo_ctl(base: str, op: str, n_steps: int | None = None,
             gamma: float | None = None) -> dict:
    payload: dict = {"op": op}
    if n_steps is not None:
        payload["n_steps"] = int(n_steps)
    if gamma is not None:
        payload["gamma"] = float(gamma)
    st, body = http_req(base, "POST", "/membrane_demo",
                        json.dumps(payload).encode())
    return json.loads(body.decode("utf-8", "replace"))


# ── checks ───────────────────────────────────────────────────────────────────

def close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


def check_init(base: str, b2: dict) -> dict:
    st, body = http_req(base, "POST", "/membrane_demo_bin",
                        md01_packet(b2, 1.0), "application/octet-stream")
    r = json.loads(body.decode("utf-8", "replace"))
    if not r.get("ok"):
        record("init", "FAIL", {"http": st, "resp": r})
        return {}
    s = r.get("status", r)
    record("init", "PASS", {"E": s.get("energy"), "E_ref": b2["E_ref"],
                            "centre": s.get("centre"), "it": s.get("iteration"),
                            "snapshot": s.get("material_snapshot")})
    return s


def check_status(base: str, name: str) -> dict:
    s = jget(base, "/membrane_demo")
    record(name, "PASS" if s.get("ok") is not False else "FAIL", {
        "it": s.get("status", s).get("iteration"),
        "E": s.get("status", s).get("energy"),
        "terminal": s.get("status", s).get("terminal_state")})
    return s.get("status", s)


def gate(base: str, b2: dict, outdir: Path) -> int:
    fails = 0

    def fail(name: str, detail: dict) -> None:
        nonlocal fails
        fails += 1
        record(name, "FAIL", detail)

    s = check_init(base, b2)
    if not s:
        return 1
    e0 = float(s["energy"])
    f0 = float(s["centre_force"][2])
    z0 = float(s["centre"][2])
    ok_e0 = close(e0, b2["E_ref"], 2e-6)
    record("init.energy_vs_fixture", "PASS" if ok_e0 else "FAIL",
           {"gpu": e0, "ref": b2["E_ref"]})
    if not ok_e0:
        fail("init.energy_vs_fixture", {"gpu": e0, "ref": b2["E_ref"]})
    ok_z0 = close(z0, 0.125, 1e-6)
    record("init.centre_z", "PASS" if ok_z0 else "FAIL", {"z": z0})
    if not ok_z0:
        fail("init.centre_z", {"z": z0})

    # fixed-state gamma doubling (gamma=2 on the SAME accepted state)
    r = demo_ctl(base, "gamma", gamma=2.0)
    s2 = r.get("status", r)
    e2, f2 = float(s2["energy"]), float(s2["centre_force"][2])
    ok_e = close(e2, 2.0 * e0, 4e-6)
    ok_f = close(f2, 2.0 * f0, 2e-6) if f0 != 0 else f2 == 0
    record("doubling.energy", "PASS" if ok_e else "FAIL",
           {"E2": e2, "2E0": 2 * e0})
    if not ok_e:
        fails += 1
    record("doubling.force", "PASS" if ok_f else "FAIL", {"F2": f2, "2F0": 2 * f0})
    if not ok_f:
        fails += 1
    demo_ctl(base, "gamma", gamma=1.0)
    s = check_status(base, "gamma_back_to_1")
    ok_back = close(float(s["energy"]), e0, 2e-6)
    record("gamma_back.energy", "PASS" if ok_back else "FAIL",
           {"E": s["energy"], "E0": e0})
    if not ok_back:
        fail("gamma_back.energy", {"E": s["energy"], "E0": e0})

    # one accepted step, then the full run
    demo_ctl(base, "step", n_steps=1)
    s = check_status(base, "step1")
    ok_step = int(s["iteration"]) == 1 and float(s["energy"]) < e0
    record("step1.descends", "PASS" if ok_step else "FAIL",
           {"it": s["iteration"], "E": s["energy"], "E0": e0})
    if not ok_step:
        fail("step1", s)
    demo_ctl(base, "run", n_steps=126)
    s = check_status(base, "run")
    record("run.terminal", "INFO", {"terminal": s.get("terminal_state"),
                                    "it": s.get("iteration"),
                                    "acc": s.get("n_accepted"),
                                    "E": s.get("energy")})

    def capture(label: str) -> None:
        st, png = http_req(base, "GET", "/frame")
        if st != 200 or png[:8] != b"\x89PNG\r\n\x1a\n":
            fail(f"capture.{label}", {"http": st})
            return
        p = outdir / f"{label}.png"
        p.write_bytes(png)
        s_now = check_status(base, f"capture.{label}.status")
        sidecar = {"label": label, "png_sha256": hashlib.sha256(png).hexdigest(),
                   "png_bytes": len(png), "utc": utc(),
                   "status": s_now, "camera": {"radius": 6.0, "theta": 0.0,
                                               "phi": 0.7, "fixed_demo_camera": True}}
        (outdir / f"{label}.json").write_text(json.dumps(sidecar, indent=1))
        record(f"capture.{label}", "PASS", {"png": p.name,
                                            "state_id": s_now.get("accepted_state_id")})

    capture("final_relaxed")
    demo_ctl(base, "reset")
    s = check_status(base, "reset")
    ok_reset = (close(float(s["energy"]), e0, 2e-6) and int(s["iteration"]) == 0
                and close(float(s["centre"][2]), z0, 1e-6))
    record("reset.restore", "PASS" if ok_reset else "FAIL",
           {"E": s["energy"], "it": s["iteration"], "z": s["centre"][2]})
    if not ok_reset:
        fail("reset.restore", s)

    # rejection-integrity control: refused trial must not touch accepted state
    sid = s.get("accepted_state_id")
    demo_ctl(base, "reject")
    s = check_status(base, "reject")
    refused = s.get("last_control") == "invalid_trial_REFUSED"
    intact = s.get("accepted_state_id") == sid
    record("reject.refused", "PASS" if refused and intact else "FAIL",
           {"last_control": s.get("last_control"), "state_id": s.get("accepted_state_id")})
    if not (refused and intact):
        fails += 1

    # gamma=0: no force, geometry unchanged, stationary
    demo_ctl(base, "gamma", gamma=0.0)
    demo_ctl(base, "step", n_steps=1)
    s = check_status(base, "gamma0_step")
    record("gamma0.stationary", "PASS" if s.get("terminal_state") == "stationary"
           else "FAIL", {"terminal": s.get("terminal_state"),
                         "it": s.get("iteration")})
    if s.get("terminal_state") != "stationary":
        fails += 1
    capture("raised_gamma0")

    return 1 if fails else 0


# ── launch mode ──────────────────────────────────────────────────────────────

def port_busy(port: int) -> bool:
    try:
        urllib.request.urlopen(f"http://localhost:{port}/state", timeout=2).read(64)
        return True
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["gate", "init", "status", "step", "run",
                                        "gamma", "reset", "reject", "capture"])
    ap.add_argument("--base", default="http://localhost:8091")
    ap.add_argument("--launch", metavar="EXE", help="engine exe to launch (gate)")
    ap.add_argument("--port", type=int, default=8091)
    ap.add_argument("--steps", type=int, default=126)
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--case", default="case_gamma1")
    args = ap.parse_args()

    b2 = load_b2(args.case)
    outdir = EVID / utc()
    outdir.mkdir(parents=True, exist_ok=True)

    proc = None
    if args.launch:
        if port_busy(args.port):
            log(f"BLOCKED: port {args.port} already in use; refusing to launch "
                f"(never touches an existing engine)")
            return 2
        exe = Path(args.launch)
        run_dir = exe.parent
        so = open(run_dir / "gate_stdout.log", "wb")
        se = open(run_dir / "gate_stderr.log", "wb")
        proc = subprocess.Popen([str(exe), str(args.port), "--no-restore",
                                 "1280", "720"], cwd=run_dir,
                                stdout=so, stderr=se)
        log(f"launched pid={proc.pid} exe={exe} cwd={run_dir}")
        for _ in range(100):
            if port_busy(args.port):
                break
            if proc.poll() is not None:
                log(f"BLOCKED: engine exited early rc={proc.returncode}")
                return 2
            time.sleep(0.2)

    base = args.base
    rc = 2
    try:
        if args.command == "gate":
            rc = gate(base, b2, outdir)
        elif args.command == "init":
            check_init(base, b2); rc = 0
        elif args.command == "status":
            log(json.dumps(jget(base, "/membrane_demo"), indent=1)); rc = 0
        elif args.command == "step":
            log(json.dumps(demo_ctl(base, "step", n_steps=args.steps), indent=1)); rc = 0
        elif args.command == "run":
            log(json.dumps(demo_ctl(base, "run", n_steps=args.steps), indent=1)); rc = 0
        elif args.command == "gamma":
            log(json.dumps(demo_ctl(base, "gamma", gamma=args.gamma), indent=1)); rc = 0
        elif args.command == "reset":
            log(json.dumps(demo_ctl(base, "reset"), indent=1)); rc = 0
        elif args.command == "reject":
            log(json.dumps(demo_ctl(base, "reject"), indent=1)); rc = 0
        elif args.command == "capture":
            st, png = http_req(base, "GET", "/frame")
            (outdir / "frame.png").write_bytes(png)
            log(f"saved {outdir / 'frame.png'} ({len(png)} bytes)"); rc = 0
    except Crash as c:
        record(c.request, "CRASH", {"cause": c.cause})
        rc = 1
    finally:
        summary = {"utc": utc(), "command": args.command, "rc": rc,
                   "checks": results,
                   "fixture": str(FIX), "fixture_sha256":
                       hashlib.sha256((FIX / "manifest.json").read_bytes()).hexdigest()}
        (outdir / "summary.json").write_text(json.dumps(summary, indent=1))
        log(f"evidence: {outdir / 'summary.json'}")
        # Archive the engine's own stdout/stderr into THIS run's evidence dir
        # (the launch-dir logs are overwritten by every subsequent launch).
        if proc is not None and args.launch:
            for tag in ("gate_stdout.log", "gate_stderr.log"):
                src = Path(args.launch).parent / tag
                if src.exists():
                    (outdir / f"engine_{tag}").write_bytes(src.read_bytes())
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            log(f"terminated own pid={proc.pid} rc={proc.returncode}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
