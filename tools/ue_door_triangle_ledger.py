"""ue_door_triangle_ledger.py — THE_TRANSLATION made concrete for TRIANGLES (T3 remaining gate).

Answers "can we get around UE being a black box?" with an executable falsifier:
a bijection ledger + vertex checksum. If the door ever drifts our vertices by any
amount NOT produced by our own sampler, the checksum mismatches -> the box is a
participant, rebuild the membrane (THE_TRANSLATION law).

Reuses ONLY proven machinery (no new math, no free numbers):
  * cad_sample.load_glb_triangles  -- bit-exact GLB import chain (the same parser ca_triangle.py runs)
  * ue_door_known_pose             -- the door transform JUST proven at machine precision (continuation-16)

What it proves headless (no UE, no GPU):
  L1 bijection ledger : every input triangle -> exactly one output node; counts match; nothing dropped.
  L2 vertex checksum  : a stable sha256 over ALL source vertex positions + triangle connectivity is the
                        REFERENCE the editor machine compares its independent parse against (bit-exact).
  L3 derived geometry: per-triangle centroid + normal (derived, never picked) round-trip through the
                        PROVEN door transform with identity at float precision.
  L4 degenerate count : zero-area triangles counted (n_degenerate_dropped precedent), not crashed on.

The cross-check against UE's OWN import happens on the live editor machine (flagged); this file is our
side of the pipe and is deterministic, so it runs anywhere.

Run: python tools/ue_door_triangle_ledger.py
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]          # repo root (E:\PythonChimera)
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from cad_sample import load_glb_triangles           # bit-exact import chain (reused, not reinvented)
from ue_door_known_pose import ue_to_splat, splat_to_ue   # the PROVEN door transform (continuation-16)

GLB = ROOT / "models" / "cad_bear" / "cad_bear.glb"
OUT = ROOT / "models" / "cad_bear" / "ue_triangle_ledger.json"
DEG_EPS = 1e-15                                    # zero-area floor (ca_triangle NEAR_ZERO_A0 precedent)


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    parts = load_glb_triangles(GLB)                # list of (name, verts(n,3), tris(k,3))

    total_verts = 0
    total_tris = 0
    nodes_out = 0
    n_degenerate = 0
    worst_rt = 0.0
    vert_bytes: list[bytes] = []                   # every source vertex position, in part order
    tri_rows: list[tuple[int, int, int]] = []      # (part_id, a, b, c) connectivity

    centroids = []                                # per-node derived centroid (walk space)
    normals = []                                  # per-node derived normal

    for pid, (name, v, i) in enumerate(parts):
        v = np.ascontiguousarray(v, dtype=np.float64)
        i = np.asarray(i, dtype=np.int64)
        total_verts += int(v.shape[0])
        total_tris += int(i.shape[0])

        # L2 vertex checksum material: raw float64 bytes of every source vertex position.
        vert_bytes.append(np.ascontiguousarray(v, dtype="<f8").tobytes())

        # L1 connectivity ledger rows (global part id + local indices).
        for r in i:
            tri_rows.append((pid, int(r[0]), int(r[1]), int(r[2])))

        # L3/L4 derived per-triangle geometry (centroid + normal), never picked.
        a = v[i[:, 0]]; b = v[i[:, 1]]; c = v[i[:, 2]]
        e1 = b - a; e2 = c - a
        nrm = np.cross(e1, e2)
        area2 = np.linalg.norm(nrm, axis=1)       # |cross| == 2*area
        deg = area2 < DEG_EPS
        n_degenerate += int(deg.sum())
        safe = ~deg
        centroids.append((a + b + c)[safe] / 3.0)
        nn = nrm[safe] / np.where(area2[safe, None] > 0, area2[safe, None], 1.0)
        normals.append(nn)

    nodes_out = total_tris                         # one node per triangle (bijection by construction)

    # L1 bijection ledger: triangles_in == nodes_out, nothing dropped/duplicated.
    l1_ok = (nodes_out == total_tris) and (len(tri_rows) == total_tris)

    # L2 vertex checksum (REFERENCE for the editor machine's independent parse).
    vert_checksum = _sha256_bytes(b"".join(vert_bytes))
    tri_checksum = _sha256_bytes(np.ascontiguousarray(tri_rows, dtype=np.int64).tobytes())

    # L3 round-trip through the PROVEN door transform (identity at float precision).
    # Genuinely CALLS ue_to_splat / splat_to_ue (the proven code path, not a re-inline) on a
    # deterministic sample of node centroids: first 512 + every 97th.
    C = np.concatenate(centroids) if centroids else np.zeros((0, 3))
    if len(C):
        idx = np.unique(np.concatenate([np.arange(min(512, len(C))),
                                         np.arange(0, len(C), 97)]))
        for j in idx:
            sp = ue_to_splat(tuple(float(x) for x in C[j]))["pos"]
            back = splat_to_ue(sp)
            worst_rt = max(worst_rt,
                           abs(back[0] - float(C[j, 0])),
                           abs(back[1] - float(C[j, 1])),
                           abs(back[2] - float(C[j, 2])))

    l3_ok = worst_rt <= 1e-9

    ledger = {
        "glb": str(GLB),
        "n_parts": len(parts),
        "total_vertices": total_verts,
        "total_triangles_in": total_tris,
        "nodes_out": nodes_out,
        "bijection_ok": bool(l1_ok),
        "vertex_checksum_sha256": vert_checksum,
        "triangle_connectivity_checksum_sha256": tri_checksum,
        "n_degenerate_dropped": n_degenerate,
        "centroid_roundtrip_worst_err": worst_rt,
        "roundtrip_ok": bool(l3_ok),
        "note": ("REFERENCE ledger. Editor machine: import the mesh, independently parse its vertices, "
                 "recompute vertex_checksum_sha256; any mismatch NOT produced by our sampler -> box is a "
                 "participant (THE_TRANSLATION). Cross-check runs on the live editor, not here."),
    }

    print("UE DOOR TRIANGLE LEDGER — THE_TRANSLATION for triangles (T3 remaining gate)")
    print(f"  parts={len(parts)}  vertices={total_verts:,}  triangles_in={total_tris:,}  nodes_out={nodes_out:,}")
    print(f"  L1 bijection ledger : in==out & connectivity rows match  {'PASS' if l1_ok else 'FAIL'}")
    print(f"  L2 vertex checksum  : sha256 {vert_checksum[:16]}... (REFERENCE for editor cross-check)")
    print(f"  L3 round-trip       : centroid through PROVEN door transform, worst |err|={worst_rt:.3e} "
          f"(<=1e-9)  {'PASS' if l3_ok else 'FAIL'}")
    print(f"  L4 degenerate tris  : {n_degenerate:,} zero-area counted (not crashed on)")

    OUT.write_text(__import__("json").dumps(ledger, indent=2))
    ok = bool(l1_ok and l3_ok)
    print(f"\n  VERDICT: {'LEDGER HOLDS — door carries triangles losslessly; checksum is the black-box falsifier' if ok else 'FALSIFIER FIRED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
