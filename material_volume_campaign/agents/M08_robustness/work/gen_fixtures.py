"""Generate the frozen M08 fixture ladder + manifest.

Mechanical materialization of PREREGISTRATION.md section 3. No exporter or
compiler module is imported or executed here (preregistration ordering):
only the exact oracle evaluates fixture geometry, so per-rung expected values,
achieved deltas, and frozen bounds are computed BEFORE the run.
"""
from __future__ import annotations
import json
import math
import sys
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import oracle as ob  # noqa: E402

HERE = Path(__file__).parent
FIX = HERE.parent / "fixtures"
FIX.mkdir(exist_ok=True)

MAT_SRC, MAT_COND = "analytic robustness fixture", "uniform"


def coupon_vertices(x=0.0):
    """Two-cell doc coupon (material_volume_body_export_*_example.json shape),
    offset by x on the X axis. Densities 12/6 as in the example."""
    verts = [
        [x + 0.0, 0.0, 0.0], [x + 1.0, 0.0, 0.0], [x + 0.0, 1.0, 0.0],
        [x + 0.0, 0.0, 1.0],
        [x + 3.0, -2.0, 1.0], [x + 3.0, -1.0, 1.0], [x + 2.0, -2.0, 1.0],
        [x + 3.0, -2.0, 2.0],
    ]
    tets = [[0, 1, 2, 3], [4, 5, 6, 7]]
    dens = [12.0, 6.0]
    return verts, tets, dens


def coupon_docs(verts, scale):
    """Manifest/partition/groups triple for the coupon at `scale` (frame
    coordinates are the given verts; SI = verts * scale)."""
    vs = [{"vertex_id": vid, "position": pos}
          for vid, pos in zip(["a0", "a1", "a2", "a3", "b0", "b1", "b2", "b3"],
                              verts)]
    manifest = {
        "schema_version": "chimera.fitting_manifest.v1",
        "fitting_id": "m08-robustness-fit", "domain_id": "m08-coupon",
        "domain_revision": "rung-v1",
        "coordinate_frame": {"frame_id": "m08-domain", "handedness": "right",
                             "coordinate_unit": "m", "scale_to_m": scale},
        "vertices": vs,
        "cells": [
            {"cell_id": "cell-A", "vertex_ids": ["a0", "a1", "a2", "a3"],
             "component_id": "component-A"},
            {"cell_id": "cell-B", "vertex_ids": ["b0", "b1", "b2", "b3"],
             "component_id": "component-B"}],
        "regions": [
            {"region_id": "region-A", "mass_owner_id": "owner-A",
             "material_id": "tissue-A"},
            {"region_id": "region-B", "mass_owner_id": "owner-B",
             "material_id": "tissue-B"}],
        "mass_authority": "reconstructed_tissue_mass",
        "source_effective_segment_ids": [],
        "matter_ownership": [
            {"matter_id": "m08-matter-A", "representation": "tetrahedral_volume",
             "mass_owner_id": "owner-A"},
            {"matter_id": "m08-matter-B", "representation": "tetrahedral_volume",
             "mass_owner_id": "owner-B"}],
    }
    partition = {
        "schema_version": "chimera.material_partition.v1",
        "coordinate_frame": manifest["coordinate_frame"],
        "vertices": vs,
        "cells": [
            {"cell_id": "cell-A", "vertex_ids": ["a0", "a1", "a2", "a3"],
             "proposals": ["region-A"]},
            {"cell_id": "cell-B", "vertex_ids": ["b0", "b1", "b2", "b3"],
             "proposals": ["region-B"]}],
        "materials": [
            {"material_id": "tissue-A", "density_kg_m3": 12.0,
             "density_source": MAT_SRC, "conditions": MAT_COND},
            {"material_id": "tissue-B", "density_kg_m3": 6.0,
             "density_source": MAT_SRC, "conditions": MAT_COND}],
        "regions": manifest["regions"],
        "mass_authority": "reconstructed_tissue_mass",
    }
    groups = {
        "schema_version": "chimera.rigid_body_cell_groups.v1",
        "body_groups": [
            {"body_id": "m08-body-all", "cell_ids": ["cell-A", "cell-B"],
             "body_frame": {"frame_id": "m08-authored", "handedness": "right",
                            "coordinate_unit": "m",
                            "domain_from_body": {
                                "rotation": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                                             [0.0, 0.0, 1.0]],
                                "origin_m": [0.0, 0.0, 0.0]}}}]
    }
    return manifest, partition, groups


