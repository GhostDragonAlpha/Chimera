"""probe_tibant_tonic.py -- the tibialis-anterior tonic moment probe, closed.

STATEMENT   In the kernel's quiet stance (theta_a = -4 deg plantarflexion,
            VERDICT 41) the tonic ankle moment demanded of the human reference
            chain (VERDICT 44 envelope [8, 31] N m per ankle) is supplied by a
            tibialis-anterior activation a_tonic that stays below 1 (physically
            realizable) when priced against the Rajagopal2016 tibant_r muscle at
            its quiet-ankle operating point.
PREDICTION  At quiet theta_a = -4 deg the TA fiber sits at the top of the active
            force-length curve (plateau [transition_norm, 1.0] = [0.77, 1.0],
            L-tilde_q = 1.02 just past its end), so f_l(L-tilde_q) ~ 1; with the
            derived moment arm MA(theta_q) = 4.19 cm (published TA moment arm
            3.0-4.5 cm), a_tonic = M_req / (Fmax * cos(alpha0) * MA(theta_q))
            < 1 for every M_req in the [8, 31] N m envelope.
FALSIFIER   f_l(L-tilde_q) < 0.95 (fiber more than 5% off the plateau top), OR
            a_tonic > 1 for any M_req in the envelope, OR the derived TA moment
            arm at neutral ankle disagrees with the published TA moment arm
            (3.0-4.5 cm) by more than 30%.

Every scalar is read from research_references/human/opensim/Rajagopal2016.osim
or derived from the two OpenSim C2 curve constructions (SmoothSegmentedFunction
Factory::createFiberActiveForceLengthCurve, SegmentedQuinticBezierToolkit).
The kinematic chain is cross-checked against gait2392_thelen2003muscle.osim
(explicit CustomJoint axes): both models yield L_mt@0 ~ 0.30-0.31 m and
MA@0 ~ 4.2-4.3 cm for the same calcn attachment point.
Nothing is chosen by taste.
"""
import json
import math
import re
from pathlib import Path

import numpy as np

OSIM = Path(__file__).resolve().parents[1] / "research_references/human/opensim/Rajagopal2016.osim"

# Kernel quiet stance ankle angle (LightEngine/kinematic/muscle_atlas.py:47,
# VERDICT 41): -4 deg plantarflexion.  Positive = dorsiflexion, matching the
# osim (gait2392 ankle axis (-0.1050, -0.1740, 0.9791); TA shortens at +theta).
_QUIET_THETA = -0.0698  # rad


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)


def rot_y(b):
    c, s = math.cos(b), math.sin(b)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)


def rot_z(g):
    c, s = math.cos(g), math.sin(g)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)


def rot_xyz(v):
    """OpenSim frame-fixed x-y-z sequence: R = Rx*Ry*Rz.

    Validated against gait2392's CustomJoint ankle axis: RA.dot(z) must equal
    (-0.10501355, -0.17402245, 0.97912632); Rx*Ry*Rz reproduces it to 6
    decimals, Rz*Ry*Rx does not.
    """
    return rot_x(v[0]) @ rot_y(v[1]) @ rot_z(v[2])


def _quintic_val(u, pts):
    p0, p1, p2, p3, p4, p5 = pts
    u5 = 1.0
    u4 = u
    u3 = u4 * u
    u2 = u3 * u
    u1 = u2 * u
    u0 = u1 * u
    return (p0 * (u0 * -1.0 + u1 * 5.0 - u2 * 10.0 + u3 * 10.0 - u4 * 5.0 + u5)
            + p1 * (u0 * 5.0 - u1 * 20.0 + u2 * 30.0 - u3 * 20.0 + u4 * 5.0)
            + p2 * (-u0 * 10.0 + u1 * 30.0 - u2 * 30.0 + u3 * 10.0)
            + p3 * (u0 * 10.0 - u1 * 20.0 + u2 * 10.0)
            + p4 * (-u0 * 5.0 + u1 * 5.0)
            + p5 * u0)


def _quintic_dudx(u, pts):
    p0, p1, p2, p3, p4, p5 = pts
    u2 = u * u
    u3 = u2 * u
    u4 = u3 * u
    return (p0 * (u4 * -5.0 + u3 * 20.0 - u2 * 30.0 + u * 20.0 - 5.0)
            + p1 * (u4 * 25.0 - u3 * 80.0 + u2 * 90.0 - u * 40.0 + 5.0)
            + p2 * (-u4 * 50.0 + u3 * 120.0 - u2 * 90.0 + u * 20.0)
            + p3 * (u4 * 50.0 - u3 * 80.0 + u2 * 30.0)
            + p4 * (-u4 * 25.0 + u3 * 20.0)
            + p5 * u4 * 5.0)


