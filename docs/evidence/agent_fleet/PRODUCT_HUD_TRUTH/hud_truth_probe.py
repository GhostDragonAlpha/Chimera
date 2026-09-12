"""product-hud-truth-01 — the PR #97 probe protocol, re-run on the fixed engine.

Run only with this task's engine/GPU reservation (rtx4090 + engine_demo).
Preregistration: PREREGISTRATION.md in this directory (committed before any
code or run). Protocol identity: product_feel_probe.py (PR #97, integrated) —
same rig pair, same joint-selection rule, same REST->PERTURB->HOLD->RESPONSE
right-arm script, same fixed camera, same 10 fps declared clip, same 6 ordered
keyframes, same capture endpoints. DECLARED ADDITIONS (preregistered):
  (a) the probe pins the show clock (POST /show {"playing":false} once — no
      ownership effect) and drives the declared interaction timeline through
      the product's own scrub (POST /show {"time": i*0.1} per frame);
  (b) numeric verification captures at each keyframe (/studio_chrome,
      /joints, /show, /reel) — they do not alter what the judge sees.

    python hud_truth_probe.py render
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]   # the repo root (4 levels up from this file)
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
from engine_demo import _launch, _wait_ready, _stop_owned, _port_busy  # noqa: E402

PORT = 8103
BASE = f"http://127.0.0.1:{PORT}"
EXE = ROOT / ".tmp/engine_build/hudtruth/Release/chimera_engine.exe"
OUT = Path(__file__).parent
FPS = 10
N_FRAMES = 45
PEAK = 0.6  # the declared mid-ROM fraction (PR #97 preregistration)
KEYFRAMES = (0, 12, 20, 25, 35, 44)  # the same ordered keyframes as PR #97
RUN_ID = os.environ.get("HUD_TRUTH_RUN_ID", "run2")   # per-run runtime identity

RECORDS: list[dict] = []
KEYFRAME_DOCS: list[dict] = []


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
    """THE DECLARED SELECTION RULE (PR #97 PREREGISTRATION.md): the R-arm chain
    by exact name match — shoulder_R first, then elbow_R."""
    joints = doc.get("joints") or []
    by_lower = {str(j.get("name", "")).lower(): j for j in joints}
    shoulder = by_lower.get("shoulder_r")
    elbow = by_lower.get("elbow_r")
    got, rule = [], "no match"
    if shoulder and elbow:
        got, rule = [shoulder, elbow], "exact name match shoulder_R + elbow_R"
    record("script.joint_selection", "PASS" if len(got) == 2 else "FAIL",
           {"rule": rule, "joints": [(j.get("name"), j.get("ext"), j.get("flex")) for j in got]})
    return got


def capture_keyframe_docs(i: int) -> None:
    """Declared addition (b): the numeric verification channels at keyframe i.
    /studio_chrome serves the exact strings build_chrome drew last frame."""
    try:
        chrome = jreq("GET", "/studio_chrome")
    except Exception as e:                       # recorded, never fatal
        chrome = {"error": repr(e)}
    try:
        joints = jreq("GET", "/joints")
    except Exception as e:
        joints = {"error": repr(e)}
    try:
        show = jreq("GET", "/show")
    except Exception as e:
        show = {"error": repr(e)}
    try:
        reel = jreq("GET", "/reel")
    except Exception as e:
        reel = {"error": repr(e)}
    KEYFRAME_DOCS.append({"i": i, "studio_chrome": chrome, "joints": joints,
                          "show": show, "reel": reel,
                          "wall_s": time.time()})
    if i in (0, 20):
        record("keyframe.docs", "CAPTURED", {"i": i,
               "hud_rows": chrome.get("rows", [])[:2],
               "show_t": show.get("t")})


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
        proc, _ = _launch(EXE, PORT, ROOT / f".tmp/engine_runtime/hudtruth-{RUN_ID}")
        _wait_ready(proc, PORT)
        record("launch", "PASS", {"pid": proc.pid, "port": PORT,
                                  "exe_sha256": hashlib.sha256(EXE.read_bytes()).hexdigest()})

        # 1) load the committed mesh + rig pair (same as PR #97)
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

        # 1b) DECLARED ADDITION (a): pin the show clock. The sweep is not the
        # motion (joints_on_ defaults off); the scrub is then the ONLY writer
        # of show_time_, so the declared interaction timeline is exact.
        jreq("POST", "/show", {"playing": False})
        record("show.pinned", "PASS", {"playing": False, "owner_untouched": True})

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
            bound = flex if flex > 0 else ext
            peak[j["name"]] = rest[j["name"]] + PEAK * bound
        record("script.peaks", "MEASURED", {"peaks_deg": peak})

        # 3) fixed camera (one variable: the pose) — same 3/4 view as PR #97
        extent = float(body_row.get("detail", "r=10.0").split("r=")[-1].rstrip(",") or 10.0)
        jreq("POST", "/camera", {"cam_radius": 2.7 * max(extent, 1.0),
                                 "cam_theta": 0.5, "cam_phi": 0.35})

        # 4) the frame-indexed script (PR #97's, unchanged) + the declared
        # timeline drive: POST /show {"time": i*0.1} — no "playing" key, so
        # pose ownership is untouched (main.cpp only resets owner on playing).
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
            jreq("POST", "/show", {"time": round(i / FPS, 6)})   # declared timeline
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
            if i in KEYFRAMES:
                capture_keyframe_docs(i)
            if i % 10 == 0:
                record("capture.frame", "PASS" if st == 200 and st2 == 200 else "FAIL",
                       {"i": i, "thetas": thetas})
        record("capture.frames", "PASS" if len(paths_glass) == N_FRAMES else "FAIL",
               {"n": len(paths_glass)})

        # 5) encode the judge artifact (the product surface) + the clean twin
        mp4_glass = cpp_bridge.encode_movie(paths_glass, str(OUT / "product_hud_after.mp4"),
                                            fps=FPS)
        mp4_frame = cpp_bridge.encode_movie(paths_frame, str(OUT / "product_hud_after_frame.mp4"),
                                            fps=FPS)
        record("encode.movie", "PASS",
               {"glass": mp4_glass, "frame": mp4_frame,
                "glass_sha256": hashlib.sha256(Path(mp4_glass).read_bytes()).hexdigest()})
        (OUT / "render_records.json").write_text(json.dumps(RECORDS, indent=1, default=str))
        (OUT / "render_records.txt").write_text("\n".join(
            f"[{r['verdict']}] {r['name']} {json.dumps(r['detail'], default=str)}"
            for r in RECORDS) + "\n")
        (OUT / "keyframe_docs.json").write_text(json.dumps(KEYFRAME_DOCS, indent=1, default=str))
        (OUT / "keyframe_docs.txt").write_text("\n".join(
            f"i={d['i']} wall={d['wall_s']:.3f} hud_rows={json.dumps(d['studio_chrome'].get('rows', []))} "
            f"show={json.dumps({k: d['show'].get(k) for k in ('time', 'playing', 'clock')})} "
            f"joints_owner={d['joints'].get('owner')} "
            f"thetas={json.dumps({j.get('name'): j.get('theta') for j in (d['joints'].get('joints') or []) if j.get('name') in ('shoulder_R', 'elbow_R')})}"
            for d in KEYFRAME_DOCS) + "\n")
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
