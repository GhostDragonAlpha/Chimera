"""Labeled skeleton overlays for bone_identification_v4
(agent lane agent/bone-id-v3-companion, base 59098314 = bone-id-v3).

Renders each specimen's final v4 labels as colored overlays on the
existing MIP projections (proj_sagittal*.png / proj_coronal*.png /
proj_axial*.png), regenerating the MIP geometry with the method the
projection history documents (.tmp/decimate_meshes.py):

    bone = binary volume at the manifest threshold (here: the committed
           segmentation meshes rasterized back onto the manifest grid --
           the same binary bone volume the projections were made from)
    mip  = bone.max(axis)  per axis: 0=axial, 1=coronal, 2=sagittal
    img  = (mip*255).T; scale = 900/max(h, w); resize NEAREST

Per-bone masks come from rasterizing the committed preview meshes
(triangle barycentric lattice, then even-odd parity fill along axis 0)
onto the manifest's volume grid -- deterministic, no random seeds.
The per-pixel projected label is the DOMINANT (mode) non-empty label
along the ray, ties to the smaller rank. Alignment of the regenerated
binary MIP against the committed PNG is measured (IoU) and printed.

Colors: per-class palette (legend in-image), unlabeled bones gray,
the axial composite (rank 1) left grayscale, per-bone rank labels at
the projected centroids. 6 PNGs -> overlays/.

Run:  python -B tools/science_funnel/data/morphosource_ct/render_overlays_v4.py
"""
import json
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
V4_JSON = HERE / "bone_identification_v4.json"
OUT_DIR = HERE / "overlays"

SPECS = [
    {"sid": "000875604", "manifest": HERE / "meshes" / "manifest.json",
     "preview_dir": HERE / "meshes_preview",
     "proj": {"sagittal": HERE / "proj_sagittal.png",
              "coronal": HERE / "proj_coronal.png",
              "axial": HERE / "proj_axial.png"}},
    {"sid": "000875599", "manifest": HERE / "meshes_875599" / "manifest.json",
     "preview_dir": HERE / "meshes_preview_875599",
     "proj": {"sagittal": HERE / "proj_sagittal_875599.png",
              "coronal": HERE / "proj_coronal_875599.png",
              "axial": HERE / "proj_axial_875599.png"}},
]

# ---- fixed palette (deterministic constants, no randomness) ----------------
CLASS_COLORS = {
    "femur": (214, 39, 40),
    "tibia": (255, 127, 14),
    "fibula": (250, 218, 50),
    "foot_class": (44, 160, 44),
    "humerus": (31, 119, 180),
    "forearm_class": (23, 190, 207),
    "hand_class": (148, 103, 189),
}
UNLABELED_RGB = (137, 137, 137)
AXIS_VIEWS = [(0, "axial"), (1, "coronal"), (2, "sagittal")]
TARGET_W = 900            # the history's projection width
RASTER_STEP_IDX = 0.30    # barycentric lattice step, voxel-index units (< 1 voxel)
LEGEND_W = 200


def font():
    try:
        return ImageFont.load_default(size=15)
    except TypeError:
        return ImageFont.load_default()


def legend_font():
    try:
        return ImageFont.load_default(size=13)
    except TypeError:
        return ImageFont.load_default()


# ---- mesh -> label volume ---------------------------------------------------
def rasterize_mesh(verts_mm, faces, shape, voxel_mm, step=RASTER_STEP_IDX):
    """Deterministic surface rasterization onto the manifest grid.
    Surface-only is sufficient for BOTH render uses: a binary MIP lights
    any ray with >= 1 mark, and the per-ray dominant label only needs the
    entry/exit wall voxels (bones do not interpenetrate, so every mark on
    a ray carries that bone's label). No parity/fill: the decimated
    preview meshes are not guaranteed watertight (measured: even-odd
    parity leaks on this data)."""
    v = verts_mm / voxel_mm                     # voxel-index coordinates
    tris = v[faces]                             # (F, 3, 3)
    surf_pts = []
    for t in tris:
        e1, e2 = t[1] - t[0], t[2] - t[0]
        n1 = int(np.ceil(np.linalg.norm(e1) / step)) + 1
        n2 = int(np.ceil(np.linalg.norm(e2) / step)) + 1
        u = np.linspace(0.0, 1.0, max(n1, 2))
        w = np.linspace(0.0, 1.0, max(n2, 2))
        uu, ww = np.meshgrid(u, w, indexing="ij")
        keep = (uu + ww) <= 1.0
        pts = t[0] + uu[keep, None] * e1 + ww[keep, None] * e2
        surf_pts.append(pts)
    pts = np.concatenate(surf_pts, axis=0)
    idx = np.clip(np.round(pts).astype(np.int64), 0, np.array(shape) - 1)
    vol = np.zeros(shape, dtype=bool)
    vol[idx[:, 0], idx[:, 1], idx[:, 2]] = True
    return vol, int(vol.sum())


