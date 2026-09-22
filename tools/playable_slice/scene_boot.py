"""scene_boot.py -- THE PLAYABLE SLICE's standing start, from committed bytes.

TWO committed-byte artifacts, both deterministic:

1. THE TICK BODY (the physics actor): the engine's movement law (gravity +
   floor contact, membrane_tick.cpp) runs on THE REAL SKELETON -- the
   committed CT skeleton (meshes_body_20260922: the committed previews,
   repaired to the aliveness importer's own closure rule and decimated under
   its 500,000-triangle cap by the cap-derived ratio r = kMaxTris/N_repaired,
   receipt slice_real_body_20260922), posed by the SAME standing compose the
   ghost runs, and committed beside this slice as standing_body.obj with its
   sha pinned in body_manifest.json. The named stand-in debt
   (mock_physics_body, the bbox capsule) is RETIRED: the payload rides the
   REAL aliveness ingestion (/mesh_import) and the engine's REAL tick.

2. THE GHOST (the visual creature): the committed standing skeleton -- the
   pose of record (standing_pose_20260921/pose.json) through the SAME FK the
   battery verified, full committed preview resolution -- served to the page
   as a DECLARED OVERLAY that rides the real body's root and the named carry
   mock. The ghost is labeled in the UI; it never animates by itself. Its
   declaration RESOLVES TO the tick body: body and ghost are the same pose of
   record -- the body is its import-grade twin (repaired + decimated), not a
   stand-in.

REALITY: import, gravity, contact, the release transient, the root stream.
FANTASY: the carry slide (MOCK[mock_carry], server-side). DECLARED: the ghost
overlay (DECLARED[ghost_standing_pose]).
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "science_funnel" / "validation" / "standing_pose_20260921"))
sys.path.insert(0, str(ROOT / "tools" / "science_funnel" / "validation" / "hip_pivot_proof_20260921"))

from standing_pose_core import StandingDerivation  # noqa: E402
from tools.science_funnel import ct_skeleton_layer as CSL  # noqa: E402
from tools.science_funnel import ct_skeleton_triangle as CST  # noqa: E402

POSE_JSON = ROOT / "tools/science_funnel/validation/standing_pose_20260921/pose.json"
# the seat height constant the compose needs -- banked in the standing-pose
# receipt with its source pin (this lineage's own graph lacks the object)
SEAT_HEIGHT_M = -0.08977588222411312

# THE ALIVENESS IMPORTER'S OWN LAW (ChimeraEngine/engine/importer.hpp): past
# kMaxTris = 500,000 triangles a body is refused BY NAME. The committed
# preview set measured 712,522 tris with 19/25 previews failing the
# importer's closure rule -- both MEASURED (receipt slice_real_body_20260922);
# the real-body lane repaired and decimated the skeleton UNDER this cap and
# the slice commits the result as its tick body.
IMPORT_TRI_CAP = 500000

# THE REAL BODY: committed import payload (posed, merged) + its pin manifest.
BODY_OBJ = HERE / "standing_body.obj"
BODY_MANIFEST = (ROOT / "tools/science_funnel/data/morphosource_ct/"
                 "meshes_body_20260922/body_manifest.json")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def edge_audit(tris: np.ndarray, n_verts: int) -> dict:
    """The importer's own closure rule, mirrored: every undirected edge exactly
    two triangles, one triangle per direction (consistent winding)."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    ea = np.sort(np.stack([a, b], axis=1), axis=1)
    eb = np.sort(np.stack([b, c], axis=1), axis=1)
    ec = np.sort(np.stack([c, a], axis=1), axis=1)
    all_e = np.concatenate([ea, eb, ec], axis=0)
    _, counts = np.unique(all_e, axis=0, return_counts=True)
    bad = int((counts != 2).sum())
    key = (np.concatenate([a, b, c]).astype(np.int64) * (n_verts + 1)
           + np.concatenate([b, c, a]))
    _, c2 = np.unique(key, return_counts=True)
    winding_bad = int((c2 != 1).sum())
    return {"boundary_edges": bad, "winding_violations": winding_bad,
            "closed": bad == 0 and winding_bad == 0}


# ── 1. THE REAL TICK BODY (the repaired + decimated committed skeleton) ──────

