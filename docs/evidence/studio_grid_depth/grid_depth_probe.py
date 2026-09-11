"""studio-grid-depth-01 phase driver — runs the preregistered comparison.

Run only with this task's engine/GPU reservation (rtx4090 + engine_demo via the
controller). One invocation per phase:

    python grid_depth_probe.py before   # pre-fix build
    python grid_depth_probe.py after    # post-fix build

Everything lands in docs/evidence/studio_grid_depth/<phase>/: the frozen B2
numerical gate records, V1/V2 membrane-demo captures + the derived occlusion
probe, V3 mesh regression, V4 idle-viewport regression, engine runtime logs
(copied as *.txt — the *.log gitignore trap), and identity sha256s. Raw outputs
verbatim; no post-hoc edits.
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from engine_demo import _launch, _wait_ready, _stop_owned, _port_busy  # noqa: E402
import membrane_demo_client as membrane  # noqa: E402

PORT = 8127
BASE = f"http://127.0.0.1:{PORT}"
EXE = ROOT / ".tmp/engine_build/studio01/Release/chimera_engine.exe"
CAMERA = {"cam_radius": 3.0, "cam_theta": 0.0, "cam_phi": 0.35}  # the parent's fixed view
PHASE = sys.argv[1] if len(sys.argv) > 1 else "before"
OUT = Path(__file__).parent / PHASE

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


def grab(endpoint: str, label: str, meta: dict) -> None:
    st, png = request("GET", endpoint)
    ok = st == 200 and png[:8] == b"\x89PNG\r\n\x1a\n"
    (OUT / f"{label}.png").write_bytes(png)
    (OUT / f"{label}.json").write_text(json.dumps({
        "endpoint": endpoint, "http": st, "png_sha256": hashlib.sha256(png).hexdigest(),
        "png_bytes": len(png), "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **meta}, indent=1))
    record(f"capture.{label}", "PASS" if ok else "FAIL", {"png": f"{label}.png", "http": st})


def project(x: float, y: float, z: float):
    r = jreq("POST", "/project", {"x": x, "y": y, "z": z})
    if not r.get("ok"):
        return None
    return float(r["sx"]), float(r["sy"])


def cam_state():
    """The engine's own camera echo (rides on every /project response)."""
    return jreq("POST", "/project", {"x": 0.0, "y": 0.0, "z": 0.0}).get("cam")


# ── the derived occlusion partition (preregistration §3) ─────────────────────
# The membrane at reset/iteration-0 IS the frozen fixture lifted by LIFT_M>0.
# For a sheet strictly above the opaque floor plane, a ray from the (above-
# horizon) camera through a grid point P on y=0 passes through the sheet BEFORE
# reaching P exactly when P's projected pixel lies inside the sheet's projected
# triangle coverage — the lift>0 monotone-ray argument replaces numeric depth
# and is strictly equivalent here. Coverage is rasterized from /project outputs
# (the engine's own VP — the probe re-implements no projection math).

def rasterize_mask(tris2d: np.ndarray, w: int, h: int, ss: int = 2) -> np.ndarray:
    mask = np.zeros((h * ss, w * ss), dtype=bool)
    for t in tris2d:
        xs, ys = t[:, 0] * ss, t[:, 1] * ss
        x0 = max(int(np.floor(xs.min())), 0); x1 = min(int(np.ceil(xs.max())), w * ss - 1)
        y0 = max(int(np.floor(ys.min())), 0); y1 = min(int(np.ceil(ys.max())), h * ss - 1)
        if x1 < x0 or y1 < y0:
            continue
        # degenerate (zero-area) check on the SCALAR doubled area
        area2 = (xs[1] - xs[0]) * (ys[2] - ys[0]) - (ys[1] - ys[0]) * (xs[2] - xs[0])
        if abs(area2) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = []
        for i in range(3):
            ax, ay = xs[i], ys[i]; bx, by = xs[(i + 1) % 3], ys[(i + 1) % 3]
            d.append((bx - ax) * (gy - ay) - (by - ay) * (gx - ax))
        area = d[0] + d[1] + d[2]
        inside = (np.sign(d[0]) == np.sign(area)) | (np.sign(d[1]) == np.sign(area)) | \
                 (np.sign(d[2]) == np.sign(area))
        mask[y0:y1 + 1, x0:x1 + 1] |= inside
    return mask.reshape(h, ss, w, ss).any(axis=(1, 3))


def edge_band(mask: np.ndarray) -> np.ndarray:
    d = mask.copy()
    d[1:, :] |= mask[:-1, :]; d[:-1, :] |= mask[1:, :]
    d[:, 1:] |= mask[:, :-1]; d[:, :-1] |= mask[:, 1:]
    return d & ~mask


