"""THE TARSAL CYCLE BATTERY (preregistration 39b5760e..., banked before THIS run).

Executes the three-part proof of docs/THE_ARTICULATION_LAW.md's differentiator —
THE CYCLES — on the two committed tarsal 3-cycles (06-20-25, 07-21-24):

  1. THE CLASS-HONEST PIVOT DERIVATION: the hip lane's registered machinery
     (inlier_rule + least-spheres, imported VERBATIM) transplanted to the six
     cycle bonds as a MEASURED CANDIDATE, never a prescribed form — the law
     prescribes a pivot derivation for the hip ball-and-socket class ONLY
     (law doc §3); the class-gap finding clause of the preregistration (§2)
     owns whatever the contrast shows.
  2. THE P6-STYLE TWO-ARM CONTRAST per bond (predicate P6' v2, class-adapted):
     seat band [0, 3.0 mm] with tol_ip = 0.08 mm as the recorded RESOLUTION
     FLOOR, plus the displacement band = the fit's own RMS; REAL arm (fit
     center pivots) vs NULL arm (realized-pair midpoints), one shared bilateral
     axis through the two homologous driver fit centers; grid
     {-R} u {R*k/5, k=-4..4} u {+R}, R = the Rajagopal2016 subtalar band edge
     (the tarsal-class cited record, symmetric both sides).
  3. THE CYCLE ARTICULATION DEMO: drive the FOOT member about the driver
     bond's pivot; the LOOP bond's seats must hold with its pivot reused from
     rest and the SIDE bond's gap must be EXACTLY constant — the loop closure
     FK cannot represent (a 3-node cycle's spanning tree holds <= 2 of its
     3 edges; counted in the battery from the parsed definition).

Read-only on the committed tree. Deterministic: no RNG, no timestamps, no
set-order leakage; the output JSON is byte-stable across runs.

Run:  python -B tools/science_funnel/validation/tarsal_cycle_pivots_20260921/tarsal_cycle_battery.py
"""

import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PRIOR = ROOT / "tools" / "science_funnel" / "validation" / "hip_pivot_proof_20260921"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PRIOR))

import hip_pivot_proof as hp  # the committed module: registered primitives only
from tools.matter_kernel.definition import TRIANGLE_BYTES  # noqa: E402

DATA = ROOT / "tools" / "science_funnel" / "data" / "morphosource_ct" / "matter_skeleton"
DEFN = DATA / "infant_skeleton.body.json"
OSIM_R = ROOT / "research_references" / "human" / "opensim" / "Rajagopal2016.osim"
OSIM_G = ROOT / "research_references" / "human" / "opensim" / "gait2392_thelen2003muscle.osim"
OSIM_R_SHA = "4ed1b573715b5747a203f6ea1dfdbbc6480ce8f24cf70fb00447591b1f599a1e"
OSIM_G_SHA = "18e5b3e406a619a78d109e81e6e2cd4f58681a967808fb52a992bbd2b27db019"

CUT_MM = 3.0                    # committed touching-class cut (upper edge)
METRIC_TRANSFER_TOL = 0.005     # house metric-transfer tolerance
FORMULA_TOL = 1e-9              # mm; the 2*|c_perp|*sin(theta/2) reproduction bound

OUT = HERE / "battery.json"
R12 = 12