def _corner_ctrl_pts(x0, y0, dydx0, x1, y1, dydx1, c):
    xC = (y1 - y0 - x1 * dydx1 + x0 * dydx0) / (dydx0 - dydx1) \
        if abs(dydx0 - dydx1) > 1e-8 else (x1 + x0) / 2.0
    yC = (xC - x1) * dydx1 + y1
    x0m = x0 + c * (xC - x0)
    y0m = y0 + c * (yC - y0)
    x1m = x1 + c * (xC - x1)
    y1m = y1 + c * (yC - y1)
    return (np.array([x0, x0m, x0m, x1m, x1m, x1]),
            np.array([y0, y0m, y0m, y1m, y1m, y1]))


def build_active_force_length_curve(x0, x1, x2, x3, ylow, dydx, curviness=0.7):
    c = 0.1 + 0.8 * curviness
    xDelta = 0.05 * x2
    xs = x2 - xDelta
    y0, dydx0 = 0.0, 0.0
    y1 = 1.0 - dydx * (xs - x1)
    dydx01 = 1.25 * (y1 - y0) / (x1 - x0)
    x01 = x0 + 0.5 * (x1 - x0)
    y01 = y0 + 0.5 * (y1 - y0)
    x1s = x1 + 0.5 * (xs - x1)
    y1s = y1 + 0.5 * (1.0 - y1)
    dydx1s = dydx
    y2, dydx2 = 1.0, 0.0
    y3, dydx3 = 0.0, 0.0
    x23 = (x2 + xDelta) + 0.5 * (x3 - (x2 + xDelta))
    y23 = y2 + 0.5 * (y3 - y2)
    dydx23 = (y3 - y2) / ((x3 - xDelta) - (x2 + xDelta))
    ctrl = [_corner_ctrl_pts(x0, ylow, dydx0, x01, y01, dydx01, c),
            _corner_ctrl_pts(x01, y01, dydx01, x1s, y1s, dydx1s, c),
            _corner_ctrl_pts(x1s, y1s, dydx1s, x2, y2, dydx2, c),
            _corner_ctrl_pts(x2, y2, dydx2, x23, y23, dydx23, c),
            _corner_ctrl_pts(x23, y23, dydx23, x3, ylow, dydx3, c)]
    spans = [(cx[0], cx[-1]) for cx, _ in ctrl]
    return {"ctrl": ctrl, "spans": spans, "lo": spans[0][0], "hi": spans[-1][1],
            "ylow": ylow, "knots": [x0, x01, x1s, x2, x23, x3]}


def active_fl_value(curve, lt):
    if lt <= curve["lo"] or lt >= curve["hi"]:
        return curve["ylow"]
    for (cx, cy), (a, b) in zip(curve["ctrl"], curve["spans"]):
        if a <= lt < b or (lt == b and b == curve["hi"]):
            u = (lt - a) / (b - a)
            for _ in range(20):
                f = _quintic_val(u, cx) - lt
                df = _quintic_dudx(u, cx)
                if abs(df) < 1e-12:
                    break
                un = min(max(u - f / df, 0.0), 1.0)
                if abs(un - u) < 1e-13:
                    u = un
                    break
                u = un
            return _quintic_val(u, cy)
    raise AssertionError(f"L-tilde {lt} outside all spans")


# ---------------------------------------------------------------------------
# 4. Extraction from the osim bytes. No hand tables.
# ---------------------------------------------------------------------------
def _grab_block(text, tag, name):
    m = re.search(rf'<{tag} name="{name}">(.*?)</{tag}>', text, re.S)
    if not m:
        raise AssertionError(f"{tag} {name} not found")
    return m.group(1)


def _grab_float(block, tag):
    m = re.search(rf"<{tag}>([^<]+)</{tag}>", block)
    if not m:
        raise AssertionError(f"tag {tag} not found")
    return float(m.group(1).strip())


def _grab_loc(block, point_name):
    m = re.search(
        rf'<PathPoint name="{point_name}">.*?<location>([^<]+)</location>',
        block, re.S)
    if not m:
        raise AssertionError(f"path point {point_name} not found")
    return np.array([float(x) for x in m.group(1).split()])


def _grab_offset(block, frame_name):
    fb = _grab_block(block, "PhysicalOffsetFrame", frame_name)
    t = np.array([float(x) for x in re.search(
        r"<translation>([^<]+)</translation>", fb).group(1).split()])
    o = np.array([float(x) for x in re.search(
        r"<orientation>([^<]+)</orientation>", fb).group(1).split()])
    return t, o


