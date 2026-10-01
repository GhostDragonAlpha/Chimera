"""render_standing.py -- THE BEFORE/AFTER STILLS through the proven triangle path
(preregistration 63e9def4... section 7, predictions P-R1..P-R4 banked before any capture).

CORPSE still: theta = 0 (the committed bytes) through the ONE committed registration
  (ct_skeleton_layer.ct_registration: trunk PCA -> scene up, dorsal -> scene left, scale
  pinned to the walker HAT length; the seat height constant the compose needs is banked in
  the receipt with its source pin -- this lineage's own creature graph lacks the object).
STANDING still: the pose of record (pose.json) through the same FK the battery verified,
  plus THE STANDING PLACEMENT: the rigid scene-frame placement carrying the posed pads'
  plane normal to the scene up and setting the pads' mean plane to y = 0 (zero free numbers).

Both layers are ONE merged indexed triangle mesh posted through the engine's /mesh_bin
(depth-tested, shaded), framed by the proven bbox camera rule, captured with the
settle-capture pattern. Pixel truth + revisit identity measured per still.

The engine binary is the build the walk-movie lane proved on /mesh_bin (sha pinned in the
receipt); it is launched on THIS lane's own bind-tested free port with the port argument
ONLY (the measured argc trap); 8127 and sibling ports are never touched; only this
script's own engine process is ever stopped.

Run:  python -B tools/science_funnel/validation/standing_pose_20260921/render_standing.py
"""

import hashlib
import json
import socket
import struct
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools" / "science_funnel" / "validation" / "hip_pivot_proof_20260921"))

from standing_pose_core import StandingDerivation, PAD_BONES, sanitize, rnd, sha256_file  # noqa: E402
import hip_pivot_proof as hp  # noqa: E402
from tools.science_funnel import ct_skeleton_layer as CSL  # noqa: E402
from tools.science_funnel import ct_skeleton_triangle as CST  # noqa: E402

ENGINE_EXE = Path("E:/ChimeraWork/mcp-agent/.tmp/wfmcp_build/Release/chimera_engine.exe")
ENGINE_EXE_SHA = "16ca3c1854289470ffed05dd4ac3789cf4a0a6163fb69d2e239e4383fc3c34dd"
PORT_BLOCKLIST = {8127, 8096, 8097}
SEAT_HEIGHT_M = -0.08977588222411312  # banked in the receipt with its source pin
OUT = HERE / "renders"
RECORD = HERE / "render_record.json"


def pick_port():
    for port in range(8130, 8200):
        if port in PORT_BLOCKLIST:
            continue
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", port))
            s.close()
            return port
        except OSError:
            continue
    raise SystemExit("no free port found in 8130..8199")