def build_label_volume(spec):
    man = json.loads(spec["manifest"].read_text(encoding="utf-8"))
    shape = tuple(man["segmentation_params"]["volume_shape"])
    voxel = man["segmentation_params"]["voxel_size_mm"]
    vol = np.zeros(shape, dtype=np.uint8)
    counts = {}
    for b in man["bones"]:
        rank = b["rank"]
        f = sorted(spec["preview_dir"].glob(f"bone_{rank:02d}_*.obj"))[0]
        m = trimesh.load(f, process=False)
        mask, n_surf = rasterize_mesh(np.asarray(m.vertices, dtype=float),
                                      np.asarray(m.faces), shape, voxel)
        vol[mask] = rank
        counts[rank] = {"manifest_voxels": b["volume_voxels"],
                        "surface_marked_voxels": n_surf}
        assert n_surf >= 500, (rank, n_surf)
    return vol, man, counts


def dominant_label_projection(vol, axis):
    """Per-pixel mode of the non-empty labels along `axis` (ties -> smaller rank)."""
    order = [d for d in range(3) if d != axis] + [axis]
    mv = np.transpose(vol, order)                # (P1, P2, D)
    p1, p2, dep = mv.shape
    flat = mv.reshape(p1 * p2, dep)
    counts = np.zeros((p1 * p2, 26), dtype=np.uint16)
    for lab in range(1, 26):
        counts[:, lab] = (flat == lab).sum(axis=1)
    dom = counts.argmax(axis=1).astype(np.uint8) + 0  # argmax ties -> smallest label
    dom[(counts[:, 1:] == 0).all(axis=1)] = 0
    return dom.reshape(p1, p2)


def scale_like_history(img2d):
    """The documented resize: scale = 900/max(h, w), NEAREST."""
    h, w = img2d.shape
    scale = TARGET_W / max(h, w)
    out = (int(w * scale), int(h * scale))
    return out, scale, Image.fromarray(img2d).resize(out, Image.Resampling.NEAREST)


