"""S1 — inventory: enumerate the XML's 27 declared hand bones, match vendor files,
record sha256/size/format/tri-count/local bbox. NO geometry measurement (no assembly,
no distances) — the prereg is frozen before this runs only inventory steps.

READ-ONLY. Writes receipts/s1_inventory.json inside the audit dir.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import handlib as H  # noqa: E402
import numpy as np  # noqa: E402

OUT = H.OUT / "receipts" / "s1_inventory.json"


def main() -> int:
    anchors_r, anchors_l, sites_r, meshes, bodies = H.parse_hand_xml()

    inv = {
        "xml": str(H.XML),
        "hand_r_world_origin_m": [float(v) for v in bodies["hand_r"]],
        "hand_r_world_origin_pin_A4": [-0.0731, 0.532647, 0.202699],
        "chain_bodies_m": {k: [float(v) for v in bodies[k]]
                           for k in ["humerus", "ulna", "radius", "hand_r"]},
        "n_right_geoms_found": len(anchors_r),
        "n_left_geoms_found": len(anchors_l),
        "sites_found": {k: [float(v) for v in sites_r[k]] for k in sites_r},
        "bones": {},
        "left_stl_present_in_vendor": {},
        "other_family_spotcheck_md5": {},
    }
    missing_geom, missing_asset = [], []
    for b in H.BONES:
        row = {"anchor_hand_r_local_m": [float(v) for v in anchors_r[b]],
               "mesh_asset": meshes.get(b)}
        if b not in meshes:
            missing_asset.append(b)
        else:
            row["scale_xml"] = meshes[b]["scale"]
            row["file_attr"] = meshes[b]["file"]
        f = H.VENDOR / f"{b}.stl"
        if not f.exists():
            missing_geom.append(b)
            row["vendor_file"] = None
        else:
            tri, meta = H.load_stl(f)
            v = tri.reshape(-1, 3)
            row["vendor_file"] = str(f)
            row["sha256"] = H.sha256(f)
            row.update(meta)
            row["bbox_stl_local_m"] = {
                "x": [float(v[:, 0].min()), float(v[:, 0].max())],
                "y": [float(v[:, 1].min()), float(v[:, 1].max())],
                "z": [float(v[:, 2].min()), float(v[:, 2].max())],
            }
            row["extent_m"] = [float((v[:, i].max() - v[:, i].min())) for i in range(3)]
        inv["bones"][b] = row
        lf = H.VENDOR / f"{b}_l.stl"
        inv["left_stl_present_in_vendor"][b] = lf.exists()

    for a, b in [("1mc", "arm_r_1mc"), ("ulna", "arm_r_ulna"), ("2mc", "hand_2mc"),
                 ("capitate", "capitate_lvs"), ("capitate", "capitate_rvs")]:
        f = H.VENDOR / f"{b}.stl"
        if f.exists():
            import hashlib
            inv["other_family_spotcheck_md5"][f"{a}_vs_{b}"] = {
                "same_md5": hashlib.md5((H.VENDOR / f"{a}.stl").read_bytes()).hexdigest()
                == hashlib.md5(f.read_bytes()).hexdigest(),
                "bytes": [f.stat().st_size for f in [H.VENDOR / f"{a}.stl", f]],
            }

    inv["missing_geom"] = missing_geom
    inv["missing_asset_decl"] = missing_asset
    inv["name_match_complete"] = (not missing_geom) and (not missing_asset) \
        and len(anchors_r) == 27 and len(anchors_l) == 27

    OUT.write_text(json.dumps(inv, indent=2), encoding="utf-8")
    print(f"hand_r world origin: {[round(v,6) for v in bodies['hand_r']]}")
    print(f"right geoms: {len(anchors_r)}  left geoms: {len(anchors_l)}  "
          f"name match complete: {inv['name_match_complete']}")
    for b in H.BONES:
        r = inv["bones"][b]
        print(f"{b:10s} scale={r.get('scale_xml')} tri={r.get('n_tri')} "
              f"ext_mm={[round(e*1000,1) for e in r.get('extent_m',[0,0,0])]} "
              f"sha={r.get('sha256','')[:12]}")
    print(f"left STLs present: {any(inv['left_stl_present_in_vendor'].values())}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
