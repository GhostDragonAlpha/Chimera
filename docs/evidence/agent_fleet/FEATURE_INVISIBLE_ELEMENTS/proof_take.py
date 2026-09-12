"""proof_take.py — feature-invisible-elements-01 deliverable C (gates T3).

    python proof_take.py

Run only with this task's granted resources (rtx4090 + engine_demo) and the
controller queue satisfied. Launches a PRIVATE fleet-built engine under this
slot's .tmp (never the operator's build path, never port 8080), starts the
viewer service on 8204, and films ONE element (water: the CA field from
POST /water_bin · GET /water_state) through the full two-phase cycle:

  invisible  ->  TOGGLE ON (visible; the judge can name it)
             ->  gate proves (auto-revert to invisible)   [Law 2]
             ->  TOGGLE ON again (a proven element deliberately re-shown)
             ->  TOGGLE OFF (invisible again)             [both ways, on camera]

 ZERO C++ is asserted at runtime: the launched build's main.cpp must hash to
 the branch HEAD's blob. Everything else is the viewer's public API.

 The take never touches /water_vis (the engine's own tint): the filmed element
 is the DATA-ONLY plane made visible by the viewer's overlay — the engine's
 renderable-but-inactive water tint stays OFF for the whole take (recorded).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.resolve().parents[3]             # .../docs/evidence/agent_fleet/<LANE>
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "product_features"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))

from engine_demo import _launch, _wait_ready, _stop_owned, _port_busy  # noqa: E402
from product_viewer.server import make_server as viewer_server         # noqa: E402

ENGINE_PORT = 8104                            # slot-04 candidate port
VIEWER_PORT = 8204                            # engine + 100 (the lanes' pattern)
ENGINE = f"http://127.0.0.1:{ENGINE_PORT}"
VIEWER = f"http://127.0.0.1:{VIEWER_PORT}"
EXE = ROOT / ".tmp/engine_build/feature-invisible-elements-01/Release/chimera_engine.exe"
RUN_ID = f"feature-invisible-elements-01-{time.strftime('%Y%m%d-%H%M%S')}"
RUNTIME = ROOT / ".tmp/engine_runtime" / RUN_ID

# water substrate via the INTEGRATED water-room module (committed at base):
# build_substrate / pack_water_bin / the measured solver constants. Read-only
# reuse of integrated code; this lane derives nothing physical.
import water_room as wr                       # noqa: E402
import cpp_bridge                             # noqa: E402

FRAME_PAUSE_S = 1.2                           # annotated cadence bound
MAX_PHASE_FRAMES = 40

RECORDS: list[dict] = []


def record(name: str, verdict: str, detail) -> None:
    RECORDS.append({"name": name, "verdict": verdict, "detail": detail})
    print(f"[{verdict}] {name} {json.dumps(detail, default=str)[:200]}", flush=True)


def request(base: str, method: str, path: str, body=None,
            ctype: str = "application/json", timeout: float = 60.0):
    req = urllib.request.Request(base + path,
                                 data=body if isinstance(body, (bytes, type(None)))
                                 else json.dumps(body).encode(),
                                 method=method)
    if body is not None:
        req.add_header("Content-Type", ctype)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def jreq(base: str, method: str, path: str, payload=None, timeout: float = 60.0) -> dict:
    st, raw = request(base, method, path,
                      None if payload is None else json.dumps(payload).encode(),
                      timeout=timeout)
    return json.loads(raw.decode("utf-8", "replace"))


def water_status(viewer: dict | None = None) -> dict:
    d = viewer if viewer is not None else jreq(VIEWER, "GET", "/api/visibility")
    for el in d.get("elements", []):
        if el["name"] == "water":
            return el
    return {}


def grab_annotated(i: int, phase: str, frames_dir: Path) -> dict:
    t0 = time.time()
    st, png = request(VIEWER, "GET", "/api/live/annotated", timeout=45)
    p = frames_dir / f"a{i:03d}_{phase}.png"
    p.write_bytes(png)
    vis = water_status()
    return {"i": i, "phase": phase, "png": str(p), "sha256": hashlib.sha256(png).hexdigest(),
            "bytes": len(png), "dt_wall": round(time.time() - t0, 3),
            "visible": vis.get("visible"), "state": vis.get("state"),
            "proven": vis.get("proven"), "gate": vis.get("last_gate")}


def identity_check() -> dict:
    """With nothing visible the annotated pane IS the ring's engine glass."""
    jreq(VIEWER, "POST", "/api/capture", {"on": False})       # pause the observer
    time.sleep(0.2)
    st, ring_png = request(VIEWER, "GET", "/api/snapshot/latest", timeout=45)
    st2, ann_png = request(VIEWER, "GET", "/api/live/annotated", timeout=45)
    jreq(VIEWER, "POST", "/api/capture", {"on": True})        # resume
    same = hashlib.sha256(ring_png).hexdigest() == hashlib.sha256(ann_png).hexdigest()
    return {"identical": bool(same and st == 200 and st2 == 200),
            "ring_sha": hashlib.sha256(ring_png).hexdigest()[:16],
            "ann_sha": hashlib.sha256(ann_png).hexdigest()[:16]}


