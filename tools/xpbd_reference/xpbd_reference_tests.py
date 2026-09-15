"""The falsifier battery as pytest-style tests — house pattern (plain
functions + asserts, runnable under pytest OR directly: `python
xpbd_reference_tests.py`).

Mirrors PREREG.md's falsifiers (a)-(d) at the AMENDED bars the battery
measured (the original P2/P3 predictions' outcomes are recorded in
BATTERY_RESULTS.md; the prereg's own amendment protocol names the measured
boundary as the successor contract):

  (a) per-cell + coupled frequencies: within +-10% at n >= n_fidelity = 11;
      the MEASURED discrete bias must equal the DERIVED map bias (the solver
      is exactly the propagator) at every probed n;
  (b) XPBD n=4 stays BOUNDED under the press that diverges the explicit
      n=1 update; the explicit family's boundary lands between n=2 and n=4;
  (c) P1 pressure law + momentum conservation + servo reaction isolation;
  (d) negative controls: wrong compliance fails by the predicted V0 ratio;
      the balance gate REFUSES a single-point-contact balance.
"""
import numpy as np

from . import measured as M
from . import solver as S
from . import battery as B
from .model import SlabChain


# -- model integrity ----------------------------------------------------------
def test_chain_jacobians_match_finite_difference():
    """Every constraint row of the planar chain: analytic J vs central
    finite differences at a perturbed pose (rotation + offset + volume
    deviation). This catches a stale or mis-assembled Jacobian class-wide."""
    ch = SlabChain()
    ch.set_servo_target(1, 0.03)
    ch.sys.q += np.array([0.1, 0.05, 0.02, -0.05, 0.03, -0.01,
                          0.02, -0.04, 0.05, 0.0, 0.1, -0.03])
    C0, J0, a0 = ch.sys.stack()
    eps = 1e-7
    for k in range(12):
        dq = np.zeros(12)
        dq[k] = eps
        ch.sys.q += dq
        Cp, _, _ = ch.sys.stack()
        ch.sys.q -= 2 * dq
        Cm, _, _ = ch.sys.stack()
        ch.sys.q += dq
        fd = (Cp - Cm) / (2 * eps)
        np.testing.assert_allclose(J0[:, k], fd, atol=1e-5, rtol=1e-4)


def test_chain_rigid_modes_leave_volumes_unchanged():
    """Translation and rotation of the whole chain about a COMMON point
    change no cell volume (the piston Jacobian has the rigid modes in its
    null space)."""
    ch = SlabChain()
    V0 = S.volume_deviations(ch.sys).copy()
    th, c, s = 0.01, np.cos(0.01), np.sin(0.01)
    for i in range(4):
        x, y = ch.sys.q[3 * i], ch.sys.q[3 * i + 1]
        ch.sys.q[3 * i] = c * x - s * y
        ch.sys.q[3 * i + 1] = s * x + c * y
        ch.sys.q[3 * i + 2] += th
    np.testing.assert_allclose(S.volume_deviations(ch.sys), V0, atol=1e-12)


# -- falsifier (a): frequencies ----------------------------------------------
def test_falsifier_a_rigs_at_fidelity_count():
    """+-10% at n = n_fidelity = 11, every cell."""
    for row in B.p3_rigs()[M.N_FIDELITY_10PCT]:
        assert abs(row["miss_percent"]) <= 10.0, row


def test_falsifier_a_ring_at_fidelity_count():
    """Coupled 1949.0 +-10% at n = 11 (all three modes)."""
    for row in B.p3_ring()[M.N_FIDELITY_10PCT]:
        assert abs(row["miss_percent"]) <= 10.0, row


def test_falsifier_a_operating_point_misses_as_derived():
    """At the operating point n=4 the stiff bars MISS +-10% (falsifier fired)
    — and the measured miss equals the DERIVED discrete-map bias to <1%:
    the miss is the discretization, not the model."""
    for rows in (B.p3_rigs()[4], B.p3_ring()[4]):
        for row in rows:
            assert abs(row["miss_percent"] - row["derived_bias_percent"]) < 0.05, row


def test_falsifier_a_model_validated_at_high_n():
    """n=32: every bar within 2% — areas, compliances and reduced masses are
    the world's; the n=4 miss was step-size, not geometry."""
    for rows in (B.p3_rigs()[32], B.p3_ring()[32]):
        for row in rows:
            assert abs(row["miss_percent"]) <= 2.0, row


# -- falsifier (b): boundedness ----------------------------------------------
def test_falsifier_b_xpbd_bounded_where_explicit_diverges():
    """THE demo: the coupled solve at n=4 stays bounded under the probe press
    that diverges the explicit n=1 update."""
    b = B.p2_boundary()
    assert b[("xpbd", 4)]["diverged_at"] is None
    assert b[("explicit", 1)]["diverged_at"] is not None
    assert b[("explicit", 1)]["diverged_at"] <= 10


def test_falsifier_b_explicit_boundary_at_predicted_n():
    """The eta<2 law is the EXPLICIT family's law: explicit diverges at n=1,2
    and is bounded at n=4 — the boundary lands exactly where derived."""
    b = B.p2_boundary()
    assert b[("explicit", 2)]["diverged_at"] is not None
    assert b[("explicit", 4)]["diverged_at"] is None
    # the measured growth rate matches the derived symplectic-Euler multiplier
    derived = np.log(B.derived_explicit_multiplier(M.OMEGA_COUPLED, 1))
    got = b[("explicit", 1)]["log_growth_per_tick"]
    assert abs(got - derived) / abs(derived) < 0.10, (got, derived)


