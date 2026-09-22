"""engine_import_parity.py -- THE ENGINE-SIDE FENCES (lane mesh-parse-20260920).

F1-PARITY: the SAME engine build, fresh --no-restore boot per run:
  boot A: POST 'O' + standing_body.obj   (the landed slow route)
  boot B: POST 'G' + standing_body.glb   (the admission cache route)
  boot C,D,E: POST 'G' again (route determinism)
Compared: /mesh_import response text (the stats), /verts payload sha,
/topology payload sha, settled start-state /verts sha, first-poll /verts sha.
The import response text and the served mesh must be byte-identical across
routes. The landed bank's settled start sha (8c040418...) is corroboration
only -- the preregistered pass condition is equality across THIS pair.

F2-BAR (isolated half): t_mesh_import per boot, upload timed separately from
the total (raw http.client), so the engine-side residue beyond the parse is
visible.

Writes engine_import_parity.json HERE. The landed lane's committed sweep
(sweep_own_engines.ps1) runs first: only engines matching THIS worktree's
exe are killed.
"""
from __future__ import annotations

import hashlib
import http.client
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SLICE = ROOT / "tools" / "playable_slice"
LANDED = HERE.parent / "slice_real_body_20260920"
sys.path.insert(0, str(SLICE))
import scene_boot as sb  # noqa: E402

EXE = ROOT / ".tmp" / "slice_build" / "Release" / "chimera_engine.exe"
LANDED_START_SHA = "8c040418fe5bfaac6f56004364d033429a8495bb5b78d2dff5545427ab2e9001"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sweep_own_engines() -> None:
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(LANDED / "sweep_own_engines.ps1"), "-ExePath", str(EXE)],
        capture_output=True, text=True)


def post_split(url: str, path: str, body: bytes, timeout: float) -> dict:
    """POST with upload timed separately from the response wait: the residue
    beyond the upload is the handler (state scan + import + handoff)."""
    host, port = url.split("//")[1].split(":")
    conn = http.client.HTTPConnection(host, int(port), timeout=timeout)
    t0 = time.perf_counter()
    conn.putrequest("POST", path)
    conn.putheader("Content-Type", "application/octet-stream")
    conn.putheader("Content-Length", str(len(body)))
    conn.endheaders()
    t1 = time.perf_counter()
    step = 1 << 20
    for i in range(0, len(body), step):
        conn.send(body[i:i + step])
    t2 = time.perf_counter()
    resp = conn.getresponse()
    raw = resp.read()
    t3 = time.perf_counter()
    conn.close()
    return {"response": raw, "t_headers_s": round(t1 - t0, 3),
            "t_upload_s": round(t2 - t1, 3),
            "t_response_wait_s": round(t3 - t2, 3),
            "t_total_s": round(t3 - t0, 3)}


def boot_engine(url: str) -> float:
    t0 = time.perf_counter()
    sb.wait_engine(url)
    return round(time.perf_counter() - t0, 2)


def settle_and_shas(url: str) -> dict:
    """Arm gravity, ride the real settle to rest, then sha the served state."""
    g = sb.http_post(url, "/tick_gravity", b'{"on":true}',
                     ctype="application/json")
    t0 = time.perf_counter()
    st = sb.wait_settled(url, timeout=30)
    last, last_t = None, time.perf_counter()
    deadline = last_t + 120.0
    while time.perf_counter() < deadline:
        cur = sb.http_get_json(url, "/tick_state")
        ry, vy = float(cur.get("root_y", 0.0)), abs(float(cur.get("root_vy", 1.0)))
        now = time.perf_counter()
        if last is not None and abs(ry - last) < 1e-7 and vy < 1e-5 \
                and now - last_t >= 2.0:
            break
        if last is None or abs(ry - last) >= 1e-7:
            last, last_t = ry, now
        time.sleep(0.1)
    v1 = sb.http_get_raw(url, "/verts")
    v2 = sb.http_get_raw(url, "/verts")
    topo = sb.http_get_raw(url, "/topology")
    return {"gravity_ok": bool(g.get("ok")),
            "settled_root_y": st.get("root_y"),
            "t_settle_s": round(time.perf_counter() - t0, 2),
            "verts_poll1_sha": sha(v1), "verts_poll2_sha": sha(v2),
            "verts_bytes": len(v1), "topology_sha": sha(topo)}