def _grab_range(block, coord):
    cb = _grab_block(block, "Coordinate", coord)
    m = re.search(r"<range>([^<]+)</range>", cb)
    return tuple(float(x) for x in m.group(1).split())


def extract():
    text = OSIM.read_text(encoding="utf-8")
    mus = _grab_block(text, "Millard2012EquilibriumMuscle", "tibant_r")
    p1 = _grab_loc(mus, "tibant_r-P1")
    p2 = _grab_loc(mus, "tibant_r-P2")
    p3 = _grab_loc(mus, "tibant_r-P3")
    p4 = _grab_loc(mus, "tibant_r-P4")
    fmax = _grab_float(mus, "max_isometric_force")
    l_opt = _grab_float(mus, "optimal_fiber_length")
    l_tslack = _grab_float(mus, "tendon_slack_length")
    alpha0 = _grab_float(mus, "pennation_angle_at_optimal")
    afl = _grab_block(mus, "ActiveForceLengthCurve",
                      "tibant_r_ActiveForceLengthCurve")
    curve_params = {
        "min_norm": _grab_float(afl, "min_norm_active_fiber_length"),
        "transition_norm": _grab_float(afl, "transition_norm_fiber_length"),
        "max_norm": _grab_float(afl, "max_norm_active_fiber_length"),
        "shallow_slope": _grab_float(afl, "shallow_ascending_slope"),
        "min_value": _grab_float(afl, "minimum_value"),
    }

    ankle = _grab_block(text, "PinJoint", "ankle_r")
    sub = _grab_block(text, "PinJoint", "subtalar_r")
    t_tib, o_tib = _grab_offset(ankle, "tibia_r_offset")
    t_sub, o_sub = _grab_offset(sub, "talus_r_offset")
    c_sub, c_sub_o = _grab_offset(sub, "calcn_r_offset")
    ankle_range = _grab_range(ankle, "ankle_angle_r")
    sub_range = _grab_range(sub, "subtalar_angle_r")

    # TA has an empty PathWrapSet: straight polyline through the 4 points.
    wraps = re.search(r"<PathWrapSet>\s*<objects\s*/>", mus)
    return {
        "p1": p1.tolist(), "p2": p2.tolist(), "p3": p3.tolist(),
        "p4": p4.tolist(),
        "fmax": fmax, "l_opt": l_opt, "l_tslack": l_tslack,
        "alpha0": alpha0, "curve_params": curve_params,
        "ankle_offset_t": t_tib.tolist(), "ankle_offset_o": o_tib.tolist(),
        "subtalar_offset_t": t_sub.tolist(),
        "subtalar_offset_o": o_sub.tolist(),
        "calcn_offset_o": c_sub_o.tolist(),
        "ankle_range": ankle_range, "subtalar_range": sub_range,
        "no_wraps": wraps is not None,
    }


# ---------------------------------------------------------------------------
# 5. Kinematics: tibia -> calcn transform, then L_mt, MA, L-tilde, f_l.
# ---------------------------------------------------------------------------
def l_mt_at(d, theta_a, theta_s=0.0):
    p3 = np.array(d["p3"])
    p4 = np.array(d["p4"])
    pa = np.array(d["ankle_offset_t"])
    ra = rot_xyz(np.array(d["ankle_offset_o"]))
    t_sub = np.array(d["subtalar_offset_t"])
    rs = rot_xyz(np.array(d["subtalar_offset_o"]))
    # Chain tibia -> calcn for a point p4 on calcn, through the two PinJoints.
    # Frames (each offset frame is a PhysicalOffsetFrame in its parent body):
    #   p4 in calcn body
    #   -> calcn_r_offset (orientation RS):            RS.T @ p4
    #   -> subtalar pin (about talus_r_offset z):      Rz(theta_s)
    #   -> subtalar talus_r_offset (in talus):         t_sub + RS @ (...)
    #   -> ankle talus_r_offset (orientation RA):      RA.T @ (...)
    #   -> ankle pin (about tibia_r_offset z):         Rz(theta_a)
    #   -> tibia_r_offset -> tibia body (RA, pa):      pa + RA @ (...)
    # The RA.T inside is NOT identity: the ankle's talus_r_offset has the same
    # orientation RA as tibia_r_offset, so the two joint axes do not coincide.
    # Cross-checked against gait2392 (CustomJoints, explicit axes): both give
    # L_mt@0 = 0.30-0.31 m and MA@0 = 4.2-4.3 cm for tib_ant_r.
    p4_tibia = pa + ra @ rot_z(theta_a) @ (ra.T @ (t_sub + rs @ rot_z(theta_s) @ (rs.T @ p4)))
    seg_const = (float(np.linalg.norm(np.array(d["p2"]) - np.array(d["p1"])))
                 + float(np.linalg.norm(np.array(d["p3"]) - np.array(d["p2"]))))
    return seg_const + float(np.linalg.norm(p4_tibia - p3)), p4_tibia