def wait_engine(url, timeout=40.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(url + "/frame", timeout=3) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def set_camera(url, radius, theta, phi, timeout=10.0):
    """The engine's /camera route (MEASURED: the /mesh_bin header camera is
    ignored -- two uploads at different header radii produced byte-identical
    frames -- while /camera is honored and bit-deterministic on return)."""
    payload = json.dumps({"cam_radius": float(radius), "cam_theta": float(theta),
                          "cam_phi": float(phi)}).encode("utf-8")
    req = urllib.request.Request(url + "/camera", data=payload,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status == 200


def post_mesh(url, verts9, tris, radius, theta, phi, timeout=180.0):
    n = int(verts9.shape[0])
    header = struct.pack("<II4f", n, int(tris.size), float(radius), float(theta), float(phi), 0.0)
    payload = (header + np.ascontiguousarray(verts9, dtype=np.float32).tobytes()
               + np.ascontiguousarray(tris, dtype=np.uint32).tobytes())
    req = urllib.request.Request(url + "/mesh_bin", data=payload,
                                 headers={"Content-Type": "application/octet-stream"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status == 200 and b'"ok":true' in r.read()


def fetch_frame(url, timeout=30.0):
    with urllib.request.urlopen(url + "/frame", timeout=timeout) as r:
        return r.read()


def settle_capture(url, timeout=30.0):
    """THREE consecutive fresh captures byte-equal -> a quiesced render
    (amendment 3: the deeper quiesce the first upload measured)."""
    t0 = time.time()
    run = 0
    last = None
    while time.time() - t0 < timeout:
        b = fetch_frame(url)
        run = run + 1 if (last is not None and b == last) else 1
        if run >= 3:
            return b
        last = b
        time.sleep(0.08)
    return last


def pixel_truth(png_bytes, name):
    """Amendment 3 mask: object = (R-B >= 25) AND (R >= 45) -- the compose's own
    bone tint against the measured neutral sky/floor classes."""
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    a = np.asarray(im, dtype=np.int16)
    R, B = a[:, :, 0], a[:, :, 2]
    mask = (R - B >= 25) & (R >= 45)
    count = int(mask.sum())
    total = mask.size
    ys, xs = np.nonzero(mask)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if count else None
    return {"name": name, "width": int(im.size[0]), "height": int(im.size[1]),
            "mask_rule": "object := (R-B >= 25) and (R >= 45) (amendment 3, derived from "
                         "the measured frame classes: sky R-B ~ -1, floor R-B ~ +6, bone R-B >= 25)",
            "object_pixels": count, "frame_pixels": int(total),
            "coverage_fraction": round(count / total, 6),
            "object_bbox_xyxy": bbox}


def coverage_in_class(pt):
    return bool(0.01 <= pt["coverage_fraction"] <= 0.40)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pose = json.loads((HERE / "pose.json").read_text(encoding="utf-8"))
    x_rec = np.array(pose["variables"]["x_R12"], dtype=np.float64)
    dv = StandingDerivation()

    # ---- the ONE committed registration (seat constant banked in the receipt) ----
    raw = CSL.WALKER_DERIVED_PATH.read_bytes()
    CSL._require(CSL._sha256(raw) == CSL.WALKER_DERIVED_SHA256, "walker_derivation_pin_drift")
    hat = float(json.loads(raw)["body_model"]["segments_Table1"]["HAT"]["length_m"])
    composite = CSL.load_obj_vertices(CSL.PREVIEW_DIR / CSL.COMPOSITE_PREVIEW)
    scale, R_reg, t_reg, reg_diag = CSL.ct_registration(composite, hat, SEAT_HEIGHT_M)

    # ---- the pads' plane from the VERIFIED FK (the tris-blob centroids) ----------
    P_ct = dv.pad_centroids(x_rec)
    spread_ct, n_ct = dv._plane_stats(P_ct)
    n_scene0 = R_reg @ n_ct
    up = np.array([0.0, 1.0, 0.0])

    def rot_to_up(v):
        v = v / np.linalg.norm(v)
        c = float(v @ up)
        axis = np.cross(v, up)
        s = float(np.linalg.norm(axis))
        if s < 1e-15:
            return np.eye(3)
        axis = axis / s
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        return np.eye(3) + K * s + K @ K * (1.0 - c)

    R_place = rot_to_up(n_scene0)
    pad_scene = (P_ct @ R_reg.T) * scale / 1000.0 + t_reg
    pad_scene = pad_scene @ R_place.T
    lift = float(pad_scene[:, 1].mean())  # pads' mean plane -> y = 0

    def place(scene_pts):
        return (scene_pts @ R_place.T) - np.array([0.0, lift, 0.0])

    # ---- layer compose (the committed registration, preview geometry) ------------
    def build_layer(x):
        T = dv.fk(x)
        chunks_v, chunks_t, bones = [], [], []
        off = 0
        man = json.loads((CSL.CT_DIR / "meshes" / "manifest.json").read_text())
        for entry in man["bones"]:
            name = Path(entry["file"]).name
            preview = name.replace(".obj", "_lo.obj")
            verts_mm, tris = CST.load_obj_mesh(CSL.PREVIEW_DIR / preview)
            bone = int(name.split("_")[1])
            posed_ct = T[bone].pts(verts_mm)
            scene = CSL.apply_registration(posed_ct, scale, R_reg, t_reg)
            normals = CST.mesh_normals(scene, tris)
            n = scene.shape[0]
            v9 = np.zeros((n, 9), dtype=np.float32)
            v9[:, 0:3] = scene.astype(np.float32)
            v9[:, 3:6] = normals.astype(np.float32)
            v9[:, 6:9] = CSL.CT_BONE_COLOR
            chunks_v.append(v9)
            chunks_t.append((tris + off).astype(np.uint32).ravel())
            bones.append({"preview": preview, "vertices": int(n), "triangles": int(tris.shape[0])})
            off += n
        return {"verts9": np.concatenate(chunks_v, axis=0),
                "tris": np.concatenate(chunks_t, axis=0), "bones": bones,
                "record": {"schema": "chimera.standing_pose_triangle_layer.v1",
                           "lane": "agent/standing-pose-20260921",
                           "bones": len(man["bones"]),
                           "vertices": int(np.concatenate(chunks_v, axis=0).shape[0]),
                           "triangles": int(np.concatenate(chunks_t, axis=0).size // 3),
                           "units": "scene metres (walker/free-root frame: +Y up, "
                                    "+X forward, +Z left)",
                           "endpoint": "/mesh_bin (engine triangle pipeline)",
                           "registration": reg_diag}}

    corpse = build_layer(np.zeros(10))
    standing = build_layer(x_rec)

    # the standing layer gets the placement (the corpse keeps the committed mount)
    for layer in (standing,):
        v = layer["verts9"][:, 0:3].astype(np.float64)
        v = place(v)
        layer["verts9"][:, 0:3] = v.astype(np.float32)

    # P-R4 (amendment 3): the render's scene spread (max-min along the placed
    # plane normal) vs the BATTERY's own verified per-pad signed distances.
    battery = json.loads((HERE / "battery.json").read_text(encoding="utf-8"))
    signed_ct = np.array([battery["pad_plane"]["bone_%02d" % r]["signed_dist_mm"]
                          for r in PAD_BONES], dtype=np.float64)
    spread_ct = float(signed_ct.max() - signed_ct.min())
    pad_scene_check = (P_ct @ R_reg.T) * scale / 1000.0 + t_reg
    signed = (pad_scene_check @ R_place.T)[:, 1] - lift
    spread_scene = float(signed.max() - signed.min())
    pr4_dev_m = abs(spread_scene - spread_ct * scale / 1000.0)

    # ---- engine on this lane's own port --------------------------------------------
    port = pick_port()
    url = "http://127.0.0.1:%d" % port
    proc = None
    engine_sha = hashlib.sha256(ENGINE_EXE.read_bytes()).hexdigest()
    if engine_sha != ENGINE_EXE_SHA:
        raise SystemExit("engine binary sha drift vs pinned provenance")
    try:
        proc = subprocess.Popen([str(ENGINE_EXE), str(port)],
                                cwd=str(ENGINE_EXE.parent),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not wait_engine(url):
            raise SystemExit("engine did not come up on %s" % url)

        stills = {}
        for tag, layer, radius_hint in (("corpse_still", corpse, None), ("standing_still", standing, None)):
            # proven camera rule, amendment-3 fit: margin 1.35 around the LARGER
            # in-plane extent (the standing body is long and low), 45 deg FOV;
            # delivered through /camera (the header camera is measured-ignored)
            cam = CST.derive_camera_from_layer(layer)
            pos = layer["verts9"][:, 0:3].astype(np.float64)
            lo, hi = pos.min(axis=0), pos.max(axis=0)
            spans = [float(hi[1] - lo[1]), float(hi[0] - lo[0]), float(hi[2] - lo[2])]
            half_fov = np.deg2rad(45.0) / 2.0
            cam["in_plane_spans_m"] = [round(v, 6) for v in spans]
            cam["fit_extent_m"] = round(max(spans), 6)
            cam["radius_m"] = round(1.35 * (max(spans) / 2.0) / float(np.tan(half_fov)), 6)
            final = CST.recenter_mesh(layer)
            ok = post_mesh(url, final["verts9"], final["tris"],
                           cam["radius_m"], 0.0, 0.3)
            if not ok:
                raise SystemExit("%s: /mesh_bin refused" % tag)
            if not set_camera(url, cam["radius_m"], 0.0, 0.3):
                raise SystemExit("%s: /camera refused" % tag)
            time.sleep(1.0)  # first-upload warmup (pipeline compile), measured
            b = settle_capture(url)
            revisit = settle_capture(url)
            png = OUT / (tag + ".png")
            png.write_bytes(b)
            pt = pixel_truth(b, tag)
            pt["revisit_byte_identical"] = bool(revisit == b)
            pt["camera"] = cam
            pt["layer"] = {"bones": len(layer["bones"]),
                           "vertices": int(layer["verts9"].shape[0]),
                           "triangles": int(layer["tris"].size // 3)}
            pt["png_sha256"] = hashlib.sha256(b).hexdigest()
            stills[tag] = pt

        diff = None
        a = np.asarray(__import__("PIL.Image", fromlist=["Image"]).open(
            OUT / "corpse_still.png").convert("RGB"), dtype=np.int16)
        b2 = np.asarray(__import__("PIL.Image", fromlist=["Image"]).open(
            OUT / "standing_still.png").convert("RGB"), dtype=np.int16)
        if a.shape == b2.shape:
            diff = int((np.abs(a - b2).max(axis=2) > 8).sum())

        predictions = {
            "P_R1_corpse_coverage_class": coverage_in_class(stills["corpse_still"]),
            "P_R1_standing_coverage_class": coverage_in_class(stills["standing_still"]),
            "P_R2_pixel_diff_count": diff,
            "P_R2_pixel_diff_at_least_1000": bool(diff is not None and diff >= 1000),
            "P_R3_corpse_revisit_identical": stills["corpse_still"]["revisit_byte_identical"],
            "P_R3_standing_revisit_identical": stills["standing_still"]["revisit_byte_identical"],
            "P_R4_scene_spread_m": rnd(spread_scene),
            "P_R4_ct_spread_mm": rnd(spread_ct),
            "P_R4_abs_dev_m": rnd(pr4_dev_m),
            "P_R4_within_1e-6": bool(pr4_dev_m <= 1e-6),
        }
        falsifiers = []
        for k in ("P_R1_corpse_coverage_class", "P_R1_standing_coverage_class",
                  "P_R2_pixel_diff_at_least_1000", "P_R3_corpse_revisit_identical",
                  "P_R3_standing_revisit_identical", "P_R4_within_1e-6"):
            if not predictions[k]:
                falsifiers.append("F10: %s failed" % k)

        record = {
            "schema": "chimera.standing_pose_render.v1",
            "lane": "agent/standing-pose-20260921",
            "base_commit": "52f101c1",
            "preregistration_sha256": sha256_file(HERE / "preregistration.md"),
            "trailer": "Agent: GLM 5.3",
            "render_path": "ct_skeleton_layer + ct_skeleton_triangle (byte-identical copies of "
                           "agent/triangle-monkey-grid-20260920 @ 1b08b29d) -> /mesh_bin "
                           "(depth-tested triangle pipeline); ONE committed registration; "
                           "standing placement = pads' plane normal -> scene up, pads' mean "
                           "plane -> y=0; pixel mask + camera fit + settle per amendment 3 "
                           "(the first capture's record: renders/first_capture/) ",
            "registration_diagnostics": reg_diag,
            "seat_height_m_banked": SEAT_HEIGHT_M,
            "engine": {"exe_sha256": engine_sha, "port": port, "pid": proc.pid,
                       "launch": "port argument ONLY; own bind-tested port; 8127 and sibling "
                                 "ports never touched"},
            "placement": {"R_place": [[rnd(v) for v in row] for row in R_place],
                          "lift_m": rnd(lift)},
            "pose_sha256": sha256_file(HERE / "pose.json"),
            "stills": stills,
            "predictions": predictions,
            "falsifiers_fired": falsifiers,
            "files": [str(OUT / "corpse_still.png"), str(OUT / "standing_still.png")],
        }
        RECORD.write_text(json.dumps(sanitize(record), indent=1, sort_keys=True,
                                     ensure_ascii=True) + "\n", encoding="utf-8")
        print("render record written:", RECORD)
        print(json.dumps(predictions, indent=1))
        return 0 if not falsifiers else 1
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except Exception:
                proc.kill()


if __name__ == "__main__":
    sys.exit(main())
