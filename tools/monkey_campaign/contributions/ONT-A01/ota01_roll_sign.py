"""ONT-A01 task-owned verifier: ulna volar-side roll sign, re-measured from pins.

Reconciliation-first card: the roll sign was already resolved by the O1 audit
(play lane `forearm-package-20260924` commit c3255f74, receipts shipped under
reference/o1_receipts/). This module RE-MEASURES the three frozen predictions
(P1 source bone, P2 target olecranon test, P3 sign law) from the pinned inputs,
cross-checks every number against the pinned receipts (N4), and emits
  evidence/state_snapshot.json   (input identities + measured state)
  evidence/numerical_receipt.json (measured vs receipt, verdicts, outcome)
Outcome is decided by the FROZEN rules in PREREGISTRATION.md: SIGN_DETERMINED or
AMBIGUITY_RECORDED. Nothing is tuned; falsifier hits are reported as they fall.

Method identity: the section machinery in this file is carried over VERBATIM from
the pinned O1 script reference/o1_source_split.py's sibling
o1_target_sections_directed.py (exact triangle-plane sections, C3-S2 method,
5-deg directed bins); method identity is then ASSERTED by comparing the
recomputed axis/basis to the pinned receipt before any verdict.

CPU-only, deterministic, no GPU, no network, no randomness except the pinned
seed-0 bootstrap reproduced from the record. Run with `python -B`.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / "reference"
RECEIPTS = REFERENCE / "o1_receipts"
EVIDENCE = HERE / "evidence"

# Pinned read-only inputs (identities verified against O1's frozen EXPECT_SHA).
INPUT_BIRTH = Path(r"E:/PythonChimera/Saved/meshes/monkey_birth.bin")
INPUT_PACK = Path(r"E:/PythonChimera/Saved/meshes/monkey_joints.bin")
INPUT_ULNA_STL = Path(r"E:/PythonChimera/vendor/myo_sim/meshes/ulna.stl")
PINS = {
    "play_repo_forearm_package_lane": "forearm-package-20260924",
    "o1_integrated_commit": "c3255f74",
    "game_lineage_master": "33e7a444",
    "ont_p02_lineage_map_commit": "8c7ed8c2",
}
EXPECT_SHA = {  # frozen inside O1's o1_target_sections_directed.py
    "birth": "550a5b3ec927ea13614ad250963b23e2948e76a238ac110da9889f339aabfa3c",
    "pack": "74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662",
}

# FROZEN tolerances (PREREGISTRATION.md; frozen before any probe ran).
TOL_MESH_MM = 0.5      # P1: olecranon x, distal y
TOL_D_MM = 0.75        # P2: D(t=+6 mm) vs receipt 3.29
TOL_ZONE_MM = 0.0      # P2: zone stations must keep D > 2 exactly (integer mm flag)
TOL_AZ_DEG = 1.0       # P3: azimuth agreement (TRIlat-P5 no-flip error ~0.15)

# Frozen anatomy label sets (O1 method (a); external-cited compartments).
ULNA_SITES = ["TRIlong-P5", "TRIlat-P5", "TRImed-P5", "ANC-P2", "BRA-P4",
              "BRA-P3", "ECU-P2", "ECU-P3", "ECU-P4", "PT-P2"]
FLEXORS = {"BRA-P4", "BRA-P3", "PT-P2"}                    # volar
EXTENSORS = set(ULNA_SITES) - FLEXORS                      # dorsal
ROLL_CANDIDATES = ["ECU-P2", "ANC-P2", "TRIlat-P5"]        # C3 sec.2.5 declared set
RENDER_SITES = ["TRIlat-P5", "ANC-P2", "BRA-P4", "BRA-P3", "PT-P2", "ECU-P2"]
ECU_COURSE = ["ECU-P2", "ECU-P3", "ECU-P4"]

STATIONS_MM = [-8, -5, -2, 0, 2, 4, 6, 8, 10, 12, 16, 20, 30, 48]
DELTA = 30.0
BIN = 5.0
XHAT = np.array([1.0, 0.0, 0.0])
ZAX = np.array([0.0, 0.0, 1.0])


def unit(v):
    return v / np.linalg.norm(v)


def wrap180(a):
    return (a + 180.0) % 360.0 - 180.0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- P1: STL ----
def load_binary_stl(path: Path):
    """Binary STL -> (V, F, normals). ulna.stl: 84 + n*50 bytes (O1: 396 tris)."""
    b = path.read_bytes()
    (n,) = struct.unpack("<I", b[80:84])
    assert len(b) == 84 + n * 50, (path, n, len(b))
    rec = np.frombuffer(b, dtype=np.uint8, count=n * 50, offset=84).reshape(n, 50)
    floats = rec[:, :48].copy().view("<f4").reshape(n, 4, 3)
    normals = floats[:, 0].astype(np.float64)
    tris = floats[:, 1:].astype(np.float64)
    verts, inv = np.unique(tris.reshape(-1, 3), axis=0, return_inverse=True)
    faces = inv.reshape(n, 3)
    return verts, faces.astype(np.int64), normals


def ulna_mesh_scaled():
    """chimanoid.xml:853 declares scale '1 1.2 1'; geom at the ulna body origin."""
    V, F, N = load_binary_stl(INPUT_ULNA_STL)
    scale = np.array([1.0, 1.2, 1.0])
    return V * scale, F, N


# ------------------------------------------------- source frame from XML ----
def quat_rotmat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def source_frame():
    """Rest-frame bodies/sites from the pinned chimanoid.xml (O1 method, verbatim walk)."""
    root = ET.parse(str(REFERENCE / "chimanoid.xml")).getroot()
    bodies, sites = {}, {}

    def walk(elem, parent_world, parent_rot):
        name = elem.get("name")
        pos = np.array([float(v) for v in (elem.get("pos") or "0 0 0").split()])
        quat = np.array([float(v) for v in (elem.get("quat") or "1 0 0 0").split()])
        rot = parent_rot @ quat_rotmat(quat)
        world = parent_world + parent_rot @ pos
        bodies[name] = {"world": world, "rot": rot, "quat": quat}
        for s in elem.findall("site"):
            sites[s.get("name")] = {
                "body": name,
                "pos_local": np.array([float(v) for v in (s.get("pos") or "0 0 0").split()]),
            }
        for child in elem.findall("body"):
            walk(child, world, rot)

    wb = root.find("worldbody")
    for b in wb.findall("body"):
        walk(b, np.zeros(3), np.eye(3))
    chain = ["humerus", "ulna", "radius", "hand_r"]
    assert all(np.allclose(bodies[n]["quat"], [1, 0, 0, 0]) for n in chain), \
        "rest-frame axis-aligned assertion (O1 method precondition) failed"
    return bodies, sites


# ------------------------------------- P2 sections: O1 method, carried over ----
def transverse_basis(a):
    e1 = XHAT - a * (a @ XHAT)
    if np.linalg.norm(e1) < 1e-9:
        e1 = ZAX - a * (a @ ZAX)
    e1 = unit(e1)
    e2 = np.cross(a, e1)
    return e1, e2


def load_birth_pack():
    sys.path.insert(0, str(REFERENCE))
    from mesh_target_o1 import MonkeyTarget  # hash-pinned copy of O1's loader
    mt = MonkeyTarget(birth_path=str(INPUT_BIRTH), pack_path=str(INPUT_PACK))
    assert mt.birth_sha.lower() == EXPECT_SHA["birth"], mt.birth_sha
    assert mt.pack_sha.lower() == EXPECT_SHA["pack"], mt.pack_sha
    return mt


def section_points(V, F, origin, a, t, rmax=0.045):
    """Exact triangle-plane intersection segment endpoints within rmax of the axis
    line (carried over VERBATIM from O1 o1_target_sections_directed.py / C3-S2)."""
    n = V @ a - (t + origin @ a)
    tri = n[F]
    sign = np.signbit(tri)
    has_cross = ~(sign.all(axis=1) | (~sign).all(axis=1))
    tris = F[has_cross]
    d3 = n[tris]
    pts = []
    for k in range(len(tris)):
        dd = d3[k]
        ids = tris[k]
        pairs = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if dd[i] == 0.0 or (dd[i] > 0) != (dd[j] > 0):
                pairs.append((i, j))
        for i, j in pairs:
            if dd[i] == dd[j]:
                continue
            w = dd[i] / (dd[i] - dd[j])
            p = V[ids[i]] + w * (V[ids[j]] - V[ids[i]])
            if np.linalg.norm(p - (origin + a * t)) <= rmax:
                pts.append(p)
    return np.array(pts)


def directed_profile(pts, cplane, e1, e2, bin_deg=BIN):
    rel = pts - cplane
    r1, r2 = rel @ e1, rel @ e2
    psi = np.degrees(np.arctan2(r2, r1))
    rho = np.hypot(r1, r2) * 1000.0
    nb = int(round(360.0 / bin_deg))
    prof = np.full(nb, np.nan)
    for k in range(nb):
        lo = -180.0 + k * bin_deg
        m = ((psi - lo) % 360.0) < bin_deg
        if m.any():
            prof[k] = rho[m].max()
    return prof, psi, rho


def sector_max(prof, center_az, delta=DELTA):
    az_centers = np.array([-180.0 + (k + 0.5) * BIN for k in range(len(prof))])
    d = np.abs((az_centers - center_az + 180.0) % 360.0 - 180.0)
    m = (d <= delta) & ~np.isnan(prof)
    return float(np.nanmax(prof[m])) if m.any() else None


def station_stats(pts, origin, a, t, e1, e2, boot=0, seed=0):
    """Directed section stats; bootstrap (seed 0) reproduced only for the best
    station, matching the record's noise floor."""
    if len(pts) < 8:
        return {"t_mm": t * 1000.0, "n": int(len(pts)), "usable": False}
    cplane = origin + a * t
    prof, psi, rho = directed_profile(pts, cplane, e1, e2)
    post = sector_max(prof, -90.0)
    ant = sector_max(prof, +90.0)
    D = post - ant
    out = {
        "t_mm": t * 1000.0, "n": int(len(pts)), "usable": True,
        "rho_post_max_mm": post, "rho_ant_max_mm": ant,
        "D_post_minus_ant_mm": float(D),
        "D_above_2mm": bool(D > 2.0),
    }
    if boot:
        rng = np.random.default_rng(seed)
        az_centers = np.array([-180.0 + (k + 0.5) * BIN for k in range(len(prof))])
        Ds = []
        for _ in range(boot):
            idx = rng.integers(0, len(rho), len(rho))
            pb, ab = [], []
            for azc, acc in ((-90.0, pb), (90.0, ab)):
                dd = np.abs((psi[idx] - azc + 180.0) % 360.0 - 180.0)
                m = dd <= DELTA
                if m.any():
                    acc.append(float(rho[idx][m].max()))
            if pb and ab:
                Ds.append(max(pb) - max(ab))
        Ds = np.array(Ds)
        out["boot_D_std_mm"] = float(Ds.std())
    return out


