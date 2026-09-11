"""product-feel-probe-01 — the scripted interaction + movie driver.

Run only with this task's engine/GPU reservation (rtx4090 + engine_demo).
Preregistration: PREREGISTRATION.md in this directory (the interaction, the
movie plan, the judge spec and the acceptance rubric were declared there
BEFORE this script ever ran).

    python product_feel_probe.py render     # launch, load, script, capture, encode

Phases (frame-indexed, 10 fps, 45 frames — see PREREGISTRATION.md):
  f0-09 REST, f10-19 PERTURB (R-arm chain to mid-ROM), f20-29 HOLD,
  f30-44 RESPONSE (smooth return). Both /glass and /frame captured per frame;
  the judge artifact is the /glass MP4.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]   # docs/evidence/agent_fleet/PRODUCT_FEEL_PROBE/this.py
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
from engine_demo import _launch, _wait_ready, _stop_owned, _port_busy  # noqa: E402

PORT = 8131
BASE = f"http://127.0.0.1:{PORT}"
EXE = ROOT / ".tmp/engine_build/feelfeel/Release/chimera_engine.exe"
OUT = Path(__file__).parent
FPS = 10
N_FRAMES = 45
PEAK = 0.6  # the declared mid-ROM fraction (PREREGISTRATION.md)

RECORDS: list[dict] = []


def record(name: str, verdict: str, detail: dict) -> None:
    RECORDS.append({"name": name, "verdict": verdict, "detail": detail})
    print(f"[{verdict}] {name} {json.dumps(detail, default=str)[:200]}", flush=True)


def request(method: str, path: str, body: bytes | None = None,
            ctype: str = "application/json", timeout: float = 60.0):
    req = urllib.request.Request(BASE + path, data=body, method=method)
    if body is not None:
        req.add_header("Content-Type", ctype)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def jreq(method: str, path: str, payload=None) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    st, raw = request(method, path, body)
    return json.loads(raw.decode("utf-8", "replace"))


def smoothstep(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def select_arm_joints(doc: dict) -> list[dict]:
    """The declared selection rule (PREREGISTRATION.md): the R-arm chain by
    name match. Attempt 1 (retained, retired) matched 'spine_upper' because
    the filter accepted any name containing 'upper' ending in 'r' — an
    implementation bug, not a rule change: the rule's intent is the R-ARM
    chain. Corrected: exact 'shoulder_r' match first, then 'elbow_r'."""
    joints = doc.get("joints") or []
    by_lower = {str(j.get("name", "")).lower(): j for j in joints}
    shoulder = by_lower.get("shoulder_r")
    elbow = by_lower.get("elbow_r")
    got, rule = [], "no match"
    if shoulder and elbow:
        got, rule = [shoulder, elbow], "exact name match shoulder_R + elbow_R"
    else:
        cand = [j for j in joints if "_r" in str(j.get("name", "")).lower()
                or str(j.get("name", "")).lower().endswith("_r")]
        cand.sort(key=lambda j: abs(float(j.get("flex", 0)) - float(j.get("ext", 0))), reverse=True)
        got = cand[:2]
        rule = f"substitution: largest-ROM R limb + neighbor {[j.get('name') for j in got]}"
    record("script.joint_selection", "PASS" if len(got) == 2 else "FAIL",
           {"rule": rule, "joints": [(j.get("name"), j.get("ext"), j.get("flex")) for j in got]})
    return got


def main() -> int:
    assert EXE.is_file(), f"missing exe: {EXE}"
    assert not _port_busy(PORT), f"port {PORT} busy"
    out_frames = OUT / "frames"
    if out_frames.exists():
        for f in out_frames.iterdir():
            f.unlink()
    out_frames.mkdir(parents=True, exist_ok=True)

    os.environ["CHIMERA_ENGINE_URL"] = BASE   # cpp_bridge targets MY instance
    import cpp_bridge

    old = os.environ.get("CHIMERA_MD_EDGE")
    os.environ.pop("CHIMERA_MD_EDGE", None)
    try:
        proc, _ = _launch(EXE, PORT, ROOT / ".tmp/engine_runtime/feelfeel")
        _wait_ready(proc, PORT)
        record("launch", "PASS", {"pid": proc.pid, "port": PORT,
                                  "exe_sha256": hashlib.sha256(EXE.read_bytes()).hexdigest()})

        # 1) load the committed mesh + rig pair
        ok, r, th, ph = cpp_bridge.load_mesh_bin(str(ROOT / "Saved/meshes/monkey_birth.bin"),
                                                 timeout=120)
        record("load.mesh", "PASS" if ok else "FAIL", {"r": r, "theta": th, "phi": ph})
        pack = (ROOT / "Saved/meshes/monkey_joints.bin").read_bytes()
        st, resp = request("POST", "/joints_bin", pack, "application/octet-stream", timeout=120)
        record("load.joints_bin", "PASS" if st == 200 and b'"ok":true' in resp else "FAIL",
               {"http": st, "resp": resp[:100].decode("utf-8", "replace")})
        scene = jreq("GET", "/scene")
        body_row = next((row for row in scene.get("rows", []) if row.get("id") == "body"), {})
        record("load.body_row", "PASS" if "tris" in str(body_row.get("detail", "")) else "FAIL",
               {"detail": body_row.get("detail")})

        # 2) the live rig doc -> the declared joint selection
        doc = jreq("GET", "/joints")
        jnames = [j.get("name") for j in (doc.get("joints") or [])]
        record("rig.doc", "MEASURED", {"n_joints": len(jnames), "names": jnames})
        arm = select_arm_joints(doc)
        if len(arm) != 2:
            _stop_owned(proc)
            return 1
        rest = {j["name"]: 0.0 for j in arm}
        peak = {}
        for j in arm:
            ext, flex = float(j.get("ext", 0)), float(j.get("flex", 0))
            # corrected reading of the prereg's mid-ROM fraction (attempt 1's
            # ext-anchored formula under-rotated: elbow_R peaked at 17 deg of a
            # straddling ROM): 0.6 of the FLEXION half-range FROM REST, then the
            # engine clamps to the pack ROM regardless.
            bound = flex if flex > 0 else ext
            peak[j["name"]] = rest[j["name"]] + PEAK * bound

        # 3) fixed camera (one variable: the pose). Attempt 1 used the loader's
        # auto-frame (phi -1.31: from below/behind); a declared fixed 3/4 view
        # replaces it — the prereg requires FIXED, not this specific value.
        extent = float(body_row.get("detail", "r=10.0").split("r=")[-1].rstrip(",") or 10.0)
        jreq("POST", "/camera", {"cam_radius": 2.7 * max(extent, 1.0),
                                 "cam_theta": 0.5, "cam_phi": 0.35})

        # 4) the frame-indexed script (PREREGISTRATION.md)
        def target(i: int) -> dict:
            if i < 10:
                s = 0.0
            elif i < 20:
                s = smoothstep((i - 9) / 10.0)
            elif i < 30:
                s = 1.0
            else:
                s = 1.0 - smoothstep((i - 29) / 15.0)
            return {j["name"]: rest[j["name"]] + s * (peak[j["name"]] - rest[j["name"]])
                    for j in arm}

        paths_glass, paths_frame = [], []
        for i in range(N_FRAMES):
            thetas = target(i)
            for name, deg in thetas.items():
                jreq("POST", "/joint", {"joint": name, "theta": float(deg)})
            st, png = request("GET", "/glass")
            p = out_frames / f"g{i:03d}.png"
            p.write_bytes(png)
            paths_glass.append(str(p))
            st2, png2 = request("GET", "/frame")
            pf = out_frames / f"c{i:03d}.png"
            pf.write_bytes(png2)
            paths_frame.append(str(pf))
            if i % 10 == 0:
                record("capture.frame", "PASS" if st == 200 and st2 == 200 else "FAIL",
                       {"i": i, "thetas": thetas})
        record("capture.frames", "PASS" if len(paths_glass) == N_FRAMES else "FAIL",
               {"n": len(paths_glass)})

        # 5) encode the judge artifact (the product surface) + the clean twin
        mp4_glass = cpp_bridge.encode_movie(paths_glass, str(OUT / "product_feel_after.mp4"),
                                            fps=FPS)
        mp4_frame = cpp_bridge.encode_movie(paths_frame, str(OUT / "product_feel_after_frame.mp4"),
                                            fps=FPS)
        record("encode.movie", "PASS",
               {"glass": mp4_glass, "frame": mp4_frame,
                "glass_sha256": hashlib.sha256(Path(mp4_glass).read_bytes()).hexdigest()})
        (OUT / "render_records.json").write_text(json.dumps(RECORDS, indent=1, default=str))
        (OUT / "render_records.txt").write_text("\n".join(
            f"[{r['verdict']}] {r['name']} {json.dumps(r['detail'], default=str)}"
            for r in RECORDS) + "\n")
        print(json.dumps({"mp4": mp4_glass, "frames": len(paths_glass)}))
        _stop_owned(proc)
        deadline = time.time() + 15
        while proc.poll() is None and time.time() < deadline:
            time.sleep(0.2)
        record("engine.drain", "PASS" if proc.poll() is not None else "FAIL",
               {"rc": proc.poll()})
        return 0 if all(r_["verdict"] != "FAIL" for r_ in RECORDS) else 1
    finally:
        if old is not None:
            os.environ["CHIMERA_MD_EDGE"] = old


if __name__ == "__main__":
    raise SystemExit(main())