def build_real_body() -> tuple[bytes, dict]:
    """THE REAL BODY: the committed CT skeleton, repaired to the aliveness
    importer's own closure rule and decimated under its kMaxTris by the
    cap-derived ratio (lane slice_real_body_20260922), posed by the SAME
    standing compose the ghost runs, and committed beside this slice as
    standing_body.obj -- its sha pinned in body_manifest.json. The named
    stand-in (mock_physics_body, the bbox capsule) is RETIRED."""
    man = json.loads(BODY_MANIFEST.read_text(encoding="utf-8"))
    pin = man["import_payload"]
    obj = BODY_OBJ.read_bytes()
    if sha256(obj) != pin["sha256"]:
        raise RuntimeError("scene_boot: standing_body.obj drift vs the "
                           "body_manifest.json pin")
    if pin["triangles"] > IMPORT_TRI_CAP:
        raise RuntimeError(f"scene_boot: real body past the importer's cap: "
                           f"{pin['triangles']} > {IMPORT_TRI_CAP}")
    rec = {"schema": "chimera.playable_slice.real_body.v1",
           "body_id": "physics_body",
           "derived_from": pin["compose"]["mesh_dir"],
           "bones": pin["compose"]["bones"],
           "vertices": pin["vertices"], "triangles": pin["triangles"],
           "sha256": pin["sha256"],
           "under_cap": True}
    return obj, rec


# ── 2. THE GHOST: the committed standing skeleton, full preview resolution ──

def build_standing_layer(preview_dir: Path | None = None,
                         obj_suffix: str = "_lo"
                         ) -> tuple[np.ndarray, np.ndarray, dict]:
    """The pose of record through the verified FK, as ONE merged indexed mesh
    (scene metres, pads' mean plane at y=0) -- the standing lane's own compose,
    byte-deterministic from committed files. `preview_dir`/`obj_suffix` select
    the per-bone mesh set (default: the full-resolution committed previews);
    the real-body lane composes its repaired/decimated bones through THIS SAME
    function, so the tick body's payload and the ghost share one compose."""
    pose = json.loads(POSE_JSON.read_text(encoding="utf-8"))
    x_rec = np.array(pose["variables"]["x_R12"], dtype=np.float64)
    dv = StandingDerivation()

    raw = CSL.WALKER_DERIVED_PATH.read_bytes()
    assert CSL._sha256(raw) == CSL.WALKER_DERIVED_SHA256, "walker_derivation_pin_drift"
    hat = float(json.loads(raw)["body_model"]["segments_Table1"]["HAT"]["length_m"])
    composite = CSL.load_obj_vertices(CSL.PREVIEW_DIR / CSL.COMPOSITE_PREVIEW)
    scale, R_reg, t_reg, reg_diag = CSL.ct_registration(composite, hat, SEAT_HEIGHT_M)

    src_dir = CSL.PREVIEW_DIR if preview_dir is None else Path(preview_dir)
    T = dv.fk(x_rec)
    chunks_v, chunks_t = [], []
    off = 0
    man = json.loads((CSL.CT_DIR / "meshes" / "manifest.json").read_text())
    for entry in man["bones"]:
        name = Path(entry["file"]).name
        preview = name.replace(".obj", obj_suffix + ".obj")
        verts_mm, tris = CST.load_obj_mesh(src_dir / preview)
        bone = int(name.split("_")[1])
        posed_ct = T[bone].pts(verts_mm)
        scene = CSL.apply_registration(posed_ct, scale, R_reg, t_reg)
        chunks_v.append(scene.astype(np.float64))
        chunks_t.append(tris + off)
        off += scene.shape[0]
    verts = np.concatenate(chunks_v, axis=0)
    tris = np.concatenate(chunks_t, axis=0).astype(np.int64)

    # the standing placement (the standing lane's own law): the posed pads'
    # plane normal -> scene up, the pads' mean plane -> y = 0
    P_ct = dv.pad_centroids(x_rec)
    _, n_ct = dv._plane_stats(P_ct)
    n_scene0 = R_reg @ n_ct
    up = np.array([0.0, 1.0, 0.0])
    v = n_scene0 / np.linalg.norm(n_scene0)
    c = float(v @ up)
    axis = np.cross(v, up)
    s = float(np.linalg.norm(axis))
    if s < 1e-15:
        R_place = np.eye(3)
    else:
        axis = axis / s
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        R_place = np.eye(3) + K * s + K @ K * (1.0 - c)
    pad_scene = (P_ct @ R_reg.T) * scale / 1000.0 + t_reg
    pad_scene = pad_scene @ R_place.T
    lift = float(pad_scene[:, 1].mean())
    # the per-bone compose already applied the registration; here ONLY the
    # standing placement rides on top (the standing lane's own order)
    verts = verts @ R_place.T
    verts = verts - np.array([0.0, lift, 0.0])

    rec = {"pose_json_sha256": sha256(POSE_JSON.read_bytes()),
           "registration_pin_sha256": CSL.WALKER_DERIVED_SHA256,
           "mesh_dir": (src_dir.relative_to(ROOT).as_posix()
                        if src_dir != CSL.PREVIEW_DIR
                        else "meshes_preview (full committed preview resolution)"),
           "bones": len(man["bones"]),
           "vertices": int(verts.shape[0]), "triangles": int(tris.shape[0]),
           "declared_id": "ghost_standing_pose" if obj_suffix == "_lo" else None,
           "units": "scene metres, +Y up, pads' mean plane at y=0"}
    return verts, tris, rec


