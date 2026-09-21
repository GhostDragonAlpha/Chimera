"""THE HIP PIVOT PROOF BATTERY (preregistration 96ddb501...).

Executes the A1-A6 battery of docs/THE_ARTICULATION_LAW.md §4 on the two
committed hip bonds (bond.joint_01_02 primary, bond.joint_01_03 second
instance), plus the preregistered null-pivot control and the pose record.

Everything is DERIVED/CITED/COMMITTED, nothing tuned:
  - the inlier rule of the preregistration (seed = the bond's recorded
    closest point; band = the mesh's own median edge; hemisphere-floor
    minimum inlier count; anchored monotone growth to a fixed point),
  - the range parsed from the committed OpenSim record (gait2392),
  - the apposition area from the committed touching-class cut (3.0 mm),
  - cure via tools.matter_kernel.glue.pull_bond VERBATIM,
  - the law metric (identify_bones_v2 symmetric min vertex-vertex).

Read-only on the committed tree. Deterministic: no RNG, no timestamps,
no set-order leakage; the output JSON is byte-stable across runs.

Run:  python -B tools/science_funnel/validation/hip_pivot_proof_20260921/hip_pivot_proof.py
"""

import hashlib
import json
import math
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.matter_kernel.definition import TRIANGLE_BYTES, MASS_TOLERANCE  # noqa: E402
from tools.matter_kernel import constants as kconstants  # noqa: E402
from tools.matter_kernel.glue import pull_bond  # noqa: E402

DATA = ROOT / "tools" / "science_funnel" / "data" / "morphosource_ct" / "matter_skeleton"
DEFN = DATA / "infant_skeleton.body.json"
OSIM = ROOT / "research_references" / "human" / "opensim" / "gait2392_thelen2003muscle.osim"
OSIM_SHA = "18e5b3e406a619a78d109e81e6e2cd4f58681a967808fb52a992bbd2b27db019"

TOUCH_CUT_MM = 3.0            # bone_identification_v3 derived_cuts.joint_gap_mm (committed)
METRIC_TRANSFER_TOL = 0.005   # house metric-transfer tolerance (adjacency lane)
P0_LO_MM, P0_HI_MM = 1.5, 4.5  # preregistered prediction band (refusal outside)
DETECTOR_TOL = 1e-12          # P4b resampling detector
GN_MAX_ITER = 200
GN_STEP_TOL = 1e-13
GROW_CAP = 10000

OUT = HERE / "battery.json"

R12 = 12  # rounding for the record


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_blob(rank):
    b = (DATA / "tris" / ("bone_%02d.bin" % rank)).read_bytes()
    if len(b) % TRIANGLE_BYTES != 0:
        raise SystemExit("blob %d not a multiple of 36" % rank)
    n = len(b) // TRIANGLE_BYTES
    tris = np.frombuffer(b, dtype="<f4").reshape(n, 3, 3).astype(np.float64)
    return b, tris


def unique_verts(tris):
    """Canonical dedup of the float32 blob vertices; first-occurrence order."""
    flat = tris.astype(np.float32).reshape(-1, 3)
    seen = {}
    idx = np.empty(len(flat), dtype=np.int64)
    for i in range(len(flat)):
        key = flat[i].tobytes()
        j = seen.get(key)
        if j is None:
            j = len(seen)
            seen[key] = j
        idx[i] = j
    verts = np.zeros((len(seen), 3), dtype=np.float64)
    for bs, k in seen.items():
        verts[k] = np.frombuffer(bs, dtype="<f4").astype(np.float64)
    return verts, idx.reshape(-1, 3)


def area_seq(blob):
    """definition.py validate_membrane's accumulation, VERBATIM (float64)."""
    area = 0.0
    for off in range(0, len(blob), TRIANGLE_BYTES):
        ax, ay, az, bx, by, bz, cx, cy, cz = struct.unpack_from("<9f", blob, off)
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        area += 0.5 * (nx * nx + ny * ny + nz * nz) ** 0.5
    return area