def measure_target_sections(mt):
    """Re-run the directed olecranon test on the R (U-STR) side."""
    e = mt.joint_pos("elbow_R")
    w = mt.joint_pos("wrist_R")
    a = unit(w - e)
    e1, e2 = transverse_basis(a)
    rows = []
    for tmm in STATIONS_MM:
        pts = section_points(mt.V, mt.F, e, a, tmm / 1000.0)
        st = station_stats(pts, e, a, tmm / 1000.0, e1, e2,
                           boot=200 if tmm == 6 else 0)
        rows.append(st)
    return {"axis_unit": a.tolist(), "e1": e1.tolist(), "e2": e2.tolist(),
            "elbow_m": e.tolist(), "wrist_m": w.tolist(), "stations": rows}


# ------------------------------------------------------------- probes ------
def probe_p1():
    V, F, _ = ulna_mesh_scaled()
    return {
        "olecranon_min_x_mm": float(V[:, 0].min()) * 1000.0,
        "distal_min_y_mm": float(V[:, 1].min()) * 1000.0,
        "x_span_mm": [float(V[:, 0].min()) * 1000.0, float(V[:, 0].max()) * 1000.0],
        "y_span_mm": [float(V[:, 1].min()) * 1000.0, float(V[:, 1].max()) * 1000.0],
        "z_span_mm": [float(V[:, 2].min()) * 1000.0, float(V[:, 2].max()) * 1000.0],
        "n_tri": int(len(F)),
    }


