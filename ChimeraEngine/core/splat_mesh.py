"""splat_mesh.py -- ENGINE-AGNOSTIC splat -> quad-mesh -> GLB geometry.

One oriented, double-sided, vertex-colored quad per splat (anisotropic when the
data carries per-splat axes), exported as a self-describing GLB (PBR material
declared so COLOR_0 multiplies; optional embedded radial-falloff texture).

Extracted 2026-08-25 from core.splat_to_ue5 (whose UE-export half died with the
retired pipeline); the measurement history in these docstrings (the 100x plate
bug, tb-0183 anisotropy, the COLOR_0-vs-texture wall) is falsifier record and
travels with the code. Full retired context: git history of core/splat_to_ue5.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

# physical target size (cm) -- pairs with quad_cloud's cm->meters export contract
TARGET_CM = 170.0

def quad_cloud(splats: dict, scale: float, tangent_scale: float = 1.15,
              overlap: float = 1.35) -> "object":
    """One small double-sided quad per splat, oriented by its normal, colored by ITS
    OWN albedo (COLOR_0). Quad half-size = tangent_scale (the SAME voxel-space footprint
    passed to emit_limb — the emission's own disk radius, not a re-guessed number) x
    scale (cm/voxel) x overlap (closes seams between neighbouring quads; tb-0179: shrink
    this ALONGSIDE tangent_scale, not instead of finer voxel pitch, when pushing density
    up — the recipe's lever (2), independent of lever (1)).

    tb-0183 ("not just squares"): the quad's two half-widths now come from the splat's
    OWN per-splat axes/radii (`t1`/`t2`/`r1`/`r2` — emit_splats' real, data-derived
    anisotropic footprint: neighbour-surface-PCA shape, muscle fiber-aligned) instead of
    re-deriving a FRESH, unrelated tangent frame from the normal and tiling one scalar
    onto it. THIS WAS THE ACTUAL GAP (the operator's own framing): the CPU/GPU
    rasterizers already composite a true anisotropic ellipse from any general `cov` —
    only this engine-side quad mesh was throwing that shape away and rebuilding an
    isotropic square from scratch. `tangent_scale`/`overlap` remain the fallback for any
    caller passing splats without per-splat axes (none do today; kept for robustness)
    and as the SCALE multiplier applied on top of the per-splat radii either way.

    UNITS (the 100x plate bug, found by engine bounds read-back, tl224 2026-07-18):
    glTF's spec unit is METERS; UE's importer multiplies by 100 on the m->cm convert.
    This function's math is in CENTIMETERS (scale = cm/voxel), so the export step below
    divides by 100 — the GLB carries meters, the importer's x100 restores true size.
    Before this fix every splat GLB spawned 100x oversized: the first 22.6k cloud's
    bounds measured 87 METERS ([3234, 8690, 3799] cm extent for an 87.7cm-radius GLB),
    which is the mechanism behind the human's original 'giant plates' — 2.7cm quads
    rendered as 2.7 METER slabs. The prediction-vs-pixels loop plus one
    get_actor_bounds call caught what three sessions of eyeballing had not measured."""
    import trimesh

    pos = splats["pos"] * scale
    n = splats["normal"]
    if "t1" in splats and "r1" in splats:
        # the REAL per-splat anisotropic axes (tb-0183) — r1/r2 are already in VOXEL
        # units exactly like the old scalar tangent_scale was, so the same scale*overlap
        # conversion to centimeters applies unchanged.
        t1, t2 = splats["t1"], splats["t2"]
        h1 = splats["r1"][:, None] * scale * overlap
        h2 = splats["r2"][:, None] * scale * overlap
    else:
        # legacy fallback: an isotropic disk, byte-identical to the pre-tb-0183 shape
        up = np.where(np.abs(n[:, 2:3]) < 0.9, np.array([0., 0., 1.]), np.array([1., 0., 0.]))
        t1 = np.cross(up, n)
        t1 /= np.clip(np.linalg.norm(t1, axis=1, keepdims=True), 1e-9, None)
        t2 = np.cross(n, t1)
        h1 = h2 = tangent_scale * scale * overlap     # tangent_scale voxels -> cm, +overlap

    corners = []
    for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        corners.append(pos + a * h1 * t1 + b * h2 * t2)
    verts = np.stack(corners, axis=1).reshape(-1, 3)            # (N*4, 3)
    verts = verts - verts.mean(axis=0)                          # CENTER the pivot —
    # uncentered verts (0..340cm from origin) made the spawned actor's geometry hang
    # far from its pivot: it hovered in the sky while its transform read (x,y,100)
    # (seen live 2026-07-18; the bake path recentres per-tissue for the same reason)
    verts = verts * 0.01                                        # cm -> glTF METERS (see docstring)
    base = np.arange(len(pos)) * 4
    f1 = np.stack([base, base + 1, base + 2], axis=1)
    f2 = np.stack([base, base + 2, base + 3], axis=1)
    # DOUBLE-SIDED VIA DUPLICATED REVERSED-WINDING FACES (tb-0183, re-measured
    # 2026-07-18): a comment here used to claim the glTF `doubleSided` material flag
    # (injected by write_splat_glb/_inject_material) "replaces the old duplicated-
    # reversed-faces hack — half the triangles, same coverage" — that claim was NEVER
    # exercised in-engine (write_splat_glb had no caller anywhere in the codebase before
    # this task wired it into main()'s default export path) and is FALSE at this
    # density: single-sided quads backface-cull per splat, and a splat CLOUD is not a
    # watertight shell (unlike a normal mesh, where backfaces are occluded by the
    # front anyway) — through the gaps between non-overlapping quads, a camera ray can
    # hit a quad from its culled (away-facing) side with nothing else behind it, so the
    # ray shows background instead. Proven side-by-side (2026-07-18, in-engine): the
    # ORIGINAL tb-0179 splatlimb_tl224.glb (4 tris/quad, both windings, no material —
    # predates write_splat_glb entirely) renders as a DENSE, CONTINUOUS blob; a
    # byte-identical-geometry re-export through single-sided+doubleSided-flag renders
    # as SPARSE, ISOLATED specks — same positions, same colors, same material JSON,
    # confirmed by direct accessor comparison. The one measured difference was exactly
    # this face count (4,479,276 vs 2,239,638 indices — precisely 2x). Restoring the
    # duplicate reversed-winding triangles costs indices (cheap; Nanite virtualizes
    # triangle count) in exchange for CORRECTNESS that does not depend on every
    # importer/material-graph path honouring a doubleSided flag identically.
    f3 = np.stack([base, base + 2, base + 1], axis=1)      # reversed winding
    f4 = np.stack([base, base + 3, base + 2], axis=1)
    faces = np.concatenate([f1, f2, f3, f4])
    rgba = np.concatenate([np.clip(splats["albedo"], 0, 1),
                           np.clip(splats["alpha"], 0, 1)[:, None]], axis=1)
    vcol = (np.repeat(rgba, 4, axis=0) * 255).astype(np.uint8)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_colors=vcol, process=False)
    scene = trimesh.Scene()
    scene.add_geometry(mesh, node_name="cloud", geom_name="cloud")
    return scene


def _inject_material(glb_path: Path) -> None:
    """Make the GLB SELF-DESCRIBING: declare a PBR material on the primitive.

    ROOT CAUSE (found by pixel-forensics, 2026-07-18): trimesh's ColorVisuals
    path exports COLOR_0 but NO material; UE's glTF importer then assigns a dead
    default that ignores vertex color, so every splat imported WHITE (verified:
    blob mean RGB 224.7/223.3/221.5 — neutral — where skin tint demands R>G>B by
    ~46 8-bit steps; the debug-material override showed white = missing attr).
    Per the glTF spec a declared material MUST be multiplied by COLOR_0, and
    UE's importer builds that graph when — and only when — a material exists in
    the file. doubleSided=true here replaces geometric double-siding."""
    import struct

    with open(glb_path, "rb") as f:
        magic, ver, _total = struct.unpack("<III", f.read(12))
        clen, ctype = struct.unpack("<II", f.read(8))
        doc = json.loads(f.read(clen))
        rest = f.read()                                    # BIN chunk(s), untouched
    doc["materials"] = [{
        "name": "M_SplatVC",
        "pbrMetallicRoughness": {"baseColorFactor": [1.0, 1.0, 1.0, 1.0],
                                  "metallicFactor": 0.0, "roughnessFactor": 0.85},
        "doubleSided": True,
    }]
    for mesh in doc.get("meshes", []):
        for prim in mesh.get("primitives", []):
            prim["material"] = 0
    payload = json.dumps(doc, separators=(",", ":")).encode()
    payload += b" " * (-len(payload) % 4)                  # 4-byte alignment (spec)
    with open(glb_path, "wb") as f:
        f.write(struct.pack("<III", magic, ver, 12 + 8 + len(payload) + len(rest)))
        f.write(struct.pack("<II", len(payload), ctype))
        f.write(payload)
        f.write(rest)


def _falloff_png_bytes(size: int = 64, sigma: float = 0.55) -> bytes:
    """A small, centred radial-Gaussian alpha texture: white RGB (so it never tints —
    COLOR_0 already carries the per-splat tissue albedo), alpha carries the falloff.
    Same Gaussian family as the Warp/CPU rasterizers' own per-splat compositing term
    `alpha * exp(-0.5*m)` (core.splat_gpu / splat_emit.rasterize_splats) — the recipe's
    'the Warp rasterizer is the ground-truth look' made into an engine-side texture
    instead of a per-pixel computation, so a MASKed quad reads as the same soft
    footprint the rasterizers already treat as reference.

    sigma=0.55 (paired with alpha_cutoff=0.15 below) is TUNED, not guessed: caught live
    in-engine (2026-07-18) — the first attempt (sigma=0.35, cutoff=0.5) passed the mask
    test on only ~13% of each quad's own area (r_cut = sigma*sqrt(-2*ln(cutoff)) = 0.41
    of the quad's half-width), so the 373k cloud rendered as sparse, isolated specks
    even at point-blank camera range — NOT a camera/framing bug (verified: moving the
    camera changed the frame completely; the object itself was the sparse thing).
    sigma=0.55/cutoff=0.15 gives r_cut ~1.07 — just PAST the quad's own flat edge — so
    almost the whole quad passes and only the outer corners taper, softening the shape
    without hollowing it out."""
    import io
    from PIL import Image

    ys, xs = np.mgrid[0:size, 0:size].astype(np.float64)
    c = (size - 1) / 2.0
    r2 = ((xs - c) ** 2 + (ys - c) ** 2) / (c ** 2)      # 0 at centre, 1 at a side's midpoint
    alpha = np.clip(np.exp(-r2 / (2.0 * sigma ** 2)), 0.0, 1.0)
    rgba = np.zeros((size, size, 4), dtype=np.uint8)
    rgba[..., :3] = 255                                   # white -- never tints COLOR_0
    rgba[..., 3] = (alpha * 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(rgba, mode="RGBA").save(buf, format="PNG")
    return buf.getvalue()


def _inject_falloff_material(glb_path: Path, alpha_mode: str = "MASK",
                             alpha_cutoff: float = 0.15, tex_size: int = 64) -> None:
    """Make the GLB SELF-DESCRIBING with a SOFT EDGE (tb-0183): extends
    _inject_material's proven chunk-surgery pattern (declare a real PBR material so
    UE's importer multiplies it by COLOR_0 — see that function's docstring) with an
    embedded radial-falloff texture + per-vertex UVs, so a quad — still geometrically a
    rectangle, now sized from the splat's own anisotropic axes by quad_cloud — RENDERS
    as a soft ellipse instead of a hard-edged shape. Same reasoning as _inject_material
    for doing this as raw GLB bytes rather than via trimesh's high-level export:
    trimesh's vertex-color path does not reliably co-export a second (UV+texture)
    attribute set on the same primitive; proven the hard way for materials already, so
    UVs get the identical treatment — computed here, appended to the SAME buffer.

    alphaMode MASK (default; the recipe's 'preferred') alpha-tests each pixel against
    `alpha_cutoff` and is Nanite-compatible; BLEND is offered for the recipe's explicit
    fallback ('only if sorting holds') — Nanite does not support translucent materials
    in general, which is the concrete mechanism the KILL check
    (drive_shape_study) is testing, not an aesthetic preference. Nothing in this
    function decides which mode wins."""
    import struct

    with open(glb_path, "rb") as f:
        magic, ver, _total = struct.unpack("<III", f.read(12))
        clen, ctype = struct.unpack("<II", f.read(8))
        doc = json.loads(f.read(clen))
        rest = f.read()
    bin_len, bin_type = struct.unpack("<II", rest[:8])
    bin_data = bytearray(rest[8:8 + bin_len])              # the buffer's true bytes only —
                                                            # anything past bin_len is outside
                                                            # the chunk's declared length (spec)

    mesh = doc["meshes"][0]
    prim = mesh["primitives"][0]
    pos_accessor = doc["accessors"][prim["attributes"]["POSITION"]]
    n_verts = int(pos_accessor["count"])
    n_quads = n_verts // 4

    # --- UVs: one unit square per quad, corner order matching quad_cloud's own
    # ((-1,-1),(1,-1),(1,1),(-1,1)) -> (0,0),(1,0),(1,1),(0,1) ------------------------
    uv_corner = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]], dtype="<f4")
    uv_bytes = np.tile(uv_corner, (n_quads, 1)).tobytes()
    assert len(uv_bytes) % 4 == 0
    uv_bv_offset = len(bin_data)
    bin_data += uv_bytes

    # --- the falloff texture, embedded as PNG bytes in the SAME buffer --------------
    png_bytes = _falloff_png_bytes(tex_size)
    img_bv_offset = len(bin_data)
    bin_data += png_bytes
    bin_data += b"\x00" * ((-len(bin_data)) % 4)           # glTF BIN padding byte is 0x00

    uv_bv_idx = len(doc["bufferViews"])
    doc["bufferViews"].append({"buffer": 0, "byteOffset": uv_bv_offset, "byteLength": len(uv_bytes)})
    img_bv_idx = len(doc["bufferViews"])
    doc["bufferViews"].append({"buffer": 0, "byteOffset": img_bv_offset, "byteLength": len(png_bytes)})

    uv_accessor_idx = len(doc["accessors"])
    doc["accessors"].append({"componentType": 5126, "type": "VEC2", "byteOffset": 0,
                             "bufferView": uv_bv_idx, "count": n_verts})
    prim["attributes"]["TEXCOORD_0"] = uv_accessor_idx

    doc["images"] = [{"bufferView": img_bv_idx, "mimeType": "image/png"}]
    doc["samplers"] = [{"magFilter": 9729, "minFilter": 9729,             # LINEAR
                        "wrapS": 33071, "wrapT": 33071}]                  # CLAMP_TO_EDGE
    doc["textures"] = [{"source": 0, "sampler": 0}]

    mat = {
        "name": "M_SplatVC_Soft",
        "pbrMetallicRoughness": {
            "baseColorFactor": [1.0, 1.0, 1.0, 1.0],
            "baseColorTexture": {"index": 0, "texCoord": 0},
            "metallicFactor": 0.0, "roughnessFactor": 0.85,
        },
        "doubleSided": True,
    }
    if alpha_mode == "MASK":
        mat["alphaMode"] = "MASK"
        mat["alphaCutoff"] = float(alpha_cutoff)
    elif alpha_mode == "BLEND":
        mat["alphaMode"] = "BLEND"
    doc["materials"] = [mat]
    for m in doc.get("meshes", []):
        for p in m.get("primitives", []):
            p["material"] = 0
    doc["buffers"][0]["byteLength"] = len(bin_data)

    payload = json.dumps(doc, separators=(",", ":")).encode()
    payload += b" " * (-len(payload) % 4)                  # 4-byte alignment (spec)
    with open(glb_path, "wb") as f:
        f.write(struct.pack("<III", magic, ver, 12 + 8 + len(payload) + 8 + len(bin_data)))
        f.write(struct.pack("<II", len(payload), ctype))
        f.write(payload)
        f.write(struct.pack("<II", len(bin_data), bin_type))
        f.write(bytes(bin_data))


def write_splat_glb(splats: dict, scale: float, path: Path, soft_edge: bool = False,
                    alpha_mode: str = "MASK", alpha_cutoff: float = 0.15,
                    tex_size: int = 64, **kw) -> Path:
    """Export + material injection in one step — the only correct way to write
    a splat GLB for engine import (a bare quad_cloud().export() produces the
    dead-default-material import; see _inject_material).

    tb-0183: soft_edge=True additionally embeds a radial-falloff texture + UVs
    (_inject_falloff_material) so the anisotropic quads quad_cloud now builds render
    as soft ellipses, not hard-edged rectangles.

    SOFT EDGES ARE OPT-IN, NOT THE DEFAULT — KILLED AT THE MATERIAL LAYER (tb-0183,
    measured in-engine 2026-07-18): the recipe's two named kill walls both HELD
    (373k-tier, BOTH clouds staged at once: fps 120-cap / 8.33ms vs Malcolm's 16.6ms
    wall; Nanite built on both; Substrate lighting shades the masked cloud fine), but a
    third wall fired: **UE's glTF importer drops the COLOR_0 multiply from its
    auto-generated material when baseColorTexture is present**, so every splat renders
    WHITE — measured on the side-by-side (pink-tissue pixel fraction: squares/textureless
    0.4394, soft-MASK 0.0000; same COLOR_0 bytes in both files, verified by accessor
    dump). Per-splat color IS the rung D-prime criterion (the anatomy render), so the
    color-correct path stays default. The falloff machinery is kept whole behind this
    flag because the export side is proven structurally sound (imports, Nanite-compatible,
    fps holds); what's missing is engine-side — a bridge-authored MASKED
    VertexColor-times-RadialGradient material to apply post-import, which is
    material-authoring work in ensure_splat_material's family, not an exporter change."""
    quad_cloud(splats, scale, **kw).export(str(path))
    if soft_edge:
        _inject_falloff_material(path, alpha_mode=alpha_mode, alpha_cutoff=alpha_cutoff,
                                 tex_size=tex_size)
    else:
        _inject_material(path)
    return path