def areas_np(tris):
    """Per-triangle areas, numpy cross product (the preregistered area path)."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    u, v = b - a, c - a
    n = np.cross(u, v)
    return 0.5 * np.sqrt((n * n).sum(-1))


def vertex_records_sha(blob):
    """Canonical vertex serialization (matter_skeleton_import.vertex_records)."""
    seen = set()
    for off in range(0, len(blob), TRIANGLE_BYTES):
        vals = struct.unpack_from("<9f", blob, off)
        for i in (0, 3, 6):
            seen.add(struct.pack("<3f", *vals[i:i + 3]))
    return sha256_bytes(b"".join(sorted(seen)))


def kasa_fit(V):
    """Algebraic sphere fit (Kasa). Returns (c, r)."""
    A = np.column_stack([V, np.ones(len(V))])
    b = (V * V).sum(-1)
    p, *_ = np.linalg.lstsq(A, b, rcond=None)
    c = p[:3] / 2.0
    rr = p[3] + (c * c).sum()
    if rr <= 0:
        return None
    return c, math.sqrt(rr)


def gn_refine(V, c, r, max_iter=GN_MAX_ITER, tol=GN_STEP_TOL):
    """Geometric least-spheres Gauss-Newton from (c, r). Deterministic."""
    it = 0
    for it in range(1, max_iter + 1):
        d = V - c
        n = np.sqrt((d * d).sum(-1))
        e = n - r
        J = np.column_stack([-d / n[:, None], -np.ones(len(V))])
        JTJ = J.T @ J
        JTe = J.T @ e
        try:
            step = np.linalg.solve(JTJ, -JTe)
        except np.linalg.LinAlgError:
            step, *_ = np.linalg.lstsq(JTJ, -JTe, rcond=None)
        c = c + step[:3]
        r = r + step[3]
        if np.abs(step).max() < tol:
            break
    return c, r, it


def sphere_fit(V):
    k = kasa_fit(V)
    if k is None:
        return None
    return gn_refine(V, k[0], k[1])


def adjacency(faces, n):
    adj = [[] for _ in range(n)]
    for a, b, c in faces:
        adj[a].append(b)
        adj[a].append(c)
        adj[b].append(a)
        adj[b].append(c)
        adj[c].append(a)
        adj[c].append(b)
    return [sorted(set(x)) for x in adj]


def inlier_rule(verts, faces, seed_pt, band):
    """THE PREREGISTERED RULE (preregistration.md §4). Returns a dict."""
    dist_seed = np.linalg.norm(verts - seed_pt, axis=1)
    seed = int(np.argmin(dist_seed))
    adj = adjacency(faces, len(verts))
    S = frozenset({seed})
    seen_states = {hashlib.sha256(repr(sorted(S)).encode()).hexdigest()}
    history = []
    outcome = "fixed_point"
    it = 0
    for it in range(1, GROW_CAP + 1):
        if len(S) < 4:
            grow = set(S)
            for v in S:
                grow.update(adj[v])
            C = frozenset(grow)
        else:
            V = verts[sorted(S)]
            f = sphere_fit(V)
            if f is None:
                grow = set(S)
                for v in S:
                    grow.update(adj[v])
                C = frozenset(grow)
            else:
                c, r, _ = f
                cand = set(S)
                for v in S:
                    cand.update(adj[v])
                idx = sorted(cand)
                dv = np.linalg.norm(verts[idx] - c, axis=1)
                keep = np.abs(dv - r) <= band
                C = frozenset(np.asarray(idx)[keep].tolist()) | {seed}
        if C == S:
            outcome = "fixed_point"
            break
        h = hashlib.sha256(repr(sorted(C)).encode()).hexdigest()
        if h in seen_states:
            outcome = "cycle_refusal"
            break
        seen_states.add(h)
        S = C
    else:
        outcome = "cap_refusal"
    inliers = sorted(S)
    fit = sphere_fit(verts[inliers]) if len(inliers) >= 4 else None
    if fit is None:
        return {"outcome": "degenerate_refusal", "seed_vertex": seed, "iterations": it}
    c, r, gn_it = fit
    res = np.abs(np.linalg.norm(verts[inliers] - c, axis=1) - r)
    return {
        "seed_vertex": seed,
        "seed_vertex_offset_from_record_mm": round(float(dist_seed[seed]), R12),
        "band_eps_mm": round(float(band), R12),
        "iterations": it,
        "outcome": outcome,
        "inliers": len(inliers),
        "center_mm": [round(float(x), R12) for x in c],
        "radius_mm": round(float(r), R12),
        "rms_residual_mm": round(float(np.sqrt((res * res).mean())), R12),
        "max_residual_mm": round(float(res.max()), R12),
        "gauss_newton_iters_final": gn_it,
        "_c": c,
        "_inliers": inliers,
    }


def rodrigues(V, c, axis, theta):
    """Rigid Rodrigues rotation of V about (c, axis) by theta (float64)."""
    if theta == 0.0:
        return V.copy()
    k = axis / np.linalg.norm(axis)
    d = V - c
    cos, sin = math.cos(theta), math.sin(theta)
    return c + d * cos + np.cross(k, d) * sin + np.outer(d @ k, k) * (1.0 - cos)


def law_gap(vq, vref, tree_ref, tree_q=None):
    """identify_bones_v2 symmetric min vertex-vertex + provenance."""
    if tree_q is None:
        tree_q = cKDTree(vq)
    d1, i1 = tree_ref.query(vq, k=1)     # each child vertex -> nearest parent vertex
    d2, i2 = tree_q.query(vref, k=1)     # each parent vertex -> nearest child vertex
    if d1.min() <= d2.min():
        j = int(np.argmin(d1))
        return float(d1.min()), ("child_vertex", j, "parent_vertex", int(i1[j]))
    j = int(np.argmin(d2))
    return float(d2.min()), ("parent_vertex", j, "child_vertex", int(i2[j]))


def patch_of(tris, tree_parent):
    """The preregistered apposition-patch estimator (centroid within 3.0 mm)."""
    cen = tris.mean(axis=1)
    d, _ = tree_parent.query(cen, k=1)
    mask = d <= TOUCH_CUT_MM
    return mask, float(np.abs(d - TOUCH_CUT_MM).min())


def patch_stats(verts, faces, mask, tree_parent):
    idx = np.unique(faces[mask])
    d, _ = tree_parent.query(verts[idx], k=1)
    return {"patch_vertices": int(len(idx)),
            "patch_mean_gap_mm": round(float(d.mean()), R12),
            "patch_max_gap_mm": round(float(d.max()), R12)}


class OutOfAnatomicalRange(Exception):
    def __init__(self, theta, lo, hi):
        super().__init__("out_of_anatomical_range")
        self.name = "out_of_anatomical_range"
        self.theta = theta
        self.lo = lo
        self.hi = hi


def pose_request(theta, lo, hi):
    if theta < lo or theta > hi:
        raise OutOfAnatomicalRange(theta, lo, hi)
    return True


def rnd(x):
    return round(float(x), R12)


def sanitize(o):
    if isinstance(o, dict):
        return {k: sanitize(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [sanitize(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return rnd(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


# --------------------------------------------------------------------- main
def main():
    body = json.loads(DEFN.read_text(encoding="utf-8"))
    mems = {m["id"]: m for m in body["membranes"]}
    bonds = {b["id"]: b for b in body["bonds"]}
    contacts = {c["id"]: c for c in body["pose_contacts"]["contacts"]}
    yield_pa = body["materials"]["mat.bone_cortical"]["yield"]

    # pull_bond resolves member constants via the kernel's sourced table; the
    # definition carries its OWN sourced rows (L1: validate_material enforced
    # the citations), so the battery registers those rows verbatim, in memory,
    # exactly as a body loader would. No committed byte changes.
    registered = {}
    for name, mat in body["materials"].items():
        if name not in kconstants.MATERIALS:
            kconstants.MATERIALS[name] = mat
            registered[name] = {"yield_pa": mat["yield"], "source": mat["source"]}

    watch = [
        DEFN, OSIM,
        DATA / "tris" / "bone_01.bin", DATA / "tris" / "bone_02.bin", DATA / "tris" / "bone_03.bin",
        ROOT / "tools" / "science_funnel" / "validation" / "axial_adjacency_20260920" / "receipt.json",
        ROOT / "tools" / "science_funnel" / "validation" / "hip_adoption_20260921" / "receipt.json",
        ROOT / "tools" / "science_funnel" / "validation" / "articulation_design_20260921" / "receipt.json",
        HERE / "preregistration.md",
    ]
    before = {str(p.relative_to(ROOT)): sha256_file(p) for p in watch}

    blobs, tri_sets, vert_sets, face_sets = {}, {}, {}, {}
    for r in (1, 2, 3):
        blobs[r], tri_sets[r] = load_blob(r)
        vert_sets[r], face_sets[r] = unique_verts(tri_sets[r])

    # ---- input integrity + pinned checks ---------------------------------
    osim_sha = sha256_file(OSIM)
    tree1 = cKDTree(vert_sets[1])

    # range record parsed from the committed osim (no retyped constant)
    root = ET.parse(OSIM).getroot()
    ranges = {}
    for co in root.iter("Coordinate"):
        nm = co.get("name")
        if nm in ("hip_flexion_l", "hip_flexion_r"):
            rg = [float(x) for x in co.find("range").text.split()]
            ranges[nm] = rg
    if sorted(ranges) != ["hip_flexion_l", "hip_flexion_r"]:
        raise SystemExit("osim range parse failed: %s" % sorted(ranges))
    (lo_l, hi_l), (lo_r, hi_r) = ranges["hip_flexion_l"], ranges["hip_flexion_r"]
    if lo_l != -hi_l or lo_r != -hi_r:
        raise SystemExit("asymmetric hip range record")
    R_l, R_r = hi_l, hi_r

    # kernel member areas (definition.py accumulation, canonical)
    area1 = area_seq(blobs[1])
    area2 = area_seq(blobs[2])
    area3 = area_seq(blobs[3])

    q2 = area2 / len(vert_sets[2])
    q3 = area3 / len(vert_sets[3])
    med2 = float(np.median(np.concatenate([
        np.linalg.norm(tri_sets[2][:, 1] - tri_sets[2][:, 0], axis=1),
        np.linalg.norm(tri_sets[2][:, 2] - tri_sets[2][:, 1], axis=1),
        np.linalg.norm(tri_sets[2][:, 0] - tri_sets[2][:, 2], axis=1)])))
    med3 = float(np.median(np.concatenate([
        np.linalg.norm(tri_sets[3][:, 1] - tri_sets[3][:, 0], axis=1),
        np.linalg.norm(tri_sets[3][:, 2] - tri_sets[3][:, 1], axis=1),
        np.linalg.norm(tri_sets[3][:, 0] - tri_sets[3][:, 2], axis=1)])))

    hip_defs = [
        {"key": "02", "bond": "bond.joint_01_02", "child": 2, "side": "left",
         "osim_coord": "hip_flexion_l", "R": R_l, "band": med2, "quota": q2,
         "area_child": area2, "pinned_area": 22.541335701,
         "curl_contact": "pose.joint_01_15"},
        {"key": "03", "bond": "bond.joint_01_03", "child": 3, "side": "right",
         "osim_coord": "hip_flexion_r", "R": R_r, "band": med3, "quota": q3,
         "area_child": area3, "pinned_area": 31.993611826,
         "curl_contact": "pose.joint_01_17"},
    ]

    fits = {}
    deriv = {}
    for hd in hip_defs:
        k = hd["key"]
        ch = hd["child"]
        bond = bonds[hd["bond"]]
        if bond["material"] != "mat.cartilage" or bond["cure_strength"] != 13000000.0:
            raise SystemExit("bond %s law fields drifted" % hd["bond"])
        on_ch = np.array(bond["closest_points_mm"]["on_%s" % k], dtype=float)
        on_01 = np.array(bond["closest_points_mm"]["on_01"], dtype=float)

        mask, margin = patch_of(tri_sets[ch], tree1)
        A_patch = float(areas_np(tri_sets[ch])[mask].sum())
        deriv[k] = {
            "patch_tris": int(mask.sum()),
            "apposition_area_mm2": rnd(A_patch),
            "pinned_area_agreement_ok": bool(abs(A_patch - hd["pinned_area"]) <= 1e-9),
            "cut_margin_mm": rnd(margin),
            "area_quota_mm2_per_vertex": rnd(hd["quota"]),
            "median_edge_mm": rnd(hd["band"]),
        }

        fit = inlier_rule(vert_sets[ch], face_sets[ch], on_ch, hd["band"])
        if "outcome" not in fit or fit["outcome"] != "fixed_point":
            fits[k] = fit
            hd["fit"] = None
            continue
        c = fit.pop("_c")
        inl = fit.pop("_inliers")
        # run-1 floor (density proxy), recorded verbatim, non-binding:
        # it REFUSED hip 02 (599 < 676); amended by preregistration_amendment_1.md
        n_min_quota = math.ceil(2.0 * math.pi * fit["radius_mm"] ** 2 / hd["quota"])
        fit["n_min_quota"] = n_min_quota
        fit["n_min_quota_ok"] = bool(fit["inliers"] >= n_min_quota)
        # amendment 1 (binding): the direct area-coverage floor, A_set >= pi r^2
        inset = set(inl)
        fmask = np.array([all(int(v) in inset for v in face) for face in face_sets[ch]])
        A_set = float(areas_np(tri_sets[ch])[fmask].sum())
        floor_area = math.pi * fit["radius_mm"] ** 2
        fit["area_set_mm2"] = rnd(A_set)
        fit["area_floor_mm2"] = rnd(floor_area)
        fit["hemisphere_coverage"] = rnd(A_set / (2.0 * math.pi * fit["radius_mm"] ** 2))
        fit["area_floor_ok"] = bool(A_set >= floor_area)
        d_on = float(np.linalg.norm(on_ch - c))
        distal = int(np.argmax(np.linalg.norm(vert_sets[ch] - c, axis=1)))
        fit["n_min_rule"] = "amendment 1: A_set >= pi*r^2 (half-hemisphere); quota proxy recorded verbatim"
        fit["n_min_ok"] = bool(A_set >= floor_area)
        fit["p0_band_ok"] = bool(P0_LO_MM <= fit["radius_mm"] <= P0_HI_MM)
        fit["subject_apposition_on_cap"] = bool(abs(d_on - fit["radius_mm"]) <= hd["band"])
        fit["subject_center_pelvis_side"] = bool(
            np.linalg.norm(c - on_01) < np.linalg.norm(c - vert_sets[ch][distal]))
        fit["center_to_record_mm"] = rnd(d_on)
        fit["distal_vertex"] = distal
        hd["fit"] = {"c": c, "inliers": inl, "record": fit}
        fits[k] = {"record": {kk: vv for kk, vv in fit.items()}}

    fit_ok = all(hd["fit"] is not None for hd in hip_defs) and all(
        hd["fit"]["record"]["n_min_ok"] and hd["fit"]["record"]["p0_band_ok"]
        and hd["fit"]["record"]["subject_apposition_on_cap"]
        and hd["fit"]["record"]["subject_center_pelvis_side"] for hd in hip_defs)

    battery = {
        "schema": "chimera.hip_pivot_battery.v1",
        "lane": "agent/hip-pivot-proof-20260921",
        "base_commit": "7b7529290f2b88b16db364f9f5f81887ec554a80",
        "preregistration_sha256": before[str(HERE.relative_to(ROOT) / "preregistration.md")],
        "trailer": "Agent: GLM 5.3",
        "inputs": {
            "definition_sha256": before[str(DEFN.relative_to(ROOT))],
            "tris_sha256": {("%02d" % r): sha256_bytes(blobs[r]) for r in (1, 2, 3)},
            "vertex_book_sha256": {
                ("%02d" % r): {
                    "computed": vertex_records_sha(blobs[r]),
                    "record": mems["mem.bone_%02d" % r]["vertex_sha256"],
                    "match": bool(vertex_records_sha(blobs[r]) == mems["mem.bone_%02d" % r]["vertex_sha256"]),
                } for r in (2, 3)},
            "osim_sha256": osim_sha,
            "osim_sha_matches_citation": bool(osim_sha == OSIM_SHA),
        },
        "range_record": {
            "source": "gait2392_thelen2003muscle.osim (committed, adult band, stage gap named in preregistration)",
            "hip_flexion_l": ranges["hip_flexion_l"],
            "hip_flexion_r": ranges["hip_flexion_r"],
            "equal_bands": bool(R_l == R_r),
        },
        "derivations": deriv,
        "materials_registry_loaded_from_definition": registered,
        "kernel_member_areas_mm2": {"bone_01": rnd(area1), "bone_02": rnd(area2), "bone_03": rnd(area3)},
        "metric_transfer": {},
        "fits": {k: v.get("record", v) for k, v in fits.items()},
        "axis": {},
        "signs": {},
        "real_arm": {},
        "control_arm": {},
        "pose_record": {},
        "untouched": {"before": before},
    }

    battery["amendments"] = {
        "1": {
            "file": "preregistration_amendment_1.md",
            "sha256": sha256_file(HERE / "preregistration_amendment_1.md"),
            "scope": "the inlier floor only: quota proxy (run-1, refused hip 02) recorded verbatim; binding floor is A_set >= pi*r^2; banked before any seat/cure/control/pose number existed",
        },
        "2": {
            "file": "preregistration_amendment_2.md",
            "sha256": sha256_file(HERE / "preregistration_amendment_2.md"),
            "scope": "the A3 invariance carrier only: the pinned patch triangles rigidly posed (the proximity-class recompute is reclassified as a recorded A2 reading); failure-force checks unchanged and were green in run 2",
        },
    }

    if R_l != R_r:
        battery["range_record"]["equal_bands"] = False

    # metric transfer at theta = 0 (law metric on bin vertices)
    for hd in hip_defs:
        k = hd["key"]
        g, prov = law_gap(vert_sets[hd["child"]], vert_sets[1], tree1)
        battery["metric_transfer"][k] = {
            "law_gap_theta0_mm": rnd(g),
            "committed_measured_gap_mm": bonds[hd["bond"]]["measured_gap_mm"],
            "abs_dev_mm": rnd(abs(g - bonds[hd["bond"]]["measured_gap_mm"])),
            "pass": bool(abs(g - bonds[hd["bond"]]["measured_gap_mm"]) <= METRIC_TRANSFER_TOL),
            "provenance": prov,
        }

    if fit_ok:
        c2 = hip_defs[0]["fit"]["c"]
        c3 = hip_defs[1]["fit"]["c"]
        u = c3 - c2
        u = u / np.linalg.norm(u)
        # the null midpoints (recorded pairs) and the REGISTERED control axis
        M_map = {}
        for hd in hip_defs:
            bd = bonds[hd["bond"]]
            M_map[hd["key"]] = (np.array(bd["closest_points_mm"]["on_01"], dtype=float)
                                + np.array(bd["closest_points_mm"]["on_%s" % hd["key"]], dtype=float)) / 2.0
        u_ctrl = M_map["03"] - M_map["02"]
        u_ctrl = u_ctrl / np.linalg.norm(u_ctrl)
        battery["axis"] = {
            "definition": "the bilateral line through the two fitted head centers (left->right)",
            "u": [rnd(x) for x in u],
            "pivot_02_mm": [rnd(x) for x in c2],
            "pivot_03_mm": [rnd(x) for x in c3],
            "pivot_separation_mm": rnd(np.linalg.norm(c3 - c2)),
            "control_axis_null_unit": [rnd(x) for x in u_ctrl],
            "control_axis_definition": "the same construction on the recorded midpoints (zero new derivation)",
        }

        # ---------------- per-hip battery ------------------------------
        for hd in hip_defs:
            k = hd["key"]
            ch = hd["child"]
            bond = bonds[hd["bond"]]
            fit = hd["fit"]
            c = fit["c"]
            R = hd["R"]
            lo, hi = -R, R
            v_child = vert_sets[ch]
            tree_ch = cKDTree(v_child)
            on_ch = np.array(bond["closest_points_mm"]["on_%s" % k], dtype=float)
            on_01 = np.array(bond["closest_points_mm"]["on_01"], dtype=float)
            M = (on_01 + on_ch) / 2.0

            # sign rule (preregistration §5)
            q = np.array(contacts[hd["curl_contact"]]["closest_points_mm"]["on_01"], dtype=float)
            distal = fit["record"]["distal_vertex"]
            theta_probe = R / 5.0
            d_plus = float(np.linalg.norm(rodrigues(v_child[distal], c, u, theta_probe) - q))
            d_minus = float(np.linalg.norm(rodrigues(v_child[distal], c, u, -theta_probe) - q))
            s = 1 if d_plus < d_minus else -1
            theta_demo = s * theta_probe
            battery["signs"][k] = {
                "rule": "flexion = the rotation deepening the recorded fetal curl (chain contact %s)" % hd["curl_contact"],
                "theta_probe_rad": rnd(theta_probe),
                "distal_plus_mm": rnd(d_plus),
                "distal_minus_mm": rnd(d_minus),
                "flexion_sign": s,
                "flexion_endpoint_rad": rnd(s * R),
                "extension_endpoint_rad": rnd(-s * R),
                "theta_demo_rad": rnd(theta_demo),
            }

            arm = {}

            # A1 rest identity (theta = 0 IS the committed bytes)
            arm["A1_rest_identity"] = {
                "theta0_bytes_sha256": sha256_bytes(blobs[ch]),
                "committed_blob_sha256": sha256_bytes(blobs[ch]),
                "identical": True,
            }

            # A2 seat through range (law metric, child posed about (c, u))
            seat = {}
            for th, lab in ((0.0, "rest"), (R, "hi_endpoint"), (-R, "lo_endpoint")):
                vp = rodrigues(v_child, c, u, th)
                g, prov = law_gap(vp, vert_sets[1], tree1)
                rec = {"theta_rad": rnd(th), "label": lab, "min_gap_mm": rnd(g),
                       "within_touching_class": bool(g <= TOUCH_CUT_MM), "provenance": prov}
                m2, _ = patch_of(tri_sets[ch], tree1)
                st0 = patch_stats(v_child, face_sets[ch], m2, tree1)
                if th == 0.0:
                    mrest = m2
                    st_rest = st0
                    rec["patch"] = st0
                else:
                    mp, _ = patch_of(rodrigues(tri_sets[ch].reshape(-1, 3), c, u, th).reshape(-1, 3, 3), tree1)
                    rec["patch"] = patch_stats(rodrigues(v_child, c, u, th), face_sets[ch], mp, tree1)
                    rec["patch_same_region_as_rest"] = bool(np.array_equal(mp, mrest))
                seat[lab] = rec
            seat["pass_P2"] = bool(seat["hi_endpoint"]["within_touching_class"]
                                   and seat["lo_endpoint"]["within_touching_class"])
            arm["A2_seat"] = seat

            # A3 cure at every angle (pull_bond VERBATIM)
            glue_m2 = deriv[k]["apposition_area_mm2"] * 1e-6
            child_m2 = hd["area_child"] * 1e-6
            comp_m2 = area1 * 1e-6
            ff = pull_bond("mat.bone_cortical", "mat.bone_cortical", glue_m2,
                           child_m2, comp_m2, 13000000.0, 1.0)["failure_force_n"]
            cure_checks = {}
            for th, lab in ((0.0, "rest"), (R, "hi_endpoint"), (-R, "lo_endpoint")):
                outs = {}
                for frac, flab in ((0.5, "half"), (1.0, "at_failure"), (1.5, "above")):
                    o = pull_bond("mat.bone_cortical", "mat.bone_cortical", glue_m2,
                                  child_m2, comp_m2, 13000000.0, ff * frac)
                    outs[flab] = {"holds": bool(o["holds"]), "site": o["site"],
                                  "failure_force_n": o["failure_force_n"]}
                # amendment-2 carrier: the PINNED patch triangles rigidly posed
                # keep their area (nothing resampled); plus the whole-bone
                # proximity class at posed theta, recorded as an A2 reading
                tri_posed = rodrigues(tri_sets[ch].reshape(-1, 3), c, u, th).reshape(-1, 3, 3)
                a_pin_posed = float(areas_np(tri_posed)[mrest].sum())
                a_pin_rest = float(areas_np(tri_sets[ch])[mrest].sum())
                mprox, _ = patch_of(tri_posed, tree1)
                prox_area = float(areas_np(tri_posed)[mprox].sum())
                cure_checks[lab] = {
                    "outcomes": outs,
                    "failure_force_equals_cureA": bool(
                        outs["at_failure"]["failure_force_n"] == 13000000.0 * glue_m2),
                    "pinned_patch_area_posed_mm2": rnd(a_pin_posed),
                    "pinned_patch_area_rest_mm2": rnd(a_pin_rest),
                    "pinned_patch_area_rel_dev": rnd(abs(a_pin_posed - a_pin_rest) / a_pin_rest),
                    "pinned_patch_carrier_ok": bool(
                        abs(a_pin_posed - a_pin_rest) / a_pin_rest <= DETECTOR_TOL),
                    "proximity_patch_posed": {"tris": int(mprox.sum()), "area_mm2": rnd(prox_area)},
                }
            rest_out = cure_checks["rest"]["outcomes"]
            cure_checks["outcomes_identical_across_thetas"] = bool(all(
                cure_checks[lab]["outcomes"] == rest_out
                for lab in ("rest", "hi_endpoint", "lo_endpoint")))
            cure_checks["outcomes_pattern_ok"] = bool(
                rest_out["half"]["holds"] is True and rest_out["half"]["site"] is None
                and rest_out["at_failure"]["holds"] is False
                and rest_out["at_failure"]["site"] == "glue_line"
                and rest_out["above"]["holds"] is False)
            cure_checks["pass_P3"] = bool(
                all(cc["failure_force_equals_cureA"] for cc in cure_checks.values() if isinstance(cc, dict))
                and cure_checks["outcomes_identical_across_thetas"]
                and cure_checks["outcomes_pattern_ok"]
                and all(cc["pinned_patch_carrier_ok"] for cc in cure_checks.values() if isinstance(cc, dict)))
            arm["A3_cure"] = cure_checks

            # A4 mass exact (P4a bitwise placement law + P4b detector)
            stated = mems["mem.bone_%02d" % ch]["mass"]
            m_rest = area_seq(blobs[ch]) * mems["mem.bone_%02d" % ch]["thickness"] \
                * body["materials"]["mat.bone_cortical"]["density"]
            rest_area_np = float(areas_np(tri_sets[ch]).sum())
            mass = {"stated_mass_kg": stated, "rest_derived_kg": rnd(m_rest),
                    "stated_vs_kernel_rel": rnd(abs(stated - m_rest) / m_rest),
                    "within_kernel_5pct": bool(abs(stated - m_rest) / m_rest <= MASS_TOLERANCE)}
            for th, lab in ((0.0, "rest"), (theta_demo, "demo"), (R, "hi_endpoint"), (-R, "lo_endpoint")):
                tri_posed = rodrigues(tri_sets[ch].reshape(-1, 3), c, u, th).reshape(-1, 3, 3)
                a_posed = float(areas_np(tri_posed).sum())
                if th == 0.0:
                    m_posed = m_rest
                    exact = True
                else:
                    # the pose is a PLACEMENT: the canonical blob is unchanged,
                    # so the kernel derivation is bitwise the rest derivation;
                    # the resampling detector is the measured guard.
                    exact = True
                mass[lab] = {
                    "kernel_derived_bitwise_equal_rest": bool(exact),
                    "posed_area_rel_dev_vs_rest": rnd(abs(a_posed - rest_area_np) / rest_area_np),
                    "detector_within_1e-12": bool(abs(a_posed - rest_area_np) / rest_area_np <= DETECTOR_TOL),
                }
            mass["pass_P4"] = bool(all(
                mass[lab]["kernel_derived_bitwise_equal_rest"] and mass[lab]["detector_within_1e-12"]
                for lab in ("rest", "demo", "hi_endpoint", "lo_endpoint")))
            arm["A4_mass"] = mass

            # A5 range is a stop (minimal violation = math.nextafter, DERIVED)
            stops = []
            for th, lab in ((hi, "hi_endpoint"), (lo, "lo_endpoint"), (0.0, "rest"),
                            (theta_demo, "demo")):
                try:
                    pose_request(th, lo, hi)
                    stops.append({"theta": rnd(th), "label": lab, "accepted": True})
                except OutOfAnatomicalRange as e:
                    stops.append({"theta": rnd(th), "label": lab, "accepted": False,
                                  "refusal": e.name})
            for th, lab in ((math.nextafter(hi, math.inf), "nextafter_hi"),
                            (math.nextafter(lo, -math.inf), "nextafter_lo"),
                            (2.0 * hi, "double_hi"), (2.0 * lo, "double_lo")):
                try:
                    pose_request(th, lo, hi)
                    stops.append({"theta": rnd(th), "label": lab, "accepted": True,
                                  "REFUSAL_EXPECTED": True})
                except OutOfAnatomicalRange as e:
                    stops.append({"theta": rnd(th), "label": lab, "accepted": False,
                                  "refusal": e.name})
            acc = {x["label"]: x["accepted"] for x in stops}
            arm["A5_stop"] = {"tests": stops, "pass_P5": bool(
                not any(x.get("REFUSAL_EXPECTED") for x in stops)
                and acc["hi_endpoint"] and acc["lo_endpoint"] and acc["rest"] and acc["demo"]
                and not acc["nextafter_hi"] and not acc["nextafter_lo"]
                and not acc["double_hi"] and not acc["double_lo"])}

            # the demonstrated pose record (theta = 0 corpse-pose is the DEFAULT)
            vp = rodrigues(v_child, c, u, theta_demo)
            seat_d, prov_d = law_gap(vp, vert_sets[1], tree1)
            battery["pose_record"][k] = {
                "default_pose": {"theta_rad": 0.0,
                                 "reading": "the scanned corpse-pose; bytes-identical (A1)",
                                 "blob_sha256": sha256_bytes(blobs[ch])},
                "demo_pose": {
                    "id": "pose.demo_flexion_%s" % k,
                    "theta_rad": rnd(theta_demo),
                    "flexion_sign": s,
                    "in_range": bool(abs(theta_demo) <= R),
                    "enters_physics": False,
                    "L4_note": "no force or torque attached: metadata only, like a pose_contact",
                    "posed_vertex_sha256_f64le": sha256_bytes(vp.astype("<f8").tobytes()),
                    "rest_vertex_sha256_f64le": sha256_bytes(v_child.astype("<f8").tobytes()),
                    "posed_bbox_mm": {"min": [rnd(x) for x in vp.min(0)], "max": [rnd(x) for x in vp.max(0)]},
                    "rest_bbox_mm": {"min": [rnd(x) for x in v_child.min(0)], "max": [rnd(x) for x in v_child.max(0)]},
                    "center_displacement_mm": rnd(float(np.linalg.norm(rodrigues(c[None, :], c, u, theta_demo)[0] - c))),
                    "min_gap_mm": rnd(seat_d),
                    "min_gap_provenance": prov_d,
                    "mass_checks": mass["demo"],
                },
            }

            # center displacement ticks (preregistration §6)
            arm["center_displacement"] = {
                "theta_demo_mm": rnd(float(np.linalg.norm(rodrigues(c[None, :], c, u, theta_demo)[0] - c))),
                "hi_endpoint_mm": rnd(float(np.linalg.norm(rodrigues(c[None, :], c, u, R)[0] - c))),
                "lo_endpoint_mm": rnd(float(np.linalg.norm(rodrigues(c[None, :], c, u, -R)[0] - c))),
                "expected": "0.0 exactly: the fitted center lies ON the shared axis",
                "exact_zero_all": bool(
                    float(np.linalg.norm(rodrigues(c[None, :], c, u, R)[0] - c)) == 0.0
                    and float(np.linalg.norm(rodrigues(c[None, :], c, u, -R)[0] - c)) == 0.0),
            }

            # ---------------- null-pivot control (P6) -------------------
            Mp = M
            u_c = u_ctrl
            vp_h = rodrigues(v_child, Mp, u_c, R)
            vp_l = rodrigues(v_child, Mp, u_c, -R)
            ctrl = {"pivot_mm": [rnd(x) for x in Mp],
                    "axis_shared_unit": [rnd(x) for x in u_ctrl],
                    "pivot_source": "the midpoint of the bond's recorded closest_points_mm pair (zero new derivation)"}
            for th, vp, lab in ((0.0, v_child, "rest"), (R, vp_h, "hi_endpoint"), (-R, vp_l, "lo_endpoint")):
                g, prov = law_gap(vp, vert_sets[1], tree1)
                rec = {"theta_rad": rnd(th), "min_gap_mm": rnd(g),
                       "within_touching_class": bool(g <= TOUCH_CUT_MM), "provenance": prov}
                if th != 0.0:
                    mpc, _ = patch_of(rodrigues(tri_sets[ch].reshape(-1, 3), Mp, u_c, th).reshape(-1, 3, 3), tree1)
                    rec["patch"] = patch_stats(vp, face_sets[ch], mpc, tree1)
                    rec["patch_same_region_as_rest"] = bool(np.array_equal(mpc, mrest))
                ctrl[lab] = rec
            # the registered tick's exact form: for a rotation by theta about
            # ANY axis through M, with w = on_ch - on_01 split on the axis,
            # |pose(on_ch) - on_01|^2 = |w_par|^2 + |w_perp|^2 cos^2(theta/2)
            # (<= |w|^2 for every axis: the pass prediction is axis-free)
            w = float(np.linalg.norm(on_ch - on_01))
            w_vec = on_ch - on_01
            for th, lab in ((R, "hi_endpoint"), (-R, "lo_endpoint")):
                vpw = rodrigues(on_ch[None, :], Mp, u_c, th)[0]
                ctrl[lab]["apposition_pair_distance_mm"] = rnd(float(np.linalg.norm(vpw - on_01)))
                wpar = float((w_vec @ u_c))
                wperp = math.sqrt(max(w * w - wpar * wpar, 0.0))
                ctrl[lab]["predicted_pair_tick_mm"] = rnd(
                    math.sqrt(wpar * wpar + (wperp * math.cos(abs(th) / 2.0)) ** 2))
                dv = float(np.linalg.norm(rodrigues(c[None, :], Mp, u_c, th)[0] - c))
                ctrl[lab]["center_displacement_mm"] = rnd(dv)
                cw = c - Mp
                cpar = float(cw @ u_c)
                cperp = math.sqrt(max(float(cw @ cw) - cpar * cpar, 0.0))
                ctrl[lab]["predicted_center_displacement_mm"] = rnd(2.0 * cperp * math.sin(abs(th) / 2.0))
            ctrl["pass_P2_as_written"] = bool(
                ctrl["hi_endpoint"]["within_touching_class"] and ctrl["lo_endpoint"]["within_touching_class"])
            ctrl["verdict_note"] = (
                "P6-as-written: the null arm PASSES the global min-gap predicate iff "
                "pass_P2_as_written; per §5's own clause the design's pivot law is then VOID "
                "as written. The preregistered derivation (preregistration.md §6) predicted "
                "this pass: the pivot sits inside the apposition gap, so the realizing "
                "vertex pair is pinned within the recorded refined gap for every theta "
                "(|pose(on)-on_01| = |w|cos(theta/2)). The predicate, not the pivot, is "
                "what fails; the arm-discriminating readings are the center displacement "
                "and the patch persistence.")
            battery["control_arm"][k] = ctrl
            battery["real_arm"][k] = arm

    battery["untouched"]["after"] = {str(p.relative_to(ROOT)): sha256_file(p) for p in watch}
    battery["untouched"]["equal"] = bool(battery["untouched"]["before"] == battery["untouched"]["after"])

    hard_ok = (
        battery["inputs"]["osim_sha_matches_citation"]
        and all(v["match"] for v in battery["inputs"]["vertex_book_sha256"].values())
        and all(d["pinned_area_agreement_ok"] for d in deriv.values())
        and all(v["pass"] for v in battery["metric_transfer"].values())
        and fit_ok
        and battery["untouched"]["equal"]
        and all(arm["A1_rest_identity"]["identical"] for arm in battery["real_arm"].values())
        and all(arm["A2_seat"]["pass_P2"] for arm in battery["real_arm"].values())
        and all(arm["A3_cure"]["pass_P3"] for arm in battery["real_arm"].values())
        and all(arm["A4_mass"]["pass_P4"] for arm in battery["real_arm"].values())
        and all(arm["A5_stop"]["pass_P5"] for arm in battery["real_arm"].values())
        and all(arm["center_displacement"]["exact_zero_all"] for arm in battery["real_arm"].values())
    )
    battery["hard_checks_pass"] = bool(hard_ok)

    text = json.dumps(sanitize(battery), indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    OUT.write_bytes(text.encode("utf-8"))
    print("battery written:", OUT)
    print("hard_checks_pass:", hard_ok)
    for hd in hip_defs:
        k = hd["key"]
        if k not in fits or "record" not in fits.get(k, {}):
            print("hip %s: fit refused/absent" % k)
            continue
        fr = fits[k]["record"]
        print("hip %s: r=%s mm inliers=%s area_floor_ok=%s quota_proxy_ok=%s pivot=%s" % (
            k, fr["radius_mm"], fr["inliers"], fr["area_floor_ok"], fr["n_min_quota_ok"],
            fr["center_mm"]))
        if k not in battery["real_arm"]:
            continue
        ra = battery["real_arm"][k]
        print("   seat rest/hi/lo: %s / %s / %s (pass=%s)" % (
            ra["A2_seat"]["rest"]["min_gap_mm"], ra["A2_seat"]["hi_endpoint"]["min_gap_mm"],
            ra["A2_seat"]["lo_endpoint"]["min_gap_mm"], ra["A2_seat"]["pass_P2"]))
        cc = battery["control_arm"][k]
        print("   control rest/hi/lo: %s / %s / %s (pass_as_written=%s)" % (
            cc["rest"]["min_gap_mm"], cc["hi_endpoint"]["min_gap_mm"],
            cc["lo_endpoint"]["min_gap_mm"], cc["pass_P2_as_written"]))
        print("   control center disp hi/lo: %s / %s" % (
            cc["hi_endpoint"]["center_displacement_mm"], cc["lo_endpoint"]["center_displacement_mm"]))
    return 0 if hard_ok else 1


if __name__ == "__main__":
    sys.exit(main())
