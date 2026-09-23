# fleet_supervisor/smoke_real_shape.py -- REAL-SHAPE SMOKE (prereg F7).
# One lane-shaped workload end-to-end through the supervisor:
#   1. a real slice server (tools/playable_slice/slice_server.py) that owns
#      and spawns a REAL engine child (chimera_engine.exe),
#   2. one bundled-chromium headless capture of the live page,
#   3. graceful completion, then: zero survivors (by exact identity), a
#      coherent registry, and a read-only census as second opinion.
# Runs against the PRODUCTION control dir + registry (it is a real fleet use).
# No GPU compute: the broker manages reservations, this smoke consumes none.
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

from . import broker, jobobject, lifecycle, registry

SCRATCH = r"E:\ChimeraWork\_supervisor_scratch"
ENGINE_SRC = r"E:\ChimeraWork\buffy-stranger-20260920\.tmp\slice_build\Release"
ENGINE_DST = os.path.join(SCRATCH, "smoke_engine")
LANE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "tools", "science_funnel", "validation", "fleet_supervisor_20260922")
NEVER_PORT = 8127  # the port law


def pick_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    if port == NEVER_PORT:
        return pick_port()
    return port


def stage_engine() -> str:
    """Copy (READ-ONLY on the source lane) the newest built engine + shaders
    into our scratch; the engine writes its session jsonl to ITS cwd, which
    is our scratch -- no other lane's tree is touched."""
    os.makedirs(ENGINE_DST, exist_ok=True)
    exe_src = os.path.join(ENGINE_SRC, "chimera_engine.exe")
    exe_dst = os.path.join(ENGINE_DST, "chimera_engine.exe")
    if not os.path.exists(exe_src):
        raise FileNotFoundError(f"no engine binary at {exe_src}")
    shutil.copy2(exe_src, exe_dst)
    shutil.copytree(os.path.join(ENGINE_SRC, "shaders"), os.path.join(ENGINE_DST, "shaders"),
                    dirs_exist_ok=True)
    return exe_dst


def census_count(fragment: str) -> int:
    return sum(1 for p in jobobject.enumerate_processes()
               if fragment.lower() in (p["name"] or "").lower())


