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

# THE BOOT CACHE (lane mesh-parse-20260920): admission-time preprocessing.
# The engine's import contract owns TWO front doors (importer.hpp): kind 'O'
# (OBJ text) and kind 'G' (glTF 2.0 / GLB binary). The text->raw conversion
# is what costs the minutes at cap scale -- measured (that lane's instrument,
# idle machine): parse_obj 59.2-66.8 s of a 59.3-67.0 s import (99.8%),
# finish() 0.12-0.14 s. So the conversion is done ONCE, offline, from the
# pinned payload, and the boot posts the derived GLB through the SAME
# finish(): the closure law, the cap, and the by-name refusals run on every
# import exactly as before -- the cache removes no check. The ghost's text
# build (the boot's second term, 7.92 s measured by slice_real_body_20260920)
# gets the same treatment: the exact derived bytes, pinned. Refusals: a cache
# file whose sha drifts from its pin, or a cache whose derivation inputs no
# longer hash to the recorded digest, is refused BY NAME -- never a stale
# boot. A MISSING cache falls back to an in-process fresh derivation
# (deterministic, byte-identical -- measured x3 -- and visibly recorded as
# the route in the boot record).
BODY_GLB = HERE / "standing_body.glb"
GHOST_CACHE = HERE / "ghost_standing.obj"
BOOT_CACHE_MANIFEST = HERE / "boot_cache_manifest.json"


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


# ── 1b. THE IMPORT CACHE: the payload's text->raw conversion, done once ──────

def derive_import_glb(obj: bytes) -> bytes:
    """The pinned payload's OBJ subset -> glTF 2.0 GLB container (the engine's
    own kind-'G' front door): f32 VEC3 POSITIONs + u32 indices, same order,
    same values -- decimal -> double -> float32 round-to-nearest on BOTH
    routes (parse_obj's sscanf and this conversion), so parse_gltf hands
    finish() the identical RawMesh parse_obj would. Deterministic; measured
    byte-identical output x3 (lane mesh-parse_20260920). Refuses BY NAME on
    the one structural trap: a negative-zero coordinate on an axis whose
    bbox center is exactly zero -- parse_gltf's identity node transform folds
    -0.0 to +0.0 before finish()'s centering, and a zero center would let
    that sign bit survive into the resident mesh (measured on the pinned
    payload: one negative zero, on z, whose center is 0.14919201 -- no bit
    changes; the parity fence proves it on the whole body anyway)."""
    import array as _array
    import struct as _struct
    pos = _array.array("f")
    idx = _array.array("I")
    if pos.itemsize != 4 or idx.itemsize != 4:
        raise RuntimeError("derive_import_glb: array itemsize is not 4")
    nverts = 0
    neg_zeros = []                       # (axis, vertex index)
    for line in obj.decode("ascii").split("\n"):
        parts = line.split()
        if not parts or parts[0] == "#":
            continue
        if parts[0] == "v" and len(parts) >= 4:
            for axis in (0, 1, 2):
                v = float(parts[1 + axis])
                if v == 0.0 and math.copysign(1.0, v) < 0.0:
                    neg_zeros.append((axis, nverts))
                pos.append(v)
            nverts += 1
        elif parts[0] == "f":
            corners = []
            for tok in parts[1:]:
                vi = int(tok.split("/")[0])
                corners.append(vi - 1 if vi > 0 else nverts + vi)
            for k in range(1, len(corners) - 1):
                idx.append(corners[0])
                idx.append(corners[k])
                idx.append(corners[k + 1])
    if nverts == 0 or len(idx) < 3 or len(idx) % 3 != 0:
        raise ValueError("derive_import_glb: payload has no triangles")
    if max(idx) >= nverts:
        raise ValueError("derive_import_glb: index out of vertex range")
    # finish()'s per-axis center is 0.5*(lo+hi) in f32; recompute it here and
    # refuse the negative-zero/zero-center combination before it can bite
    lo = np.array([min(pos[0::3]), min(pos[1::3]), min(pos[2::3])],
                  dtype=np.float32)
    hi = np.array([max(pos[0::3]), max(pos[1::3]), max(pos[2::3])],
                  dtype=np.float32)
    ctr = (0.5 * (lo + hi)).astype(np.float32)
    for axis, _vi in neg_zeros:
        if ctr[axis] == 0.0:
            raise ValueError(
                "derive_import_glb: negative-zero coordinate on axis %d whose "
                "center is exactly zero -- the 'G' identity transform would "
                "break byte parity; record the gap, do not cache" % axis)
    pos_blob = pos.tobytes()
    idx_blob = idx.tobytes()
    bin_len = len(pos_blob) + len(idx_blob)
    bin_pad = b"\x00" * ((-bin_len) % 4)
    gltf = {
        "asset": {"version": "2.0",
                  "generator": "chimera.mesh_parse_20260920 admission cache"},
        "scene": 0, "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0},
                                    "indices": 1}]}],
        "buffers": [{"byteLength": bin_len + len(bin_pad)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(pos_blob)},
            {"buffer": 0, "byteOffset": len(pos_blob),
             "byteLength": len(idx_blob)}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": nverts,
             "type": "VEC3",
             "min": [float(lo[0]), float(lo[1]), float(lo[2])],
             "max": [float(hi[0]), float(hi[1]), float(hi[2])]},
            {"bufferView": 1, "componentType": 5125, "count": len(idx),
             "type": "SCALAR"}],
    }
    js = json.dumps(gltf, separators=(",", ":")).encode("ascii")
    js_pad = b" " * ((-len(js)) % 4)
    total = 12 + 8 + len(js) + len(js_pad) + 8 + bin_len + len(bin_pad)
    out = _struct.pack("<4sII", b"glTF", 2, total)
    out += _struct.pack("<I4s", len(js) + len(js_pad), b"JSON") + js + js_pad
    out += (_struct.pack("<I4s", bin_len + len(bin_pad), b"BIN\x00")
            + pos_blob + idx_blob + bin_pad)
    return out


