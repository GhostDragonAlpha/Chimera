"""engine-root-translation-01 — the preregistered parity battery + the take.

Run only with this task's engine/GPU reservation (rtx4090 + engine_demo).
Prereg: PREREGISTRATION.md in this directory (committed FIRST, before any
build/run; every tolerance below is frozen there).

    python parity_battery.py battery --exe <chimera_engine.exe> --tag <name> [--no-root]
    python parity_battery.py take    --exe <chimera_engine.exe>

battery: drives one binary through the preregistered states and records the
artifacts (sha256 + pixel analysis) to battery_<tag>.txt/.json in this dir.
  --no-root  → the R2 regression arm: only the deterministic states (s0 rest,
               s1 edit-pose) are captured; the /root route is NEVER posted.
  default    → the NEW-binary arm: R2 states PLUS the parity controls P1-P5.
R2 verdict: byte-identical artifact identities between the base arm and the
new arm (compare battery_base.txt vs battery_new.txt: the s0/s1 sha256 sets).
take: the packet's primary prediction — the creature translating across the
grid while the march plays; frames + mp4 to Desktop/CHIMERA_PROOF.

Public HTTP surface only, plus the harness wrappers the integrated lanes
already use (tools/engine_demo.py launch/stop; ChimeraEngine/cpp_bridge
load_mesh_bin/encode_movie; tools/product_features_walk pack derivation).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]          # docs/evidence/... -> repo root of the slot
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
from engine_demo import _launch, _wait_ready, _stop_owned, _port_busy  # noqa: E402
import cpp_bridge                                    # noqa: E402
import product_features_walk as v1                   # the integrated v1 lane (hinge/gait blobs)

EVIDENCE = ROOT / "docs/evidence/agent_fleet/ENGINE_ROOT_TRANSLATION"
PORT_CANDIDATES = (8105, 8115, 8125)                 # fleet-range candidates; first free wins
PROOF = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop/CHIMERA_PROOF/ENGINE_root_translation"

RECORDS: list[dict] = []


def record(name: str, verdict: str, detail: dict) -> None:
    RECORDS.append({"name": name, "verdict": verdict, "detail": detail})
    print(f"[{verdict}] {name} {json.dumps(detail, default=str)[:200]}", flush=True)


BASE_URL = {"v": "http://127.0.0.1:0"}


def request(method: str, path: str, body: bytes | None = None,
            ctype: str = "application/json", timeout: float = 60.0):
    req = urllib.request.Request(BASE_URL["v"] + path, data=body, method=method)
    if body is not None:
        req.add_header("Content-Type", ctype)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def jreq(method: str, path: str, payload=None) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    st, raw = request(method, path, body)
    return json.loads(raw.decode("utf-8", "replace"))


def pick_port() -> int:
    for p in PORT_CANDIDATES:
        if not _port_busy(p):
            return p
    raise RuntimeError("no free fleet-range port")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def thetas_of(doc: dict) -> list[float]:
    return [float(j["theta"]) for j in doc.get("joints", [])]


def pivot_of(doc: dict, name: str) -> list[float]:
    for j in doc.get("joints", []):
        if j.get("name") == name:
            return [float(j["J"][0]), float(j["J"][1]), float(j["J"][2])]
    raise KeyError(name)


def wait_root_applied(target: list[float], timeout: float = 5.0) -> dict:
    deadline = time.monotonic() + timeout
    last = {}
    while time.monotonic() < deadline:
        last = jreq("GET", "/root")
        ap = last.get("applied", [0, 0, 0])
        if all(abs(ap[i] - target[i]) <= 1e-4 for i in range(3)):
            return last
        time.sleep(0.05)
    return last


def grab_frame() -> tuple[bytes, np.ndarray]:
    st, png = request("GET", "/frame", timeout=60)
    return png, np.asarray(Image.open(io.BytesIO(png)).convert("RGB"))


def changed_mask(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.any(a != b, axis=2)


def bbox_of(mask: np.ndarray):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def centroid_of(mask: np.ndarray):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return (float(xs.mean()), float(ys.mean()))


def run_battery(exe: Path, tag: str, no_root: bool) -> int:
    port = pick_port()
    BASE_URL["v"] = f"http://127.0.0.1:{port}"
    RUNTIME = ROOT / f".tmp/engine_runtime/engine-root-translation-{tag}-{time.strftime('%Y%m%d-%H%M%S')}"
    exe_sha = sha(exe.read_bytes())
    record("launch.identity", "PASS", {"tag": tag, "exe": str(exe), "exe_sha256": exe_sha,
                                       "port": port, "no_root": no_root})
    proc, _ = _launch(exe, port, RUNTIME)
    _wait_ready(proc, port)
    record("launch", "PASS", {"pid": proc.pid, "port": port})
    fail = 0
    try:
        # 1) the committed subject pair (identical to PR #97 / the walk lanes)
        ok, r, th, ph = cpp_bridge.load_mesh_bin(str(ROOT / "Saved/meshes/monkey_birth.bin"), timeout=120)
        record("load.mesh", "PASS" if ok else "FAIL", {"r": r, "theta": th, "phi": ph})
        pack = (ROOT / "Saved/meshes/monkey_joints.bin").read_bytes()
        st, resp = request("POST", "/joints_bin", pack, "application/octet-stream", timeout=120)
        record("load.joints_bin", "PASS" if st == 200 and b'"ok":true' in resp else "FAIL", {})
        jreq("POST", "/joints", {"on": False})     # the show clock owns nothing (determinism)
        doc = jreq("GET", "/joints")
        scene = jreq("GET", "/scene")
        body_row = next((row for row in scene.get("rows", []) if row.get("id") == "body"), {})
        extent = float(str(body_row.get("detail", "r=10.0")).split("r=")[-1].rstrip(",") or 10.0)
        jreq("POST", "/camera", {"cam_radius": 3.4 * max(extent, 1.0), "cam_theta": 0.5, "cam_phi": 0.35})
        record("camera.set", "PASS", {"cam_radius": 3.4 * max(extent, 1.0), "cam_theta": 0.5, "cam_phi": 0.35})

        def project_knee() -> dict:
            J = pivot_of(jreq("GET", "/joints"), "knee_R")
            pr = jreq("POST", "/project", {"x": J[0], "y": J[1], "z": J[2]})
            return {"pivot": J, "sx": pr.get("sx"), "sy": pr.get("sy")}

        # ── s0: REST state (no pose owner) ────────────────────────────────
        png_a, img_a = grab_frame()
        proj_a = project_knee()
        doc_a = jreq("GET", "/joints")
        record("s0.rest", "PASS", {"frame_sha": sha(png_a), "sx": proj_a["sx"], "sy": proj_a["sy"]})

        # ── s1: deterministic EDIT pose (editor owns; thetas frozen) ──────
        jreq("POST", "/joint", {"joint": "knee_R", "theta": 20.0})
        jreq("POST", "/joint", {"joint": "elbow_L", "theta": -30.0})
        time.sleep(0.3)
        png_b, img_b = grab_frame()
        proj_b = project_knee()
        doc_b = jreq("GET", "/joints")
        record("s1.edit", "PASS", {"frame_sha": sha(png_b), "sx": proj_b["sx"], "sy": proj_b["sy"]})

        # s0/s1 artifacts ARE the R2 regression set. /joints docs carry the
        # wall clock ("t") — compare the thetas arrays only.
        r2 = {"tag": tag, "no_root": no_root,
              "s0_frame": sha(png_a), "s1_frame": sha(png_b),
              "s0_thetas": thetas_of(doc_a), "s1_thetas": thetas_of(doc_b),
              "s0_proj": [proj_a["sx"], proj_a["sy"]],
              "s1_proj": [proj_b["sx"], proj_b["sy"]]}

        if not no_root:
            # ── P1 THETA PARITY (paused-clock owner; exact) ──────────────
            t1 = thetas_of(jreq("GET", "/joints"))
            D = [0.6, 0.25, -0.4]
            root_doc = jreq("POST", "/root", {"x": D[0], "y": D[1], "z": D[2]})
            wait_root_applied(D)
            t2 = thetas_of(jreq("GET", "/joints"))
            p1 = "PASS" if t1 == t2 else "FAIL"
            if p1 == "FAIL":
                fail += 1
            record("P1.theta_parity", p1, {"n_thetas": len(t1),
                                           "max_abs_diff": max((abs(a - b) for a, b in zip(t1, t2)), default=0.0),
                                           "readback": root_doc})

            # ── P2 PIXEL PARITY (rest vs translated) ─────────────────────
            # back to rest pose first (owner EDIT with zeroed thetas = rest)
            jreq("POST", "/joint", {"joint": "knee_R", "theta": 0.0})
            jreq("POST", "/joint", {"joint": "elbow_L", "theta": 0.0})
            time.sleep(0.3)
            png_c, img_c = grab_frame()            # body at root 0 (reference refreshed)
            J0 = pivot_of(jreq("GET", "/joints"), "knee_R")
            proj0 = jreq("POST", "/project", {"x": J0[0], "y": J0[1], "z": J0[2]})
            jreq("POST", "/root", {"x": D[0], "y": D[1], "z": D[2]})
            wait_root_applied(D)
            J1 = pivot_of(jreq("GET", "/joints"), "knee_R")
            proj1 = jreq("POST", "/project", {"x": J1[0], "y": J1[1], "z": J1[2]})
            png_d, img_d = grab_frame()
            mask = changed_mask(img_c, img_d)
            cx = centroid_of(mask)
            dsx = float(proj1["sx"]) - float(proj0["sx"])
            dsy = float(proj1["sy"]) - float(proj0["sy"])
            h, w = mask.shape
            border = 4  # the outer 4-px band must be untouched (body is centered)
            border_ok = (not mask[:border, :].any() and not mask[-border:, :].any()
                         and not mask[:, :border].any() and not mask[:, -border:].any())
            area_frac = float(mask.mean())
            # centroid: the changed-pixel mask is the symmetric difference of
            # body(+shadow) at two positions; its centroid sits near the MIDPOINT
            # of the two body centroids — compare against proj0 + dsx/2.
            mid_x, mid_y = float(proj0["sx"]) + dsx / 2.0, float(proj0["sy"]) + dsy / 2.0
            cen_ok = cx is not None and abs(cx[0] - mid_x) <= 40.0 and abs(cx[1] - mid_y) <= 40.0
            p2 = "PASS" if (border_ok and cen_ok and mask.any() and area_frac <= 0.25) else "FAIL"
            if p2 == "FAIL":
                fail += 1
            record("P2.pixel_parity", p2,
                   {"centroid": cx, "mid_expected": [mid_x, mid_y], "proj_shift": [dsx, dsy],
                    "border_band_untouched": border_ok, "changed_area_frac": round(area_frac, 5),
                    "mask_bbox": bbox_of(mask), "pivot_moved": [J0, J1]})

            # ── P4 ROUND TRIP (translate back = the EXACT original bytes) ─
            jreq("POST", "/root", {"x": 0.0, "y": 0.0, "z": 0.0})
            wait_root_applied([0.0, 0.0, 0.0])
            png_e, img_e = grab_frame()
            p4 = "PASS" if sha(png_e) == sha(png_c) else "FAIL"
            if p4 == "FAIL":
                fail += 1
            record("P4.round_trip_exact", p4, {"rest_sha": sha(png_c), "returned_sha": sha(png_e)})

            # ── P5 READBACK (exact values + per-axis merge) ──────────────
            g = jreq("POST", "/root", {"x": 0.5, "y": 0.25, "z": -0.125})["target"]
            g2 = jreq("POST", "/root", {"y": 2.0})["target"]
            p5 = "PASS" if (all(abs(g[i] - v) <= 1e-6 for i, v in enumerate([0.5, 0.25, -0.125]))
                            and abs(g2[0] - 0.5) <= 1e-6 and abs(g2[1] - 2.0) <= 1e-6
                            and abs(g2[2] + 0.125) <= 1e-6) else "FAIL"
            if p5 == "FAIL":
                fail += 1
            record("P5.readback_merge", p5, {"first": g, "merged": g2})
            jreq("POST", "/root", {"x": 0.0, "y": 0.0, "z": 0.0})
            wait_root_applied([0.0, 0.0, 0.0])

            # ── P3 COMPOSITION (the walk-realism composition test) ───────
            hinge_blob, hinge_facts = v1.build_hinge_blob()
            gait_payload = v1.build_gait_payload()
            st, resp = request("POST", "/hinge_bin", hinge_blob, "application/octet-stream", timeout=60)
            record("P3.engage.hinge_bin", "PASS" if b'"ok":true' in resp else "FAIL", {})
            st, resp = request("POST", "/gait_bin", gait_payload, "application/octet-stream", timeout=60)
            record("P3.engage.gait_bin", "PASS" if b'"ok":true' in resp else "FAIL", {})
            jreq("POST", "/gait", {"on": True, "steps": v1.GAIT_STEPS, "omega": v1.OMEGA_REF})
            time.sleep(0.5)
            g1 = jreq("GET", "/gait")["steps_total"]
            png_m0, img_m0 = grab_frame()
            Jm0 = pivot_of(jreq("GET", "/joints"), "knee_R")
            pm0 = jreq("POST", "/project", {"x": Jm0[0], "y": Jm0[1], "z": Jm0[2]})
            jreq("POST", "/root", {"x": 0.3, "y": 0.0, "z": 0.0})
            wait_root_applied([0.3, 0.0, 0.0])
            time.sleep(1.5)                        # the march keeps playing
            g2 = jreq("GET", "/gait")["steps_total"]
            png_m1, img_m1 = grab_frame()
            Jm1 = pivot_of(jreq("GET", "/joints"), "knee_R")
            pm1 = jreq("POST", "/project", {"x": Jm1[0], "y": Jm1[1], "z": Jm1[2]})
            # knee oscillation continues: per-pixel temporal std across 10
            # consecutive frames inside the full frame (the marching body)
            frames_seq = []
            for i in range(10):
                _, im = grab_frame()
                frames_seq.append(im.astype(np.int16))
            stack = np.stack(frames_seq)
            body_var = float(stack.std(axis=0).mean())
            var_ok = body_var > 0.5
            mask3 = changed_mask(img_m0, img_m1)
            cx3 = centroid_of(mask3)
            dsx3 = float(pm1["sx"]) - float(pm0["sx"])
            mid3 = float(pm0["sx"]) + dsx3 / 2.0
            steps_ok = g2 > g1
            comp_ok = cx3 is not None and abs(cx3[0] - mid3) <= 60.0
            p3 = "PASS" if (steps_ok and var_ok and comp_ok) else "FAIL"
            if p3 == "FAIL":
                fail += 1
            record("P3.gait_composition", p3,
                   {"steps_before": g1, "steps_after": g2, "march_advanced": steps_ok,
                    "body_temporal_std": round(body_var, 3), "still_stepping": var_ok,
                    "centroid": cx3, "mid_expected_x": mid3, "proj_shift_x": dsx3,
                    "composed": comp_ok})
            jreq("POST", "/gait", {"on": False})

        # ── record the R2 set ────────────────────────────────────────────
        (EVIDENCE / f"battery_{tag}.json").write_text(json.dumps(r2, indent=1))
        ok_txt = [f"battery tag={tag} exe={exe} exe_sha256={exe_sha} no_root={no_root}",
                  f"s0_frame {r2['s0_frame']}", f"s1_frame {r2['s1_frame']}",
                  f"s0_proj {r2['s0_proj']}", f"s1_proj {r2['s1_proj']}",
                  f"s0_thetas {r2['s0_thetas']}", f"s1_thetas {r2['s1_thetas']}"]
        (EVIDENCE / f"battery_{tag}.txt").write_text("\n".join(ok_txt) + "\n")
        record("battery.records", "PASS", {"file": f"battery_{tag}.txt"})
    finally:
        _stop_owned(proc)
        record("stop", "PASS", {"drained": proc.poll() is not None})
    return fail


def run_take(exe: Path) -> int:
    port = pick_port()
    BASE_URL["v"] = f"http://127.0.0.1:{port}"
    RUNTIME = ROOT / f".tmp/engine_runtime/engine-root-translation-take-{time.strftime('%Y%m%d-%H%M%S')}"
    PROOF.mkdir(parents=True, exist_ok=True)
    frames_dir = PROOF / "take_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    proc, _ = _launch(exe, port, RUNTIME)
    _wait_ready(proc, port)
    record("take.launch", "PASS", {"pid": proc.pid, "port": port})
    try:
        ok, r, th, ph = cpp_bridge.load_mesh_bin(str(ROOT / "Saved/meshes/monkey_birth.bin"), timeout=120)
        pack = (ROOT / "Saved/meshes/monkey_joints.bin").read_bytes()
        request("POST", "/joints_bin", pack, "application/octet-stream", timeout=120)
        jreq("POST", "/joints", {"on": False})
        scene = jreq("GET", "/scene")
        body_row = next((row for row in scene.get("rows", []) if row.get("id") == "body"), {})
        extent = float(str(body_row.get("detail", "r=10.0")).split("r=")[-1].rstrip(",") or 10.0)
        jreq("POST", "/camera", {"cam_radius": 3.4 * max(extent, 1.0), "cam_theta": 0.5, "cam_phi": 0.35})
        hinge_blob, _ = v1.build_hinge_blob()
        gait_payload = v1.build_gait_payload()
        request("POST", "/hinge_bin", hinge_blob, "application/octet-stream", timeout=60)
        request("POST", "/gait_bin", gait_payload, "application/octet-stream", timeout=60)
        jreq("POST", "/gait", {"on": True, "steps": v1.GAIT_STEPS, "omega": v1.OMEGA_REF})
        record("take.march_on", "PASS", {})
        N, FPS = 300, 10                      # 30 s take; travel +1.5 wu in x
        t0 = time.monotonic()
        for i in range(N):
            target = t0 + i / FPS
            now = time.monotonic()
            if now < target:
                time.sleep(target - now)
            if i % 10 == 0:                    # 2 s per step, +0.05 wu/s => +1.5 wu total
                jreq("POST", "/root", {"x": round(0.05 * i / FPS, 4), "y": 0.0, "z": 0.0})
            st, glass = request("GET", "/glass", timeout=60)
            (frames_dir / f"g{i:03d}.png").write_bytes(glass)
        steps = jreq("GET", "/gait")["steps_total"]
        root = jreq("GET", "/root")["applied"]
        record("take.captured", "PASS", {"frames": N, "march_steps_total": steps, "root_applied": root})
        out_mp4 = PROOF / "engine_root_translation_take.mp4"
        cpp_bridge.encode_movie([str(p) for p in sorted(frames_dir.glob("g*.png"))], str(out_mp4), fps=FPS)
        record("take.encoded", "PASS", {"mp4": str(out_mp4), "bytes": out_mp4.stat().st_size})
    finally:
        _stop_owned(proc)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["battery", "take"])
    ap.add_argument("--exe", required=True, type=Path)
    ap.add_argument("--tag", default="new")
    ap.add_argument("--no-root", action="store_true")
    a = ap.parse_args()
    fail = run_battery(a.exe, a.tag, a.no_root) if a.mode == "battery" else run_take(a.exe)
    lines = [f"{r['verdict']} {r['name']} {json.dumps(r['detail'], default=str)}" for r in RECORDS]
    (EVIDENCE / (f"battery_{a.tag}_records.txt" if a.mode == "battery" else "take_records.txt")).write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print("FAILURES:", fail)
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