def classify(px, refs: dict, tol: float = 26.0) -> str:
    best, bd = "AMBIGUOUS", 1e9
    for name, ref in refs.items():
        dist = float(np.sqrt(((px - np.array(ref, dtype=np.float64)) ** 2).sum()))
        if dist < bd and dist <= tol:
            best, bd = name, dist
    return best


def run_membrane_probe(img: Image.Image, b2: dict, tag: str) -> dict:
    """Preregistered partition: occluded vs visible grid samples, pixel classes."""
    arr = np.asarray(img.convert("RGB"), dtype=np.float64)
    H, W = arr.shape[:2]
    cam_before = cam_state()
    pos = b2["pos"].astype(np.float64).reshape(-1, 3)
    idx = b2["idx"].astype(np.int64).reshape(-1, 3)
    lift = float(membrane.LIFT_M)
    assert lift > 0, "lift must be >0 for the monotone-ray equivalence"
    # present-stage mapping (membrane_demo.comp stage 5): fixture (x,y,z) ->
    # engine (x, z + lift, -y) — "presentation lift along engine y".
    lifted = np.column_stack([pos[:, 0], pos[:, 2] + lift, -pos[:, 1]])

    verts2d = []
    for p in lifted:
        r = project(float(p[0]), float(p[1]), float(p[2]))
        if r is None:
            record(f"probe.{tag}.vertex_project", "FAIL", {"v": p.tolist()})
            return {"ok": False}
        verts2d.append(r)
    verts2d = np.array(verts2d)
    tris = verts2d[idx]

    # self-check: wire ink (the ~230 edge color, CHIMERA_MD_EDGE=1) should land
    # near projected vertices — proves the lift interpretation before any count.
    wire_hits = 0
    for v in verts2d:
        x, y = int(round(v[0])), int(round(v[1]))
        if 0 <= x < W and 0 <= y < H:
            patch = arr[max(0, y - 2):y + 3, max(0, x - 2):x + 3]
            if patch.size and patch.reshape(-1, 3).max(axis=0)[0] > 200:
                wire_hits += 1
    hit_rate = wire_hits / len(verts2d)
    record(f"probe.{tag}.lift_selfcheck", "PASS" if hit_rate >= 0.5 else "FAIL",
           {"wire_hit_rate": round(hit_rate, 3)})

    mask = rasterize_mask(tris, W, H)
    eb = edge_band(mask)

    # grid line sampling law (engine.cpp push_grid_overlay, same derivation)
    R = CAMERA["cam_radius"]
    sp = float(10.0 ** np.floor(np.log10(R / 5.0)))
    n = int(np.ceil(R / sp))
    wx0, wx1 = lifted[:, 0].min() - sp, lifted[:, 0].max() + sp
    wz0, wz1 = lifted[:, 2].min() - sp, lifted[:, 2].max() + sp

    refs = {
        "GRID_INK_ON_FILL": (101, 107, 132),   # 0.7*ink + 0.3*fill157
        "GRID_INK_ON_FLOOR": (70, 77, 98),     # 0.7*ink + 0.3*floor55
        "FILL": (157, 157, 167),               # measured demo fill band centre
        "WIRE": (230, 230, 242),               # edge-contrast ink
    }
    counts = {"occluded": {}, "visible": {}}
    samples = []
    for i in range(-n, n + 1):
        v = float(sp * i)
        for lo, hi, axis in ((wx0, wx1, "z"), (wz0, wz1, "x")):
            steps = max(int((hi - lo) / 0.02), 2)
            for s in range(steps + 1):
                t = lo + (hi - lo) * s / steps
                wp = (t, v) if axis == "z" else (v, t)   # (along, fixed) on y=0
                wx, wz = (wp[0], wp[1]) if axis == "z" else (wp[1], wp[0])
                r = project(wx, 0.0, wz)
                if r is None:
                    continue
                sx, sy = r
                x, y = int(round(sx)), int(round(sy))
                if not (1 <= x < W - 1 and 1 <= y < H - 1):
                    continue
                occ = bool(mask[y, x])
                on_edge = bool(eb[y, x])
                px = arr[y, x]
                cls = classify(px, refs)
                bucket = "edge" if on_edge else ("occluded" if occ else "visible")
                if bucket != "edge":
                    counts[bucket][cls] = counts[bucket].get(cls, 0) + 1
                if (occ or cls.startswith("GRID")) and len(samples) < 4000:
                    samples.append({"x": wx, "z": wz, "sx": sx, "sy": sy,
                                    "occluded": occ, "edge": on_edge, "class": cls,
                                    "rgb": [int(c) for c in px]})
    (OUT / f"{tag}_probe_samples.json").write_text(json.dumps(samples, indent=1))
    ink_occ = counts["occluded"].get("GRID_INK_ON_FILL", 0) + \
        counts["occluded"].get("GRID_INK_ON_FLOOR", 0)
    total_occ = sum(counts["occluded"].values())
    result = {"ok": True, "spacing": sp, "n_lines": 2 * n + 1, "lift": lift,
              "cam_before": cam_before, "cam_after": cam_state(),
              "counts": counts, "ink_at_occluded": ink_occ,
              "occluded_total": total_occ,
              "ink_at_occluded_frac": round(ink_occ / max(total_occ, 1), 4),
              "fill_at_occluded_frac": round(
                  counts["occluded"].get("FILL", 0) / max(total_occ, 1), 4)}
    result["cam_stable"] = result["cam_before"] == result["cam_after"]
    (OUT / f"{tag}_probe.json").write_text(json.dumps(result, indent=1))
    record(f"probe.{tag}", "MEASURED", {k: result[k] for k in
                                        ("ink_at_occluded", "occluded_total",
                                         "ink_at_occluded_frac", "fill_at_occluded_frac",
                                         "cam_stable")})
    return result