def main():
    d = extract()
    curve = build_active_force_length_curve(
        d["curve_params"]["min_norm"], d["curve_params"]["transition_norm"],
        1.0, d["curve_params"]["max_norm"], d["curve_params"]["min_value"],
        d["curve_params"]["shallow_slope"])
    l_opt, l_ts = d["l_opt"], d["l_tslack"]
    cos_a0 = math.cos(d["alpha0"])

    theta_a = np.radians(np.linspace(-40.0, 30.0, 71))
    rows = []
    for th in theta_a:
        lmt, _ = l_mt_at(d, th)
        lt = (lmt - l_ts) / (cos_a0 * l_opt)
        fl = active_fl_value(curve, lt)
        rows.append({"theta_deg": float(np.degrees(th)), "theta_rad": float(th),
                     "l_mt": lmt, "l_tilde": lt, "f_l": fl,
                     "f_l_cos": fl * cos_a0})

    # moment arm at quiet angle: -dL_mt/d theta (central difference)
    def ma_at(th):
        h = 1e-5
        lm_p, _ = l_mt_at(d, th + h)
        lm_m, _ = l_mt_at(d, th - h)
        return -(lm_p - lm_m) / (2.0 * h)

    q = min(rows, key=lambda r: abs(r["theta_deg"] - math.degrees(_QUIET_THETA)))
    ma_q = ma_at(_QUIET_THETA)
    m_full = d["fmax"] * q["f_l_cos"] * ma_q
    env = (8.0, 31.0)
    a_lo = env[0] / m_full
    a_hi = env[1] / m_full

    lt_range = (rows[0]["l_tilde"], rows[-1]["l_tilde"])
    fmax = d["fmax"]
    result = {
        "muscle": "tibant_r", "source": str(OSIM),
        "fmax_N": fmax, "l_opt_m": l_opt, "l_tslack_m": l_ts,
        "pennation_rad": d["alpha0"], "cos_alpha0": cos_a0,
        "no_wraps": d["no_wraps"],
        "curve_params": d["curve_params"],
        "quiet": {"theta_deg": q["theta_deg"], "l_mt": q["l_mt"],
                  "l_tilde": q["l_tilde"], "f_l": q["f_l"],
                  "f_l_cos": q["f_l_cos"]},
        "moment_arm_m": ma_q,
        "full_moment_Nm": m_full,
        "envelope_Nm": list(env),
        "a_tonic": {"low": a_lo, "high": a_hi},
        "l_tilde_range": {"min": lt_range[0], "max": lt_range[1]},
        "ankle_range_deg": list(np.degrees(d["ankle_range"])),
        "rows": rows,
    }
    out = Path(__file__).resolve().parents[1] / "agent_logs/tibant_tonic_probe.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("STATEMENT/PREDICTION/FALSIFIER  probe_tibant_tonic")
    print(f"Fmax = {fmax:.1f} N   l_opt = {l_opt:.4f} m   l_tslack = {l_ts:.4f} m"
          f"   alpha0 = {d['alpha0']:.4f} rad   cos = {cos_a0:.4f}")
    print(f"quiet:  L_mt = {q['l_mt']:.4f} m   L-tilde = {q['l_tilde']:.4f}"
          f"   f_l = {q['f_l']:.4f}   f_l*cos = {q['f_l_cos']:.4f}")
    print(f"moment arm @{math.degrees(_QUIET_THETA):.1f} = {ma_q*100:.2f} cm")
    print(f"full-activation moment = {m_full:.1f} N m")
    print(f"a_tonic for envelope {env} = {a_lo:.3f} .. {a_hi:.3f}")
    print(f"L-tilde over ankle range {result['ankle_range_deg']} = "
          f"{lt_range[0]:.3f} .. {lt_range[1]:.3f}")
    for r in rows[::10]:
        print(f"  theta={r['theta_deg']:6.1f}  L_mt={r['l_mt']:.4f}  "
              f"L~={r['l_tilde']:.3f}  f_l={r['f_l']:.4f}")


if __name__ == "__main__":
    main()

