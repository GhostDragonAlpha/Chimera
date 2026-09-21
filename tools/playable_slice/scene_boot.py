"""scene_boot.py -- THE PLAYABLE SLICE's standing start, from committed bytes.

TWO committed-byte artifacts, both deterministic:

1. THE TICK BODY (the physics actor): the engine's movement law (gravity +
   floor contact, membrane_tick.cpp) runs on a body admitted by the REAL
   aliveness ingestion (/mesh_import). The importer's own engine law refuses
   past 500,000 triangles BY NAME, and the committed preview skeleton measures
   712,522 triangles -- AND 19 of 25 committed previews carry render-grade
   seams (boundary/inconsistent-winding edges) that the closure check refuses.
   BOTH facts were measured this lane (receipt). So the tick body is a STAND-IN
   capsule DERIVED from the committed standing skeleton's own bbox (one rule,
   no free numbers), named MOCK[mock_physics_body] in mock_registry.json.
   Every physics number the slice shows comes from THIS body through the
   engine's REAL tick.

2. THE GHOST (the visual creature): the committed standing skeleton -- the pose
   of record (standing_pose_20260921/pose.json) through the SAME FK the battery
   verified, full committed preview resolution -- served to the page as a
   DECLARED OVERLAY that rides the tick body's real root and the named carry
   mock. The ghost is labeled in the UI; it never animates by itself.

REALITY: import, gravity, contact, the release transient, the root stream.
FANTASY: the carry slide (MOCK[mock_carry], server-side), the stand-in body
(MOCK[mock_physics_body]), the ghost overlay (DECLARED[ghost_standing_pose]).
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
# preview set is 712,522 tris (25 bones x ~30k), and 19/25 previews carry
# render-grade seams the closure check refuses -- both MEASURED this lane
# (receipt). Hence the stand-in tick body; hence the ghost.
IMPORT_TRI_CAP = 500000


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


# ── 1. THE STAND-IN TICK BODY (derived from the committed skeleton bbox) ─────

def build_stand_in_body(segments: int = 24, rings: int = 12) -> tuple[bytes, dict]:
    """A closed capsule sized by ONE rule from the committed standing
    skeleton's bbox: radius = min(bbox_x, bbox_z)/2, height = bbox_y.
    Deterministic; edge-audited under the importer's own rule."""
    ghost_v, ghost_t, _ = build_standing_layer()
    lo, hi = ghost_v.min(axis=0), ghost_v.max(axis=0)
    bbox = (hi - lo)
    radius = float(min(bbox[0], bbox[2]) / 2.0)
    height = float(bbox[1])

    verts: list[list[float]] = []
    half = rings // 2
    # profile: top-hemisphere rings from the equator UP (excluding the pole),
    # the equator appears once; bottom hemisphere mirrors it
    for i in range(half + 1):                  # i=0: equator .. i=half: below top pole
        theta = (math.pi / 2) * i / half
        r = radius * math.cos(theta)
        y = height / 2 + radius * math.sin(theta)
        for j in range(segments):
            phi = 2 * math.pi * j / segments
            verts.append([r * math.sin(phi), y, r * math.cos(phi)])
    for i in range(1, half + 1):               # below the equator, excluding pole
        theta = (math.pi / 2) * i / half
        r = radius * math.cos(theta)
        y = -height / 2 - radius * math.sin(theta)
        for j in range(segments):
            phi = 2 * math.pi * j / segments
            verts.append([r * math.sin(phi), y, r * math.cos(phi)])
    V = np.array(verts, dtype=np.float64)
    bands = len(V) // segments                 # = rings + 1
    tris: list[tuple[int, int, int]] = []
    for band in range(bands - 1):
        for j in range(segments):
            j2 = (j + 1) % segments
            a = band * segments + j
            b = band * segments + j2
            c = (band + 1) * segments + j
            d = (band + 1) * segments + j2
            tris.append((a, b, d))
            tris.append((a, d, c))
    # pole caps: one apex vertex each, fan to the first/last ring
    top = len(V); V = np.vstack([V, [[0.0, height / 2 + radius, 0.0]]])
    bot = len(V); V = np.vstack([V, [[0.0, -height / 2 - radius, 0.0]]])
    last_band = (bands - 1) * segments
    for j in range(segments):
        j2 = (j + 1) % segments
        tris.append((top, j2, j))                          # outward top fan
        tris.append((bot, last_band + j, last_band + j2))  # outward bottom fan
    T = np.array(tris, dtype=np.int64)
    audit = edge_audit(T, len(V))
    if not audit["closed"]:
        raise RuntimeError(f"scene_boot: stand-in body not closed: {audit}")

    out = io.BytesIO()
    out.write(b"# chimera.playable_slice MOCK[mock_physics_body] stand-in tick body\n")
    out.write(b"# derived: radius=min(bbox_x,bbox_z)/2, height=bbox_y of the committed standing skeleton\n")
    for p in V:
        out.write(("v %.6f %.6f %.6f\n" % (p[0], p[1], p[2])).encode("ascii"))
    for t in T:
        out.write(("f %d %d %d\n" % (t[0] + 1, t[1] + 1, t[2] + 1)).encode("ascii"))
    rec = {"schema": "chimera.playable_slice.stand_in_body.v1",
           "mock_id": "mock_physics_body",
           "derived_from": "the committed standing skeleton's bbox",
           "radius_m": radius, "height_m": height,
           "vertices": int(len(V)), "triangles": int(len(T)), **audit}
    return out.getvalue(), rec