# ---- BANKED CONSTANTS (preregistration.md section 4, sha 39b5760e...) -----
BANKED_PREREG_SHA = "39b5760e70882da02fff0c488180dbcf61642ec5668f29575ed6761d70f02e44"
BANKED = {
    "bond.joint_06_20": dict(
        gap0=0.479999542236, inl=653, it=62, seed=855,
        center=[42.510281096263, 28.580577124817, 49.84341727624],
        radius=1.798457133157, rms=0.085764861488,
        M=[42.400001525879, 28.799999237061, 47.839998245239],
        cpar=-1.810106381765, cperp=0.893034348418,
        null_d_endpoint=0.310147574043, ratio=3.616255),
    "bond.joint_06_25": dict(
        gap0=0.659698121371, inl=2079, it=80, seed=6897,
        center=[36.83565478293, 32.260135932044, 46.224951880972],
        radius=2.725501481479, rms=0.083161873871,
        M=[39.039999008179, 30.719999313354, 44.959999084473],
        cpar=-2.104964542012, cperp=2.097709255799,
        null_d_endpoint=0.728526778265, ratio=8.760346),
    "bond.joint_20_25": dict(
        gap0=2.468359650708, inl=1940, it=115, seed=7017,
        center=[37.102235303594, 32.005134837085, 46.103602819749],
        radius=2.568014657909, rms=0.084481592551,
        M=[39.839998245239, 30.159997940063, 47.840000152588],
        cpar=0.488059902892, cperp=3.698208934346,
        null_d_endpoint=1.284374482709, ratio=15.203010),
    "bond.joint_07_21": dict(
        gap0=0.452547908376, inl=572, it=43, seed=627,
        center=[47.968308156265, 28.636882624647, 20.432938517872],
        radius=2.199498152185, rms=0.080396592835,
        M=[48.479999542236, 28.319999694824, 22.799999237061],
        cpar=2.005378537752, cperp=1.394157894337,
        null_d_endpoint=0.484185954915, ratio=6.022469),
    "bond.joint_07_24": dict(
        gap0=0.861625547431, inl=2221, it=62, seed=7244,
        center=[43.784032845164, 29.623876636742, 26.559001107115],
        radius=2.69091894703, rms=0.079898136736,
        M=[46.879999160767, 29.119998931885, 25.760000228882],
        cpar=-1.83384129355, cperp=2.667269893034,
        null_d_endpoint=0.926333111495, ratio=11.593926),
    "bond.joint_21_24": dict(
        gap0=2.899930898961, inl=2216, it=60, seed=6641,
        center=[43.783660151501, 29.630446227854, 26.556460834362],
        radius=2.68938625145, rms=0.079675095915,
        M=[46.680000305176, 28.639999389648, 23.639999389648],
        cpar=-3.809625572542, cperp=1.833649797708,
        null_d_endpoint=0.636819890982, ratio=7.992709),
}
BANKED_AXIS = [0.330508327523, -0.125396983699, -0.935435642851]
BANKED_AXIS_SEP = 21.023307080657
BANKED_R = 0.34906585000000001

CYCLES = {
    "A": {"side": "bond.joint_06_20", "driver": "bond.joint_06_25",
          "loop": "bond.joint_20_25", "child": 25, "child_driver": "mem.bone_25"},
    "B": {"side": "bond.joint_07_21", "driver": "bond.joint_07_24",
          "loop": "bond.joint_21_24", "child": 24, "child_driver": "mem.bone_24"},
}
ALL_BONDS = ["bond.joint_06_20", "bond.joint_06_25", "bond.joint_20_25",
             "bond.joint_07_21", "bond.joint_07_24", "bond.joint_21_24"]
BOND_MEMBERS = {"bond.joint_06_20": (6, 20), "bond.joint_06_25": (6, 25),
                "bond.joint_20_25": (20, 25), "bond.joint_07_21": (7, 21),
                "bond.joint_07_24": (7, 24), "bond.joint_21_24": (21, 24)}


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


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


def median_edge(tris):
    return float(np.median(np.concatenate([
        np.linalg.norm(tris[:, 1] - tris[:, 0], axis=1),
        np.linalg.norm(tris[:, 2] - tris[:, 1], axis=1),
        np.linalg.norm(tris[:, 0] - tris[:, 2], axis=1)])))


def areas_np(tris):
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    u, v = b - a, c - a
    n = np.cross(u, v)
    return 0.5 * np.sqrt((n * n).sum(-1))