def mesh_bin_packet() -> bytes:
    """A small 5-face box on the floor for the V3 ordinary-mesh regression."""
    s, hgt = 0.8, 0.8
    v = [(-s, 0, -s), (s, 0, -s), (s, 0, s), (-s, 0, s),
         (-s, hgt, -s), (s, hgt, -s), (s, hgt, s), (-s, hgt, s)]
    faces = [(0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
             (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
             (4, 5, 6)]  # four sides + top: the floor grid must yield to these
    verts = []
    for p in v:
        verts.extend([*p, 0.0, 1.0, 0.0, 0.72, 0.42, 0.30])
    payload = struct.pack("<II4f", len(v), len(faces) * 3, 4.0, 0.5, 0.42, 0.0)
    payload += np.array(verts, dtype="<f4").tobytes()
    payload += np.array([i for f in faces for i in f], dtype="<u4").tobytes()
    return payload


def drain(proc: subprocess.Popen, name: str) -> None:
    _stop_owned(proc)
    deadline = time.time() + 15
    while proc.poll() is None and time.time() < deadline:
        time.sleep(0.2)
    record(f"{name}.drain", "PASS" if proc.poll() is not None else "FAIL",
           {"rc": proc.poll()})


def capture_and_probe(view_fn, label: str, tag: str, b2: dict, attempts: int = 3):
    """Fixed-camera capture + probe, retried while the camera moves under us.

    The engine window is visible on a shared desktop, so an external drag can
    move the camera between the capture and the /project probe. Each attempt
    re-sets the fixed camera, snapshots the engine's own camera echo, captures,
    probes, and only accepts the attempt when the camera echo is IDENTICAL at
    capture time and probe end and the probe's own lift self-check passed.
    Failed attempts stay in the records (retained, never hidden).
    """
    r = {"ok": False}
    for attempt in range(1, attempts + 1):
        view_fn()
        jreq("POST", "/camera", CAMERA)
        time.sleep(0.4)
        cam_at_capture = cam_state()
        grab("/frame", f"{tag}_frame", {"view": label, "attempt": attempt,
                                        "camera": CAMERA, "cam_echo": cam_at_capture})
        grab("/glass", f"{tag}_glass", {"view": label + " (composited)",
                                        "attempt": attempt, "camera": CAMERA})
        r = run_membrane_probe(Image.open(OUT / f"{tag}_frame.png"), b2, tag)
        stable = bool(r.get("cam_stable")) and r.get("cam_before") == cam_at_capture
        selfcheck_ok = any(rec["name"] == f"probe.{tag}.lift_selfcheck"
                          and rec["verdict"] == "PASS"
                          for rec in RECORDS[-3:])
        if stable and selfcheck_ok:
            record(f"probe.{tag}.accepted", "PASS", {"attempt": attempt})
            return r
        record(f"probe.{tag}.retry", "FAIL" if attempt == attempts else "RETRIED",
               {"attempt": attempt, "cam_stable": stable, "selfcheck_ok": selfcheck_ok})
    return r


def main() -> int:
    assert EXE.is_file(), f"missing exe: {EXE}"
    assert not _port_busy(PORT), f"port {PORT} busy"
    OUT.mkdir(parents=True, exist_ok=True)
    fails = []

    old = os.environ.get("CHIMERA_MD_EDGE")
    os.environ["CHIMERA_MD_EDGE"] = "1"
    try:
        # ── instance 1: membrane demo (gate + V1 + V2) ──
        proc, _ = _launch(EXE, PORT, ROOT / f".tmp/engine_runtime/grid_{PHASE}_membrane")
        _wait_ready(proc, PORT)
        record("launch", "PASS", {"pid": proc.pid, "port": PORT,
                                  "exe_sha256": hashlib.sha256(EXE.read_bytes()).hexdigest()})
        st, _ = request("GET", "/state")
        record("state.ready", "PASS" if st == 200 else "FAIL", {"http": st})

        b2 = membrane.load_b2()
        nv, nf = len(b2["pos"]) // 3, len(b2["idx"]) // 3
        record("b2.fixture", "PASS" if nf == 6 else "FAIL", {"n_verts": nv, "n_faces": nf})

        gate_rc = membrane.gate(BASE, b2, OUT, CAMERA["cam_phi"], CAMERA["cam_radius"])
        (OUT / "b2_gate_records.json").write_text(
            json.dumps(membrane.results, indent=1, default=str))
        (OUT / "b2_gate_records.txt").write_text("\n".join(
            f"[{r['verdict']}] {r['name']}" for r in membrane.results) + "\n")
        gate_fails = [r for r in membrane.results if r["verdict"] == "FAIL"]
        record("b2.gate", "PASS" if gate_rc == 0 and not gate_fails else "FAIL",
               {"rc": gate_rc, "records": len(membrane.results), "fails": len(gate_fails)})

        # V1: reset state (geometry == fixture), fixed camera
        r1 = capture_and_probe(
            lambda: (membrane.demo_ctl(BASE, "reset"),
                     membrane.check_status(BASE, "v1.reset")),
            "V1 membrane reset (fixture geometry)", "v1", b2)

        # V2: gamma0 raised stationary (the parent's retained view)
        r2 = capture_and_probe(
            lambda: (membrane.demo_ctl(BASE, "reset"),
                     membrane.demo_ctl(BASE, "gamma", gamma=0.0),
                     membrane.demo_ctl(BASE, "step", n_steps=1),
                     membrane.check_status(BASE, "v2.gamma0")),
            "V2 gamma0 raised stationary", "v2", b2)

        drain(proc, "membrane.instance")

        # ── instance 2: V4 idle FIRST (nothing loaded), then V3 mesh ──
        proc2, _ = _launch(EXE, PORT, ROOT / f".tmp/engine_runtime/grid_{PHASE}_mesh")
        _wait_ready(proc2, PORT)
        jreq("POST", "/camera", CAMERA)
        time.sleep(0.4)
        grab("/glass", "v4_idle_glass", {"view": "V4 idle empty viewport (composited)"})
        grab("/frame", "v4_idle_frame", {"view": "V4 idle empty viewport"})
        body = mesh_bin_packet()
        st, resp = request("POST", "/mesh_bin", body, "application/octet-stream")
        record("v3.mesh_bin", "PASS" if st == 200 and b'"ok":true' in resp else "FAIL",
               {"http": st, "resp": resp[:120].decode("utf-8", "replace")})
        time.sleep(0.6)
        grab("/glass", "v3_mesh_glass", {"view": "V3 ordinary mesh box (composited)"})
        grab("/frame", "v3_mesh_frame", {"view": "V3 ordinary mesh box"})
        drain(proc2, "mesh.instance")

        # runtime logs -> evidence as *.txt (never *.log — the gitignore trap)
        for src, tag in ((ROOT / f".tmp/engine_runtime/grid_{PHASE}_membrane", "mem"),
                         (ROOT / f".tmp/engine_runtime/grid_{PHASE}_mesh", "mesh")):
            for f in sorted(src.glob("engine.*.log")):
                (OUT / f"{tag}_{f.name}.txt").write_bytes(f.read_bytes())

        (OUT / "records.json").write_text(json.dumps(RECORDS, indent=1, default=str))
        (OUT / "records.txt").write_text("\n".join(
            f"[{r['verdict']}] {r['name']} {json.dumps(r['detail'], default=str)}"
            for r in RECORDS) + "\n")
        fails = [r for r in RECORDS if r["verdict"] == "FAIL"]
        print(json.dumps({"phase": PHASE, "fails": len(fails),
                          "probe_v1_ink_occluded": r1.get("ink_at_occluded"),
                          "probe_v2_ink_occluded": r2.get("ink_at_occluded")}))
        return 0 if not fails else 1
    finally:
        if old is None:
            os.environ.pop("CHIMERA_MD_EDGE", None)
        else:
            os.environ["CHIMERA_MD_EDGE"] = old


if __name__ == "__main__":
    raise SystemExit(main())
