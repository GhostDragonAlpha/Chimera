"""standing_pose_core_v2.py -- the AMENDED DEFINITION machinery for the
standing-pose-v2 lane (preregistration_amendment_4.md, sha 3ad74c44...,
banked BEFORE the v2 solve).

Everything here is DERIVED from committed bytes, nothing tuned:
  - EPSILON_MM = 0.08 is the committed P6' interpenetration tolerance REUSED
    (tol_ip = specimen.resolution_um/2 = 0.08 mm, law doc section 5B; the
    definition's own resolution_um = 160),
  - the pads'-plane normal SIGN RULE (trunk centroid above the plane),
  - the head window (bone_01 vertices beyond the hand pads' distal extreme),
  - h_min(m; x) = min over the membrane's posed unique vertices of the signed
    height above the pads' least-squares centroid plane,
  - the strict solve (v1 objective + T3 constraints) and the maximin
    (maximize t s.t. V <= V_rest, d <= d_rest, seats, ranges),
  - the structural-pin plane (hand-pinned, trunk-parallel) and its constants.

The v1 objective machinery is used VERBATIM (dv.objective_terms); only the
sign-fixed reading and the new constraint terms are added.

Deterministic: no RNG, no timestamps, no set-order leakage.
"""

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools" / "science_funnel" / "validation" / "hip_pivot_proof_20260921"))

from standing_pose_core import StandingDerivation, CUT_MM, PAD_BONES, rnd  # noqa: E402

EPSILON_MM = 0.08          # tol_ip = specimen.resolution_um/2 (committed)
SECONDARY_EPSILON_MM = CUT_MM  # the 3.0 mm committed cut, the recorded secondary reading
V1_POSE = HERE / "pose.json"   # the committed v1 record (T1/T2 verdict bands)

NONPAD_BONES = tuple(r for r in range(1, 26) if r not in PAD_BONES)  # 21, ascending