def main():
    body = json.loads(DEFN.read_text(encoding="utf-8"))
    bonds = {b["id"]: b for b in body["bonds"]}
    mems = {m["id"]: m for m in body["membranes"]}

    watch = [
        DEFN,
        OSIM_R, OSIM_G,
        DATA / "tris" / "bone_01.bin", DATA / "tris" / "bone_02.bin", DATA / "tris" / "bone_03.bin",
        DATA / "tris" / "bone_06.bin", DATA / "tris" / "bone_07.bin",
        DATA / "tris" / "bone_20.bin", DATA / "tris" / "bone_21.bin",
        DATA / "tris" / "bone_24.bin", DATA / "tris" / "bone_25.bin",
        ROOT / "tools" / "science_funnel" / "validation" / "axial_adjacency_20260920" / "receipt.json",
        ROOT / "tools" / "science_funnel" / "validation" / "hip_adoption_20260921" / "receipt.json",
        ROOT / "tools" / "science_funnel" / "validation" / "articulation_design_20260921" / "receipt.json",
        PRIOR / "preregistration.md", PRIOR / "battery.json", PRIOR / "receipt.json",
        PRIOR / "hip_pivot_proof.py",
        ROOT / "tools" / "science_funnel" / "validation" / "p6_repreregistration_20260921" / "preregistration.md",
        ROOT / "tools" / "science_funnel" / "validation" / "p6_repreregistration_20260921" / "battery.json",
        ROOT / "tools" / "science_funnel" / "validation" / "p6_repreregistration_20260921" / "receipt.json",
        ROOT / "tools" / "science_funnel" / "validation" / "p6_repreregistration_20260921" / "p6_contrast.py",
        ROOT / "docs" / "THE_ARTICULATION_LAW.md",
        HERE / "preregistration.md", HERE / "preregistration.sha256",
    ]
    before = {str(p.relative_to(ROOT)): sha256_file(p) for p in watch}

    # input integrity
    osim_r_sha = sha256_file(OSIM_R)
    osim_g_sha = sha256_file(OSIM_G)
    prereg_sha = sha256_file(HERE / "preregistration.md")
    prereg_bank = (HERE / "preregistration.sha256").read_text(encoding="utf-8").split()[0]

    # committed geometry
    geo = {}
    for r in (6, 7, 20, 21, 24, 25):
        blob, tris = hp.load_blob(r)
        verts, faces = hp.unique_verts(tris)
        geo[r] = dict(blob=blob, tris=tris, verts=verts, faces=faces,
                      med=median_edge(tris), tree=cKDTree(verts))

    # range record parsed from the committed osim (no retyped constant)
    root = ET.parse(OSIM_R).getroot()
    sub_ranges = {}
    for co in root.iter("Coordinate"):
        nm = co.get("name")
        if nm in ("subtalar_angle_l", "subtalar_angle_r", "ankle_angle_l", "ankle_angle_r"):
            sub_ranges[nm] = [float(x) for x in co.find("range").text.split()]
    if sorted(sub_ranges) != ["ankle_angle_l", "ankle_angle_r", "subtalar_angle_l", "subtalar_angle_r"]:
        raise SystemExit("osim range parse failed: %s" % sorted(sub_ranges))
    lo_l, hi_l = sub_ranges["subtalar_angle_l"]
    lo_r, hi_r = sub_ranges["subtalar_angle_r"]
    if not (lo_l == -hi_l and lo_r == -hi_r and hi_l == hi_r):
        raise SystemExit("asymmetric subtalar band record")
    R = hi_l
    if R != BANKED_R:
        raise SystemExit("range drift vs banked R")

    # bands + tol floor
    resolution_um = body["specimen"]["resolution_um"]
    tol_ip_mm = (resolution_um / 2.0) / 1000.0

    # ---- THE PIVOT DERIVATIONS (one per bond, at rest; total 6) -----------
    fits = {}
    repro = {}
    for bid in ALL_BONDS:
        a, ch = BOND_MEMBERS[bid]
        vq, fq, medq = geo[ch]["verts"], geo[ch]["faces"], geo[ch]["med"]
        vp, tp = geo[a]["verts"], geo[a]["tree"]
        g0, prov = hp.law_gap(vq, vp, tp)
        seed = int(prov[1])
        fit = hp.inlier_rule(vq, fq, vq[seed], medq)
        if fit.get("outcome") != "fixed_point":
            raise SystemExit("%s: fit refused (%s)" % (bid, fit.get("outcome")))
        c = fit.pop("_c")
        inl = fit.pop("_inliers")
        cc, rr, gn_it = hp.sphere_fit(vq[inl])
        res = np.abs(np.linalg.norm(vq[inl] - cc, axis=1) - rr)
        rms = float(np.sqrt((res * res).mean()))
        M = (vq[seed] + vp[prov[3]]) / 2.0
        rec = {
            "gap0_mm": rnd(g0), "seed_vertex": seed, "iterations": fit["iterations"],
            "inliers": fit["inliers"],
            "center_mm": [rnd(x) for x in cc], "radius_mm": rnd(rr),
            "rms_residual_mm": rnd(rms), "max_residual_mm": rnd(res.max()),
            "gauss_newton_iters_final": gn_it,
            "band_eps_mm": rnd(medq),
            "M_mm": [rnd(x) for x in M],
        }
        bk = BANKED[bid]
        diffs = []
        if rec["gap0_mm"] != bk["gap0"]:
            diffs.append("gap0_mm")
        if rec["seed_vertex"] != bk["seed"]:
            diffs.append("seed_vertex")
        if rec["iterations"] != bk["it"]:
            diffs.append("iterations")
        if rec["inliers"] != bk["inl"]:
            diffs.append("inliers")
        if rec["center_mm"] != bk["center"]:
            diffs.append("center_mm")
        if rec["radius_mm"] != bk["radius"]:
            diffs.append("radius_mm")
        if rec["rms_residual_mm"] != bk["rms"]:
            diffs.append("rms_residual_mm")
        if rec["M_mm"] != bk["M"]:
            diffs.append("M_mm")
        repro[bid] = {"repro_diffs": diffs, "matches_banked": not diffs}
        # metric transfer vs the committed measured_gap_mm
        committed_gap = bonds[bid]["measured_gap_mm"]
        transfer_ok = bool(abs(g0 - committed_gap) <= METRIC_TRANSFER_TOL)
        fits[bid] = dict(c=cc, r=rr, rms=rms, M=M, gap0=g0, rec=rec,
                         committed_gap=committed_gap, transfer_ok=transfer_ok)

    # axis (registered): the line through the two homologous DRIVER fit centers
    cA = fits[CYCLES["A"]["driver"]]["c"]
    cB = fits[CYCLES["B"]["driver"]]["c"]
    u = (cB - cA) / np.linalg.norm(cB - cA)
    axis_matches_banked = bool(
        [rnd(x) for x in u] == BANKED_AXIS
        and rnd(np.linalg.norm(cB - cA)) == BANKED_AXIS_SEP)

    # graph guards (counted FK contrast)
    ids = [m["id"] for m in body["membranes"]]
    idx_of = {m: i for i, m in enumerate(ids)}
    parent = list(range(len(ids)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for b in body["bonds"]:
        x, y = (idx_of[m] for m in b["members"])
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry
    comp = len({find(i) for i in range(len(ids))})
    E, V = len(body["bonds"]), len(ids)
    cyclomatic = E - V + comp
    bond_set = set(bonds)
    tri_A = {"bond.joint_06_20", "bond.joint_06_25", "bond.joint_20_25"} <= bond_set
    tri_B = {"bond.joint_07_21", "bond.joint_07_24", "bond.joint_21_24"} <= bond_set

    # grid (registered): endpoints exact + the probe fraction R/5
    thetas = [(-R, "lo_endpoint"), (R, "hi_endpoint")]
    for kk in range(-4, 5):
        th = R * kk / 5.0
        lab = "rest" if kk == 0 else "grid_k%+d" % kk
        thetas.append((th, lab))
    thetas.sort(key=lambda t: t[0])

    # ---- TWO-ARM CONTRAST PER BOND ----------------------------------------
    def run_arm(pivot_of, band_of):
        out = {}
        for bid in ALL_BONDS:
            a, ch = BOND_MEMBERS[bid]
            vq = geo[ch]["verts"]
            vp, tp = geo[a]["verts"], geo[a]["tree"]
            c = fits[bid]["c"]
            band = band_of(bid)
            piv = pivot_of(bid)
            rows = []
            for th, lab in thetas:
                vpq = hp.rodrigues(vq, piv, u, th)
                g, prov = hp.law_gap(vpq, vp, tp)
                d = float(np.linalg.norm(hp.rodrigues(c[None, :], piv, u, th)[0] - c))
                row = {
                    "theta_rad": rnd(th), "label": lab,
                    "seat_gap_mm": rnd(g), "provenance": prov,
                    "seat_ok": bool(0.0 <= g <= CUT_MM),
                    "reading_class": "below_resolution_floor" if g < tol_ip_mm else "resolved",
                    "displacement_mm": rnd(d),
                    "band_mm": rnd(band),
                    "displacement_exact_zero": bool(d == 0.0),
                    "displacement_ok": bool(d <= band),
                    "predicted_displacement_mm": None,
                    "formula_abs_dev_mm": None,
                    "formula_ok": None,
                }
                if piv is not c:
                    w = c - piv
                    cpar = float(w @ u)
                    cperp = math.sqrt(max(float(w @ w) - cpar * cpar, 0.0))
                    pred = 2.0 * cperp * math.sin(abs(th) / 2.0)
                    row["predicted_displacement_mm"] = rnd(pred)
                    row["formula_abs_dev_mm"] = rnd(abs(d - pred))
                    row["formula_ok"] = bool(abs(d - pred) <= FORMULA_TOL)
                rows.append(row)
            seat_all = all(r["seat_ok"] for r in rows)
            disp_all = all(r["displacement_ok"] for r in rows)
            formula_all = all((r["formula_ok"] is not False) for r in rows)
            exact_zero_all = all(r["displacement_exact_zero"] for r in rows)
            out[bid] = {
                "rows": rows,
                "seat_clause_ok_all_grid": seat_all,
                "displacement_clause_ok_all_grid": disp_all,
                "formula_ok_all_grid": formula_all,
                "displacement_exact_zero_all_grid": exact_zero_all,
                "min_seat_mm": rnd(min(r["seat_gap_mm"] for r in rows)),
                "max_seat_mm": rnd(max(r["seat_gap_mm"] for r in rows)),
                "max_displacement_mm": rnd(max(r["displacement_mm"] for r in rows)),
                "below_floor_readings": [r["label"] for r in rows
                                         if r["reading_class"] == "below_resolution_floor"],
                "clause_breaches_at": [r["label"] for r in rows
                                       if not (r["seat_ok"] and r["displacement_ok"])],
                "pass_p6_class_adapted": bool(seat_all and disp_all and exact_zero_all),
            }
        return out

    real = run_arm(lambda bid: fits[bid]["c"], lambda bid: fits[bid]["rms"])
    null = run_arm(lambda bid: fits[bid]["M"], lambda bid: fits[bid]["rms"])

    # null endpoint displacement reproduction vs the BANKED exact values
    null_endpoint_checks = {}
    for bid in ALL_BONDS:
        nmap = {r["label"]: r for r in null[bid]["rows"]}
        null_endpoint_checks[bid] = bool(
            nmap["hi_endpoint"]["displacement_mm"] == BANKED[bid]["null_d_endpoint"]
            and nmap["lo_endpoint"]["displacement_mm"] == BANKED[bid]["null_d_endpoint"]
            and nmap["rest"]["displacement_mm"] == 0.0)

    per_bond = {}
    for bid in ALL_BONDS:
        per_bond[bid] = {
            "real_pass": real[bid]["pass_p6_class_adapted"],
            "null_fail": not null[bid]["pass_p6_class_adapted"],
            "discriminate": bool(real[bid]["pass_p6_class_adapted"]
                                 and not null[bid]["pass_p6_class_adapted"]),
            "null_max_disp_over_band": rnd(null[bid]["max_displacement_mm"] / fits[bid]["rms"]),
        }

    # ---- THE CYCLE ARTICULATION DEMO --------------------------------------
    demo = {}
    for cyc in ("A", "B"):
        cd = CYCLES[cyc]
        driver, loop, side = cd["driver"], cd["loop"], cd["side"]
        ch = cd["child"]
        a_d, _ = BOND_MEMBERS[driver]
        a_l, _ = BOND_MEMBERS[loop]
        a_s, _ = BOND_MEMBERS[side]
        v_ch = geo[ch]["verts"]
        v_l, t_l = geo[a_l]["verts"], geo[a_l]["tree"]
        v_s, t_s = geo[a_s]["verts"], geo[a_s]["tree"]
        s_a, s_b = BOND_MEMBERS[side]  # neither member of the side bond is ever posed
        c_drv = fits[driver]["c"]
        c_loop = fits[loop]["c"]
        g_side_rest, _ = hp.law_gap(geo[s_b]["verts"], geo[s_a]["verts"], geo[s_a]["tree"])
        arms = {}
        for arm, piv in (("real", c_drv), ("null", fits[driver]["M"])):
            rows = []
            for th, lab in thetas:
                vpq = hp.rodrigues(v_ch, piv, u, th)
                g_d, prov_d = hp.law_gap(vpq, geo[a_d]["verts"], geo[a_d]["tree"])
                d_d = float(np.linalg.norm(hp.rodrigues(c_drv[None, :], piv, u, th)[0] - c_drv))
                g_l, _ = hp.law_gap(vpq, v_l, t_l)
                d_l = float(np.linalg.norm(hp.rodrigues(c_loop[None, :], piv, u, th)[0] - c_loop))
                # side-bond members (tibia, fibula) are never posed: the gap must be
                # EXACTLY constant at every pose (guards accidental transform aliasing)
                g_s, _ = hp.law_gap(geo[s_b]["verts"], geo[s_a]["verts"], geo[s_a]["tree"])
                band_d = fits[driver]["rms"]
                rows.append({
                    "theta_rad": rnd(th), "label": lab,
                    "driver_seat_mm": rnd(g_d), "driver_seat_ok": bool(0.0 <= g_d <= CUT_MM),
                    "driver_displacement_mm": rnd(d_d),
                    "driver_displacement_ok": bool(d_d <= band_d),
                    "driver_reading_class": "below_resolution_floor" if g_d < tol_ip_mm else "resolved",
                    "loop_seat_mm": rnd(g_l), "loop_seat_ok": bool(0.0 <= g_l <= CUT_MM),
                    "loop_reading_class": "below_resolution_floor" if g_l < tol_ip_mm else "resolved",
                    "loop_pivot_transport_mm": rnd(d_l),
                    "loop_pivot_transport_recorded_only": True,
                    "side_gap_mm": rnd(g_s),
                    "side_gap_exact_constant": bool(g_s == g_side_rest),
                    "provenance": prov_d,
                })
            loop_closes = all(r["driver_seat_ok"] and r["driver_displacement_ok"]
                              and r["loop_seat_ok"] and r["side_gap_exact_constant"]
                              for r in rows)
            arms[arm] = {
                "pivot_of_motion_mm": [rnd(x) for x in piv],
                "rows": rows,
                "driver_seat_ok_all": all(r["driver_seat_ok"] for r in rows),
                "driver_displacement_ok_all": all(r["driver_displacement_ok"] for r in rows),
                "loop_seat_ok_all": all(r["loop_seat_ok"] for r in rows),
                "side_identity_ok_all": all(r["side_gap_exact_constant"] for r in rows),
                "loop_closes": bool(loop_closes),
                "max_loop_seat_mm": rnd(max(r["loop_seat_mm"] for r in rows)),
                "max_driver_seat_mm": rnd(max(r["driver_seat_mm"] for r in rows)),
                "breaches_at": [r["label"] for r in rows
                                if not (r["driver_seat_ok"] and r["driver_displacement_ok"]
                                        and r["loop_seat_ok"] and r["side_gap_exact_constant"])],
            }
        demo["cycle_%s" % cyc] = {
            "side_bond": side, "driver_bond": driver, "loop_bond": loop,
            "posed_member": "mem.bone_%02d" % ch,
            "loop_pivot_reused_from_rest": True,
            "arms": arms,
        }

    # non-binding area-invariance reading on the posed demo children (endpoints)
    area_reading = {}
    for cyc in ("A", "B"):
        ch = CYCLES[cyc]["child"]
        tris = geo[ch]["tris"]
        a_rest = areas_np(tris)
        c_drv = fits[CYCLES[cyc]["driver"]]["c"]
        worst = 0.0
        for th in (-R, R):
            flat = hp.rodrigues(tris.reshape(-1, 3), c_drv, u, th).reshape(-1, 3, 3)
            drift = np.abs(areas_np(flat) - a_rest) / np.maximum(a_rest, 1e-300)
            worst = max(worst, float(drift.max()))
        area_reading["cycle_%s" % cyc] = rnd(worst)

    # ---- PREDICTION CHECKS / FALSIFIERS -----------------------------------
    checks = {}
    checks["preregistration_bank_matches_file"] = bool(prereg_sha == prereg_bank
                                                       == BANKED_PREREG_SHA)
    checks["osim_rajagopal_sha_matches_citation"] = bool(osim_r_sha == OSIM_R_SHA)
    checks["osim_gait2392_sha_matches_citation"] = bool(osim_g_sha == OSIM_G_SHA)
    checks["subtalar_band_parsed_equals_banked"] = bool(R == BANKED_R)
    checks["all_fits_match_banked_constants"] = bool(all(v["matches_banked"]
                                                         for v in repro.values()))
    checks["all_metric_transfers_pass"] = bool(all(v["transfer_ok"] for v in fits.values()))
    checks["axis_matches_banked"] = axis_matches_banked
    checks["graph_cyclomatic_equals_4"] = bool(cyclomatic == 4 and comp == 6 and E == 23 and V == 25)
    checks["both_named_triangles_present"] = bool(tri_A and tri_B)
    checks["real_displacement_exact_zero_all_grid_all_bonds"] = bool(all(
        r["displacement_exact_zero_all_grid"] for r in real.values()))
    checks["null_formula_ok_all_grid_all_bonds"] = bool(all(
        r["formula_ok_all_grid"] for r in null.values()))
    checks["null_endpoint_displacement_matches_banked_all_bonds"] = bool(all(
        null_endpoint_checks.values()))
    checks["null_disp_beyond_band_all_bonds"] = bool(all(
        not null[bid]["displacement_clause_ok_all_grid"] for bid in ALL_BONDS))
    checks["real_seats_within_cut_all_grid_all_bonds"] = bool(all(
        real[bid]["seat_clause_ok_all_grid"] for bid in ALL_BONDS))
    checks["all_bonds_discriminate"] = bool(all(per_bond[bid]["discriminate"]
                                                for bid in ALL_BONDS))
    checks["demo_real_loop_closes_both_cycles"] = bool(
        demo["cycle_A"]["arms"]["real"]["loop_closes"]
        and demo["cycle_B"]["arms"]["real"]["loop_closes"])
    checks["demo_side_identity_ok_both_cycles"] = bool(
        demo["cycle_A"]["arms"]["real"]["side_identity_ok_all"]
        and demo["cycle_B"]["arms"]["real"]["side_identity_ok_all"]
        and demo["cycle_A"]["arms"]["null"]["side_identity_ok_all"]
        and demo["cycle_B"]["arms"]["null"]["side_identity_ok_all"])

    falsifiers_fired = []
    if not checks["real_seats_within_cut_all_grid_all_bonds"]:
        falsifiers_fired.append("L6/P-C/F: a REAL-arm seat exceeds the 3.0 mm cut")
    if not checks["all_bonds_discriminate"]:
        falsifiers_fired.append("L5/P-D/F: the null arm passes both clauses on a bond "
                                "(the class-gap finding is confirmed by measurement there)")
    if not checks["demo_real_loop_closes_both_cycles"]:
        falsifiers_fired.append("L7/P-E/F: the loop does not close under the real motion")
    for k in ("preregistration_bank_matches_file", "osim_rajagopal_sha_matches_citation",
              "osim_gait2392_sha_matches_citation", "subtalar_band_parsed_equals_banked",
              "all_fits_match_banked_constants", "all_metric_transfers_pass",
              "axis_matches_banked", "graph_cyclomatic_equals_4",
              "both_named_triangles_present", "real_displacement_exact_zero_all_grid_all_bonds",
              "null_formula_ok_all_grid_all_bonds",
              "null_endpoint_displacement_matches_banked_all_bonds",
              "demo_side_identity_ok_both_cycles"):
        if not checks[k]:
            falsifiers_fired.append("L8/VOID-class: %s failed" % k)

    battery = {
        "schema": "chimera.tarsal_cycle_battery.v1",
        "lane": "agent/tarsal-cycle-pivots-20260921",
        "base_commit": "13d7c31e (agent/p6-repreregistration-20260921, the reinstatement head)",
        "parent_lanes": [
            "agent/articulation-semantics-20260921 (the design; receipt articulation_design_20260921)",
            "agent/hip-pivot-proof-20260921 (the registered primitives)",
            "agent/p6-repreregistration_20260921 (the corrected predicate P6' v2)",
        ],
        "preregistration_sha256": prereg_sha,
        "preregistration_bank_matches_file": checks["preregistration_bank_matches_file"],
        "predicate": {
            "definition": "SEATED at theta iff (0 <= seat_gap <= cut) AND (displacement <= band_b); "
                          "an arm PASSES a bond iff both hold at every theta of the registered grid. "
                          "The pivot form is a MEASURED CANDIDATE (transplanted hip sphere machinery), "
                          "never a prescribed form: the law prescribes a pivot derivation for the hip "
                          "ball-and-socket class ONLY (law doc section 3); the preregistration's "
                          "class-gap clause (section 2) owns the interpretation.",
            "tol_ip_mm": rnd(tol_ip_mm),
            "tol_ip_derivation": "specimen.resolution_um/2 = %d um / 2 = 0.08 mm: the gap metric's "
                                 "RESOLUTION FLOOR; readings below it RECORDED per pose, never "
                                 "clause-binding (law doc section 5B)" % resolution_um,
            "cut_mm": CUT_MM,
            "band_source": "the bond's own registered fit RMS residual (section 5A Leg 2 verbatim)",
            "grid": "endpoints exact + R*k/5, k=-4..4 (the registered probe fraction); 11 poses",
            "R_rad": rnd(R),
            "R_source": "Rajagopal2016.osim subtalar_angle_l/r band edge (the tarsal-class cited "
                        "record, symmetric both sides); gait2392 wide band recorded as context",
            "axis": "the unit line through the two homologous DRIVER fit centers "
                    "(bond.joint_06_25 child fit, bond.joint_07_24 child fit); shared by both arms",
            "null_pivot": "the realized rest closest-pair midpoint (derivation-free)",
            "sign_labeling": "DEFERRED - no held curl-contact rule binds a tarsal child; every "
                             "clause is sign-symmetric; the class amendment owns dorsi/plantar labeling",
            "tasking_correction": "the tasking's 'bone 19<->24' is NO COMMITTED BOND: mem.bone_19 "
                                  "is a committed unpaired singleton (no bond, no cycle); the "
                                  "tarsal 3-cycle members are the six bonds measured here",
        },
        "trailer": "Agent: GLM 5.3",
        "inputs": {
            "definition_sha256": before[str(DEFN.relative_to(ROOT))],
            "osim_rajagopal_sha256": osim_r_sha,
            "osim_gait2392_sha256": osim_g_sha,
            "osim_shas_match_citations": bool(osim_r_sha == OSIM_R_SHA and osim_g_sha == OSIM_G_SHA),
            "ranges_parsed": {k: sub_ranges[k] for k in sorted(sub_ranges)},
            "vertex_books_checked": {
                ("bone_%02d" % r): bool(hp.vertex_records_sha(geo[r]["blob"])
                                        == mems["mem.bone_%02d" % r]["vertex_sha256"])
                for r in (6, 7, 20, 21, 24, 25)},
        },
        "graph": {
            "membranes": V, "bonds": E, "components": comp,
            "cyclomatic_number": cyclomatic,
            "independent_cycles_prediction": 4,
            "triangle_A_06_20_25_present": bool(tri_A),
            "triangle_B_07_21_24_present": bool(tri_B),
            "fk_contrast_counted": "a spanning tree of a 3-node cycle holds <= 2 of its 3 edges; "
                                   "the engine's FK loader is a TREE (law doc section 1.3a), so the "
                                   "cycle-closing bond is unrepresentable at ANY pose; the materials "
                                   "graph reads it at every pose of the demo below",
        },
        "fits": {bid: fits[bid]["rec"] for bid in ALL_BONDS},
        "metric_transfer": {bid: {
            "law_gap_theta0_mm": rnd(fits[bid]["gap0"]),
            "committed_measured_gap_mm": fits[bid]["committed_gap"],
            "abs_dev_mm": rnd(abs(fits[bid]["gap0"] - fits[bid]["committed_gap"])),
            "pass": fits[bid]["transfer_ok"]} for bid in ALL_BONDS},
        "bands": {bid: rnd(fits[bid]["rms"]) for bid in ALL_BONDS},
        "axis": {
            "u": [rnd(x) for x in u],
            "driver_center_A_mm": [rnd(x) for x in cA],
            "driver_center_B_mm": [rnd(x) for x in cB],
            "separation_mm": rnd(np.linalg.norm(cB - cA)),
        },
        "reproduction_guards": repro,
        "grid": {"thetas_rad": [rnd(t) for t, _ in thetas],
                 "labels": [lab for _, lab in thetas]},
        "real_arm": real,
        "null_arm": null,
        "null_endpoint_reproduction": null_endpoint_checks,
        "per_bond": per_bond,
        "cycle_demo": demo,
        "area_invariance_reading_non_binding": area_reading,
        "pivot_derivation_count": 6,
        "prediction_checks": checks,
        "falsifiers_fired": falsifiers_fired,
        "untouched": {"before": before},
    }
    battery["untouched"]["after"] = {str(p.relative_to(ROOT)): sha256_file(p) for p in watch}
    battery["untouched"]["equal"] = bool(battery["untouched"]["before"] == battery["untouched"]["after"])
    checks["untouched_watch_equal"] = battery["untouched"]["equal"]
    if not battery["untouched"]["equal"]:
        falsifiers_fired.append("L2/VOID-class: a watched sha256 changed during the run")

    hard_ok = all(checks.values())
    battery["hard_checks_pass"] = bool(hard_ok)

    text = json.dumps(sanitize(battery), indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    OUT.write_bytes(text.encode("utf-8"))
    print("battery written:", OUT)
    print("hard_checks_pass:", hard_ok)
    print("falsifiers_fired:", falsifiers_fired)
    for bid in ALL_BONDS:
        print("%s: real seat %s..%s disp0==%s | null max_disp %s (band %s, x%s) | discriminate %s" % (
            bid, real[bid]["min_seat_mm"], real[bid]["max_seat_mm"],
            real[bid]["displacement_exact_zero_all_grid"],
            null[bid]["max_displacement_mm"], fits[bid]["rms"],
            per_bond[bid]["null_max_disp_over_band"], per_bond[bid]["discriminate"]))
    for cyc in ("A", "B"):
        for arm in ("real", "null"):
            d = demo["cycle_%s" % cyc]["arms"][arm]
            print("demo %s %s: loop_closes %s (driver seat ok %s, disp ok %s, loop seat ok %s, "
                  "side id %s; max loop seat %s, breaches %s)" % (
                      cyc, arm, d["loop_closes"], d["driver_seat_ok_all"],
                      d["driver_displacement_ok_all"], d["loop_seat_ok_all"],
                      d["side_identity_ok_all"], d["max_loop_seat_mm"], d["breaches_at"]))
    return 0 if hard_ok else 1


if __name__ == "__main__":
    sys.exit(main())