def compose(spec_row, view, base_png, vol, v4, out_path):
    axis = {"axial": 0, "coronal": 1, "sagittal": 2}[view]
    # regenerated binary MIP (documented method) + alignment IoU vs committed PNG
    mip = (vol > 0).max(axis=axis)
    shape_out, scale, mip_img = scale_like_history((mip * 255).astype(np.uint8).T)
    ref = Image.open(base_png).convert("L")
    assert ref.size == mip_img.size, (ref.size, mip_img.size, view)
    a = np.asarray(ref) > 0
    b = np.asarray(mip_img) > 0
    iou = float((a & b).sum()) / float((a | b).sum())

    # dominant-label projection, resized with the same transform
    dom = dominant_label_projection(vol, axis)
    _, _, dom_img = scale_like_history(dom.T)

    # compose RGB: committed PNG grayscale underlay + class colors on top
    rgb = np.stack([np.asarray(ref)] * 3, axis=-1).astype(np.uint8)
    dom_np = np.asarray(dom_img)
    color = np.zeros(dom_np.shape + (3,), dtype=np.uint8)
    rows = v4["specimens"][spec_row]["bones"]
    rank_to_rgb = {}
    for r in rows:
        rank = r["rank"]
        if rank == 1:
            continue
        cls = r["segment_label"]
        rank_to_rgb[rank] = CLASS_COLORS.get(cls, UNLABELED_RGB) if cls else UNLABELED_RGB
    for rank, rgb3 in rank_to_rgb.items():
        m = dom_np == rank
        color[m] = rgb3
    colored = color.any(axis=-1)
    rgb[colored] = color[colored]
    im = Image.fromarray(rgb).convert("RGB")

    # per-bone rank labels at projected centroids (voxel index -> pixels)
    draw = ImageDraw.Draw(im)
    fnt = font()
    h_in, w_in = dom.T.shape
    w_out, h_out = im.size
    sx, sy = w_out / w_in, h_out / h_in
    for r in rows:
        rank = r["rank"]
        if rank == 1:
            continue
        c = np.array(r["centroid_mm"]) / 0.16     # voxel index (mm / voxel)
        ci = {"axial": [2, 1], "coronal": [2, 0], "sagittal": [1, 0]}[view]
        row_f, col_f = float(c[ci[0]]), float(c[ci[1]])
        x = int(min(max(col_f * sx, 1), w_out - 20))
        y = int(min(max(row_f * sy, 1), h_out - 18))
        draw.text((x, y), str(rank), fill=(255, 255, 255), font=fnt,
                  stroke_width=2, stroke_fill=(0, 0, 0))

    # legend panel
    panel = Image.new("RGB", (LEGEND_W, im.size[1]), (255, 255, 255))
    d2 = ImageDraw.Draw(panel)
    lf = legend_font()
    y = 8
    d2.text((8, y), f"{spec_row} {view}", fill=(0, 0, 0), font=lf); y += 20
    d2.text((8, y), f"MIP + v4 labels", fill=(90, 90, 90), font=lf); y += 22
    for cls, rgb3 in CLASS_COLORS.items():
        d2.rectangle([8, y, 24, y + 13], fill=rgb3, outline=(0, 0, 0))
        d2.text((30, y + 1), cls, fill=(0, 0, 0), font=lf)
        y += 19
    d2.rectangle([8, y, 24, y + 13], fill=UNLABELED_RGB, outline=(0, 0, 0))
    d2.text((30, y + 1), "unlabeled bone", fill=(0, 0, 0), font=lf); y += 19
    d2.rectangle([8, y, 24, y + 13], fill=(210, 210, 210), outline=(0, 0, 0))
    d2.text((30, y + 1), "axial composite (r1)", fill=(0, 0, 0), font=lf); y += 24
    n_conf = v4["prediction_outcome"][spec_row]["confident_total"]
    d2.text((8, y), f"confident {n_conf}/24", fill=(0, 0, 0), font=lf); y += 19
    d2.text((8, y), "numbers = bone ranks", fill=(120, 120, 120), font=lf)
    combined = Image.new("RGB", (im.size[0] + LEGEND_W, im.size[1]), (255, 255, 255))
    combined.paste(im, (0, 0))
    combined.paste(panel, (im.size[0], 0))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.save(out_path)
    return iou


def main():
    v4 = json.loads(V4_JSON.read_text(encoding="utf-8"))
    assert v4["schema"] == "chimera.ct_bone_identification.v4"
    report = {}
    for spec in SPECS:
        sid = spec["sid"]
        print(f"[{sid}] rasterizing meshes -> label volume ...")
        vol, man, counts = build_label_volume(spec)
        print(f"  {len(counts)} bones rasterized (surface marks; "
              f"min {min(c['surface_marked_voxels'] for c in counts.values())} voxels)")
        report[sid] = {"voxel_check": counts, "alignment_iou": {}}
        for view, png in spec["proj"].items():
            out = OUT_DIR / f"overlay_{view}_{sid}.png"
            iou = compose(sid, view, png, vol, v4, out)
            report[sid]["alignment_iou"][view] = round(iou, 4)
            print(f"  {view}: {out.name}  (regenerated-MIP vs committed-PNG IoU {iou:.4f})")
    (OUT_DIR / "overlay_render_receipt.json").write_text(
        json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print("receipt:", OUT_DIR / "overlay_render_receipt.json")


if __name__ == "__main__":
    main()