def test_falsifier_b_xpbd_bounded_at_all_n():
    """The prereg's named alternative branch: the IMPLICIT coupled solve is
    bounded at every probed substep count (the gate over-predicted for it;
    measured boundary replaces the prediction — see BATTERY_RESULTS.md)."""
    b = B.p2_boundary()
    for (family, n), row in b.items():
        if family == "xpbd":
            assert row["diverged_at"] is None, (family, n, row)


# -- falsifier (c) / P1: the pressure law ------------------------------------
def test_p1_pressure_law_at_rest():
    r = B.p1_rest()
    assert r["max_P_pa"] < 1e-6
    assert r["max_dV_rel"] < 1e-12


def test_p1_pressure_recovery_under_press():
    r = B.p1_under_press()
    assert r["miss_percent"] < 1.0, r


def test_pressure_sign_convention():
    """Compress a cell (dV < 0): recovered P must be POSITIVE and equal
    -dV/(kappa V0) — Astra's sign convention, the engine's law."""
    sys = B.ring_coupled()
    sys.q[:] = 0.0
    sys.q[2] = -1e-4          # hip plane pushed down: cells 2,3 compressed
    rep = S.xpbd_tick(sys, n_sub=M.N_STABILITY)
    dV = S.volume_deviations(sys)
    P = rep.pressure
    compressed = dV < 0
    assert np.any(compressed)
    assert np.all(P[compressed] > 0.0)


# -- P4: servo reactions (the coupling is real) ------------------------------
def test_p4_servo_exerts_reaction_pair_not_pose_write():
    """The servo row is (0,...,-1,+1,...): equal and opposite torque on the
    two joined slabs, by construction; the battery measures the momentum
    isolation, here we assert the row shape + zero net impulse directly."""
    ch = SlabChain()
    ch.set_servo_target(1, 0.05)
    sys = ch.sys
    C, J, a = sys.stack()
    servo_rows = [i for i, r in enumerate(sys.rows) if r.name.startswith("servo")]
    j = 1  # knee
    row = J[4 + 2 * j + 1]   # rows: 4 volume + (pin,servo)x3 -> servo_j = 4+2j+1
    assert row[3 * 1 + 2] == -1.0 and row[3 * 2 + 2] == +1.0
    assert np.count_nonzero(row) == 2
    # net generalized impulse of that row is identically zero (reaction pair)
    assert abs(row.sum()) < 1e-15
    # ...and the solve keeps BOTH momenta at the transport floor while the
    # servo drives the joint from rest (measured: dp 6.8e-13, dL 2.4e-3)
    r = B.p4_servo_reaction()
    assert r["solve_dp"] < 1e-9, r
    assert abs(r["solve_dL"]) < 0.01, r


def test_p4_pose_overwrite_injects_momentum():
    """P4 is where the two architectures differ: the pose overwrite (the
    joint_deg_ idealization) injects angular momentum ~700x the coupled
    solve's transport floor — the measurable signature of bypassed coupling."""
    r = B.p4_servo_reaction()
    assert abs(r["overwrite_dL"]) > 0.1, r                     # measured 1.63
    assert abs(r["solve_dL"]) < 0.02 * abs(r["overwrite_dL"]), r


# -- P5: momentum conservation -----------------------------------------------
def test_p5_momentum_conserved_100_ticks():
    """Prereg bar: drift < 0.1% of the momentum scale over 100 coupled ticks.
    Measured 4e-6 percent (consistent rigid-field start): the constraint
    kicks are momentum-neutral to machine precision; what remains is bounded
    projection-transport during corrections."""
    r = B.p5_momentum()
    assert r["drift_percent"] < 0.1, r          # the prereg bar
    assert r["drift_percent"] < 0.001, r        # 100x margin; measured 4e-6
    assert r["max_dp"] < 1e-9, r                # linear momentum: exact to fp
    assert r["transient_start_max_dL"] < 1.0, r  # bounded even from a
    # constraint-violating impulse start (measured 0.055 of |L0|=22814)


# -- falsifier (d): negative controls ----------------------------------------
def test_wrong_compliance_fails_by_predicted_ratio():
    """alpha = kappa (missing V0) must fail the pressure check with
    P_wrong/P_true = V0 per cell — the predicted ratio."""
    r = B.wrong_compliance_control()
    np.testing.assert_allclose(r["measured_ratio"], r["predicted_ratio"],
                               rtol=0.05)
    assert r["miss_percent"] > 1.0   # the check itself FAILS, as predicted


def test_balance_gate_refuses_single_point_contact():
    p6 = {k: v[0] for k, v in B.p6_balance().items()}
    detail = {k: v[1] for k, v in B.p6_balance().items()}
    assert p6["stance"] is True                    # real stance passes
    assert p6["single_point"] is False             # knife edge refused
    assert p6["com_outside"] is False              # outside support refused
    assert not detail["single_point"]["support_ok"]
    # the finding the prereg names: the FORCE gate alone can pass on a single
    # point — the refusal comes from the support-interior and moment gates
    assert detail["single_point"]["force_ok"]
    assert not detail["single_point"]["moment_ok"]


if __name__ == "__main__":
    import sys
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS %s" % name)
            except AssertionError as e:
                fails += 1
                print("FAIL %s: %s" % (name, e))
    sys.exit(1 if fails else 0)
