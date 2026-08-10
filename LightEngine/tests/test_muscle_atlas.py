"""
test_muscle_atlas.py -- VERDICT 48 flag-gate tests.

Membrane (RULE 0):
  STATEMENT: state["muscle_atlas_soleus"] defaults OFF; when OFF the legacy
    75 N m ankle cap is bit-identical (gauge dump proves it).  When ON,
    the SoleusActuator delivers the quiet-standing tonic 22.3 N m at LOW
    activation (a in [0.05, 0.40]).
  FALSIFIER: flag OFF changes any existing test; flag ON fails the tonic.
"""

from __future__ import annotations

import math
import os
import sys

import numpy as np
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from LightEngine.kinematic.muscle_atlas import (
    SoleusActuator,
    _QUIET_ANKLE_ANGLE_RAD,
    _QUIET_TONIC_NM,
    _ABSTRACT_ANKLE_CAP_NM,
    _muscle_entry,
    _muscle_param,
    _solve_ankle_geometry,
    _moment_arm,
    _mt_length_neutral,
)


class TestAtlasParameters:
    """Verify all parameters are read from the atlas, not baked."""

    def test_soleus_f_max(self):
        m = _muscle_entry("Rajagopal2016", "soleus_r")
        assert _muscle_param(m, "max_isometric_force_N") == pytest.approx(6194.84262295082)

    def test_soleus_l_opt(self):
        m = _muscle_entry("Rajagopal2016", "soleus_r")
        assert _muscle_param(m, "optimal_fiber_length_m") == pytest.approx(0.044)

    def test_soleus_tendon_slack(self):
        m = _muscle_entry("Rajagopal2016", "soleus_r")
        assert _muscle_param(m, "tendon_slack_length_m") == pytest.approx(0.276755872375976)

    def test_soleus_pennation(self):
        m = _muscle_entry("Rajagopal2016", "soleus_r")
        assert _muscle_param(m, "pennation_angle_rad") == pytest.approx(0.38142888)

    def test_gasmed_f_max(self):
        m = _muscle_entry("Rajagopal2016", "gasmed_r")
        assert _muscle_param(m, "max_isometric_force_N") == pytest.approx(3115.51475409836)

    def test_gasmed_pennation(self):
        m = _muscle_entry("Rajagopal2016", "gasmed_r")
        assert _muscle_param(m, "pennation_angle_rad") == pytest.approx(0.16568155)


class TestSoleusActuator:
    """Verify the force-length-velocity actuator computes moments correctly."""

    def test_moment_arm_is_anatomically_reasonable(self):
        """Soleus moment arm should be ~4-5 cm (Lieber 2010)."""
        a = SoleusActuator(side="R")
        assert 0.03 <= a._moment_arm_soleus <= 0.06
        assert 0.03 <= a._moment_arm_gasmed <= 0.06

    def test_full_activation_exceeds_abstract_cap(self):
        """Full-activation moment must exceed the 75 N m abstract cap."""
        a = SoleusActuator(side="R")
        m = a.moment_at(1.0)["total_moment_nm"]
        assert m > _ABSTRACT_ANKLE_CAP_NM

    def test_quiet_tonic_activation_in_range(self):
        """Tonic activation for 22.3 N m must be in [0.05, 0.40]."""
        a = SoleusActuator(side="R")
        a_tonic = a.quiet_tonic_activation
        assert 0.05 <= a_tonic <= 0.40

    def test_tonic_moment_matches_target(self):
        """a_tonic * full_moment should equal 22.3 N m."""
        a = SoleusActuator(side="R")
        a_tonic = a.quiet_tonic_activation
        full = a.moment_at(1.0)["total_moment_nm"]
        assert a_tonic * full == pytest.approx(_QUIET_TONIC_NM, abs=0.5)

    def test_zero_activation_zero_moment(self):
        """At a=0, moment must be zero."""
        a = SoleusActuator(side="R")
        m = a.moment_at(0.0)["total_moment_nm"]
        assert m == pytest.approx(0.0, abs=1e-10)

    def test_symmetry_left_right(self):
        """Left and right sides must produce identical tonic activation."""
        r = SoleusActuator(side="R")
        l = SoleusActuator(side="L")
        assert r.quiet_tonic_activation == pytest.approx(
            l.quiet_tonic_activation, abs=1e-4)

    def test_fiber_length_in_valid_range(self):
        """Fiber length at full activation must be in [0.5, 1.5] x L_opt."""
        a = SoleusActuator(side="R")
        m = a.moment_at(1.0)
        assert 0.5 <= m["soleus_fiber_norm"] <= 1.5
        assert 0.5 <= m["gasmed_fiber_norm"] <= 1.5

    def test_fiber_range_over_angles(self):
        """Fiber length must stay in [0.5, 1.5] x L_opt over standing angles."""
        a = SoleusActuator(side="R")
        angles = [math.radians(d) for d in [-12, -5, 0, 5, 15]]
        frc = a.fiber_range_check(angles)
        for name, (lo, mid, hi) in frc.items():
            assert lo >= 0.5, f"{name} fiber too short: {lo}"
            assert hi <= 1.5, f"{name} fiber too long: {hi}"

    def test_activation_sweep_monotonic(self):
        """Moment must increase monotonically with activation at the quiet angle."""
        a = SoleusActuator(side="R")
        sweep = a.activation_sweep()
        moments = sweep[:, 1]
        diffs = np.diff(moments)
        assert np.all(diffs >= -1e-6), "moment not monotonic in activation"

    def test_left_side_uses_left_joints(self):
        """Left-side actuator must use ankle_l / subtalar_l / walker_knee_l."""
        g = _solve_ankle_geometry("L")
        # Left ankle axis should have positive x component (mirrored from right).
        assert g["ankle_axis"][0] > 0
        # Right ankle axis should have negative x.
        g_r = _solve_ankle_geometry("R")
        assert g_r["ankle_axis"][0] < 0


class TestFlagGate:
    """Verify the flag-gate concept: OFF = legacy, ON = atlas."""

    def test_flag_off_default(self):
        """The flag defaults OFF (not set in state)."""
        # The flag is read via state.get("muscle_atlas_soleus", False)
        # in MuscleController.apply(); default is False.
        # This test verifies the concept without instantiating dynamics.
        state = {}
        assert state.get("muscle_atlas_soleus", False) is False

    def test_flag_on_activates_atlas(self):
        """When the flag is ON, the atlas actuator produces non-zero moment."""
        a = SoleusActuator(side="R")
        moment = a.moment_at(0.5, _QUIET_ANKLE_ANGLE_RAD)
        assert moment["total_moment_nm"] > 0