def main() -> int:
    frames_dir = HERE / "take_frames"
    frames_dir.mkdir(exist_ok=True)
    if _port_busy(ENGINE_PORT):
        record("precheck.port", "FAIL", {"port": ENGINE_PORT,
                                         "error": "busy — collision is a named refusal"})
        return 2
    if not EXE.is_file():
        record("precheck.exe", "FAIL", {"exe": str(EXE)})
        return 2
    main_cpp = ROOT / "ChimeraEngine/engine/main.cpp"
    src_sha = hashlib.sha256(main_cpp.read_bytes()).hexdigest()

    proc = None
    viewer = None
    try:
        # ── launch the private engine (visible, non-headless, slot-owned) ──
        wr.BASE = ENGINE                      # the substrate module reads MY instance
        os.environ["CHIMERA_ENGINE_URL"] = ENGINE
        proc, manifest = _launch(EXE, ENGINE_PORT, RUNTIME)
        _wait_ready(proc, ENGINE_PORT)
        exe_sha = hashlib.sha256(EXE.read_bytes()).hexdigest()
        record("launch", "PASS", {"pid": proc.pid, "port": ENGINE_PORT,
                                  "runtime_cwd": str(manifest.parent), "exe_sha256": exe_sha,
                                  "main_cpp_sha256": src_sha})
        import subprocess
        blob = subprocess.run(["git", "-C", str(ROOT), "rev-parse",
                               "HEAD:ChimeraEngine/engine/main.cpp"],
                              capture_output=True, text=True).stdout.strip()
        blob_bytes = subprocess.run(["git", "-C", str(ROOT), "show", blob],
                                    capture_output=True).stdout
        same_src = hashlib.sha256(blob_bytes).hexdigest() == src_sha
        record("zero_cpp.main_cpp_matches_HEAD", "PASS" if same_src else "FAIL",
               {"worktree_sha": src_sha[:16], "HEAD_blob_sha":
                hashlib.sha256(blob_bytes).hexdigest()[:16]})

        # ── the creature + the DRY water substrate (public HTTP only) ──
        ok, r, th, ph = cpp_bridge.load_mesh_bin(str(wr.MESH_BIN), timeout=120)
        record("load.mesh", "PASS" if ok else "FAIL", {"r": r, "theta": th, "phi": ph})
        substrate = wr.build_substrate(wr.MESH_BIN)
        wr.ST = substrate
        st, resp = request(ENGINE, "POST", "/water_bin", wr.pack_water_bin(substrate),
                           "application/octet-stream", timeout=120)
        record("load.water_bin", "PASS" if b'"ok":true' in resp else "FAIL",
               {"resp": resp[:60].decode("utf-8", "replace"),
                "n_cells": substrate["n"]})
        jreq(ENGINE, "POST", "/camera",
             {"cam_radius": wr.CAM_RADIUS_FACTOR * 10.0, "cam_theta": 0.5,
              "cam_phi": 0.35})
        record("camera.set", "PASS", {"cam_radius": wr.CAM_RADIUS_FACTOR * 10.0,
                                      "cam_theta": 0.5, "cam_phi": 0.35})
        record("engine_water_vis", "OFF (by design)",
               {"note": "the filmed element is the data-only plane drawn by the "
                        "viewer; the engine's renderable-but-inactive tint stays off"})

        # ── the viewer service ──
        viewer = viewer_server(ENGINE, VIEWER_PORT)
        threading.Thread(target=viewer.serve_forever, daemon=True).start()
        record("viewer.up", "PASS", {"port": VIEWER_PORT})
        for _ in range(60):                    # wait for the ring to fill
            if jreq(VIEWER, "GET", "/api/health").get("ring", {}).get("count", 0) >= 3:
                break
            time.sleep(1.0)

        frames: list[dict] = []
        idx = 0

        # ── PHASE inv: INVISIBLE baseline ────────────────────────────────────
        jreq(VIEWER, "POST", "/api/visibility", {"element": "water",
                                                 "action": "reset"})
        for k in range(5):
            frames.append(grab_annotated(idx, "inv", frames_dir)); idx += 1
            time.sleep(FRAME_PAUSE_S)
        ident0 = identity_check()
        record("gate.T3-inv-identity", "PASS" if ident0["identical"] else "FAIL", ident0)
        record("phase.inv.status", "MEASURED", water_status())

        # ── PHASE vis: TOGGLE ON (on camera) + the pour ──────────────────────
        r1 = jreq(VIEWER, "POST", "/api/visibility", {"element": "water", "on": True})
        record("toggle.on", "PASS" if r1.get("visible") else "FAIL", r1)
        st, resp = request(ENGINE, "POST", "/water_clock",
                           {"on": True, "steps": wr.STEPS_PER_FRAME,
                            "dt": wr.DT_MACRO, "inj_target": substrate["inj_target"],
                            "inj_count": wr.INJ_COUNT})
        record("action.pour_on", "PASS" if b'"ok":true' in resp else "FAIL",
               {"inj_target": substrate["inj_target"], "inj_count": wr.INJ_COUNT})
        seen_visible = 0
        for k in range(MAX_PHASE_FRAMES):
            f = grab_annotated(idx, "vis", frames_dir); idx += 1
            frames.append(f)
            seen_visible += 1 if f["visible"] else 0
            if water_status().get("proven"):
                f["phase_note"] = "gate passed this frame"
                break
            time.sleep(FRAME_PAUSE_S)
        record("phase.vis.frames", "MEASURED",
               {"visible_frames": seen_visible, "status": water_status()})

        # ── PHASE prov: the AUTO-REVERT lands on camera ──────────────────────
        reverted_at = None
        for k in range(MAX_PHASE_FRAMES):
            f = grab_annotated(idx, "prov", frames_dir); idx += 1
            frames.append(f)
            if f["visible"] is False and f["proven"] is True:
                reverted_at = f["i"]
                break
            time.sleep(FRAME_PAUSE_S)
        for k in range(3):                     # the invisible-after-proof tail
            frames.append(grab_annotated(idx, "prov", frames_dir)); idx += 1
            time.sleep(FRAME_PAUSE_S)
        ident1 = identity_check()
        record("gate.T3-auto-revert", "PASS" if reverted_at is not None else "FAIL",
               {"reverted_at_frame": reverted_at, "status": water_status()})
        record("gate.T3-proven-identity", "PASS" if ident1["identical"] else "FAIL",
               ident1)

        # ── PHASE re: TOGGLE ON again (a proven element, deliberately) ───────
        jreq(VIEWER, "POST", "/api/visibility", {"action": "auto_prove", "on": False})
        r2 = jreq(VIEWER, "POST", "/api/visibility", {"element": "water", "on": True})
        record("toggle.on-again", "PASS" if r2.get("visible") else "FAIL",
               {"status": r2, "note": "auto_prove paced off so the OFF flip is "
                                      "the user's, not the gate's"})
        for k in range(5):
            frames.append(grab_annotated(idx, "re", frames_dir)); idx += 1
            time.sleep(FRAME_PAUSE_S)

        # ── PHASE off: TOGGLE OFF (both ways demonstrated) ───────────────────
        r3 = jreq(VIEWER, "POST", "/api/visibility", {"element": "water", "on": False})
        record("toggle.off", "PASS" if not r3.get("visible") else "FAIL", r3)
        for k in range(4):
            frames.append(grab_annotated(idx, "off", frames_dir)); idx += 1
            time.sleep(FRAME_PAUSE_S)
        ident2 = identity_check()
        record("gate.T3-toggle-both-ways",
               "PASS" if (r1.get("visible") and r2.get("visible")
                          and not r3.get("visible")) else "FAIL",
               {"on": bool(r1.get("visible")), "on_again": bool(r2.get("visible")),
                "off": not r3.get("visible")})
        record("gate.T3-off-identity", "PASS" if ident2["identical"] else "FAIL", ident2)

        # ── the motion is nameable: visible-phase frames DIFFER (it moves) ──
        vis_shas = {f["sha256"] for f in frames if f["phase"] == "vis"}
        record("gate.T3-visible-motion",
               "PASS" if len(vis_shas) >= 3 else "FAIL",
               {"distinct_visible_frames": len(vis_shas),
                "note": "the poured field moves; a frozen overlay could not name "
                        "itself as motion"})

        # ── the movie ──
        mp4_path = HERE / "take.mp4"
        out = Path(cpp_bridge.encode_movie([f["png"] for f in frames],
                                           str(mp4_path), fps=6))
        record("movie", "PASS" if out.is_file() and out.stat().st_size > 0 else "FAIL",
               {"frames": len(frames), "mp4_bytes": out.stat().st_size if out.is_file() else 0})

        # ── records ──
        with (HERE / "take_records.json").open("w", encoding="utf-8") as fh:
            json.dump({"records": RECORDS, "frames": frames}, fh, indent=1)
        head_sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                  capture_output=True, text=True).stdout.strip()
        identity = (
            f"task feature-invisible-elements-01 run {RUN_ID}\n"
            f"source HEAD: {head_sha}\n"
            f"main.cpp sha256: {src_sha}\n"
            f"exe sha256: {exe_sha}\n"
            f"engine port: {ENGINE_PORT}  viewer port: {VIEWER_PORT}\n"
            f"engine pid: {proc.pid}\n"
            f"runtime cwd: {cwd}\n"
            f"frames: {len(frames)}  mp4: {out.name}\n")
        with (HERE / "ENGINE_IDENTITY.txt").open("w", encoding="utf-8") as fh:
            fh.write(identity)
        fails = [r for r in RECORDS if r["verdict"] == "FAIL"]
        record("T3.summary", "PASS" if not fails else "FAIL",
               {"gates_failed": [f["name"] for f in fails]})
        return 0 if not fails else 3
    finally:
        if viewer is not None:
            viewer.shutdown()
        if proc is not None:
            _stop_owned(proc)
            record("engine.stop", "PASS", {"pid": proc.pid,
                                           "port_rebind_free": not _port_busy(ENGINE_PORT)})


if __name__ == "__main__":
    sys.exit(main())