class StandingV2:
    """The amended-definition layer over the v1 derivation."""

    def __init__(self):
        self.dv = StandingDerivation()
        self.x_v1 = None  # set by load_v1_record()
        self.load_v1_record()

    # ------------------------------------------------- the committed v1 record
    def load_v1_record(self):
        pose = json.loads(V1_POSE.read_text(encoding="utf-8"))
        self.x_v1 = np.array(pose["variables"]["x_R12"], dtype=np.float64)
        self.V_v1 = float(pose["objective"]["V_pose_mm2"])
        self.d_v1 = float(pose["objective"]["d_pose"])
        self.v1_pose_normal = None  # measured in sign_fixed_plane below
        return pose

    # ------------------------------------------------- the sign-fixed plane
    def sign_fixed_plane(self, x):
        """(V, n_hat sign-fixed, cbar): n̂ oriented so the axial composite's
        centroid has positive height (amendment 4 section 1; refuses on 0)."""
        dv = self.dv
        P = dv.pad_centroids(x)
        V, n = dv._plane_stats(P)
        cbar = P.mean(axis=0)
        s = float((dv.geo[1]["verts"].mean(axis=0) - cbar) @ n)
        if s == 0.0:
            raise SystemExit("degenerate sign rule: trunk centroid ON the pads' plane")
        if s < 0.0:
            n = -n
        return V, n, cbar

    # ------------------------------------------------------------- heights
    def heights(self, x):
        """Per membrane: (h_min, h_cen, argmin vertex) above the sign-fixed
        pads' centroid plane. Computed on the posed UNIQUE vertices."""
        dv = self.dv
        _, n, cbar = self.sign_fixed_plane(x)
        T = dv.fk(x)
        out = {}
        for r in NONPAD_BONES:
            h = (T[r].pts(dv.geo[r]["verts"]) - cbar) @ n
            i = int(np.argmin(h))
            out[r] = (float(h[i]), float(h.mean()), dv.geo[r]["verts"][i].copy())
        return out, n, cbar

    def pad_report(self, x):
        """Per pad: (h_cen, vertex h_min, vertex h_max) w.r.t. the sign-fixed plane."""
        dv = self.dv
        _, n, cbar = self.sign_fixed_plane(x)
        T = dv.fk(x)
        out = {}
        for r in PAD_BONES:
            h = (T[r].pts(dv.geo[r]["verts"]) - cbar) @ n
            out[r] = (float((dv.geo[r]["verts"].mean(axis=0) - cbar) @ n),
                      float(h.min()), float(h.max()))
        return out

    # ---------------------------------------------------------- head window
    def head_window(self):
        """The skull region: bone_01 vertices beyond the hand pads' distal
        extreme (amendment 4 section 1; zero free numbers)."""
        dv = self.dv
        cut = max(dv.geo[8]["verts"][:, 0].max(), dv.geo[9]["verts"][:, 0].max())
        v01 = dv.geo[1]["verts"]
        mask = v01[:, 0] > cut
        if not bool(mask.any()):
            raise SystemExit("empty head window")
        return cut, mask

    def skull_window_hmin(self, x):
        dv = self.dv
        cut, mask = self.head_window()
        _, n, cbar = self.sign_fixed_plane(x)
        h = (dv.fk(x)[1].pts(dv.geo[1]["verts"]) - cbar) @ n
        return float(h[mask].min()), float(cut)

    # --------------------------------------------------- T3 constraint set
    def t3_slacks(self, x, eps_mm=EPSILON_MM):
        """h_min(m; x) - eps for the 21 non-pad membranes (ascending id)."""
        hs, _, _ = self.heights(x)
        return np.array([hs[r][0] - eps_mm for r in NONPAD_BONES])

    # ------------------------------------------------- the structural pin
    def pinned_plane(self):
        """The UNIQUE plane through the fixed hand centroids, parallel to the
        trunk axis (amendment 4 section 1)."""
        dv = self.dv
        c8 = dv.geo[8]["verts"].mean(axis=0)
        c9 = dv.geo[9]["verts"].mean(axis=0)
        n = np.cross(dv.trunk_axis, c8 - c9)
        n = n / np.linalg.norm(n)
        cbar = (c8 + c9) / 2.0
        if float((dv.geo[1]["verts"].mean(axis=0) - cbar) @ n) <= 0.0:
            n = -n
        return n, cbar

    def pinned_constants(self):
        """The fixed+forced membranes' h_min at the pinned plane (constants of
        the corpse: empty BONE_PLAN chains; forearms at the forced elbow floor)."""
        dv = self.dv
        n, cbar = self.pinned_plane()
        out = {}
        for r in NONPAD_BONES:
            h = (dv.geo[r]["verts"] - cbar) @ n
            out[r] = float(h.min())
        return out, n

    # ------------------------------------------------------ seat constraints
    def seats(self, x):
        return self.dv.all_seat_constraints(x)

    # -------------------------------------------------------- strict solve
    def strict_objective(self, x):
        V, d = self.dv.objective_terms(x)
        return V + self.dv.kappa * d

    def strict_solve(self, x0):
        from scipy.optimize import minimize
        dv = self.dv
        res = minimize(self.strict_objective, np.asarray(x0, dtype=np.float64),
                       method="SLSQP", bounds=dv.bounds(),
                       constraints=[{"type": "ineq", "fun": lambda z: self.t3_slacks(z)}],
                       options={"ftol": 1e-12, "maxiter": 400})
        x = np.asarray(res.x, dtype=np.float64)
        V, d = dv.objective_terms(x)
        t3 = self.t3_slacks(x)
        seats = self.seats(x)
        return {
            "start": [rnd(v) for v in np.asarray(x0, dtype=np.float64)],
            "success": bool(res.success), "status": int(res.status),
            "message": str(res.message), "iterations": int(res.nit),
            "J_at_return": rnd(self.strict_objective(x)),
            "V_at_return": rnd(V), "d_at_return": rnd(d),
            "min_T3_slack_mm": rnd(float(t3.min())),
            "argmin_membrane": "bone_%02d" % NONPAD_BONES[int(np.argmin(t3))],
            "max_T3_violation_mm": rnd(max(0.0, float(-t3.min()))),
            "min_seat_slack_mm": rnd(float(seats.min())),
            "T1_V_le_V_v1": bool(V <= self.V_v1),
            "T2_d_le_d_v1": bool(d <= self.d_v1),
            "clearance_feasible_T1_T2": bool(res.success and t3.min() >= 0.0
                                             and seats.min() >= 0.0
                                             and V <= self.V_v1 and d <= self.d_v1),
        }

    # --------------------------------------------------------- the maximin
    def maximin_constraints(self, z):
        """All ineq >= 0: h_min(m) - t (21), V_rest - V, d_rest - d, seats (4)."""
        x, t = np.asarray(z[:10], dtype=np.float64), float(z[10])
        hs, _, _ = self.heights(x)
        vals = [hs[r][0] - t for r in NONPAD_BONES]
        V, d = self.dv.objective_terms(x)
        vals.append(self.dv.V_rest - V)
        vals.append(self.dv.d_rest - d)
        vals.extend(float(v) for v in self.seats(x))
        return np.array(vals)

    def maximin_solve(self, x0, t0):
        from scipy.optimize import minimize
        dv = self.dv
        z0 = np.concatenate([np.asarray(x0, dtype=np.float64), [float(t0)]])
        bounds = list(dv.bounds()) + [(-100.0, 100.0)]
        res = minimize(lambda z: -float(z[10]), z0, method="SLSQP",
                       bounds=bounds,
                       constraints=[{"type": "ineq", "fun": self.maximin_constraints}],
                       options={"ftol": 1e-12, "maxiter": 400})
        z = np.asarray(res.x, dtype=np.float64)
        x, t_solver = z[:10], float(z[10])
        hs, n, cbar = self.heights(x)
        t_true = min(hs[r][0] for r in NONPAD_BONES)
        V, d = dv.objective_terms(x)
        seats = self.seats(x)
        # binding-record table: each variable's distance to its nearest bound
        bnd = dv.bounds()
        binding = []
        for i, (nm, (lo, hi)) in enumerate(zip(StandingDerivation.VAR_NAMES, bnd)):
            dist_lo, dist_hi = abs(x[i] - lo), abs(x[i] - hi)
            edge = "lo" if dist_lo <= dist_hi else "hi"
            dist = min(dist_lo, dist_hi)
            binding.append({"var": nm, "theta": rnd(x[i]), "nearest_bound": edge,
                            "bound": rnd(lo if edge == "lo" else hi),
                            "distance_rad": rnd(dist),
                            "binding": bool(dist <= 1e-8)})
        argmin_r = NONPAD_BONES[int(np.argmin([hs[r][0] for r in NONPAD_BONES]))]
        # the FV2 lawfulness screen (amendment 4 section 6; boundary convention
        # per amendment 5: raw breaches recorded, clause-binding iff > tol_ip
        # = EPSILON_MM -- the committed resolution floor, section 5B)
        seat_breach = max(0.0, float(-seats.min()))
        capV_breach = max(0.0, float(V - dv.V_rest))
        capd_breach = max(0.0, float(d - dv.d_rest))
        range_breach = 0.0
        for i, (lo, hi) in enumerate(bnd):
            range_breach = max(range_breach, lo - x[i], x[i] - hi)
        lawful = bool(res.success
                      and t_true <= EPSILON_MM + 1e-9
                      and seat_breach <= EPSILON_MM
                      and capV_breach <= EPSILON_MM
                      and capd_breach <= EPSILON_MM
                      and range_breach <= EPSILON_MM)
        in_ranges = True
        for i, (lo, hi) in enumerate(bnd):
            if not (lo - 1e-12 <= x[i] <= hi + 1e-12):
                in_ranges = False
        return {
            "start_x": [rnd(v) for v in np.asarray(x0, dtype=np.float64)],
            "start_t": rnd(t0),
            "success": bool(res.success), "status": int(res.status),
            "message": str(res.message), "iterations": int(res.nit),
            "t_solver": rnd(t_solver), "t_max_recomputed_mm": rnd(t_true),
            "argmin_membrane": "bone_%02d" % argmin_r,
            "x_full": [float(v) for v in x],
            "x_R12": [rnd(v) for v in x],
            "V_at_pose": rnd(V), "d_at_pose": rnd(d),
            "cap_slack_V": rnd(dv.V_rest - V), "cap_slack_d": rnd(dv.d_rest - d),
            "cap_breaches_recorded": {"V_over_mm2": rnd(capV_breach),
                                      "d_over": rnd(capd_breach)},
            "seat_breach_mm_recorded": rnd(seat_breach),
            "min_seat_slack_mm": rnd(float(seats.min())),
            "in_ranges": bool(in_ranges),
            "lawful_screen_FV2": bool(lawful and in_ranges),
            "binding_bounds": binding,
            "per_membrane_h_min_mm": {("bone_%02d" % r): rnd(hs[r][0])
                                      for r in NONPAD_BONES},
        }

    def maximin_t0(self, x):
        hs, _, _ = self.heights(x)
        return min(hs[r][0] for r in NONPAD_BONES)