_LAYER_CACHE = None


def build_standing_layer_cached():
    """One build per process: the FK + registration is deterministic, so the
    body and the ghost share it (the clean-machine launch pays it once)."""
    global _LAYER_CACHE
    if _LAYER_CACHE is None:
        _LAYER_CACHE = build_standing_layer()
    return _LAYER_CACHE


def build_ghost_obj():
    verts, tris, rec = build_standing_layer_cached()
    out = io.BytesIO()
    out.write(b"# chimera.playable_slice DECLARED[ghost_standing_pose] visual overlay\n")
    out.write(b"# the committed standing skeleton (pose of record); rides the tick body's real root\n")
    # vectorized writers: 355k verts + 712k tris must build in ~1 s or the
    # clean-machine launch bar (10 s) pays for string formatting
    np.savetxt(out, verts, fmt="v %.6f %.6f %.6f")
    np.savetxt(out, tris + 1, fmt="f %d %d %d")
    return out.getvalue(), rec


# ── the engine front (tiny, own-port law) ───────────────────────────────────

def free_port(avoid=(8127,)) -> int:
    import socket
    if 8127 not in avoid:
        avoid = tuple(avoid) + (8127,)
    for _ in range(64):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        if port in avoid:
            continue
        try:
            s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s2.bind(("127.0.0.1", port))
            s2.close()
        except OSError:
            continue
        return port
    raise RuntimeError("scene_boot: no bind-tested free port")


def http_post(base: str, path: str, body: bytes, timeout: int = 180,
              ctype: str = "application/octet-stream") -> dict:
    req = urllib.request.Request(base + path, data=body, method="POST",
                                 headers={"Content-Type": ctype})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def http_get_raw(base: str, path: str, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


def http_get_json(base: str, path: str, timeout: int = 60) -> dict:
    return json.loads(http_get_raw(base, path, timeout))


def wait_engine(url: str, timeout: float = 60.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            http_get_raw(url, "/frame", timeout=5)
            return
        except OSError:
            time.sleep(0.25)
    raise RuntimeError("scene_boot: engine not ready")


def boot_standing_start(engine_url: str) -> dict:
    """Import THE REAL BODY (the committed repaired + decimated skeleton) and
    arm the movement law. DETERMINISTIC: committed bytes, same import bytes
    every call (the basis of F-SLICE-RESTART)."""
    obj, rec = build_real_body()
    # the real body's parse costs minutes on this machine (measured this lane:
    # 130-238 s, variable with load, for the pinned 499,976-tri payload) --
    # the capsule's 180 s default cut the boot off mid-parse
    res = http_post(engine_url, "/mesh_import", b"O" + obj, timeout=900)
    if not res.get("ok"):
        raise RuntimeError("scene_boot: import refused: " + str(res.get("error")))
    # THE MOVEMENT LAW, armed: gravity + ground contact on the root
    # ("a creature that cannot FALL cannot WALK")
    g = http_post(engine_url, "/tick_gravity", b'{"on":true}',
                  ctype="application/json")
    if not g.get("ok"):
        raise RuntimeError("scene_boot: gravity refused: " + str(g.get("error")))
    rec["scene_sha256"] = sha256(obj)
    rec["import_stats"] = {k: res[k] for k in res if k != "ok"}
    rec["gravity_armed"] = bool(g.get("gravity_on"))
    return rec


def wait_settled(engine_url: str, settle_vy: float = 0.05,
                 timeout: float = 20.0) -> dict:
    """The standing start = the engine's own settle: |root_vy| -> ~0 twice."""
    st: dict = {}
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        st = http_get_json(engine_url, "/tick_state")
        vy = float(st.get("root_vy", 0.0))
        if abs(vy) <= settle_vy and last is not None and abs(last) <= settle_vy:
            return st
        last = vy
        time.sleep(0.05)
    return st


def verts_payload(engine_url: str) -> bytes:
    return http_get_raw(engine_url, "/verts")


def topology_payload(engine_url: str) -> bytes:
    return http_get_raw(engine_url, "/topology")
