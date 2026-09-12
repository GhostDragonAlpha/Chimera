"""product-motion-sweep-01 — the multi-region motion sweep + movie driver.

Run only with this task's engine/GPU reservation (rtx4090 + engine_demo).
Preregistration: PREREGISTRATION.md in this directory (the 13-joint set, the
ROM fractions, the 70-frame phase schedule, the 6 judge keyframes, the
engine-truth gate and the blind rubric were declared there BEFORE this script
ever ran).

    python product_motion_sweep.py render     # launch, load, script, capture, encode

Phases (frame-indexed, 10 fps, 70 frames — see PREREGISTRATION.md):
  f000-009 REST, f010-019 ARMS-RISE, f020-029 LEGS-STEP (L leads, R +4 frames),
  f030-041 SPINE-TAIL-WAVE (tail lags spine), f041-049 FULL-HOLD,
  f050-069 RESPONSE (everything returns to rest).
Both /glass and /frame are captured every frame; the judge artifact is the
/glass channel; at the 6 declared keyframes a GET /joints readback of all 28
thetas is recorded (the engine-truth evidence, not UI text).

Public HTTP surface only: POST /joint, POST /camera, POST /joints_bin,
GET /joints, GET /scene, GET /glass, GET /frame — plus the two harness
wrappers the accepted PR #97 probe used (tools/engine_demo.py launch/stop;
cpp_bridge.load_mesh_bin == POST /mesh_bin, cpp_bridge.encode_movie).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]   # docs/evidence/agent_fleet/PRODUCT_MOTION_SWEEP/this.py
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
from engine_demo import _launch, _wait_ready, _stop_owned, _port_busy  # noqa: E402

PORT = 8104                                  # slot-04 candidate port (prereg)
BASE = f"http://127.0.0.1:{PORT}"
EXE = ROOT / ".tmp/engine_build/motionsweep/Release/chimera_engine.exe"
OUT = Path(__file__).parent
FPS = 10
N_FRAMES = 70                                # 7.0 s continuous take (prereg)
KEYFRAMES = (0, 19, 30, 41, 49, 69)          # the 6 judge keyframes (prereg)
CAM_RADIUS_FACTOR = 3.4                      # prereg: probe 2.7 + measured head-crop fix
ROM_TOL_DEG = 0.5                            # declared-vs-live ROM match tolerance
GATE_FRACTION = 0.5                          # full-hold engine-truth gate (prereg)

# The declared scripted set (PREREGISTRATION.md): region -> (fraction, joints)
SCRIPTED = {
    "arm":   (0.6, ["shoulder_L", "elbow_L", "shoulder_R", "elbow_R"]),
    "leg":   (0.6, ["hip_L", "knee_L", "hip_R", "knee_R"]),
    "spine": (0.3, ["spine_mid", "spine_upper"]),
    "tail":  (0.6, ["tail_base", "tail_mid", "tail_tip"]),
}
# Declared ROM windows parsed from the committed JNT3 pack
# (tools/gait_mirror.py::load_pack) and recorded in PREREGISTRATION.md.
DECLARED_ROM = {
    "shoulder_L": (-149.0, 60.0), "elbow_L": (-145.0, 125.0),
    "shoulder_R": (-149.0, 60.0), "elbow_R": (-145.0, 125.0),
    "hip_L": (-159.0, 119.0), "knee_L": (-131.0, 147.0),
    "hip_R": (-159.0, 119.0), "knee_R": (-131.0, 147.0),
    "spine_mid": (-124.5, 126.2), "spine_upper": (-169.7, 119.2),
    "tail_base": (-30.0, 87.1), "tail_mid": (-139.1, 138.7),
    "tail_tip": (-45.0, 45.0),
}

RECORDS: list[dict] = []


def record(name: str, verdict: str, detail: dict) -> None:
    RECORDS.append({"name": name, "verdict": verdict, "detail": detail})
    print(f"[{verdict}] {name} {json.dumps(detail, default=str)[:220]}", flush=True)


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


def region_wave(region: str, i: int) -> float:
    """The declared phase schedule (PREREGISTRATION.md), verbatim."""
    if region == "arm":
        return 0.0 if i < 10 else smoothstep((i - 9) / 10.0) if i < 20 else 1.0
    if region == "legL":
        return 0.0 if i < 20 else smoothstep((i - 19) / 6.0) if i < 26 else 1.0
    if region == "legR":
        return 0.0 if i < 24 else smoothstep((i - 23) / 6.0) if i < 30 else 1.0
    if region == "spine":
        return 0.0 if i < 30 else smoothstep((i - 29) / 10.0) if i < 40 else 1.0
    if region == "tail":
        return 0.0 if i < 32 else smoothstep((i - 31) / 9.0) if i < 41 else 1.0
    raise ValueError(region)


JOINT_REGION = {j: ("legL" if j.endswith("_L") else "legR") if r == "leg" else r
                for r, (_, js) in SCRIPTED.items() for j in js}


def take_value(joint: str, i: int) -> float:
    """Script value at frame i: the region wave, released by the RESPONSE law."""
    s = region_wave(JOINT_REGION[joint], i)
    if i >= 50:                              # f050-069 RESPONSE (prereg)
        s *= 1.0 - smoothstep((i - 49) / 20.0)
    return s


def verify_rig(doc: dict) -> bool:
    """Declared verification: the live rig doc must match the prereg table."""
    joints = {str(j.get("name", "")): j for j in (doc.get("joints") or [])}
    missing = [j for r in SCRIPTED for j in SCRIPTED[r][1] if j not in joints]
    record("rig.names", "PASS" if not missing else "FAIL",
           {"n_joints": len(joints), "missing": missing})
    bad_rom = []
    for jname, (ext, flex) in DECLARED_ROM.items():
        j = joints.get(jname)
        if j is None:
            continue
        if (abs(float(j.get("ext", 0)) - ext) > ROM_TOL_DEG
                or abs(float(j.get("flex", 0)) - flex) > ROM_TOL_DEG):
            bad_rom.append({"joint": jname, "live": [j.get("ext"), j.get("flex")],
                            "declared": [ext, flex]})
    record("rig.rom_match", "PASS" if not bad_rom else "FAIL",
           {"tolerance_deg": ROM_TOL_DEG, "mismatches": bad_rom})
    rest_bad = {jname: j.get("theta") for jname, j in joints.items()
                if abs(float(j.get("theta", 0.0))) > 0.01}
    record("rig.rest_zero", "PASS" if not rest_bad else "FAIL", {"nonzero": rest_bad})
    return not missing and not bad_rom and not rest_bad


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
        proc, _ = _launch(EXE, PORT, ROOT / ".tmp/engine_runtime/product-motion-sweep-01")
        _wait_ready(proc, PORT)
        record("launch", "PASS", {"pid": proc.pid, "port": PORT,
                                  "exe_sha256": hashlib.sha256(EXE.read_bytes()).hexdigest()})

        # 1) load the committed mesh + rig pair (identical to PR #97)
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

        # 2) the live rig doc -> declared verification (prereg)
        doc = jreq("GET", "/joints")
        jnames = [j.get("name") for j in (doc.get("joints") or [])]
        record("rig.doc", "MEASURED", {"n_joints": len(jnames), "names": jnames})
        if not verify_rig(doc):
            (OUT / "render_records.json").write_text(json.dumps(RECORDS, indent=1, default=str))
            (OUT / "render_records.txt").write_text(
                "\n".join(f"[{x['verdict']}] {x['name']} {json.dumps(x['detail'], default=str)}"
                          for x in RECORDS) + "\n")
            _stop_owned(proc)
            return 1

        # 3) peaks from the LIVE doc's ROM fields (the declared fractions)
        live = {str(j.get("name", "")): j for j in (doc.get("joints") or [])}
        rest, peak = {}, {}
        for region, (fraction, jnames_r) in SCRIPTED.items():
            for jname in jnames_r:
                j = live[jname]
                ext, flex = float(j.get("ext", 0)), float(j.get("flex", 0))
                bound = flex if flex > 0 else ext   # the probe's flexion-side law
                rest[jname] = float(j.get("theta", 0.0))
                peak[jname] = rest[jname] + fraction * bound
        record("script.peaks", "PASS",
               {"joints": {j: round(peak[j], 2) for j in peak},
                "fractions": {r: SCRIPTED[r][0] for r in SCRIPTED}})

        # 4) fixed camera (one variable: the pose) — prereg 3.4x head-crop fix
        extent = float(body_row.get("detail", "r=10.0").split("r=")[-1].rstrip(",") or 10.0)
        jreq("POST", "/camera", {"cam_radius": CAM_RADIUS_FACTOR * max(extent, 1.0),
                                 "cam_theta": 0.5, "cam_phi": 0.35})
        record("camera.set", "PASS", {"cam_radius": CAM_RADIUS_FACTOR * max(extent, 1.0),
                                      "cam_theta": 0.5, "cam_phi": 0.35,
                                      "extent": extent})

        # 5) the continuous take (prereg schedule)
        paths_glass, paths_frame = [], []
        readbacks: dict[int, dict] = {}
        for i in range(N_FRAMES):
            for jname in peak:
                jreq("POST", "/joint", {"joint": jname,
                                        "theta": rest[jname] + take_value(jname, i)
                                        * (peak[jname] - rest[jname])})
            st, png = request("GET", "/glass")
            p = out_frames / f"g{i:03d}.png"
            p.write_bytes(png)
            paths_glass.append(str(p))
            st2, png2 = request("GET", "/frame")
            pf = out_frames / f"c{i:03d}.png"
            pf.write_bytes(png2)
            paths_frame.append(str(pf))
            if i in KEYFRAMES:
                rb = jreq("GET", "/joints")
                readbacks[i] = {str(j.get("name")): float(j.get("theta", 0.0))
                                for j in (rb.get("joints") or [])}
                record("capture.keyframe", "PASS" if st == 200 and st2 == 200 else "FAIL",
                       {"i": i, "scripted_thetas": {j: round(readbacks[i][j], 2) for j in peak}})
        record("capture.frames", "PASS" if len(paths_glass) == N_FRAMES else "FAIL",
               {"n": len(paths_glass)})

        # 6) the declared engine-truth gate at FULL-HOLD (f049)
        gate = {}
        for jname in peak:
            got = readbacks[49].get(jname)
            want = 0.5 * peak[jname]
            gate[jname] = {"readback": got, "required_min": round(want, 2),
                           "ok": bool(got is not None and got >= want)}
        n_ok = sum(1 for g in gate.values() if g["ok"])
        record("gate.full_hold_theta", "PASS" if n_ok == len(gate) else "FAIL",
               {"ok": n_ok, "of": len(gate), "per_joint": gate})

        # 7) engine-truth keyframe table (28 thetas x 6 keyframes)
        with (OUT / "joint_thetas_keyframes.txt").open("w", encoding="utf-8") as fh:
            fh.write("product-motion-sweep-01 — GET /joints readback at the 6 declared "
                     "keyframes (28 live joints, degrees)\n")
            for i in KEYFRAMES:
                fh.write(f"\nkeyframe f{i:03d}\n")
                for jname in sorted(readbacks[i]):
                    fh.write(f"  {jname:<12} theta={readbacks[i][jname]:.3f}\n")

        # 8) encode the judge artifact (the product surface) + the clean twin
        mp4_glass = cpp_bridge.encode_movie(paths_glass, str(OUT / "product_motion_sweep.mp4"),
                                            fps=FPS)
        mp4_frame = cpp_bridge.encode_movie(paths_frame,
                                            str(OUT / "product_motion_sweep_frame.mp4"),
                                            fps=FPS)
        record("encode.movie", "PASS",
               {"glass": mp4_glass, "frame": mp4_frame,
                "glass_sha256": hashlib.sha256(Path(mp4_glass).read_bytes()).hexdigest()})
        (OUT / "render_records.json").write_text(json.dumps(RECORDS, indent=1, default=str))
        (OUT / "render_records.txt").write_text(
            "\n".join(f"[{x['verdict']}] {x['name']} {json.dumps(x['detail'], default=str)}"
                      for x in RECORDS) + "\n")
        print(json.dumps({"mp4": mp4_glass, "frames": len(paths_glass)}))
        _stop_owned(proc)
        deadline = time.time() + 15
        while proc.poll() is None and time.time() < deadline:
            time.sleep(0.2)
        record("engine.drain", "PASS" if proc.poll() is not None else "FAIL",
               {"rc": proc.poll()})
        return 0 if all(x["verdict"] != "FAIL" for x in RECORDS) else 1
    finally:
        if old is not None:
            os.environ["CHIMERA_MD_EDGE"] = old


if __name__ == "__main__":
    raise SystemExit(main())