def compiler_doc(verts, tets, dens):
    return {
        "schema_version": "chimera.material_volume.v1",
        "coordinate_unit": "m", "density_unit": "kg/m^3",
        "mass_source_kind": "reconstructed_material_volume",
        "vertices_m": verts, "tetrahedra": tets,
        "materials": [{"material_id": f"mat-{i}", "density_kg_m3": d,
                       "density_source": MAT_SRC, "conditions": MAT_COND}
                      for i, d in enumerate(dens)],
        "regions": [{"region_id": f"region-{i}", "mass_owner_id": f"owner-{i}",
                     "material_id": f"mat-{i}"} for i in range(len(dens))],
        "cell_proposals": [[f"region-{i}"] for i in range(len(tets))],
    }


def si_vertices(verts, scale):
    return [[x * scale for x in row] for row in verts]


def make_rung(rung_id, klass, path, verts, tets, dens, scale, predicted,
              extra=None):
    """Evaluate the oracle on the exact SI floats and freeze bounds."""
    if path == "compiler":
        si = [[float(x) for x in row] for row in verts]
    else:
        si = si_vertices(verts, scale)
    if predicted.get("outcome") == "refuse":
        # Expected values/bounds are undefined for refusal rungs (geometry is
        # collapsed or intentionally non-computable), but record the exact
        # shape where computable (it shows HOW FAR inside/outside the gate
        # the rung sits). E8's exact determinant overflows float on purpose.
        try:
            shape = ob.fixture_shape(si, tets)
        except (OverflowError, ZeroDivisionError):
            shape = None
        rung = {"id": rung_id, "class": klass, "path": path, "scale": scale,
                "tets": tets, "densities": dens, "vertices": verts,
                "predicted": predicted, "expected": None,
                "shape": shape, "bounds": None}
        if extra:
            rung.update(extra)
        return rung
    exp = ob.oracle(si, tets, dens)
    shape = ob.fixture_shape(si, tets)
    bounds = ob.bounds_for(shape["delta"], shape["scale"], shape["x_max"])
    rung = {"id": rung_id, "class": klass, "path": path, "scale": scale,
            "tets": tets, "densities": dens, "vertices": verts,
            "predicted": predicted,
            "expected": {"volume": exp["volume"], "mass": exp["mass"],
                         "com": exp["com"], "inertia": exp["inertia"]},
            "shape": {"delta": shape["delta"], "scale_edge": shape["scale"],
                      "x_max": shape["x_max"]},
            "bounds": bounds}
    if extra:
        rung.update(extra)
    return rung


