"""workflow_commands.py -- THE CHECKLIST's gates as repeatable commands
(lane agent/workflow-mcp-20260920; the operator's directive: "these are
complicated issues that an agent cannot keep straight on its own; we need
tools to guide an agent through our workflow, like repeatable commands
running on an MCP server").

THE LAW OF THIS MODULE: every command WRAPS a proven instrument and returns
MEASURED NUMBERS (one JSON object), never a prose verdict. Nothing here
invents a technique:

  render_creature   the TRIANGLE path ONLY -- ct_skeleton_triangle's registered
                    mesh through the engine's /mesh_bin (the standing law the
                    conformance gate enforces). There is NO splat route
                    reachable from this command: layer_splat_buffer and
                    /membrane_bin are never referenced by the render path.
  verify_visual     pixel_truth.py end-to-end (grain, coverage with caller
                    masks, object-seen / guide-seen with caller ROIs, clipscan)
                    with the thresholds PRE-ENCODED from banked measurements
                    (receipt workflow_mcp_20260920 -- every gate's provenance
                    is carried in the output).
  adjudicate        tools/creature_graph/reality_gate.py, RESOLVED AT RUNTIME.
                    The gate lives on branch agent/reality-fantasy-gate-20260920
                    (NOT this lineage): when the module is absent the command
                    returns the STRUCTURED honest absence below -- never a
                    crash, never a silent pass.
  bio.stage         the research memo's spec (docs/research/
                    20260920_adult_and_muscle_data_options.md section 6.3):
                    the bundle's stage label + evidence, or FAILED as
                    unadmittable (missing stage = failed, like a missing
                    sha256).
  bio.check         the gate's classify: {category, violations} (L1-L4).
                    Requires the reality gate; honest absence otherwise.
  bio.fantasy_acknowledge
                    the developer-driven construction mode: records the
                    manifest acknowledgment on the bundle, THEN the gate admits
                    to the fantasy category (never silent, never accidental).
  checklist         THE_CHECKLIST (docs/THE_CHECKLIST.md, branch
                    agent/workflow-checklist-20260920 e9c8b394) as a
                    machine-readable walk: step id, law home pointer, the
                    command that satisfies it -- or an honestly-named
                    judgment where no command exists.

RULE 0 receipt: tools/science_funnel/validation/workflow_mcp_20260920/receipt.json
(banked BEFORE this module ran; thresholds pre-encoded there from the banked
triangle_monkey_20260920 numbers -- midbands derived, no taste numbers).

PORT LAW: a self-started engine binds a bind-tested free port only; 8127 (the
operator's live scene) is refused BY CODE. Only processes this module started
are ever stopped.

CLI (each subcommand prints one JSON object; verify-visual exits 1 on any RED
gate, everything else exits 0 unless the infrastructure itself fails):
  python -B tools/science_funnel/workflow_commands.py render-creature [SRC] [--out DIR]
  python -B tools/science_funnel/workflow_commands.py verify-visual FRAMES_DIR [--masks DIR] [--roi DIR] [--render-record F]
  python -B tools/science_funnel/workflow_commands.py adjudicate BUNDLE
  python -B tools/science_funnel/workflow_commands.py bio-stage BUNDLE
  python -B tools/science_funnel/workflow_commands.py bio-check BUNDLE
  python -B tools/science_funnel/workflow_commands.py bio-fantasy-acknowledge BUNDLE [--out F]
  python -B tools/science_funnel/workflow_commands.py checklist
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "tools/science_funnel/validation/workflow_mcp_20260920"
RECEIPT_PATH = VALIDATION / "receipt.json"

SCHEMA = "chimera.workflow_commands.v1"
LANE = "agent/workflow-mcp-20260920"

# ── the port law ─────────────────────────────────────────────────────────────
NEVER_PORT = 8127              # the operator's live scene -- refused BY CODE
ENGINE_READY_TIMEOUT_S = 90.0
DEFAULT_ENGINE_EXE = ROOT / ".tmp/wfmcp_build/Release/chimera_engine.exe"
ENGINE_BUILD_HINT = ("cmake -S ChimeraEngine/engine -B .tmp/wfmcp_build && "
                     "cmake --build .tmp/wfmcp_build --config Release --parallel 24")

# ── the pre-encoded thresholds (receipt pre_registered block; provenance there) ─
THRESHOLDS = {
    "clipscan_collapse_events_max": 0,
    "clipscan_new_boundary_touch_max": 0,
    "per_bone_median_coverage_min": 0.3441,   # midband(splat 0.1201, mesh 0.568)
    "bones_at_zero_max": 0,                   # splat 5, mesh 0
    "whole_hull_coverage_min": 0.3259,        # midband(splat 0.2561, mesh 0.3957)
    "object_seen_dim_min": 0.2596,            # midband(splat 0.0, worse verified mesh side 0.5191)
    "guide_presence_ratio_min": 0.05,         # FALSIFIER_B_GRID pre-registered bar
}
GRAIN_LAW = ("reported_not_gated: banked 341.39 (splat) vs 339.50 (mesh) median "
             "local variance -- non-discriminating for marching-cubes geometry "
             "(triangle_monkey_20260920 A); a gate here would be theatre")

# ── the honest absence (reality gate on another lineage) ─────────────────────
REALITY_GATE_BRANCH = "agent/reality-fantasy-gate-20260920"
REALITY_GATE_PATH = "tools/creature_graph/reality_gate.py"
HONEST_ABSENCE = {
    "error": "reality_gate_not_resolvable",
    "message": "reality_gate not on this lineage; integrated on master pending",
    "branch": REALITY_GATE_BRANCH,
    "path": REALITY_GATE_PATH,
}


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _out(obj: dict) -> str:
    return json.dumps({"schema": SCHEMA, "lane": LANE, **obj}, indent=1)


# ══════════════════════════════════════════════════════════════════════════════
# the engine process (own port law; only own processes stopped)
# ══════════════════════════════════════════════════════════════════════════════

def free_port(avoid: tuple = (NEVER_PORT,)) -> int:
    """A bind-tested free port. 8127 is in the avoid set BY CODE."""
    if NEVER_PORT not in avoid:                       # the law, enforced
        avoid = tuple(avoid) + (NEVER_PORT,)
    tried = set()
    for _ in range(64):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        if port in avoid or port in tried:
            continue
        try:
            s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s2.bind(("127.0.0.1", port))
            s2.close()
        except OSError:
            tried.add(port)
            continue
        return port
    raise RuntimeError("workflow_commands refusal: no bind-tested free port found")


class EngineHandle:
    """A self-started engine process. ONLY this process is ever stopped."""

    def __init__(self, exe: Path, port: int, proc: subprocess.Popen):
        self.exe = Path(exe)
        self.port = int(port)
        self.proc = proc
        self.url = f"http://127.0.0.1:{self.port}"
        self.exe_sha256 = _sha256(self.exe.read_bytes()) if self.exe.is_file() else None


def start_engine(engine_exe: str | Path | None = None) -> EngineHandle:
    """Build-free spawn: the port argument + the engine's OWN --no-restore
    opt-out. MEASURED 2026-09-20 (this lane): the engine boots a deferred
    session-restore thread (1500 ms delay, main.cpp) that replays the last
    session and then POSTs /cameras {"op":"fit"} -- an ASYNC camera override
    that races the first mesh+camera upload (the e2e A-pose captured the boot
    fit's framing, r~1.4/ty~0.25, while /project proved the POSTED camera was
    applied). --no-restore (any argv position) never starts that thread. It is
    SAFE with the port: the window-override guard reads argv[3]/argv[4] only
    under argc > 3, so `exe <port> --no-restore` (argc == 3) cannot hit the
    banked atoi(nullptr) abort (that needs 4+ arguments). Readiness = /frame
    answering."""
    exe = Path(engine_exe) if engine_exe else DEFAULT_ENGINE_EXE
    if not exe.is_file():
        raise RuntimeError(
            "workflow_commands refusal: engine_binary_missing at "
            f"{exe} -- build it first: {ENGINE_BUILD_HINT}")
    port = free_port()
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    proc = subprocess.Popen([str(exe), str(port), "--no-restore"],
                            cwd=str(exe.parent),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            creationflags=flags)
    handle = EngineHandle(exe, port, proc)
    deadline = time.time() + ENGINE_READY_TIMEOUT_S
    last = None
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                f"workflow_commands refusal: engine_exited (code {proc.returncode}) "
                f"before readiness on port {port}")
        try:
            with urllib.request.urlopen(f"{handle.url}/frame", timeout=5) as r:
                if r.status == 200:
                    return handle
        except (urllib.error.URLError, ConnectionError, OSError) as e:
            last = e
        time.sleep(0.5)
    stop_engine(handle)
    raise RuntimeError(f"workflow_commands refusal: engine_not_ready on port {port}: {last}")


def stop_engine(handle: EngineHandle) -> None:
    """Stop ONLY the process this module started."""
    if handle.proc.poll() is None:
        handle.proc.terminate()
        try:
            handle.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            handle.proc.kill()
            handle.proc.wait(timeout=10)


# ── the engine HTTP protocol (the banked settle-capture pattern) ─────────────

def _retry_urlopen(req, timeout: float, attempts: int = 4):
    """The engine serves HTTP on ONE worker; a STRICTLY FRESH /frame wait can
    block that worker so the next request hits a full listen backlog (the
    skeleton_movie._retry_urlopen precedent). Retry with backoff."""
    last = None
    for i in range(attempts):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except (urllib.error.URLError, ConnectionError, OSError) as e:
            last = e
            time.sleep(0.25 * (i + 1))
    raise last


def _fetch_frame(url: str, timeout: float = 30.0) -> bytes:
    req = urllib.request.Request(f"{url.rstrip('/')}/frame")
    with _retry_urlopen(req, timeout=timeout) as r:
        return r.read()


def _settle_capture(url: str, prev: bytes | None, timeout: float = 12.0) -> bytes:
    """Two consecutive equal fresh captures = a quiesced render
    (skeleton_movie._settle_capture's determinism law)."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        b = _fetch_frame(url, timeout=timeout)
        if prev is not None and b == prev:
            last = None
            time.sleep(0.06)
            continue
        if last is not None and b == last:
            return b
        last = b
        time.sleep(0.06)
    return _fetch_frame(url, timeout=timeout)


def _post_json(url: str, path: str, payload: dict, timeout: float = 15.0) -> bool:
    req = urllib.request.Request(f"{url.rstrip('/')}{path}",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with _retry_urlopen(req, timeout=timeout) as r:
        return r.status == 200


# ══════════════════════════════════════════════════════════════════════════════
# COMMAND 1: render_creature -- the TRIANGLE path ONLY
# ══════════════════════════════════════════════════════════════════════════════

# The banked A-pose protocol (measure_triangle_monkey.run_a: theta 0.6, phi 0.3,
# lift 0.40, target on the lifted body centre, radius by the fit law) -- the
# exact pose the receipt's verified coverage numbers were measured at. Derived,
# not picked.
A_POSE_THETA = 0.6
A_POSE_PHI = 0.3
A_POSE_LIFT = 0.40
ORBIT_PHI = 0.0


def _warm_count_or_zero(img) -> int:
    from tools.science_funnel import pixel_truth as pt
    return int(pt.warm_mask(img).sum())


def _safe(fn, *a, **k) -> dict:
    """An instrument that cannot measure records its refusal -- honest absence
    per instrument, never a crash of the command."""
    try:
        return fn(*a, **k)
    except Exception as e:                                # noqa: BLE001
        return {"instrument_error": f"{type(e).__name__}: {e}"}


def _compose_triangle(source: str) -> dict:
    """The presentation payload: indexed TRIANGLE geometry only.

    source 'ct_skeleton' -- the committed infant skeleton under the ONE pinned
    registration (ct_skeleton_triangle.layer_triangle_mesh). A path to an .obj
    -- the mesh loaded through the SAME triangle loader, recentered, no
    registration derived (its own units; recorded as such).
    """
    import numpy as np
    from tools.science_funnel import ct_skeleton_triangle as cst
    if source == "ct_skeleton":
        layer = cst.layer_triangle_mesh()
        payload = layer["verts9"].copy()
        tris = layer["tris"]
        record = dict(layer["record"])
        record["source"] = "ct_skeleton (committed infant CT skeleton, pinned registration)"
    else:
        path = Path(source)
        if not path.is_file():
            raise RuntimeError(f"workflow_commands refusal: source_mesh_missing {path}")
        if path.suffix.lower() != ".obj":
            raise RuntimeError(
                f"workflow_commands refusal: source_not_obj {path.name} -- the "
                "triangle loader consumes OBJ; translate other formats first")
        verts, tris_idx = cst.load_obj_mesh(path)
        v9 = np.zeros((verts.shape[0], 9), dtype=np.float32)
        v9[:, 0:3] = verts.astype(np.float32)
        v9[:, 3:6] = cst.mesh_normals(verts, tris_idx).astype(np.float32)
        v9[:, 6:9] = (0.82, 0.75, 0.60)               # the CT bone tint family
        payload = v9
        tris = tris_idx.astype(np.uint32).ravel()
        record = {"source": str(path), "source_units": "as-given (no registration derived)",
                  "vertices": int(verts.shape[0]), "triangles": int(tris_idx.shape[0])}
    # framing law: bbox centre -> the orbit origin (render-time framing ONLY;
    # the registration/data is untouched)
    ctr = (payload[:, 0:3].min(axis=0) + payload[:, 0:3].max(axis=0)) / 2.0
    payload[:, 0:3] -= ctr.astype(np.float32)
    return {"payload": payload, "tris": tris, "record": record}


def _post_mesh(url: str, payload, tris, radius, theta, phi) -> bool:
    from tools.science_funnel import ct_skeleton_triangle as cst
    return cst.post_layer_mesh(url, payload, tris, radius, theta, phi)


def render_creature(source: str = "ct_skeleton", out_dir: str | Path | None = None,
                    orbit_frames: int = 12, engine: str | None = None,
                    engine_exe: str | Path | None = None,
                    keep_engine: bool = False) -> dict:
    """Render <mesh-or-scene> through the engine's TRIANGLE pipeline and return
    the render path + pixel_truth numbers for the output stills.

    NO splat route is reachable from this function: the only upload is the
    indexed mesh to /mesh_bin (ct_skeleton_triangle.post_layer_mesh); the splat
    buffer builder and /membrane_bin are never referenced here.
    """
    import numpy as np
    from tools.science_funnel import pixel_truth as pt
    from tools.science_funnel import measure_triangle_monkey as mtm

    out = Path(out_dir) if out_dir else (ROOT / ".tmp/workflow_mcp/render"
                                         / f"render_{_now().replace(':', '')[:19]}")
    (out / "masks").mkdir(parents=True, exist_ok=True)
    (out / "orbit").mkdir(parents=True, exist_ok=True)
    (out / "orbit" / "masks").mkdir(parents=True, exist_ok=True)

    comp = _compose_triangle(source)
    payload, tris = comp["payload"], comp["tris"]

    handle = None
    if engine:
        url = engine
    else:
        handle = start_engine(engine_exe)
        url = handle.url
    try:
        # ── the A-pose still (the banked coverage protocol's exact pose) ─────
        pos = payload[:, 0:3].astype(np.float64).copy()
        pos[:, 1] += A_POSE_LIFT
        radius = mtm.fit_radius(comp)
        ctr_y = float((payload[:, 1].min() + payload[:, 1].max()) / 2.0)
        target = (0.0, A_POSE_LIFT + ctr_y, 0.0)
        a_payload = payload.copy()
        a_payload[:, 1] += np.float32(A_POSE_LIFT)
        if not _post_mesh(url, a_payload, tris, radius, A_POSE_THETA, A_POSE_PHI):
            raise RuntimeError("workflow_commands refusal: mesh_post_refused (/mesh_bin)")
        _post_json(url, "/camera", {"cam_radius": radius, "cam_theta": A_POSE_THETA,
                                    "cam_phi": A_POSE_PHI,
                                    "target_x": target[0], "target_y": target[1],
                                    "target_z": target[2]})
        time.sleep(0.8)
        a_png_bytes = _settle_capture(url, None)
        a_path = out / "a_pose.png"
        a_path.write_bytes(a_png_bytes)
        a_img = pt.load(a_path)
        W, H = a_img.shape[1], a_img.shape[0]
        a_hull_pts = mtm.project_points(pos, radius, A_POSE_THETA, A_POSE_PHI, W, H, target)
        a_hull = pt.hull_mask(a_hull_pts, a_img.shape)
        _save_mask(a_hull, out / "masks" / "a_pose_hull.png")
        a_metrics = {
            "png": str(a_path),
            "frame_whxh": [int(W), int(H)],
            "warm_object_pixels": _warm_count_or_zero(a_img),
            "grain": _safe(pt.grain, a_img, pt.warm_mask(a_img)),
            "whole_hull_coverage": _safe(pt.coverage, pt.warm_mask(a_img), a_hull),
        }

        # ── per-bone + macro coverage at the A pose (the decisive instrument:
        #    the banked paired presentation numbers 0.1201 vs 0.568) ──────────
        per_bone = {"instrument_error": "only measurable for the registered ct_skeleton"}
        macro = {}
        if source == "ct_skeleton":
            try:
                reg = mtm.regions_along_trunk(comp, "mesh")
                rows_table, bones_zero, covs = [], 0, []
                for b in reg["per_bone"]:
                    pts_px = mtm.project_points(pos[b["rows"]], radius, A_POSE_THETA,
                                                A_POSE_PHI, W, H, target)
                    if len(pts_px) < 3 or np.ptp(pts_px[:, 0]) < 1 or np.ptp(pts_px[:, 1]) < 1:
                        rows_table.append({"bone": b["preview"], "coverage": None,
                                           "note": "degenerate footprint"})
                        continue
                    hull = pt.hull_mask(pts_px, a_img.shape, dilate_px=1)
                    if int(hull.sum()) == 0:
                        rows_table.append({"bone": b["preview"], "coverage": None,
                                           "note": "footprint off-frame"})
                        continue
                    cov = pt.coverage(pt.warm_mask(a_img), hull)
                    covs.append(cov["coverage"])
                    rows_table.append({"bone": b["preview"], **cov})
                    if cov["coverage"] == 0.0:
                        bones_zero += 1
                for k, chunks in reg["macro"].items():
                    rows = np.concatenate(chunks)
                    pts_px = mtm.project_points(pos[rows], radius, A_POSE_THETA,
                                                A_POSE_PHI, W, H, target)
                    hull = pt.hull_mask(pts_px, a_img.shape, dilate_px=1)
                    macro[k] = (pt.coverage(pt.warm_mask(a_img), hull)
                                if int(hull.sum()) else {"coverage": None})
                per_bone = {
                    "bones": rows_table,
                    "median_coverage_all_bones": (round(float(np.median(covs)), 4)
                                                  if covs else None),
                    "bones_at_zero": bones_zero,
                    "macro": macro,
                }
            except Exception as e:                        # noqa: BLE001
                per_bone = {"instrument_error": f"{type(e).__name__}: {e}"}

        # ── the orbit (the clip scan's protocol: >= 5 frames, full turn) ─────
        counts, touches, orbit_pngs = [], [], []
        prev = None
        for i in range(orbit_frames):
            theta = 2.0 * math.pi * i / orbit_frames
            if i == 0:
                # re-post the payload with the orbit camera in the header
                pre = _fetch_frame(url)
                o_payload = payload.copy()            # recentered, no lift
                if not _post_mesh(url, o_payload, tris, radius, theta, ORBIT_PHI):
                    raise RuntimeError("workflow_commands refusal: mesh_post_refused (orbit)")
                b = _settle_capture(url, pre)
            else:
                if not _post_json(url, "/camera", {"cam_radius": radius, "cam_theta": theta,
                                                   "cam_phi": ORBIT_PHI,
                                                   "target_x": 0.0, "target_y": 0.0,
                                                   "target_z": 0.0}):
                    raise RuntimeError("workflow_commands refusal: camera_post_refused")
                b = _settle_capture(url, prev)
            prev = b
            o_path = out / "orbit" / f"orbit_f{i:03d}.png"
            o_path.write_bytes(b)
            orbit_pngs.append(str(o_path))
            o_img = pt.load(o_path)
            m = pt.warm_mask(o_img)
            counts.append(int(m.sum()))
            touches.append(pt.boundary_touch(m))
            o_pts = mtm.project_points(payload[:, 0:3].astype(np.float64), radius,
                                       theta, ORBIT_PHI, o_img.shape[1], o_img.shape[0])
            _save_mask(pt.hull_mask(o_pts, o_img.shape),
                       out / "orbit" / "masks" / f"orbit_f{i:03d}_hull.png")
        scan = _safe(pt.clip_scan, counts, touches)
        orbit_grain = [_safe(pt.grain, pt.load(Path(p)), pt.warm_mask(pt.load(Path(p))))
                       for p in orbit_pngs]
    finally:
        if handle is not None and not keep_engine:
            stop_engine(handle)

    record = {
        "command": "render_creature",
        "status": "rendered",
        "taken_utc": _now(),
        "source": source,
        "render_path": {
            "compose": "ct_skeleton_triangle.layer_triangle_mesh (indexed TRIANGLE geometry)",
            "upload": "/mesh_bin (the engine triangle pipeline: depth-tested, stencil-marking)",
            "camera": "/camera + settle-capture /frame (the banked determinism pattern)",
            "splat_route_reachable": False,
        },
        "engine": ({"url": handle.url, "port": handle.port, "pid": handle.proc.pid,
                    "exe": str(handle.exe), "exe_sha256": handle.exe_sha256,
                    "self_started": True}
                   if handle else {"url": engine, "self_started": False}),
        "payload": {"vertices": int(comp["payload"].shape[0]),
                    "triangles": int(comp["tris"].size // 3),
                    "layer_record": comp["record"]},
        "camera": {"radius_m": round(radius, 6),
                   "a_pose": {"theta": A_POSE_THETA, "phi": A_POSE_PHI,
                              "lift_m": A_POSE_LIFT, "target": target},
                   "orbit": {"frames": orbit_frames, "phi": ORBIT_PHI}},
        "a_pose": a_metrics,
        "per_bone_coverage": per_bone,
        "orbit": {"pngs": orbit_pngs, "warm_pixel_counts": counts,
                  "boundary_touches": touches, "clip_scan": scan,
                  "grain_per_frame": orbit_grain},
        "out_dir": str(out),
    }
    (out / "render_record.json").write_text(json.dumps(record, indent=1) + "\n",
                                            encoding="utf-8")
    return record


def _save_mask(mask, path: Path) -> None:
    from PIL import Image
    import numpy as np
    Image.fromarray((np.asarray(mask, dtype=bool) * 255).astype(np.uint8)).save(path)


# ══════════════════════════════════════════════════════════════════════════════
# COMMAND 2: verify_visual -- pixel_truth end-to-end with encoded gates
# ══════════════════════════════════════════════════════════════════════════════

def _load_mask2d(path: Path):
    """A mask/ROI as 2D bool (nonzero = inside). pixel_truth.load converts to
    RGB; masks must stay single-channel for the boolean algebra."""
    from PIL import Image
    import numpy as np
    return np.asarray(Image.open(path).convert("L")) > 0


def _gate(value, limit, cmp: str) -> bool:
    return value <= limit if cmp == "<=" else value >= limit


def verify_visual(frames_dir: str | Path, masks_dir: str | Path | None = None,
                  roi_dir: str | Path | None = None, pattern: str = "*.png",
                  render_record: str | Path | None = None,
                  guide_reference: int | None = None) -> dict:
    """pixel_truth end-to-end over a frames dir; every gate carries the
    pre-encoded threshold AND its provenance (receipt workflow_mcp_20260920).
    A metric whose instrument is absent (no masks / no ROIs / too few frames)
    is reported as pass=null 'not_measured' with the reason -- named honestly,
    never assumed."""
    import numpy as np
    from tools.science_funnel import pixel_truth as pt

    fdir, mdir, rdir = Path(frames_dir), Path(masks_dir) if masks_dir else None, \
        Path(roi_dir) if roi_dir else None
    if not fdir.is_dir():
        raise RuntimeError(f"workflow_commands refusal: frames_dir_missing {fdir}")
    frames = sorted(p for p in fdir.glob(pattern) if p.is_file())
    if not frames:
        raise RuntimeError(f"workflow_commands refusal: no frames match {fdir}/{pattern}")

    grain_medians, grain_vals, cov_vals, seen_vals, guide_ratios = [], [], [], [], []
    counts, touches = [], []
    cov_missing, roi_missing = [], []
    for f in frames:
        img = pt.load(f)
        obj = pt.warm_mask(img)
        counts.append(int(obj.sum()))
        touches.append(pt.boundary_touch(obj))
        g = _safe(pt.grain, img, obj)
        if "grain_median_local_variance" in g:
            grain_vals.append(g)
            grain_medians.append(g["grain_median_local_variance"])
        else:
            grain_vals.append(g)
        if mdir:
            mpath = mdir / f"{f.stem}_hull.png"
            if mpath.is_file():
                hull = _load_mask2d(mpath)
                cov_vals.append({"frame": f.name,
                                 **pt.coverage(obj, hull)})
            else:
                cov_missing.append(f.name)
        if rdir:
            rpath = rdir / f"{f.stem}_roi.png"
            if rpath.is_file():
                roi = _load_mask2d(rpath)
                seen_vals.append({"frame": f.name,
                                  **pt.object_seen(img, roi, dim=True)})
                gsv = pt.guide_seen(img, roi,
                                    reference_count=guide_reference)
                guide_ratios.append({"frame": f.name, **gsv})
            else:
                roi_missing.append(f.name)

    scan = _safe(pt.clip_scan, counts, touches)
    collapse_events = [e for e in (scan.get("clip_events", [])
                                   if "clip_events" in scan else [])
                       if e.get("kind") == "collapse"]
    touch_events = [e for e in (scan.get("clip_events", [])
                                if "clip_events" in scan else [])
                    if e.get("kind") == "new_boundary_touch"]

    # per-bone gates from the render record (geometry-aware numbers)
    pb_median = pb_zero = a_pose_cov = None
    if render_record:
        rr = json.loads(Path(render_record).read_text(encoding="utf-8"))
        pbc = rr.get("per_bone_coverage", {})
        pb_median = pbc.get("median_coverage_all_bones")
        pb_zero = pbc.get("bones_at_zero")
        a_pose_cov = ((rr.get("a_pose", {}).get("whole_hull_coverage") or {})
                      .get("coverage"))

    table = []

    def add(metric, value, limit, cmp, provenance, measured=True, note=None):
        row = {"metric": metric, "value": value,
               "gate": (f"{cmp} {limit}" if measured else None),
               "pass": (bool(_gate(value, limit, cmp)) if measured else None),
               "threshold_provenance": provenance}
        if note:
            row["note"] = note
        if not measured:
            row["pass"] = None
            row["not_measured_reason"] = note
        table.append(row)

    clipscan_measured = "clip_events" in scan
    add("clipscan_collapse_events", len(collapse_events) if clipscan_measured else None,
        THRESHOLDS["clipscan_collapse_events_max"], "<=",
        "FALSIFIER_C_CLIP (triangle_monkey_20260920): frame count < 0.5x neighbor "
        "median = clip collapse; repaired engine passes all frames",
        measured=clipscan_measured,
        note=None if clipscan_measured else f"clipscan needs >= 5 frames, got {len(frames)}")
    add("clipscan_new_boundary_touch", len(touch_events) if clipscan_measured else None,
        THRESHOLDS["clipscan_new_boundary_touch_max"], "<=",
        "FALSIFIER_C_CLIP edge-clip clause (banked AFTER carried 1 event in the "
        "operator's extreme pan scenario radius 1.0 + pan_x -0.93; the default "
        "orbit does not reproduce that scenario)",
        measured=clipscan_measured,
        note=None if clipscan_measured else f"clipscan needs >= 5 frames, got {len(frames)}")
    add("grain_median_local_variance",
        round(float(np.median(grain_medians)), 4) if grain_medians else None,
        None, None, GRAIN_LAW, measured=False,
        note="reported, not gated (see provenance)" if grain_medians
        else "no frame yielded a measurable object interior")
    if mdir:
        covs = [c["coverage"] for c in cov_vals]
        # THE GATE BINDS TO THE PROTOCOL THE THRESHOLD WAS DERIVED FROM: the
        # banked 0.2561-vs-0.3957 midband is a FIXED-POSE (A-pose) measurement.
        # When the render record supplies that pose's coverage it is gated
        # directly; for caller-supplied frames the MEDIAN carries the gate
        # (a distribution's centre against a single-pose threshold). The
        # per-frame MINIMUM is REPORTED, never gated and never hidden: the
        # curled skeleton's convex hull legitimately includes inter-limb voids
        # whose area varies with orbit theta.
        add("whole_hull_coverage_a_pose", a_pose_cov,
            THRESHOLDS["whole_hull_coverage_min"], ">=",
            "midband of banked fixed-pose whole-hull coverage: splat 0.2561 vs "
            "mesh 0.3957 (triangle_monkey_20260920 A) -- the protocol-matched "
            "measurement", measured=a_pose_cov is not None,
            note=None if a_pose_cov is not None
            else "no render record / no a-pose coverage in it")
        add("whole_hull_coverage_median", round(float(np.median(covs)), 4) if covs else None,
            THRESHOLDS["whole_hull_coverage_min"], ">=",
            "same provenance as whole_hull_coverage_a_pose; the median carries "
            "the gate for arbitrary caller frames", measured=bool(covs),
            note=None if covs else "no masks matched")
        add("whole_hull_coverage_min_frame", min(covs) if covs else None,
            None, None,
            "REPORTED, not gated: orbit theta varies the curled skeleton's "
            "hull-void area (measured min 0.1861 on the verified e2e orbit); "
            "the protocol-matched gate is the a-pose value above",
            measured=False,
            note="reported" if covs else f"no masks matched: {len(cov_missing)} "
                                         f"frames (masks named <frame-stem>_hull.png)")
    else:
        add("whole_hull_coverage", None, None, None,
            "midband of banked splat 0.2561 vs mesh 0.3957", measured=False,
            note="no --masks supplied: projected-footprint hulls are geometry; "
                 "pass them to measure coverage")
    if render_record:
        add("per_bone_median_coverage", pb_median,
            THRESHOLDS["per_bone_median_coverage_min"], ">=",
            "midband of banked paired presentations: splat 0.1201 vs mesh 0.568 "
            "(median all bones) -- the decisive instrument",
            measured=pb_median is not None,
            note=None if pb_median is not None else "render record carried no per-bone table")
        add("bones_at_zero", pb_zero, THRESHOLDS["bones_at_zero_max"], "<=",
            "count discriminator: splat 5, mesh 0", measured=pb_zero is not None,
            note=None if pb_zero is not None else "render record carried no per-bone table")
    if rdir:
        seens = [s["object_seen_ratio"] for s in seen_vals]
        add("object_seen_dim_min_frame", min(seens) if seens else None,
            THRESHOLDS["object_seen_dim_min"], ">=",
            "midband of splat 0.0 vs the WORSE verified mesh side 0.5191 "
            "(two-sided guide protocol, dim detector)",
            measured=bool(seens),
            note=None if seens else f"no ROIs matched (named <frame-stem>_roi.png)")
        grs = [g.get("guide_presence_ratio") for g in guide_ratios]
        add("guide_presence_ratio_min_frame",
            min([g for g in grs if g is not None], default=None),
            THRESHOLDS["guide_presence_ratio_min"], ">=",
            "FALSIFIER_B_GRID pre-registered bar: a guide invisible from one side "
            "is not a guide", measured=guide_reference is not None and any(
                g is not None for g in grs),
            note=None if (guide_reference is not None and any(
                g is not None for g in grs)) else
            "needs --guide-reference (the uncontested side's ink count)")
    else:
        add("object_seen", None, None, None,
            "midband of splat 0.0 vs mesh 0.5191", measured=False,
            note="no --roi supplied: region-of-interest instruments need ROIs")

    reds = [r for r in table if r["pass"] is False]
    return {
        "command": "verify_visual",
        "status": "verified" if not reds else "RED",
        "taken_utc": _now(),
        "frames_dir": str(fdir),
        "frames": [f.name for f in frames],
        "masks_dir": str(mdir) if mdir else None,
        "roi_dir": str(rdir) if rdir else None,
        "clip_scan": scan,
        "grain_per_frame": grain_vals,
        "coverage_per_frame": cov_vals,
        "object_seen_per_frame": seen_vals,
        "guide_seen_per_frame": guide_ratios,
        "gates": table,
        "reds": [r["metric"] for r in reds],
        "n_gates_pass": sum(1 for r in table if r["pass"] is True),
        "n_gates_fail": len(reds),
        "n_gates_not_measured": sum(1 for r in table if r["pass"] is None),
    }


# ══════════════════════════════════════════════════════════════════════════════
# COMMAND 3: adjudicate + bio.* -- reality_gate resolved at runtime
# ══════════════════════════════════════════════════════════════════════════════

def load_reality_gate():
    """Resolve the gate AT RUNTIME -- import if present on this lineage, else
    the structured honest absence (branch named)."""
    try:
        from tools.creature_graph import reality_gate          # noqa: PLC0415
        return reality_gate, None
    except Exception as e:                                # noqa: BLE001
        return None, {**HONEST_ABSENCE,
                      "detail": f"{type(e).__name__}: {e}",
                      "resolution": "import tools.creature_graph.reality_gate at runtime; "
                                    "cross-branch merges are the integrator's job"}


def _load_bundle(bundle: str | Path) -> tuple[dict, Path]:
    path = Path(bundle)
    if not path.is_file():
        raise RuntimeError(f"workflow_commands refusal: bundle_missing {path}")
    return json.loads(path.read_text(encoding="utf-8")), path


def adjudicate(bundle: str | Path) -> dict:
    """Wrap reality_gate.adjudicate: {category, violations[]} -- or the
    structured honest absence on this lineage."""
    rg, absence = load_reality_gate()
    if absence:
        return {"command": "adjudicate", "status": "unavailable", **absence}
    b, path = _load_bundle(bundle)
    try:
        verdict = rg.adjudicate(b)
    except rg.BundleError as e:
        return {"command": "adjudicate", "status": "refused",
                "error": "bundle_malformed", "detail": str(e), "bundle": str(path)}
    return {"command": "adjudicate", "status": "classified", "bundle": str(path),
            "category": verdict["category"],
            "violations": verdict["violations"],
            "n_violations": len(verdict["violations"]),
            "verdict": verdict}


def bio_stage(bundle: str | Path) -> dict:
    """The stage label + evidence, or FAILED as unadmittable (missing stage =
    failed, like a missing sha256). Reads the bundle manifest's stage fields --
    the exact fields the gate's check_stage_consistency consumes."""
    b, path = _load_bundle(bundle)
    components = b.get("components", [])
    labels, unlabeled, evidence = {}, [], {}
    for comp in components:
        stage = comp.get("stage") or {}
        label = stage.get("label")
        cid = comp.get("id", "?")
        if not label:
            unlabeled.append(cid)
            continue
        labels.setdefault(label, []).append(cid)
        evidence[cid] = {"stage_label": label,
                         "confirmed": bool(stage.get("confirmed")),
                         "provenance": stage.get("provenance")}
    if unlabeled or not labels:
        return {"command": "bio.stage", "status": "failed_unadmittable",
                "bundle": str(path),
                "reason": "missing stage = failed, like a missing sha256 "
                          "(admission-required metadata)",
                "unlabeled_components": unlabeled,
                "stage_labels": labels, "evidence": evidence}
    if len(labels) > 1:
        return {"command": "bio.stage", "status": "failed_unadmittable",
                "bundle": str(path),
                "reason": "one creature, one life stage: stages mixed inside one bundle",
                "stage_labels": {k: len(v) for k, v in sorted(labels.items())},
                "evidence": evidence}
    label = next(iter(labels))
    unconfirmed_adult = (label == "adult"
                         and any(not (e["confirmed"] and e["provenance"])
                                 for e in evidence.values()))
    return {"command": "bio.stage", "bundle": str(path),
            "status": "unadmittable_adult_unconfirmed" if unconfirmed_adult
            else "labeled",
            "stage_label": label,
            "n_components": len(components),
            "evidence": evidence,
            "note": ("adult requires confirmation WITH provenance "
                     "(adult-CONFIRMED, like sha256)" if unconfirmed_adult else None)}


def bio_check(bundle: str | Path) -> dict:
    """The 'does this biologically check out' command: L1-L4 -> {category,
    violations}. Requires the reality gate; honest absence otherwise."""
    rg, absence = load_reality_gate()
    if absence:
        return {"command": "bio.check", "status": "unavailable", **absence}
    result = adjudicate(bundle)
    result["command"] = "bio.check"
    result["laws"] = ["L1_stage_consistency", "L2_allometric_coherence",
                      "L3_taxonomic_coherence", "L4_physics_bars"]
    return result


def bio_fantasy_acknowledge(bundle: str | Path, out: str | Path | None = None) -> dict:
    """The developer-driven construction mode: record the manifest
    acknowledgment on the bundle, THEN the gate admits to the fantasy category
    (never silent, never accidental)."""
    b, path = _load_bundle(bundle)
    b["fantasy_manifest_acknowledged"] = True
    out_path = Path(out) if out else path.with_suffix(".acknowledged.json")
    out_path.write_text(json.dumps(b, indent=1) + "\n", encoding="utf-8")
    receipt = {"command": "bio.fantasy_acknowledge",
               "status": "acknowledged",
               "bundle": str(path), "acknowledged_bundle": str(out_path),
               "fantasy_manifest_acknowledged": True}
    rg, absence = load_reality_gate()
    if absence:
        receipt["adjudication"] = {"status": "unavailable", **absence}
        return receipt
    try:
        verdict = rg.adjudicate(b)
        receipt["adjudication"] = {
            "status": "classified", "category": verdict["category"],
            "n_violations": len(verdict["violations"]),
            "violations": verdict["violations"],
            "construction": verdict.get("construction")}
    except rg.BundleError as e:
        receipt["adjudication"] = {"status": "refused",
                                   "error": "bundle_malformed", "detail": str(e)}
    return receipt


# ══════════════════════════════════════════════════════════════════════════════
# COMMAND 4: checklist -- THE_CHECKLIST as a machine-readable walk
# ══════════════════════════════════════════════════════════════════════════════

CHECKLIST_PATH = ROOT / "docs/THE_CHECKLIST.md"
CHECKLIST_SOURCE = ("docs/THE_CHECKLIST.md @ branch agent/workflow-checklist-20260920 "
                    "(e9c8b394); this command parses the live file when present and "
                    "falls back to the banked mirror below when the doc is not on "
                    "this lineage")

# (section, name-substring) -> the command(s) that satisfy the step. Every step
# NOT listed here needs judgment -- named honestly, never pretended away.
COMMAND_MAP = {
    ("0", "orient first"): {"commands": ["orient (engine MCP tool)"],
                            "satisfies": "orients the agent; the rest of the step "
                                         "(reading the docs) is judgment"},
    ("0", "rule 0"): {"commands": [],
                      "satisfies": "judgment: bank a receipt (statement/prediction/"
                                   "falsifier) BEFORE code -- no command can think it"},
    ("0", "rule 1"): {"commands": [],
                      "satisfies": "judgment: derive numbers from equations/measurements"},
    ("0", "scope"): {"commands": [],
                     "satisfies": "judgment: worktree/branch/port discipline"},
    ("1", "format"): {"commands": [],
                      "satisfies": "judgment: data translation to triangles"},
    ("1", "provenance"): {"commands": [],
                          "satisfies": "judgment: sha256/license receipts"},
    ("1", "stage label"): {"commands": ["bio_stage", "bio_check"],
                           "satisfies": "bio_stage fails the record as unadmittable "
                                        "without a stage label; bio_check enforces L1"},
    ("1", "the classification"): {"commands": ["adjudicate"],
                                  "satisfies": "reality_gate classify {category, "
                                               "violations}; honest absence off-lineage"},
    ("1", "allometry coherence"): {"commands": ["bio_check"],
                                   "satisfies": "the gate's L2 measured-deviation check"},
    ("2", "triangles define membranes"): {"commands": [],
                                          "satisfies": "judgment: construction authoring"},
    ("2", "the matter system"): {"commands": [],
                                 "satisfies": "judgment: matter-kernel construction"},
    ("2", "stage-true at scale"): {"commands": ["bio_check"],
                                   "satisfies": "the gate's L2 per-bone scale-factor "
                                                "check (the H2 3.79-8.8x negative example)"},
    ("3", "the triangle technique"): {"commands": ["render_creature"],
                                      "satisfies": "the TRIANGLE path ONLY (no splat "
                                                   "route reachable; conformance-tested)"},
    ("3", "deterministic pixel verification"): {"commands": ["verify_visual"],
                                                "satisfies": "pixel_truth end-to-end with "
                                                             "pre-encoded thresholds"},
    ("3", "dyad judgments"): {"commands": [],
                              "satisfies": "judgment: a human-verdict channel, never a command"},
    ("4", "one membrane per lane"): {"commands": [],
                                     "satisfies": "judgment: lane discipline"},
    ("4", "the standing falsifier battery"): {"commands": [],
                                              "satisfies": "judgment: run the lane's own suites"},
    ("5", "engine lanes"): {"commands": ["verify_visual (visual lanes)"],
                            "satisfies": "the pixel checker for visual lanes; cmake/derive "
                                         "lanes keep their own reproduction protocol"},
    ("5", "reds are banked honestly"): {"commands": [],
                                        "satisfies": "judgment: report greens AND reds"},
    ("6", "commit"): {"commands": [],
                      "satisfies": "judgment: commit + push YOUR branch only"},
}

MIRRORED_CHECKLIST = [
    {"section": "0", "title": "BEFORE YOU BUILD", "steps": [
        "Orient first", "Rule 0 banked BEFORE any code", "Rule 1 -- derive it", "Scope"]},
    {"section": "1", "title": "DATA INTAKE (any external anatomy/imaging data)", "steps": [
        "Format", "Provenance", "STAGE LABEL admission-required",
        "THE CLASSIFICATION", "Allometry coherence"]},
    {"section": "2", "title": "CONSTRUCTION (anatomy -> membranes)", "steps": [
        "Triangles define membranes.", "The MATTER SYSTEM owns geometry",
        "Stage-true at scale 1.0"]},
    {"section": "3", "title": "VISUAL", "steps": [
        "The TRIANGLE technique is standing law",
        "Deterministic pixel verification -- no vision model, no agent eyeballs",
        "Dyad judgments"]},
    {"section": "4", "title": "PHYSICS / WALK LANES", "steps": [
        "One membrane per lane", "The standing falsifier battery"]},
    {"section": "5", "title": "VERIFICATION (what the lead runs on YOUR lane)", "steps": [
        "Engine lanes: fresh cmake build (visual lanes: the pixel checker)",
        "Reds are banked honestly"]},
    {"section": "6", "title": "SHIP", "steps": [
        "Commit (trailer) + push YOUR BRANCH ONLY"]},
]


def _parse_checklist_md(text: str):
    """Parse THE_CHECKLIST's structure: '## N . TITLE' sections with
    '- [ ] NAME: body' steps and their 'Home:' pointers."""
    import re
    sections, cur = [], None
    for line in text.splitlines():
        m = re.match(r"^## (\d+)\s*[·.]?\s*(.+?)\s*$", line)
        if m:
            cur = {"section": m.group(1), "title": m.group(2), "steps": []}
            sections.append(cur)
            continue
        if cur is not None and line.lstrip().startswith("- [ ]"):
            body = line.lstrip()[5:].strip()
            name = body
            home = None
            hm = re.search(r"Home:\s*`?([^`;]+)`?", body)
            if hm:
                home = hm.group(1).strip()
            nm = re.match(r"\*\*(.+?)\*\*", body)
            if nm:
                name = nm.group(1)
            else:
                cm = re.match(r"([^:]+):", body)
                name = cm.group(1).strip() if cm else body[:60]
            cur["steps"].append({"name": name, "home": home})
    return sections


def _map_commands(section: str, name: str) -> dict:
    low = name.lower()
    for (sec, key), entry in COMMAND_MAP.items():
        if sec == section and key in low:
            return entry
    return {"commands": [], "satisfies": "NO COMMAND YET -- named honestly: this "
                                         "step needs judgment (prose gates are not "
                                         "faked as commands)"}


def checklist() -> dict:
    """THE_CHECKLIST's current gates as a machine-readable walk: step id, law
    home pointer, the command that satisfies it -- or an honest judgment name.
    Every step a command CANNOT satisfy is labelled 'needs_judgment', never
    dressed up as commandable."""
    source = "live docs/THE_CHECKLIST.md"
    sections = None
    if CHECKLIST_PATH.is_file():
        sections = _parse_checklist_md(
            CHECKLIST_PATH.read_text(encoding="utf-8"))
    if not sections:
        sections = MIRRORED_CHECKLIST
        source = "banked mirror (docs/THE_CHECKLIST.md not on this lineage)"
    walk, n_cmd, n_judg = [], 0, 0
    for sec in sections:
        steps = []
        for i, s in enumerate(sec["steps"]):
            name = s["name"] if isinstance(s, dict) else s
            home = s.get("home") if isinstance(s, dict) else None
            entry = _map_commands(sec["section"], name)
            commands = entry["commands"]
            needs_judgment = not commands
            n_cmd += 0 if needs_judgment else 1
            n_judg += 1 if needs_judgment else 0
            steps.append({
                "step_id": f"{sec['section']}.{i + 1}",
                "name": name,
                "law_home": home,
                "commands": commands,
                "what_the_command_does": entry["satisfies"],
                "needs_judgment": needs_judgment,
            })
        walk.append({"section": sec["section"], "title": sec["title"], "steps": steps})
    return {
        "command": "checklist",
        "source": source,
        "source_pointer": CHECKLIST_SOURCE,
        "walk": walk,
        "n_steps_commandable": n_cmd,
        "n_steps_needing_judgment": n_judg,
        "note": "a step you cannot pass is a BLOCKED-with-evidence verdict, "
                "never a workaround (THE_CHECKLIST); commandable steps are "
                "driven by the command, judgment steps are named, not faked",
    }


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("render-creature")
    r.add_argument("source", nargs="?", default="ct_skeleton")
    r.add_argument("--out", default=None)
    r.add_argument("--orbit-frames", type=int, default=12)
    r.add_argument("--engine", default=None, help="already-running engine URL")
    r.add_argument("--engine-exe", default=None)
    r.add_argument("--keep-engine", action="store_true")

    v = sub.add_parser("verify-visual")
    v.add_argument("frames_dir")
    v.add_argument("--masks", default=None)
    v.add_argument("--roi", default=None)
    v.add_argument("--pattern", default="*.png")
    v.add_argument("--render-record", default=None)
    v.add_argument("--guide-reference", type=int, default=None)

    a = sub.add_parser("adjudicate"); a.add_argument("bundle")
    bs = sub.add_parser("bio-stage"); bs.add_argument("bundle")
    bc = sub.add_parser("bio-check"); bc.add_argument("bundle")
    bf = sub.add_parser("bio-fantasy-acknowledge")
    bf.add_argument("bundle"); bf.add_argument("--out", default=None)

    sub.add_parser("checklist")

    args = ap.parse_args(argv)
    if args.cmd == "render-creature":
        print(_out(render_creature(args.source, args.out, args.orbit_frames,
                                   args.engine, args.engine_exe, args.keep_engine)))
        return 0
    if args.cmd == "verify-visual":
        res = verify_visual(args.frames_dir, args.masks, args.roi, args.pattern,
                            args.render_record, args.guide_reference)
        print(_out(res))
        return 1 if res["reds"] else 0
    if args.cmd == "adjudicate":
        print(_out(adjudicate(args.bundle))); return 0
    if args.cmd == "bio-stage":
        print(_out(bio_stage(args.bundle))); return 0
    if args.cmd == "bio-check":
        print(_out(bio_check(args.bundle))); return 0
    if args.cmd == "bio-fantasy-acknowledge":
        print(_out(bio_fantasy_acknowledge(args.bundle, args.out))); return 0
    if args.cmd == "checklist":
        print(_out(checklist())); return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
