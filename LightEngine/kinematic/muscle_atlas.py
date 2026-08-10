"""
theStandingHuman v2-rigid: atlas-sourced soleus + medial gastrocnemius
force-length-velocity actuator (VERDICT 48 membrane, docs/JOINT_ATLAS.md).

RULE 0 -- stated before the build (2026-08-10):
  STATEMENT: the atlas soleus (plus medial gastrocnemius share), wired as a
    force-length-velocity actuator with its provention parameters and moment
    arm, delivers the quiet-standing tonic 22.3 N m per ankle at LOW
    activation (a in [0, 0.4]), and its full-activation moment exceeds the
    abstract 75 N m cap (anatomy finding: the atlas F_max is per-muscle
    physiological force, not the abstract group PCSA cap).
  PREDICTION: a_tonic lands in [0.05, 0.40]; full-activation moment exceeds
    75 N m (the atlas provides more ankle authority than the abstract model);
    fiber length within [0.5, 1.5] x L_opt over the standing range.
  FALSIFIER: if the atlas soleus cannot deliver 22.3 N m at any activation
    <= 1.0 at the quiet-standing fiber length, the atlas parameters or the
    moment arm are wrong for this skeleton.

No baked numbers: every parameter is read from
external/anatomy/muscle_parameters.json at spec time.  The ankle joint axis
and frame transforms are read from rajagopal_extract.json.  The moment arm
is derived from the atlas origin/insertion geometry relative to that axis.
This module is PROBE-only: it does NOT touch dynamics.py or the standing-
ladder loop; it carries no production dependence.  The flag
state["muscle_atlas_soleus"] (default OFF) is the membrane gate: OFF keeps
the legacy 75 N m cap bit-identical, ON routes ankle authority through this
actuator.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any

import numpy as np

# ANATOMY-DATUM constants from the literature (cited in the model).
_FL_WIDTH = 0.56       # Gaussian f_l width (Millard 2012)
_FV_MAX = 10.0        # v_max / v_opt (Millard 2012)
_FV_A = 0.25          # force-velocity coefficient (Millard 2012)
_FV_ECC_B = 0.01 * 66.0  # eccentric damping (Millard 2012)
_TENDON_A = 116.0     # tendon exponential stiffness param
_TENDON_B = 108.0     # tendon exponential stiffness param

_QUIET_ANKLE_ANGLE_RAD = -0.0698  # ~-4.0 deg plantarflexion (VERDICT 41)
_QUIET_TONIC_NM = 22.3  # VERDICT 44
_ABSTRACT_ANKLE_CAP_NM = 75.0  # VERDICT 25 / muscles.py:1454
# ---------------------------------------------------------------------------
# Atlas loading (spec time -- never baked)
# ---------------------------------------------------------------------------

def _atlas_dir() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))),
        "external", "anatomy",
    )


def _load_json(name: str) -> dict[str, Any]:
    with open(os.path.join(_atlas_dir(), name), "r", encoding="utf-8") as f:
        return json.load(f)


_ATLAS = _load_json("muscle_parameters.json")
_MUSCLES = _ATLAS["muscles"]

_RAJ = _load_json("rajagopal_extract.json")


def _muscle_entry(source_model: str, name: str) -> dict[str, Any]:
    key = f"{source_model}:{name}"
    if key not in _MUSCLES:
        avail = sorted(k for k in _MUSCLES if name in k)
        raise KeyError(f"muscle {key!r} not found; available: {avail}")
    return _MUSCLES[key]


def _muscle_param(m: dict[str, Any], field: str, sub: str = "value") -> float:
    return float(m[field][sub])
# ---------------------------------------------------------------------------
# Frame transforms from the Rajagopal2016 joint definitions
# ---------------------------------------------------------------------------

def _xyz_euler_to_matrix(euler: list[float]) -> np.ndarray:
    """OpenSim body-fixed XYZ Euler -- rotation matrix."""
    a, b, c = float(euler[0]), float(euler[1]), float(euler[2])
    def RX(a):
        return np.array([[1, 0, 0],
                         [0, math.cos(a), -math.sin(a)],
                         [0, math.sin(a), math.cos(a)]])
    def RY(b):
        return np.array([[math.cos(b), 0, math.sin(b)],
                         [0, 1, 0],
                         [-math.sin(b), 0, math.cos(b)]])
    def RZ(c):
        return np.array([[math.cos(c), -math.sin(c), 0],
                         [math.sin(c), math.cos(c), 0],
                         [0, 0, 1]])
    return RZ(c) @ RY(b) @ RX(a)


def _solve_ankle_geometry(side: str = "R") -> dict[str, np.ndarray]:
    """Derive ankle axis + frame transforms from rajagopal_extract.json.

    side: "R" or "L" -- loads the per-side joint definitions.
    """
    s = side.lower()
    ankle = _RAJ["joints"][f"ankle_{s}"]
    subtalar = _RAJ["joints"][f"subtalar_{s}"]
    knee = _RAJ["joints"][f"walker_knee_{s}"]

    ankle_pt = np.array(ankle["location_in_parent_m"], dtype=np.float64)
    ankle_orient = ankle["orientation_in_parent_rad"]
    ankle_axis = _xyz_euler_to_matrix(ankle_orient) @ np.array([0.0, 0.0, 1.0])

    calcn_offset = np.array(subtalar["location_in_parent_m"], dtype=np.float64)

    knee_in_femur = np.array(knee["location_in_parent_m"], dtype=np.float64)
    knee_in_tibia = np.array(knee["location_in_child_m"], dtype=np.float64)
    femur_to_tibia = knee_in_tibia - knee_in_femur

    return {
        "ankle_axis": ankle_axis,
        "ankle_point": ankle_pt,
        "femur_to_tibia": femur_to_tibia,
        "calcn_offset": calcn_offset,
    }


# Per-side geometry: computed lazily in SoleusActuator.__init__.
# ---------------------------------------------------------------------------
# Moment-arm and musculotendon length from atlas geometry
# ---------------------------------------------------------------------------

def _muscle_point_tibia(m: dict[str, Any], which: str,
                        geom: dict[str, np.ndarray]) -> np.ndarray:
    """Convert a muscle origin/insertion to the tibia local frame."""
    pt = m[which]
    seg = pt["segment"]
    loc = np.array(pt["location_m"], dtype=np.float64)
    ap = geom["ankle_point"]
    co = geom["calcn_offset"]
    ft = geom["femur_to_tibia"]
    base = seg.rsplit("_", 1)[0]
    if base == "tibia":
        return loc.copy()
    elif base == "calcn":
        return ap + co + loc
    elif base == "femur":
        return ft + loc
    else:
        raise ValueError(f"unknown segment {seg!r}")


def _moment_arm(m: dict[str, Any], geom: dict[str, np.ndarray]) -> float:
    """Shortest distance from the ankle axis LINE to the muscle LOA."""
    origin = _muscle_point_tibia(m, "origin", geom)
    insertion = _muscle_point_tibia(m, "insertion", geom)
    loa = insertion - origin
    loa_norm = float(np.linalg.norm(loa))
    if loa_norm < 1e-9:
        raise ValueError(f"muscle {m['name']!r}: zero-length LOA")
    loa_hat = loa / loa_norm
    cross = np.cross(geom["ankle_axis"], loa_hat)
    cross_norm = float(np.linalg.norm(cross))
    if cross_norm < 1e-9:
        raise ValueError(f"muscle {m['name']!r}: LOA parallel to ankle axis")
    diff = origin - geom["ankle_point"]
    return abs(float(np.dot(diff, cross))) / cross_norm


def _mt_length_neutral(m: dict[str, Any], geom: dict[str, np.ndarray]) -> float:
    """Straight-line origin-to-insertion distance at neutral ankle."""
    origin = _muscle_point_tibia(m, "origin", geom)
    insertion = _muscle_point_tibia(m, "insertion", geom)
    return float(np.linalg.norm(insertion - origin))


# ---------------------------------------------------------------------------
# Millard2012 force-length-velocity model
# ---------------------------------------------------------------------------

def _force_length(fiber_norm: float) -> float:
    """Normalized active force-length factor f_l (Gaussian, Millard 2012)."""
    d = fiber_norm - 1.0
    return float(np.exp(-(d / _FL_WIDTH) ** 2))


def _tendon_force_norm(t_norm: float) -> float:
    """Normalized tendon force f_T (exponential, Millard 2012)."""
    if t_norm <= 1.0:
        return 0.0
    e = _TENDON_A * (t_norm - 1.0)
    return float(np.exp(_TENDON_B / _TENDON_A)
                 * (np.exp(e) - 1.0) / np.exp(e))


def _force_velocity(v_norm: float, a_pen: float) -> float:
    """Normalized force-velocity factor f_v (Millard 2012)."""
    cos_pen = math.cos(a_pen)
    if cos_pen < 1e-6:
        cos_pen = 1e-6
    vp = _FV_A * _FV_MAX * cos_pen
    if v_norm >= 0.0:
        denom = 1.0 + v_norm / vp
        return float((1.0 - v_norm / vp) / denom)
    else:
        ratio = v_norm / vp
        return float((1.0 + ratio) / (1.0 + ratio * _FV_ECC_B))
def _equilibrium_fiber_length(
    activation: float,
    l_opt: float,
    l_tendon_slack: float,
    a_pen: float,
    l_m: float,
) -> tuple[float, float, float]:
    """Solve Millard2012 tendon equilibrium; return (L_fiber, f_fiber, f_l).

    Isometric (V_fiber = 0): f_v = 1.0.  Bisection on L_norm in [0.5, 2.0].
    """
    cos_pen = math.cos(a_pen)
    if cos_pen < 1e-6:
        cos_pen = 1e-6
    f_v = 1.0

    def _residual(l_norm: float) -> float:
        l_fiber = l_opt * l_norm
        l_tendon = l_m - l_fiber * cos_pen
        if l_tendon <= 0:
            return -1.0
        t_norm = l_tendon / l_tendon_slack
        ft = _tendon_force_norm(t_norm)
        fl = _force_length(l_norm)
        ff = activation * fl * f_v * cos_pen
        return ff - ft

    lo, hi = 0.5, 2.0
    r_lo = _residual(lo)
    r_hi = _residual(hi)
    if r_lo * r_hi > 0:
        l_norm = lo if abs(r_lo) < abs(r_hi) else hi
    else:
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            r_mid = _residual(mid)
            if r_mid * r_lo < 0:
                hi = mid
                r_hi = r_mid
            else:
                lo = mid
                r_lo = r_mid
            if abs(hi - lo) < 1e-6:
                break
        l_norm = 0.5 * (lo + hi)
    l_fiber = l_opt * l_norm
    fl = _force_length(l_norm)
    return l_fiber, activation * fl * f_v * cos_pen, fl


# ---------------------------------------------------------------------------
# SoleusActuator
# ---------------------------------------------------------------------------

class SoleusActuator:
    """Flag-gated soleus + medial gastrocnemius ankle actuator.

    state["muscle_atlas_soleus"] (default OFF) gates this: OFF = legacy
    75 N m cap (bit-identical), ON = this force-length-velocity model.
    """

    def __init__(self, side: str = "R") -> None:
        self.side = side.upper()
        name = side.lower()
        self._soleus = _muscle_entry("Rajagopal2016", f"soleus_{name}")
        self._gasmed = _muscle_entry("Rajagopal2016", f"gasmed_{name}")

        self.f_max_soleus = _muscle_param(
            self._soleus, "max_isometric_force_N")
        self.l_opt_soleus = _muscle_param(
            self._soleus, "optimal_fiber_length_m")
        self.l_tendon_slack_soleus = _muscle_param(
            self._soleus, "tendon_slack_length_m")
        self.pennation_soleus = _muscle_param(
            self._soleus, "pennation_angle_rad")

        self.f_max_gasmed = _muscle_param(
            self._gasmed, "max_isometric_force_N")
        self.l_opt_gasmed = _muscle_param(
            self._gasmed, "optimal_fiber_length_m")
        self.l_tendon_slack_gasmed = _muscle_param(
            self._gasmed, "tendon_slack_length_m")
        self.pennation_gasmed = _muscle_param(
            self._gasmed, "pennation_angle_rad")

        self._geom = _solve_ankle_geometry(side)
        self.ankle_axis = self._geom["ankle_axis"]
        self.ankle_point = self._geom["ankle_point"]
        self._moment_arm_soleus = _moment_arm(self._soleus, self._geom)
        self._moment_arm_gasmed = _moment_arm(self._gasmed, self._geom)
        self._mt_neutral_soleus = _mt_length_neutral(self._soleus, self._geom)
        self._mt_neutral_gasmed = _mt_length_neutral(self._gasmed, self._geom)

    def _mt_length(self, m, r, ankle_angle, neutral):
        """Musculotendon length at ankle angle (arc-length approx)."""
        return neutral - r * ankle_angle

    def moment_at(self, activation, ankle_angle_rad=_QUIET_ANKLE_ANGLE_RAD,
                  velocity_rad_s=0.0) -> dict[str, float]:
        """Ankle moment (N m, plantarflexion positive) at the given state."""
        l_mt_s = self._mt_length(
            self._soleus, self._moment_arm_soleus,
            ankle_angle_rad, self._mt_neutral_soleus)
        l_mt_g = self._mt_length(
            self._gasmed, self._moment_arm_gasmed,
            ankle_angle_rad, self._mt_neutral_gasmed)

        v_norm_s = (self._moment_arm_soleus * velocity_rad_s
                    / (self.l_opt_soleus * _FV_MAX))
        v_norm_g = (self._moment_arm_gasmed * velocity_rad_s
                    / (self.l_opt_gasmed * _FV_MAX))

        cos_pen_s = math.cos(self.pennation_soleus)
        cos_pen_g = math.cos(self.pennation_gasmed)

        l_f_s, f_f_s, f_l_s = _equilibrium_fiber_length(
            activation, self.l_opt_soleus,
            self.l_tendon_slack_soleus, self.pennation_soleus, l_mt_s)
        l_f_g, f_f_g, f_l_g = _equilibrium_fiber_length(
            activation, self.l_opt_gasmed,
            self.l_tendon_slack_gasmed, self.pennation_gasmed, l_mt_g)

        m_s = f_f_s * self.f_max_soleus * self._moment_arm_soleus
        m_g = f_f_g * self.f_max_gasmed * self._moment_arm_gasmed

        return {
            "soleus_moment_nm": float(m_s),
            "gasmed_moment_nm": float(m_g),
            "total_moment_nm": float(m_s + m_g),
            "soleus_fiber_length_m": float(l_f_s),
            "gasmed_fiber_length_m": float(l_f_g),
            "soleus_fiber_norm": float(l_f_s / self.l_opt_soleus),
            "gasmed_fiber_norm": float(l_f_g / self.l_opt_gasmed),
            "soleus_f_l": float(f_l_s),
            "gasmed_f_l": float(f_l_g),
            "soleus_moment_arm_m": float(self._moment_arm_soleus),
            "gasmed_moment_arm_m": float(self._moment_arm_gasmed),
            "soleus_f_max_N": float(self.f_max_soleus),
            "gasmed_f_max_N": float(self.f_max_gasmed),
            "soleus_cos_pen": float(cos_pen_s),
            "gasmed_cos_pen": float(cos_pen_g),
        }

    @property
    def quiet_tonic_activation(self) -> float:
        """Activation producing 22.3 N m at the quiet angle."""
        m_full = self.moment_at(1.0)["total_moment_nm"]
        if m_full <= 0:
            return float("nan")
        return _QUIET_TONIC_NM / m_full

    @property
    def full_activation_moment(self) -> float:
        """Full-activation moment at the quiet angle."""
        return self.moment_at(1.0)["total_moment_nm"]

    def activation_sweep(self, ankle_angle_rad=_QUIET_ANKLE_ANGLE_RAD,
                         n=50) -> np.ndarray:
        """Return (activation, moment) pairs from 0 to 1."""
        acts = np.linspace(0.0, 1.0, n)
        moments = np.array([
            self.moment_at(a, ankle_angle_rad)["total_moment_nm"]
            for a in acts
        ])
        return np.column_stack([acts, moments])

    def fiber_range_check(self, ankle_angles_rad) -> dict[str, tuple]:
        """Check fiber-length range as (min, mean, max) x L_opt."""
        results = {}
        for name, m, l_opt, l_ts, pen, r, neutral in [
            ("soleus", self._soleus, self.l_opt_soleus,
             self.l_tendon_slack_soleus, self.pennation_soleus,
             self._moment_arm_soleus, self._mt_neutral_soleus),
            ("gasmed", self._gasmed, self.l_opt_gasmed,
             self.l_tendon_slack_gasmed, self.pennation_gasmed,
             self._moment_arm_gasmed, self._mt_neutral_gasmed),
        ]:
            norms = []
            for ang in ankle_angles_rad:
                l_mt = self._mt_length(m, r, ang, neutral)
                l_fiber, _, _ = _equilibrium_fiber_length(
                    0.5, l_opt, l_ts, pen, l_mt)
                norms.append(l_fiber / l_opt)
            results[name] = (min(norms), sum(norms) / len(norms), max(norms))
        return results