def probe_p3():
    src = json.loads((RECEIPTS / "o1_source_split.json").read_text())
    cmb = json.loads((RECEIPTS / "o1_combine_sign.json").read_text())
    witness_az = cmb["inputs"]["witness_b_prime_azimuth_deg"]
    psi_v = cmb["inputs"]["target_volar_azimuth_deg"]
    rows = []
    for rc in ROLL_CANDIDATES:
        geo = src["ustr_frame"]["roll_candidates"][rc]
        alpha = geo["volar_azimuth_relative_to_b_deg"]
        phi = wrap180(witness_az + alpha)
        phi_flip = wrap180(phi + 180.0)
        e_no = abs(wrap180(phi - psi_v))
        e_flip = abs(wrap180(phi_flip - psi_v))
        rows.append({
            "roll_candidate": rc,
            "volar_az_relative_to_b_deg": alpha,
            "phi_no_flip_deg": phi,
            "phi_flip_deg": phi_flip,
            "error_no_flip_deg": e_no,
            "error_flip_deg": e_flip,
            "verdict": "NO-FLIP" if e_no < e_flip else "FLIP-REQUIRED",
        })
    law_residual = max(abs(wrap180(r["phi_no_flip_deg"] - psi_v)) for r in rows)
    return {
        "witness_b_prime_azimuth_deg": witness_az,
        "target_volar_azimuth_deg": psi_v,
        "per_candidate": rows,
        "unanimous_no_flip": len({r["verdict"] for r in rows}) == 1,
        "max_volar_law_residual_deg": law_residual,
        "law": "az_target = az_source + 90 deg (mod 360); source volar +x -> target volar +z",
    }