def main() -> int:
    control = broker.DEFAULT_CONTROL_DIR
    reg = registry.DEFAULT_REGISTRY
    d = os.path.join(SCRATCH, "smoke")
    os.makedirs(d, exist_ok=True)
    results = {"steps": {}, "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    ok = True

    # 0. mode: set fleet via the operator's own setter (idempotent, default)
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File",
                        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "set_fleet_mode.ps1"), "fleet"],
                       capture_output=True, text=True, timeout=60,
                       creationflags=jobobject.CREATE_NO_WINDOW)
    results["steps"]["mode_set"] = {"out": (r.stdout or "").strip(), "rc": r.returncode}
    ok &= r.returncode == 0

    sup = lifecycle.Supervisor(registry_path=reg, control_dir=control)

    # 1. live broker gate in production: gpu_phase without reservation refused
    gpu_spec = {"session_id": f"smoke-gpu-probe-{int(time.time())}",
                "owner_lane": "supervisor-smoke", "worktree": None,
                "command": ["cmd", "/c", "exit"], "ports": [], "kind": "gpu_phase",
                "resources": {"cpu_pct": None, "mem_gib": 1, "max_procs": 4}}
    res = sup.launch(gpu_spec)
    results["steps"]["gpu_phase_refused_live"] = {
        "ok": (not res.ok), "why": (res.error or "")[:120]}
    ok &= not res.ok  # the launch must be REFUSED (and no reservation exists)

    # 2. the slice server with its REAL engine child
    engine_exe = stage_engine()
    port = pick_port()
    engines_before = census_count("chimera_engine")
    spec = {"session_id": f"smoke-slice-{int(time.time())}",
            "owner_lane": "supervisor-smoke",
            "worktree": r"E:\ChimeraWork\supervisor-agent",
            "command": [sys.executable,
                        os.path.join(r"E:\ChimeraWork\supervisor-agent",
                                     "tools", "playable_slice", "slice_server.py"),
                        "--port", str(port), "--engine-exe", engine_exe, "--no-browser"],
            "ports": [port], "kind": "server",
            "resources": {"cpu_pct": None, "mem_gib": 4, "max_procs": 32},
            "stdout_file": os.path.join(d, "slice_server.out.log"),
            "stderr_file": os.path.join(d, "slice_server.err.log")}
    t0 = time.time()
    res = sup.launch(spec)
    results["steps"]["server_launch"] = res.to_dict()
    if not res.ok:
        results["ok"] = False
        _finish(results)
        return 1
    sid = res.session_id

    # 3. wait for /api/health (the server boots its engine child inside)
    health = None
    deadline = time.time() + 120.0
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=3) as resp:
                health = json.loads(resp.read().decode())
            break
        except Exception:
            time.sleep(1.0)
    results["steps"]["health"] = {"ok": health is not None, "body": health,
                                  "waited_s": round(time.time() - t0, 1)}
    ok &= health is not None

    # 4. containment proof: a chimera_engine.exe member lives in OUR job
    jh = sup.handles.get(sid)
    members = lifecycle.live_member_identities(jh) if jh else []
    engine_members = []
    for m in members:
        img = (jobobject.process_image_name(m["pid"]) or "")
        if "chimera_engine" in img.lower():
            engine_members.append({**m, "image": img})
    results["steps"]["engine_child_contained"] = {
        "members": len(members), "engine_members": engine_members}
    ok &= len(engine_members) >= 1

    # 5. browser capture THROUGH the supervisor (bundled chromium)
    cap_png = os.path.join(d, "slice_capture.png")
    cap_json = os.path.join(d, "capture_result.json")
    capture_script = os.path.join(LANE_DIR, "smoke_capture.py")
    bspec = {"session_id": f"smoke-capture-{int(time.time())}",
             "owner_lane": "supervisor-smoke", "worktree": None,
             "command": [sys.executable, capture_script,
                         f"http://127.0.0.1:{port}/", cap_png, cap_json],
             "ports": [], "kind": "browser",
             "resources": {"cpu_pct": None, "mem_gib": 2, "max_procs": 64}}
    t1 = time.time()
    bres = sup.launch(bspec)
    results["steps"]["browser_launch"] = bres.to_dict()
    capture_ok = False
    if bres.ok:
        deadline = time.time() + 90.0
        while time.time() < deadline:
            if os.path.exists(cap_json):
                try:
                    cap = json.load(open(cap_json))
                    capture_ok = bool(cap.get("ok")) and os.path.exists(cap_png)
                    results["steps"]["capture"] = {"ok": capture_ok, "cap": cap,
                                                   "png_bytes": os.path.getsize(cap_png)}
                    break
                except (json.JSONDecodeError, OSError):
                    pass
            time.sleep(1.0)
        else:
            results["steps"]["capture"] = {"ok": False, "why": "capture never completed"}
        sup.complete(bspec["session_id"], deadline=10, reason="smoke done")
    else:
        results["steps"]["capture"] = {"ok": False, "why": bres.error}
    ok &= capture_ok

    # 6. complete the server (engine child dies with the job)
    out = sup.complete(sid, deadline=10, reason="smoke done")
    results["steps"]["server_complete"] = out
    time.sleep(1.5)

    # 7. zero survivors, by identity and by census
    time.sleep(1.0)
    survivors = [m for m in members
                 if jobobject.process_running(m["pid"], m["creation_time_us"])]
    engines_after = census_count("chimera_engine")
    results["steps"]["zero_survivors"] = {
        "members_tracked": len(members), "running_survivors": survivors,
        "engines_before": engines_before, "engines_after": engines_after,
        "health_url": f"http://127.0.0.1:{port}/",
        "url_dead": not _url_alive(port)}
    ok &= not survivors and engines_after <= engines_before

    # 8. registry coherence: one folded record per session, terminal statuses
    folded = registry.fold(reg)
    srec = folded.get(sid, {})
    brec = folded.get(bspec.get("session_id") or "", {})
    coherent = (srec.get("status") in ("completed", "terminated")
                and srec.get("pid") == res.pid
                and srec.get("creation_time_us") == res.creation_time_us)
    results["steps"]["registry_coherent"] = {
        "server_status": srec.get("status"), "pid_matches": srec.get("pid") == res.pid,
        "browser_status": brec.get("status")}
    ok &= coherent

    results["ok"] = bool(ok)
    _finish(results)
    return 0 if ok else 1


def _url_alive(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2) as r:
            return True
    except Exception:
        return False


def _finish(results: dict) -> None:
    results["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(SCRATCH, "smoke", "smoke_results.json"), "w") as f:
        json.dump(results, f, indent=1)
    compact = dict(results)
    compact["steps"] = {k: {kk: vv for kk, vv in v.items() if kk != "body"}
                        for k, v in results["steps"].items() if isinstance(v, dict)}
    with open(os.path.join(LANE_DIR, "smoke_results.json"), "w") as f:
        json.dump(compact, f, indent=1)
    print(json.dumps(results, indent=1))


if __name__ == "__main__":
    sys.exit(main())