def _load_body_import(obj: bytes, rec: dict) -> tuple[str, bytes]:
    """The import payload the boot posts: the pinned derived GLB ('cache'),
    or the same bytes derived in-process ('fresh' -- a missing cache pays the
    conversion once, ~seconds, and says so). A cache that EXISTS but lies --
    file bytes off its pin, or derived_from a different payload -- is
    refused by name, exactly like payload-pin drift. The scene sha stays the
    OBJ payload's sha either way: the pin is about which body, not which
    encoding of it."""
    if not BOOT_CACHE_MANIFEST.is_file():
        return "fresh", derive_import_glb(obj)
    man = json.loads(BOOT_CACHE_MANIFEST.read_text(encoding="utf-8"))
    entry = man.get("import_glb")
    if entry is None:
        return "fresh", derive_import_glb(obj)
    if entry["derived_from"]["payload_sha256"] != rec["sha256"]:
        raise RuntimeError("scene_boot: boot cache derived_from a different "
                           "payload than the pinned one -- refusing by name")
    if BODY_GLB.is_file():
        raw = BODY_GLB.read_bytes()
        if sha256(raw) != entry["sha256"]:
            raise RuntimeError("scene_boot: standing_body.glb drift vs "
                               "boot_cache_manifest.json pin")
        return "cache", raw
    return "fresh", derive_import_glb(obj)


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


def _build_ghost_obj_fresh():
    """The ghost bytes through the unchanged compose (the ONLY source of
    truth; the cache below is a pinned copy of this output)."""
    verts, tris, rec = build_standing_layer_cached()
    out = io.BytesIO()
    out.write(b"# chimera.playable_slice DECLARED[ghost_standing_pose] visual overlay\n")
    out.write(b"# the committed standing skeleton (pose of record); rides the tick body's real root\n")
    # vectorized writers: 355k verts + 712k tris must build in ~1 s or the
    # clean-machine launch bar (10 s) pays for string formatting
    np.savetxt(out, verts, fmt="v %.6f %.6f %.6f")
    np.savetxt(out, tris + 1, fmt="f %d %d %d")
    return out.getvalue(), rec


def _ghost_cache_drift(entry: dict) -> str | None:
    """Why the ghost cache may not be served, or None. Two pins: the
    composition's cheap named inputs (pose of record + the exact file set the
    compose opened at derivation time -- a changed input means a STALE cache,
    which is a refusal, never a serve) and, in the caller, the output bytes
    sha (a corrupted cache file)."""
    pose_sha = sha256(POSE_JSON.read_bytes())
    if pose_sha != entry["compose_record"]["pose_json_sha256"]:
        return "pose of record changed since the cache was derived"
    for rel in entry.get("compose_inputs", []):
        p = ROOT / rel["path"]
        if not p.is_file():
            return "compose input missing: " + rel["path"]
        if sha256(p.read_bytes()) != rel["sha256"]:
            return "compose input changed: " + rel["path"]
    return None


def build_ghost_obj():
    """The ghost bytes: the committed cache (pinned, compose-input-audited)
    loads in milliseconds; a MISSING cache or manifest derives fresh through
    the unchanged compose; a cache whose output pin or input digest drifts is
    REFUSED BY NAME (stale bytes are a lie about the body, not a slow boot).
    Byte-identical either way -- measured x3 (lane mesh-parse-20260920)."""
    entry = None
    if BOOT_CACHE_MANIFEST.is_file():
        man = json.loads(BOOT_CACHE_MANIFEST.read_text(encoding="utf-8"))
        entry = man.get("ghost_obj")
    if entry is not None and GHOST_CACHE.is_file():
        why = _ghost_cache_drift(entry)
        if why:
            raise RuntimeError("scene_boot: ghost cache refused: " + why)
        raw = GHOST_CACHE.read_bytes()
        if sha256(raw) != entry["sha256"]:
            raise RuntimeError("scene_boot: ghost_standing.obj drift vs "
                               "boot_cache_manifest.json pin")
        rec = dict(entry["compose_record"])
        rec["ghost_source"] = "cache"
        return raw, rec
    out, rec = _build_ghost_obj_fresh()
    rec["ghost_source"] = "fresh_compose"
    return out, rec


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
    every call (the basis of F-SLICE-RESTART). The import rides the boot
    cache: the derived GLB through the engine's kind-'G' door (same finish(),
    same closure law); rec["import_route"] names cache vs fresh, and
    rec["scene_sha256"] STAYS the pinned OBJ's sha -- the pin says which body,
    not which encoding of it."""
    obj, rec = build_real_body()
    route, payload = _load_body_import(obj, rec)
    # timeout 900 stays the boot's own safety net: the cached import measures
    # in seconds (lane mesh-parse-20260920), the fresh fallback pays only the
    # in-process conversion, and a refused import must never be a timeout
    res = http_post(engine_url, "/mesh_import", b"G" + payload, timeout=900)
    if not res.get("ok"):
        raise RuntimeError("scene_boot: import refused: " + str(res.get("error")))
    # THE MOVEMENT LAW, armed: gravity + ground contact on the root
    # ("a creature that cannot FALL cannot WALK")
    g = http_post(engine_url, "/tick_gravity", b'{"on":true}',
                  ctype="application/json")
    if not g.get("ok"):
        raise RuntimeError("scene_boot: gravity refused: " + str(g.get("error")))
    rec["scene_sha256"] = sha256(obj)
    rec["import_route"] = route
    rec["import_bytes"] = len(payload)
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