def run_boot(tag: str, kind: str, payload: bytes) -> dict:
    port = sb.free_port()
    rec = {"boot": tag, "kind": kind, "payload_bytes": len(payload),
           "port": port}
    proc = subprocess.Popen(
        [str(EXE), str(port), "--no-restore", "--hidden"],
        cwd=str(EXE.parent), stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    url = f"http://127.0.0.1:{port}"
    try:
        rec["t_engine_ready_s"] = boot_engine(url)
        r = post_split(url, "/mesh_import", kind.encode() + payload,
                       timeout=900)
        rec["import_response_text"] = r["response"].decode("utf-8", "replace")
        rec["t_mesh_import_s"] = r["t_total_s"]
        rec["t_upload_s"] = r["t_upload_s"]
        rec["t_response_wait_s"] = r["t_response_wait_s"]
        ok = json.loads(r["response"]).get("ok")
        rec["import_ok"] = bool(ok)
        if rec["import_ok"]:
            rec.update(settle_and_shas(url))
    finally:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                       capture_output=True)
        time.sleep(0.8)
    return rec


def main() -> int:
    sweep_own_engines()
    obj, _rec = sb.build_real_body()
    glb = (SLICE / "standing_body.glb").read_bytes()
    out = {"falsifier": "F1-PARITY + F2-BAR(isolated)",
           "engine": str(EXE),
           "laned_start_sha_corroboration": LANDED_START_SHA,
           "boots": []}
    plan = [("A", "O", obj), ("B", "G", glb),
            ("C", "G", glb), ("D", "G", glb), ("E", "G", glb)]
    for tag, kind, payload in plan:
        print(f"boot {tag} ({kind}, {len(payload)} B) ...", flush=True)
        r = run_boot(tag, kind, payload)
        out["boots"].append(r)
        print(json.dumps({k: r[k] for k in r if k != "import_response_text"},
                         indent=1), flush=True)
        (HERE / "engine_import_parity.json").write_text(
            json.dumps(out, indent=1), encoding="utf-8")

    # ── the comparisons ──
    a, b = out["boots"][0], out["boots"][1]
    g_boots = out["boots"][1:]
    checks = {}
    checks["import_response_text_equal_A_B"] = \
        a["import_response_text"] == b["import_response_text"]
    checks["import_ok_all"] = all(x["import_ok"] for x in out["boots"])
    if a["import_ok"] and b["import_ok"]:
        checks["verts_first_poll_equal_A_B"] = \
            a["verts_poll1_sha"] == b["verts_poll1_sha"]
        checks["topology_equal_A_B"] = \
            a["topology_sha"] == b["topology_sha"]
        checks["settled_state_equal_A_B"] = \
            a["verts_poll1_sha"] == b["verts_poll1_sha"] and \
            a["settled_root_y"] == b["settled_root_y"]
        checks["g_route_determinism_x4"] = len(
            {x["verts_poll1_sha"] for x in g_boots}) == 1 and len(
            {x["topology_sha"] for x in g_boots}) == 1 and len(
            {x["import_response_text"] for x in g_boots}) == 1
        checks["serving_stable_across_polls"] = all(
            x["verts_poll1_sha"] == x["verts_poll2_sha"] for x in out["boots"])
        checks["settled_sha_matches_landed_bank"] = \
            a["verts_poll1_sha"] == LANDED_START_SHA
        checks["stats"] = json.loads(a["import_response_text"])
    checks["t_mesh_import_s_per_boot"] = {
        x["boot"]: x["t_mesh_import_s"] for x in out["boots"]}
    checks["t_upload_s_per_boot"] = {
        x["boot"]: x["t_upload_s"] for x in out["boots"]}
    out["checks"] = checks
    out["f1_pass"] = bool(
        checks["import_response_text_equal_A_B"] and
        checks["import_ok_all"] and
        checks.get("verts_first_poll_equal_A_B") and
        checks.get("topology_equal_A_B") and
        checks.get("g_route_determinism_x4"))
    (HERE / "engine_import_parity.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(checks, indent=1))
    return 0 if out["f1_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
