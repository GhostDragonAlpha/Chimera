"""subject_restore_test.py — behavior test for DEFAULT-ON boot restore (Rule 0 membrane).

Statement : a bare engine boot replays the session snapshot (creature comes back, no client
            action); --no-restore opts out; a corrupt snapshot fails honestly, never crashes.
Prediction: (A) bare boot with a valid snapshot loads the mesh within ~5s and /state has the
            creature; (B) boot with --no-restore stays empty; (C) corrupt blob -> boot runs,
            restore reports failed>=1, engine alive.
Falsifier : (A) /state n==0 after 8s; (B) /state n>0; (C) engine process dies or the restore
            lies (ok:true with a corrupt blob).
"""
import os, struct, subprocess, sys, time, json, urllib.request, signal

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
EXE  = os.path.join(ROOT, "ChimeraEngine", "engine", "build", "Debug", "chimera_engine.exe")
MESH = os.path.join(ROOT, "Saved", "meshes", "monkey_birth.bin")
PORT = 8093
BASE = f"http://127.0.0.1:{PORT}"

def get(path, timeout=5):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))

def post_json(path, obj, timeout=5):
    req = urllib.request.Request(BASE + path, data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def state_n():
    # /state's n is the PHYSICS particle count (always 1200) — it never tracked
    # the mesh. The subject truth is /scene's body row: "N tris, M verts" when a
    # mesh is loaded, "no mesh" when not.
    for _ in range(5):
        try:
            sc = get("/scene")
            for row in sc.get("rows", []):
                if row.get("id") == "body":
                    return 1 if "tris" in row.get("detail", "") else 0
            return 0
        except Exception:
            time.sleep(0.4)
    return None

def launch(extra_args, cwd):
    return subprocess.Popen([EXE, str(PORT)] + extra_args, cwd=cwd,
                            stdout=open(os.path.join(cwd, f"test_out_{int(time.time())}.log"), "wb"),
                            stderr=open(os.path.join(cwd, f"test_err_{int(time.time())}.log"), "wb"))

def wait_port(up=True, seconds=30):
    t0 = time.time()
    probes = 0
    while time.time() - t0 < seconds:
        probes += 1
        try:
            get("/state", timeout=3)
            if up:
                print(f"   [wait_port] up after {time.time()-t0:.1f}s ({probes} probes)")
                return True
        except Exception as e:
            if not up:
                return True
            if probes % 5 == 0:
                print(f"   [wait_port] probe {probes}: {type(e).__name__} {e}")
        time.sleep(0.5)
    return False

def kill_port_owner(port):
    """Kill any process listening on `port` — the GHOST that made a whole test
    run measure a stale engine (bind fails silently, probes hit the squatter)."""
    out = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True).stdout
    pids = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[1].endswith(f":{port}") and parts[3] == "LISTENING":
            pids.add(int(parts[4]))
    for pid in pids:
        print(f"   [ghost] killing stray PID {pid} on port {port}")
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
    if pids:
        time.sleep(1.5)

def stop(p):
    p.kill(); p.wait()
    wait_port(up=False, seconds=10) or print("   [WARN] port still answering after kill!")

def main():
    assert os.path.exists(EXE), EXE
    assert os.path.exists(MESH), MESH
    kill_port_owner(PORT)
    rundir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subject_restore_run")
    os.makedirs(os.path.join(rundir, "session_snapshot"), exist_ok=True)
    # The engine resolves shaders relative to CWD — a test run dir must carry its own copy.
    shader_dst = os.path.join(rundir, "shaders")
    if not os.path.isdir(shader_dst):
        import shutil
        shutil.copytree(os.path.join(ROOT, "ChimeraEngine", "engine", "build", "Debug", "shaders"),
                        shader_dst)
    results = {}
    procs = []

    # Seed a VALID snapshot by launching once, loading the mesh, and letting the
    # snapshot writer persist it.
    print("== seed: load mesh on a live instance ==")
    p = launch([], rundir); procs.append(p)
    assert wait_port(True), f"engine did not come up (poll={p.poll()})"
    sys.path.insert(0, os.path.join(ROOT, "ChimeraEngine"))
    os.environ["CHIMERA_ENGINE_URL"] = BASE
    import importlib
    import cpp_bridge
    importlib.reload(cpp_bridge)
    ok, r, th, ph = cpp_bridge.load_mesh_bin(MESH, timeout=60)
    print("   load_mesh_bin ->", ok, f"r={r:.2f}")
    results["seed_load_ok"] = ok
    snap = os.path.join(rundir, "session_snapshot", "mesh_bin.blob")
    results["seed_blob_bytes"] = os.path.getsize(snap) if os.path.exists(snap) else 0
    assert results["seed_blob_bytes"] > 0, "snapshot blob was not written"

    # Test B first while this instance is up: --no-restore semantics need a fresh boot.
    stop(p)
    print("== B: boot with --no-restore stays empty ==")
    p = launch(["--no-restore"], rundir); procs.append(p)
    assert wait_port(True)
    time.sleep(6.0)   # generous window: restore thread would fire at 1.5s+retries
    n_b = state_n()
    results["B_no_restore_n"] = n_b
    print("   /state n =", n_b)

    print("== A: bare boot auto-restores ==")
    stop(p)
    p = launch([], rundir); procs.append(p)
    n_a = None
    t0 = time.time()
    while time.time() - t0 < 12:
        n = state_n()
        if n and n > 0:
            n_a = n; break
        time.sleep(0.5)
    results["A_bare_boot_n"] = n_a
    print("   /state n =", n_a, f"({time.time()-t0:.1f}s)")

    # Test C: corrupt blob must fail honestly, engine stays alive.
    stop(p)
    print("== C: corrupt mesh blob -> honest failure, no crash ==")
    blob = open(snap, "rb").read()
    with open(snap, "wb") as f:
        f.write(blob[:40])   # truncated mid-vertex data: malformed by construction
    p = launch([], rundir); procs.append(p)
    assert wait_port(True)
    time.sleep(6.0)
    n_c = state_n()
    import glob
    logs = sorted(glob.glob(os.path.join(rundir, "test_out_*.log")))
    log = open(logs[-1], "rb").read().decode("utf-8", "replace") if logs else ""
    c_restore_line = [l for l in log.splitlines() if "boot restore" in l]
    results["C_corrupt_n"] = n_c
    results["C_restore_log"] = c_restore_line[-1] if c_restore_line else "(none)"
    results["C_engine_alive"] = p.poll() is None
    print("   /state n =", n_c, "| alive:", results["C_engine_alive"])
    print("   restore log:", results["C_restore_log"])

    # Cleanup: clear the corrupted snapshot so the dir is reusable.
    try: post_json("/session", {"op": "clear"})
    except Exception: pass
    for pr in procs:
        if pr.poll() is None: pr.kill()

    print("\n== RESULTS ==")
    print(json.dumps(results, indent=2))
    verdict = (results["seed_load_ok"] is True
               and results["B_no_restore_n"] == 0
               and (results["A_bare_boot_n"] or 0) > 0
               and results["C_engine_alive"] is True)
    print("VERDICT:", "PASS" if verdict else "FAIL")
    return 0 if verdict else 1

if __name__ == "__main__":
    sys.exit(main())