def bisect_sliver_eps2(target_delta, side):
    """Deterministic eps2 selection: enumerate floats around the analytic
    solution of det(eps2) = 0.85*eps2 - 0.62 = target_delta*scale^3 and pick
    the candidate whose EXACT delta is closest to target on the required side
    ('above' -> delta >= target, accepted; 'below' -> delta <= target,
    predicted gate refusal). Signed det must stay POSITIVE (D4): a negative-det
    candidate would be an inverted cell, not a gate-boundary rung."""
    base = [(0.0, 0.0, 0.0), (1.0, 0.3, 0.7), (0.5, 1.0, 1.0)]

    def signed_det(eps2):
        V = [[F(x) for x in row]
             for row in (base + [(0.9, 0.4, eps2)])]
        p = [V[0], V[1], V[2], V[3]]
        d1 = [p[1][k] - p[0][k] for k in range(3)]
        d2 = [p[2][k] - p[0][k] for k in range(3)]
        d3 = [p[3][k] - p[0][k] for k in range(3)]
        return ob._det3(d1, d2, d3)

    scale3 = 3.375                      # scale = max edge = 1.5 exactly
    det_target = F(target_delta) * F(scale3)
    eps2_star = (F(62, 100) + det_target) / F(85, 100)
    cand = float(eps2_star)
    best, best_gap = None, None
    for k in range(-200, 201):
        e = cand
        for _ in range(abs(k)):
            e = math.nextafter(e, math.inf if k > 0 else -math.inf)
        det = signed_det(e)
        if det <= 0:
            continue                    # keep orientation positive (D4)
        verts = base + [(0.9, 0.4, e)]
        d = ob.fixture_shape(verts, [[0, 1, 2, 3]])["delta"]
        if side == "above" and d < target_delta:
            continue
        if side == "below" and d > target_delta:
            continue
        gap = abs(d - target_delta)
        if best_gap is None or gap < best_gap:
            best, best_gap = e, gap
    if best is None:
        raise RuntimeError(f"no eps2 candidate for target={target_delta}")
    return best