def build_state_and_receipt():
    inputs = {
        "birth": {"path": str(INPUT_BIRTH), "sha256": sha256_file(INPUT_BIRTH)},
        "pack": {"path": str(INPUT_PACK), "sha256": sha256_file(INPUT_PACK)},
        "ulna_stl": {"path": str(INPUT_ULNA_STL), "sha256": sha256_file(INPUT_ULNA_STL)},
    }
    assert inputs["birth"]["sha256"] == EXPECT_SHA["birth"]
    assert inputs["pack"]["sha256"] == EXPECT_SHA["pack"]

    receipt_mesh = json.loads((RECEIPTS / "o1_ulna_mesh_probe.json").read_text())
    receipt_sec = json.loads((RECEIPTS / "o1_target_sections_directed.json").read_text())
    receipt_src = json.loads((RECEIPTS / "o1_source_split.json").read_text())

    # P1 ---------------------------------------------------------------------
    p1 = probe_p1()
    r1x = receipt_mesh["mesh_extents_m"]["x"][0] * 1000.0
    r1y = receipt_mesh["mesh_extents_m"]["y"][0] * 1000.0
    p1["receipt_olecranon_min_x_mm"] = r1x
    p1["receipt_distal_min_y_mm"] = r1y
    p1["d_olecranon_mm"] = p1["olecranon_min_x_mm"] - r1x
    p1["d_distal_mm"] = p1["distal_min_y_mm"] - r1y
    p1["verdict"] = (abs(p1["d_olecranon_mm"]) <= TOL_MESH_MM
                     and abs(p1["d_distal_mm"]) <= TOL_MESH_MM)

    # P2 ---------------------------------------------------------------------
    mt = load_birth_pack()
    p2 = measure_target_sections(mt)
    rec_R = receipt_sec["sides"]["R"]
    # method identity: recomputed basis must equal the pinned receipt basis
    p2["axis_matches_receipt"] = bool(np.allclose(p2["axis_unit"], rec_R["axis_unit"], atol=1e-9))
    p2["e1_matches_receipt"] = bool(np.allclose(p2["e1"], rec_R["e1"], atol=1e-9))
    p2["e2_matches_receipt"] = bool(np.allclose(p2["e2"], rec_R["e2"], atol=1e-9))
    by_t = {round(r["t_mm"], 6): r for r in rec_R["stations"] if r.get("usable")}
    zone = []
    for r in p2["stations"]:
        rec = by_t.get(round(r["t_mm"], 6))
        if rec is None:
            continue
        r["receipt_D_mm"] = rec["D_post_minus_ant_mm"]
        r["d_D_mm"] = r["D_post_minus_ant_mm"] - rec["D_post_minus_ant_mm"]
    best = max((r for r in p2["stations"] if r.get("usable") and r["t_mm"] <= 16.0),
               key=lambda r: r["D_post_minus_ant_mm"])
    zone_rows = [r for r in p2["stations"]
                 if r.get("usable") and -2.0 <= r["t_mm"] <= 12.0]
    zone_ok = all(r["D_above_2mm"] for r in zone_rows)
    best_rec = receipt_sec["verdict"]["best_elbow_station"]
    p2["best_station"] = best
    p2["receipt_best_station"] = {k: best_rec[k] for k in
                                  ("t_mm", "rho_post_max_mm", "rho_ant_max_mm",
                                   "D_post_minus_ant_mm", "boot_D_std_mm")}
    p2["d_best_D_mm"] = best["D_post_minus_ant_mm"] - best_rec["D_post_minus_ant_mm"]
    p2["zone_rows"] = zone_rows
    p2["zone_all_above_2mm"] = zone_ok
    p2["verdict"] = (p2["axis_matches_receipt"] and p2["e1_matches_receipt"]
                     and p2["e2_matches_receipt"]
                     and abs(p2["d_best_D_mm"]) <= TOL_D_MM and zone_ok)

    # P3 ---------------------------------------------------------------------
    p3 = probe_p3()
    cmb = json.loads((RECEIPTS / "o1_combine_sign.json").read_text())
    by_rc = {r["roll_candidate"]: r for r in cmb["per_candidate"]}
    for r in p3["per_candidate"]:
        rec = by_rc[r["roll_candidate"]]
        r["receipt_error_no_flip_deg"] = rec["error_no_flip_deg"]
        r["receipt_error_flip_deg"] = rec["error_flip_deg"]
        r["d_err_no_flip_deg"] = r["error_no_flip_deg"] - rec["error_no_flip_deg"]
    trilat = next(r for r in p3["per_candidate"] if r["roll_candidate"] == "TRIlat-P5")
    p3["receipt_unanimous_no_flip"] = cmb["unanimous_verdict"]
    p3["trilat_no_flip_err_deg"] = trilat["error_no_flip_deg"]
    p3["verdict"] = (p3["unanimous_no_flip"] and cmb["unanimous_verdict"]
                     and all(r["error_no_flip_deg"] < r["error_flip_deg"]
                             for r in p3["per_candidate"])
                     and abs(p3["trilat_no_flip_err_deg"]) <= TOL_AZ_DEG
                     and all(abs(r["d_err_no_flip_deg"]) <= 1e-9 for r in p3["per_candidate"]))

    # Falsifier evaluation (frozen rules; both outcomes satisfy done_when) ----
    fired = []
    if not p1["verdict"]:
        fired.append("F1")
    if not (best["D_post_minus_ant_mm"] > 0 and zone_ok):
        fired.append("F2")
    if any(r["verdict"] == "FLIP-REQUIRED" for r in p3["per_candidate"]):
        fired.append("F3")
    agreement = p1["verdict"] and p2["verdict"] and p3["verdict"]
    if not agreement:
        fired.append("F4")
    outcome = "SIGN_DETERMINED" if not fired else "AMBIGUITY_RECORDED"

    state = {
        "schema": "chimera.ota01_state.v1",
        "task_id": "A01",
        "card_id": "ONT-A01",
        "attempt_id": "fb552e4136ef4bfdaaa93686fb063e78",
        "preregistration": "PREREGISTRATION.md (committed before probes)",
        "pins": PINS,
        "inputs": inputs,
        "source_rest_frame": {
            "definition": "chimanoid.xml rest frame: +x volar/anterior, +y up, +z right; bodies axis-aligned (asserted)",
            "ulna_origin_m": receipt_src["origins_m"]["ulna"],
        },
        "target_world_frame": {
            "definition": "pack frame (O1 sec.1): anterior +z, up +y, right -x",
            "elbow_R_m": p2["elbow_m"],
            "wrist_R_m": p2["wrist_m"],
        },
        "sites_world_m": {
            k: (np.array(receipt_src["origins_m"]["ulna"])
                + np.array(next(s["pos_local_m"] for s in receipt_src["site_table"]
                                if s["site"] == k))).tolist()
            for k in RENDER_SITES + ECU_COURSE
        },
        "outcome": outcome,
    }

    receipt = {
        "schema": "chimera.ota01_numerical_receipt.v1",
        "task_id": "A01",
        "card_id": "ONT-A01",
        "attempt_id": "fb552e4136ef4bfdaaa93686fb063e78",
        "criteria_sha256": "2bcf59fa0b786b009b30711334e38fe374d9a2a2bdefdba9566a4018c4a9c775",
        "honesty": {
            "cpu_only": True, "gpu_used": False, "network_used": False,
            "deterministic": True, "native_engine_run": False,
            "note": "offline re-measurement from pinned inputs; not a runtime claim",
        },
        "frozen_tolerances": {"mesh_mm": TOL_MESH_MM, "D_mm": TOL_D_MM,
                              "az_deg": TOL_AZ_DEG},
        "P1_source_bone": p1,
        "P2_target_olecranon_test": p2,
        "P3_sign_law": p3,
        "fired_falsifiers": fired,
        "outcome": outcome,
        "done_when": ("Independent anatomical evidence determines roll sign"
                      if outcome == "SIGN_DETERMINED"
                      else "Records ambiguity (see fired falsifiers; both readings preserved)"),
        "sign_statement": {
            "world_mapping": "source volar +x <-> target volar +z (anterior); source dorsal -x <-> target dorsal -z (posterior)",
            "law": "az_target = az_source + 90 deg (mod 360) in the C3 (e1,e2) section bases",
            "unanimous_witnesses": ROLL_CANDIDATES,
            "authority": "O1 audit, play lane forearm-package-20260924 commit c3255f74; re-verified here from pins",
        },
        "explicit_unresolved_inventory": [
            "CT MorphoSource 000875604 bones: forearm bones are forearm_class only; "
            "bone_identification_v3 side_rule = 'sides never assigned (the curl jumbles them)' -> "
            "the CT dataset cannot yet re-decide radius-vs-ulna or volar side; recorded, not invented.",
            "U-STR remains the architect's PROVISIONAL candidate (kept-separate forearm/paddle lane); "
            "this receipt is diagnostic evidence, NOT a production mapping and not a containment claim.",
            "Membranes bones/skeleton/skin/inspection remain binding=unresolved, physics=not_qualified "
            "per tools/membrane_ontology/ontology.json rev 2.",
        ],
    }
    return state, receipt


def write_receipts():
    EVIDENCE.mkdir(exist_ok=True)
    state, receipt = build_state_and_receipt()
    (EVIDENCE / "state_snapshot.json").write_text(
        json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    (EVIDENCE / "numerical_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    return state, receipt


def main() -> int:
    state, receipt = write_receipts()
    print("outcome:", receipt["outcome"], "| fired:", receipt["fired_falsifiers"])
    print("P1 verdict:", receipt["P1_source_bone"]["verdict"],
          "olecranon x", round(receipt["P1_source_bone"]["olecranon_min_x_mm"], 3), "mm")
    b = receipt["P2_target_olecranon_test"]["best_station"]
    print("P2 verdict:", receipt["P2_target_olecranon_test"]["verdict"],
          "D(+6)", round(b["D_post_minus_ant_mm"], 3), "mm")
    print("P3 verdict:", receipt["P3_sign_law"]["verdict"],
          "unanimous:", receipt["P3_sign_law"]["unanimous_no_flip"])
    print("wrote", EVIDENCE / "state_snapshot.json")
    print("wrote", EVIDENCE / "numerical_receipt.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