# ── 2. THE GHOST: the committed standing skeleton, full preview resolution ──

def build_standing_layer() -> tuple[np.ndarray, np.ndarray, dict]:
    """The pose of record through the verified FK, as ONE merged indexed mesh
    (scene metres, pads' mean plane at y=0) -- the standing lane's own compose,
    byte-deterministic from committed files."""
    pose = json.loads(POSE_JSON.read_text(encoding="utf-8"))
    x_rec = np.array(pose["variables"]["x_R12"], dtype=np.float64)
    dv = StandingDerivation()

    raw = CSL.WALKER_DERIVED_PATH.read_bytes()
    assert CSL._sha256(raw) == CSL.WALKER_DERIVED_SHA256, "walker_derivation_pin_drift"
    hat = float(json.loads(raw)["body_model"]["segments_Table1"]["HAT"]["length_m"])
    composite = CSL.load_obj_vertices(CSL.PREVIEW_DIR / CSL.COMPOSITE_PREVIEW)
    scale, R_reg, t_reg, reg_diag = CSL.ct_registration(composite, hat, SEAT_HEIGHT_M)

    T = dv.fk(x_rec)
    chunks_v, chunks_t = [], []
    off = 0
    man = json.loads((CSL.CT_DIR / "meshes" / "manifest.json").read_text())
    for entry in man["bones"]:
        name = Path(entry["file"]).name
        preview = name.replace(".obj", "_lo.obj")
        verts_mm, tris = CST.load_obj_mesh(CSL.PREVIEW_DIR / preview)
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
           "bones": len(man["bones"]),
           "vertices": int(verts.shape[0]), "triangles": int(tris.shape[0]),
           "declared_id": "ghost_standing_pose",
           "units": "scene metres, +Y up, pads' mean plane at y=0"}
    return verts, tris, rec


def build_ghost_obj() -> tuple[bytes, dict]:
    verts, tris, rec = build_standing_layer()
    out = io.BytesIO()
    out.write(b"# chimera.playable_slice DECLARED[ghost_standing_pose] visual overlay\n")
    out.write(b"# the committed standing skeleton (pose of record); rides the tick body's real root\n")
    for p in verts:
        out.write(("v %.6f %.6f %.6f\n" % (p[0], p[1], p[2])).encode("ascii"))
    for t in tris:
        out.write(("f %d %d %d\n" % (t[0] + 1, t[1] + 1, t[2] + 1)).encode("ascii"))
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
    """Import the stand-in tick body and arm the movement law. DETERMINISTIC:
    same import bytes every call (the basis of F-SLICE-RESTART)."""
    obj, rec = build_stand_in_body()
    res = http_post(engine_url, "/mesh_import", b"O" + obj)
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