def main():
    rungs = []

    # ---- Class A: offset ladder (compiler path) --------------------------
    for i, x in enumerate([0.0, 1e3, 1e6, 1e9, 1e12, 1e15]):
        verts, tets, dens = coupon_vertices(x)
        rungs.append(make_rung(f"A{i}", "A-offset", "compiler", verts, tets,
                               dens, 1.0, {"outcome": "accept"}))
    # A7: offset horizon, X=1e16 (ulp=2 -> X+1 collapses onto X)
    verts, tets, dens = coupon_vertices(1e16)
    rungs.append(make_rung("A7", "A-offset", "compiler", verts, tets, dens,
                           1.0,
                           {"outcome": "refuse",
                            "reason": "duplicate_vertex_position"}))

    # ---- Class A export-path subset (cross-path vs compiler) -------------
    for x, tag in [(0.0, "A0x"), (1e12, "A4x"), (1e15, "A5x")]:
        verts, tets, dens = coupon_vertices(x)
        man, part, grp = coupon_docs(verts, 1.0)
        rungs.append(make_rung(tag, "A-offset", "export", verts, tets, dens,
                               1.0, {"outcome": "accept"},
                               extra={"docs": {"manifest": man, "partition": part,
                                               "groups": grp}}))

    # ---- Class B: um ladder, single right tet ----------------------------
    for i, s in enumerate([1.0, 1e-2, 1e-4, 1e-6, 1e-8, 1e-10]):
        verts = [[0.0, 0.0, 0.0], [s, 0.0, 0.0], [0.0, s, 0.0], [0.0, 0.0, s]]
        rungs.append(make_rung(f"B{i}", "B-small", "compiler", verts,
                               [[0, 1, 2, 3]], [12.0], 1.0,
                               {"outcome": "accept"}))

    # ---- Class C: flat/thin friendly ladder ------------------------------
    scale_c = math.sqrt(2.0)
    for i, h in enumerate([1.0, 1e-2, 1e-6, 1e-10, 1e-13, 5e-14]):
        verts = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                 [0.5, 0.5, h]]
        rungs.append(make_rung(f"C{i}", "C-flat", "compiler", verts,
                               [[0, 1, 2, 3]], [4.0], 1.0,
                               {"outcome": "accept"}))
    for i, h in enumerate([3e-14, 1e-14]):
        verts = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                 [0.5, 0.5, h]]
        rungs.append(make_rung(f"C{6+i}", "C-flat", "compiler", verts,
                               [[0, 1, 2, 3]], [4.0], 1.0,
                               {"outcome": "refuse",
                                "reason": "degenerate_tetrahedron"}))

    # ---- Class S: near-degenerate-but-allowed sliver (exact-delta bisection)
    for i, (target, side) in enumerate([(2.5 * ob.G, "above"),
                                        (1.2 * ob.G, "above"),
                                        (0.87 * ob.G, "below"),
                                        (0.5 * ob.G, "below")]):
        eps2 = bisect_sliver_eps2(target, side)
        outcome = "accept" if side == "above" else "refuse"
        rungs.append(make_rung(
            f"S{i}", "S-sliver", "compiler",
            [(0.0, 0.0, 0.0), (1.0, 0.3, 0.7), (0.5, 1.0, 1.0),
             (0.9, 0.4, eps2)],
            [[0, 1, 2, 3]], [4.0], 1.0,
            {"outcome": outcome,
             "reason": None if outcome == "accept" else "degenerate_tetrahedron"},
            extra={"params": {"eps2": eps2, "target_delta": target,
                              "side": side}}))

    # ---- Class D: needle ladder ------------------------------------------
    L = 1e3
    for i, w in enumerate([10.0, 0.1, 1e-2, 1.5e-4]):
        verts = [[0.0, 0.0, 0.0], [float(L), 0.0, 0.0], [L / 2, w, 0.0],
                 [L / 2, 0.0, w]]
        rungs.append(make_rung(f"D{i}", "D-needle", "compiler", verts,
                               [[0, 1, 2, 3]], [4.0], 1.0,
                               {"outcome": "accept"}))
    for i, w in enumerate([1.1e-4, 1e-4]):
        verts = [[0.0, 0.0, 0.0], [float(L), 0.0, 0.0], [L / 2, w, 0.0],
                 [L / 2, 0.0, w]]
        rungs.append(make_rung(f"D{4+i}", "D-needle", "compiler", verts,
                               [[0, 1, 2, 3]], [4.0], 1.0,
                               {"outcome": "refuse",
                                "reason": "degenerate_tetrahedron"}))

    # ---- Class E: scale_to_m extremes (export path) ----------------------
    p1v, tets_e, dens_e = coupon_vertices(0.0)
    ids = ["a0", "a1", "a2", "a3", "b0", "b1", "b2", "b3"]
    for rid, p, sc, note in [
            ("E1", 1.0, 1.0, "SI reference"),
            ("E2", 2.0 ** 20, 2.0 ** -20, "bitwise twin of E1"),
            ("E3", 2.0 ** -20, 2.0 ** 20, "bitwise twin of E1"),
            ("E4a", 2.0 ** 30, 2.0 ** 30, "SI=2^60 uniform-large"),
            ("E4b", 2.0 ** 40, 2.0 ** 20, "bitwise twin of E4a"),
            ("E5", 1e6, 1e-6, "decimal um declaration (twin of E1)"),
            ("E6", 1.0, 1e6, "SI=1e6 uniform-large")]:
        verts = [[row[0] * p, row[1] * p, row[2] * p] for row in p1v]
        man, part, grp = coupon_docs(verts, sc)
        rungs.append(make_rung(rid, "E-scale", "export", verts, tets_e, dens_e,
                               sc, {"outcome": "accept"},
                               extra={"docs": {"manifest": man,
                                               "partition": part,
                                               "groups": grp},
                                      "params": {"note": note}}))

    # E7: collapse attempt — PRESERVED INVALID RUNG: the ulp pair was placed on
    # one axis together with a third collinear vertex, so the cell is degenerate
    # in FRAME coordinates already (delta=0 before any scaling), and a
    # power-of-two scale is exact anyway. The exporter/compiler refusal this
    # rung produced (degenerate_tetrahedron) is correct declared behavior on a
    # genuinely degenerate input; it never tested SI collapse. Kept frozen and
    # preserved; the real collapse coverage is E7b below.
    one, one_p = 1.0, math.nextafter(1.0, 2.0)
    verts = [[0.0, 0.0, 0.0], [one, 0.0, 0.0], [one_p, 0.0, 0.0],
             [0.0, 1.0, 0.0],
             [3.0, -2.0, 1.0], [3.0, -1.0, 1.0], [2.0, -2.0, 1.0],
             [3.0, -2.0, 2.0]]
    man, part, grp = coupon_docs(verts, 2.0 ** -60)
    rungs.append(make_rung("E7", "E-scale", "export", verts, tets_e, dens_e,
                           2.0 ** -60,
                           {"outcome": "refuse",
                            "reason": "duplicate_vertex_position"},
                           extra={"docs": {"manifest": man, "partition": part,
                                           "groups": grp}}))

    # E7b: real collapse rung (post-hoc fixture correction, no v1 rung changed).
    # Two frame-distinct vertices (1,0,0) and (nextafter(1,2),0,0) can only map
    # to ONE SI position when the SI product is SUBNORMAL: at scale_to_m=1e-310
    # (positive finite => inside declared support D6) both products round to the
    # same subnormal float (verified: fl(1*1e-310) == fl(nextafter(1,2)*1e-310),
    # difference 2.2e-326 vs subnormal half-ulp 2.47e-324). For normal SI values
    # this is impossible: multiplying a float by (1+2^-52) shifts it by >= 1 ulp,
    # so decimal scales like 1e-18 preserve distinctness — hence this, not E7's
    # power-of-two attempt, is the reachable collapse. The frame cell is
    # non-degenerate and positively oriented: det = 2^-52 > 0 (exact).
    verts = [[0.0, 1.0, 0.0], [one, 0.0, 0.0], [one_p, 0.0, 0.0],
             [0.0, 0.0, 1.0]]
    tets_1 = [[0, 1, 2, 3]]
    dens_1 = [12.0]
    scale_b = 1e-310
    frame_ids = ["v0", "v1", "v2", "v3"]
    vs = [{"vertex_id": vid, "position": pos}
          for vid, pos in zip(frame_ids, verts)]
    frame_block = {"frame_id": "m08-domain", "handedness": "right",
                   "coordinate_unit": "m", "scale_to_m": scale_b}
    man = {"schema_version": "chimera.fitting_manifest.v1",
           "fitting_id": "m08-robustness-fit", "domain_id": "m08-collapse",
           "domain_revision": "rung-v1", "coordinate_frame": frame_block,
           "vertices": vs,
           "cells": [{"cell_id": "cell-A",
                      "vertex_ids": frame_ids, "component_id": "component-A"}],
           "regions": [{"region_id": "region-A", "mass_owner_id": "owner-A",
                        "material_id": "tissue-A"}],
           "mass_authority": "reconstructed_tissue_mass",
           "source_effective_segment_ids": [],
           "matter_ownership": [
               {"matter_id": "m08-matter-A",
                "representation": "tetrahedral_volume",
                "mass_owner_id": "owner-A"}]}
    part = {"schema_version": "chimera.material_partition.v1",
            "coordinate_frame": frame_block, "vertices": vs,
            "cells": [{"cell_id": "cell-A", "vertex_ids": frame_ids,
                       "proposals": ["region-A"]}],
            "materials": [{"material_id": "tissue-A", "density_kg_m3": 12.0,
                           "density_source": MAT_SRC, "conditions": MAT_COND}],
            "regions": man["regions"],
            "mass_authority": "reconstructed_tissue_mass"}
    grp = {"schema_version": "chimera.rigid_body_cell_groups.v1",
           "body_groups": [
               {"body_id": "m08-body-all", "cell_ids": ["cell-A"],
                "body_frame": {"frame_id": "m08-authored",
                               "handedness": "right", "coordinate_unit": "m",
                               "domain_from_body": {
                                   "rotation": [[1.0, 0.0, 0.0],
                                                [0.0, 1.0, 0.0],
                                                [0.0, 0.0, 1.0]],
                                   "origin_m": [0.0, 0.0, 0.0]}}}]}
    rungs.append(make_rung("E7b", "E-scale", "export", verts, tets_1, dens_1,
                           scale_b,
                           {"outcome": "refuse",
                            "reason": "duplicate_vertex_position"},
                           extra={"docs": {"manifest": man, "partition": part,
                                           "groups": grp}}))

    # E8: overflow — scale 1e300 pushes SI arithmetic past float64 range
    verts, tets_e2, dens_e2 = coupon_vertices(0.0)
    man, part, grp = coupon_docs(verts, 1e300)
    rungs.append(make_rung("E8", "E-scale", "export", verts, tets_e2, dens_e2,
                           1e300,
                           {"outcome": "refuse", "reason": "numeric_overflow"},
                           extra={"docs": {"manifest": man, "partition": part,
                                           "groups": grp}}))

    # E1f: authored rotated frame (exporter-only feature, per bound (i))
    verts, tets, dens = coupon_vertices(0.0)
    man, part, grp = coupon_docs(verts, 1.0)
    grp = {
        "schema_version": "chimera.rigid_body_cell_groups.v1",
        "body_groups": [
            {"body_id": "body-A", "cell_ids": ["cell-A"],
             "body_frame": {"frame_id": "m08-frame-id", "handedness": "right",
                            "coordinate_unit": "m",
                            "domain_from_body": {
                                "rotation": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                                             [0.0, 0.0, 1.0]],
                                "origin_m": [0.0, 0.0, 0.0]}}},
            {"body_id": "body-B", "cell_ids": ["cell-B"],
             "body_frame": {"frame_id": "m08-frame-rot", "handedness": "right",
                            "coordinate_unit": "m",
                            "domain_from_body": {
                                "rotation": [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0],
                                             [0.0, 0.0, 1.0]],
                                "origin_m": [3.0, -2.0, 1.0]}}}],
    }
    rungs.append(make_rung("E1f", "E-scale", "export", verts, tets, dens, 1.0,
                           {"outcome": "accept"},
                           extra={"docs": {"manifest": man, "partition": part,
                                           "groups": grp},
                                  "params": {"note": "two authored frames"}}))

    # ---- Freeze fixture JSON documents + manifest ------------------------
    for rung in rungs:
        if rung["path"] == "compiler":
            doc = compiler_doc(rung["vertices"], rung["tets"], rung["densities"])
            (FIX / f"{rung['id']}.json").write_text(
                json.dumps(doc, indent=1), encoding="utf-8")
        else:
            for kind in ("manifest", "partition", "groups"):
                (FIX / f"{rung['id']}_{kind}.json").write_text(
                    json.dumps(rung["docs"][kind], indent=1), encoding="utf-8")
        # keep the manifest light: vertices only (docs live in fixture files)
        rung.pop("docs", None)

    manifest = {
        "campaign": "mvc-20260924/M08 numerical robustness",
        "preregistration": "PREREGISTRATION.md (frozen before generation)",
        "constants": {"u": ob.U, "eps": ob.EPS, "gate": ob.G},
        "rung_count": len(rungs),
        "rungs": rungs,
    }
    (FIX / "manifest.json").write_text(json.dumps(manifest, indent=1),
                                       encoding="utf-8")
    print(f"froze {len(rungs)} rungs")
    for r in rungs:
        d = (r["shape"] or {}).get("delta")
        ds = f"{d:.6e}" if d is not None else "n/a (refusal)"
        print(f"  {r['id']:>4} {r['class']:<9} {r['path']:<8} "
              f"delta={ds} predicted={r['predicted']['outcome']}"
              + (f":{r['predicted']['reason']}" if r['predicted'].get("reason") else ""))


if __name__ == "__main__":
    main()
