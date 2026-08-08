"""
Tests for LightEngine/kinematic/dynamics.py (Lane K2 rigid-body dynamics).

Verifies semi-implicit Euler + one iterated constraint-projection loop on
simplified rigs and on the full 77-link skeleton.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest

from LightEngine.kinematic import build_spec
from LightEngine.kinematic import transforms
from LightEngine.kinematic.dynamics import (
    center_of_mass,
    contact_forces,
    derive_ligament_stiffness,
    init_state,
    joint_reactions,
    state_poses,
    step,
)
from LightEngine.kinematic.skeleton_spec import BALL_CUP, HINGE, SUTURE


GRAVITY = 9.80665


def _mklink(name, parent, prox, dist, mass, inertia):
    """Build a minimal link record for a dynamics spec."""
    axis = dist - prox
    length = float(np.linalg.norm(axis))
    return {
        "name": name,
        "parent_name": parent,
        "joint_name": name if parent else None,
        "prox_lu": prox,
        "dist_lu": dist,
        "prox_m": prox,
        "dist_m": dist,
        "length_lu": length,
        "length_m": length,
        "mass_kg": mass,
        "com_offset_lu": 0.5 * axis,
        "com_offset_m": 0.5 * axis,
        "inertia_diag_lu": inertia,
        "inertia_diag_m": inertia,
        "R_world_to_local": np.eye(3),
        "basis_x": np.array([1.0, 0.0, 0.0]),
        "basis_y": np.array([0.0, 1.0, 0.0]),
        "basis_z": np.array([0.0, 0.0, 1.0]),
        "joint_center_local_lu": (np.zeros(3) if parent else None),
        "joint_center_local_m": (np.zeros(3) if parent else None),
    }


@pytest.fixture(scope="module")
def spec():
    """Shared full 77-link spec built once per test module."""
    return build_spec(1.80, 80.0)


def _ligament_spec() -> dict[str, Any]:
    """Parent rod + child rod with a slack/taut ligament between endpoints."""
    links = {
        "parent": _mklink(
            "parent", None, np.zeros(3), np.array([0.0, 0.0, 1.0]), 1.0, np.ones(3) * 0.1
        ),
        "child": _mklink(
            "child",
            "parent",
            np.array([0.0, 0.0, 1.0]),
            np.array([0.0, 0.0, 2.0]),
            1.0,
            np.ones(3) * 0.1,
        ),
    }
    joints = {
        "child": {
            "name": "child",
            "parent_link": "parent",
            "child_link": "child",
            "center_parent_local_lu": np.array([0.0, 0.0, 1.0]),
            "center_parent_local_m": np.array([0.0, 0.0, 1.0]),
            "center_child_local_lu": np.array([0.0, 0.0, 0.0]),
            "center_child_local_m": np.array([0.0, 0.0, 0.0]),
            "center_lu": np.array([0.0, 0.0, 1.0]),
            "center_m": np.array([0.0, 0.0, 1.0]),
            "dof_class": BALL_CUP,
            "axes": [],
        },
    }
    # Ligament from parent distal to child COM; length varies with child angle.
    spec = {
        "links": links,
        "joints": joints,
        "ligaments": [
            {
                "name": "test_lig",
                "anchor_a": {"link": "parent", "offset_m": np.array([0.0, 0.0, 0.5])},
                "anchor_b": {"link": "child", "offset_m": np.array([0.0, 0.0, 0.5])},
                "rest_length_m": 1.0,
                "stiffness": None,
            }
        ],
        "contacts": {"L": [], "R": []},
        "lam": 1.0,
        "mass_kg": 2.0,
    }
    derive_ligament_stiffness(spec)
    return spec


def _hinge_spec() -> dict[str, Any]:
    """Single hinge pendulum: pinned base + uniform rod."""
    links = {
        "base": _mklink("base", None, np.zeros(3), np.zeros(3), 0.0, np.ones(3)),
        "rod": _mklink(
            "rod",
            "base",
            np.array([0.0, 0.0, 0.0]),
            np.array([0.0, 0.0, 1.0]),
            1.0,
            np.array([0.1, 0.1, 0.01]),
        ),
    }
    joints = {
        "rod": {
            "name": "rod",
            "parent_link": "base",
            "child_link": "rod",
            "center_parent_local_lu": np.zeros(3),
            "center_parent_local_m": np.zeros(3),
            "center_child_local_lu": np.zeros(3),
            "center_child_local_m": np.zeros(3),
            "center_lu": np.zeros(3),
            "center_m": np.zeros(3),
            "dof_class": HINGE,
            "axes": [np.array([0.0, 1.0, 0.0])],
        },
    }
    return {
        "links": links,
        "joints": joints,
        "ligaments": [],
        "contacts": {"L": [], "R": []},
        "lam": 1.0,
        "mass_kg": 1.0,
    }


def _suture_spec() -> dict[str, Any]:
    """Two-link chain locked by a suture joint."""
    links = {
        "base": _mklink("base", None, np.zeros(3), np.zeros(3), 0.0, np.ones(3)),
        "rod": _mklink(
            "rod", "base", np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]), 1.0, np.ones(3) * 0.1
        ),
    }
    joints = {
        "rod": {
            "name": "rod",
            "parent_link": "base",
            "child_link": "rod",
            "center_parent_local_lu": np.zeros(3),
            "center_parent_local_m": np.zeros(3),
            "center_child_local_lu": np.zeros(3),
            "center_child_local_m": np.zeros(3),
            "center_lu": np.zeros(3),
            "center_m": np.zeros(3),
            "dof_class": SUTURE,
            "axes": [],
        },
    }
    return {
        "links": links,
        "joints": joints,
        "ligaments": [],
        "contacts": {"L": [], "R": []},
        "lam": 1.0,
        "mass_kg": 1.0,
    }


def _chain3_spec() -> dict[str, Any]:
    """Three-link vertical chain in free fall."""
    links = {
        "A": _mklink("A", None, np.zeros(3), np.array([0.0, 0.0, 1.0]), 1.0, np.ones(3) * 0.1),
        "B": _mklink("B", "A", np.array([0.0, 0.0, 1.0]), np.array([0.0, 0.0, 2.0]), 1.0, np.ones(3) * 0.1),
        "C": _mklink("C", "B", np.array([0.0, 0.0, 2.0]), np.array([0.0, 0.0, 3.0]), 1.0, np.ones(3) * 0.1),
    }
    joints = {}
    for child, parent in (("B", "A"), ("C", "B")):
        joints[child] = {
            "name": child,
            "parent_link": parent,
            "child_link": child,
            "center_parent_local_lu": np.array([0.0, 0.0, 0.5]),
            "center_parent_local_m": np.array([0.0, 0.0, 0.5]),
            "center_child_local_lu": np.array([0.0, 0.0, -0.5]),
            "center_child_local_m": np.array([0.0, 0.0, -0.5]),
            "center_lu": np.array([0.0, 0.0, 0.0]),
            "center_m": np.array([0.0, 0.0, 0.0]),
            "dof_class": BALL_CUP,
            "axes": [],
        }
    return {
        "links": links,
        "joints": joints,
        "ligaments": [],
        "contacts": {"L": [], "R": []},
        "lam": 1.0,
        "mass_kg": 3.0,
    }


# ---------------------------------------------------------------------------
# Ligament behavior
# ---------------------------------------------------------------------------
def test_ligament_tension_only():
    """A ligament shorter than rest length must exert no force; stretched, it pulls."""
    spec = _ligament_spec()

    # Slack configuration: child points up, anchor distance == rest length, so
    # the rope is not stretched and must exert NO force (exact free fall).
    state = init_state(spec, joint_angles={"child": np.zeros(3)})
    state["lin_vel"][:] = 0.0
    step(spec, state, 1e-3, n_proj_iters=20)
    # No ligament force -> child falls with gravity only.
    np.testing.assert_allclose(
        state["lin_vel"][state["name_to_idx"]["child"]],
        np.array([0.0, 0.0, -GRAVITY * 1e-3]),
        atol=1e-10,
    )

    # Taut configuration: the child HANGS from the ligament alone.  The
    # velocity-level rope only resists SEPARATION, so a meaningful test needs
    # the anchor above the load: pin the parent (massless), point the child
    # down, and strip the joint from the state arrays so only the ligament
    # can act (the joint would carry the load and mask the rope).
    spec2 = _ligament_spec()
    spec2["links"]["parent"]["mass_kg"] = 0.0
    spec2["ligaments"][0]["anchor_a"]["offset_m"] = np.array([0.0, 0.0, 1.0])
    spec2["ligaments"][0]["anchor_b"]["offset_m"] = np.array([0.0, 0.0, 0.5])
    spec2["ligaments"][0]["rest_length_m"] = 0.6
    state = init_state(spec2, joint_angles={"child": np.array([0.0, math.pi, 0.0])})
    for key in ("joint_parent", "joint_child", "joint_dof", "joint_axes_arr",
                "r_joint_parent_local", "r_joint_child_local", "joint_q_rel0"):
        state[key] = state[key][:0]
    state["joint_names"] = []
    child_idx = state["name_to_idx"]["child"]

    # The child free-falls the 0.1 m slack (bind distance 0.5, rest 0.6),
    # which takes sqrt(2*0.1/g) ~ 143 ticks, then the rope catches and holds.
    for _ in range(200):
        step(spec2, state, 1e-3, n_proj_iters=20)

    child_v = state["lin_vel"][child_idx]
    # Held: vertical velocity ~ 0 (free fall for 0.2 s would be ~ -2 m/s).
    assert child_v[2] > -1e-6
    # Ligament is along z, so no horizontal force.
    assert abs(child_v[0]) < 1e-10
    assert abs(child_v[1]) < 1e-10
    # Hangs exactly at anchor_z - rest_length (1.0 - 0.6).
    assert state["pos"][child_idx][2] == pytest.approx(0.4, abs=1e-6)


# ---------------------------------------------------------------------------
# Contact behavior
# ---------------------------------------------------------------------------
def test_contact_repulsion_only():
    """Contacts push up only when penetrating and do not pull when separated."""
    # Free root foot (NO joint): a joint to a pinned base would carry the load
    # and mask the contact entirely.  Use the tarsals_L name so the dynamics
    # module builds contact records for it.  Zero-length link so the contact
    # point sits at the COM.
    links = {
        "tarsals_L": _mklink(
            "tarsals_L", None, np.zeros(3), np.zeros(3), 1.0, np.ones(3) * 0.01
        ),
    }
    spec = {
        "links": links,
        "joints": {},
        "ligaments": [],
        "contacts": {
            "L": [{"point_m": np.array([0.0, 0.0, 0.0])}],
            "R": [],
        },
        "lam": 1.0,
        "mass_kg": 1.0,
    }

    # Foot above ground: no contact force.
    state = init_state(spec)
    foot_idx = state["name_to_idx"]["tarsals_L"]
    state["pos"][foot_idx] = np.array([0.0, 0.0, 0.2])
    step(spec, state, 1e-3, n_proj_iters=20)
    cf = contact_forces(spec, state)
    assert len(cf) == 0

    # Foot penetrating: contact force upward (supports the link's weight).
    state = init_state(spec)
    state["pos"][foot_idx] = np.array([0.0, 0.0, -0.01])
    step(spec, state, 1e-3, n_proj_iters=20)
    cf = contact_forces(spec, state)
    assert len(cf) == 1
    f = list(cf.values())[0]
    assert f[2] > 0.0
    # Horizontal friction should be zero when there is no tangential velocity.
    assert abs(f[0]) < 1e-6
    assert abs(f[1]) < 1e-6


# ---------------------------------------------------------------------------
# Suture lock
# ---------------------------------------------------------------------------
def test_suture_locks_relative_orientation():
    """A suture joint keeps the child aligned with the parent despite torques."""
    spec = _suture_spec()
    state = init_state(spec, joint_angles={"rod": 0.05})

    for _ in range(100):
        step(spec, state, 1e-3, n_proj_iters=50)

    q_rel = transforms.multiply(transforms.conjugate(state["quat"][0]), state["quat"][1])
    if q_rel[0] < 0:
        q_rel = -q_rel
    q_err = transforms.multiply(transforms.conjugate(state["joint_q_rel0"][0]), q_rel)
    if q_err[0] < 0:
        q_err = -q_err
    assert np.linalg.norm(q_err[1:]) < 1e-3


# ---------------------------------------------------------------------------
# Hinge pendulum
# ---------------------------------------------------------------------------
def test_hinge_pendulum_period():
    """A uniform rod hinged at one end oscillates with the expected period."""
    spec = _hinge_spec()
    # Release HANGING with 0.1 rad amplitude: pi - 0.1 about the free axis
    # puts the rod straight down, tilted 0.1 toward +x.  (A near-vertical
    # release is an inverted pendulum that topples; its atan2 trace wraps at
    # +-pi and the peak detector below cannot count it.)
    state = init_state(spec, joint_angles={"rod": math.pi - 0.1})
    dt = 1e-3

    thetas = []
    for _ in range(3500):
        step(spec, state, dt, n_proj_iters=50)
        distal = state_poses(spec, state)["rod"][0] + transforms.rotate(
            state["quat"][1], np.array([0.0, 0.0, 1.0])
        )
        theta = math.atan2(distal[0], distal[2])
        thetas.append(theta)

    # Unwrap: the hanging pendulum's atan2 trace crosses the +-pi discontinuity
    # at the bottom of every swing, which would count a spurious "peak" at the
    # wrap and halve the measured period (measured 0.841 s vs 1.64 s).
    thetas = list(np.unwrap(np.array(thetas)))

    # Locate positive peaks; the interval between consecutive peaks is one period.
    peaks = []
    for i in range(1, len(thetas) - 1):
        if thetas[i] > thetas[i - 1] and thetas[i] > thetas[i + 1] and thetas[i] > 0.01:
            peaks.append(i)
        if len(peaks) >= 3:
            break

    assert len(peaks) >= 2, "pendulum did not complete a full oscillation"
    period_steps = peaks[1] - peaks[0]
    period = period_steps * dt

    # Theoretical small-angle period for a uniform rod pivoted at one end.
    L = 1.0
    T_theory = 2.0 * math.pi * math.sqrt(2.0 * L / (3.0 * GRAVITY))
    # Allow 8% tolerance for finite amplitude and numerical damping.
    assert period == pytest.approx(T_theory, rel=0.08)


# ---------------------------------------------------------------------------
# Free-fall COM
# ---------------------------------------------------------------------------
def test_three_link_chain_com_free_fall():
    """A chain with no constraints on the root falls with COM acceleration g."""
    spec = _chain3_spec()
    state = init_state(spec)
    initial_com_z = float(center_of_mass(spec, state)[2])
    dt = 1e-3
    steps = 100

    for _ in range(steps):
        step(spec, state, dt, n_proj_iters=20)

    com_z = float(center_of_mass(spec, state)[2])
    t = steps * dt
    expected_z = initial_com_z - 0.5 * GRAVITY * t * t
    assert com_z == pytest.approx(expected_z, abs=1e-2)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------
def test_determinism():
    """Two identical runs produce identical states."""
    spec = _chain3_spec()
    state_a = init_state(spec)
    state_b = init_state(spec)
    dt = 1e-3

    for _ in range(50):
        step(spec, state_a, dt, n_proj_iters=20)
        step(spec, state_b, dt, n_proj_iters=20)

    np.testing.assert_allclose(state_a["pos"], state_b["pos"], atol=1e-12)
    np.testing.assert_allclose(state_a["quat"], state_b["quat"], atol=1e-12)
    np.testing.assert_allclose(state_a["lin_vel"], state_b["lin_vel"], atol=1e-12)
    np.testing.assert_allclose(state_a["ang_vel"], state_b["ang_vel"], atol=1e-12)


# ---------------------------------------------------------------------------
# Full-skeleton smoke tests
# ---------------------------------------------------------------------------
def test_full_skeleton_init_and_free_fall_com(spec):
    """The 77-link spec initializes and its COM accelerates downward under gravity."""
    state = init_state(spec)
    # Disable contacts for the free-fall test: the numba core reads the FLAT
    # arrays, so clearing the dict records alone does nothing.
    state["contact_records"] = []
    state["contact_link_idx"] = state["contact_link_idx"][:0]
    state["contact_off_local"] = state["contact_off_local"][:0]
    initial_com_z = float(center_of_mass(spec, state)[2])
    dt = 1e-3
    steps = 50

    for _ in range(steps):
        step(spec, state, dt, n_proj_iters=50)

    com_z = float(center_of_mass(spec, state)[2])
    # COM must fall.
    assert com_z < initial_com_z
    # Velocity must remain bounded (no explosion).
    assert np.max(np.linalg.norm(state["lin_vel"], axis=1)) < 100.0


def test_full_skeleton_static_equilibrium_contact_forces(spec):
    """Contacts push upward and carry a substantial fraction of the crumple.

    STATIC equilibrium is IMPOSSIBLE for this frame: the 77-link skeleton is
    unactuated (no muscles), and its hinge/saddle dofs are free, so the body
    crumples under gravity even with rotation locks (measured 2026-08-08:
    head z 1.76 m -> 0.04 m in 600 ticks through the FREE dofs).  A crumpling
    body legitimately has F_up < M*g because the COM accelerates downward.
    What this test asserts instead of equilibrium:
      - contacts engage and push UP (never pull),
      - over the first 100 ticks the mean upward force is a substantial
        fraction of body weight (the feet genuinely carry the lower body),
      - velocities stay bounded (the crumple dissipates; no explosion).
    """
    state = init_state(spec)
    dt = 1e-3

    ups = []
    vmax = 0.0
    for _ in range(100):
        step(spec, state, dt, n_proj_iters=20)
        cf = contact_forces(spec, state)
        ups.append(sum(f[2] for f in cf.values()))
        vmax = max(vmax, float(np.max(np.linalg.norm(state["lin_vel"], axis=1))))

    ups = np.asarray(ups)
    total_weight = spec["mass_kg"] * GRAVITY
    # Contacts engage (nearly every tick) and push up.
    assert (ups > 0.0).sum() >= 90
    # They carry a substantial fraction of the crumpling body's weight.
    assert ups.mean() > 0.2 * total_weight
    # The crumple dissipates; nothing explodes.
    assert vmax < 15.0


# ---------------------------------------------------------------------------
# Reactions telemetry
# ---------------------------------------------------------------------------
def test_joint_reactions_shape_and_units():
    """joint_reactions returns a force and torque for every joint after a step."""
    spec = _hinge_spec()
    state = init_state(spec)
    step(spec, state, 1e-3, n_proj_iters=20)

    reactions = joint_reactions(spec, state)
    assert set(reactions.keys()) == set(spec["joints"].keys())
    for force, torque in reactions.values():
        assert force.shape == (3,)
        assert torque.shape == (3,)
        assert np.all(np.isfinite(force))
        assert np.all(np.isfinite(torque))


def test_joint_reactions_balance_weight():
    """For a stationary rod hinged to a pinned base, the vertical joint reaction equals weight."""
    spec = _hinge_spec()
    state = init_state(spec)
    # Hold the rod near vertical and let it settle.
    for _ in range(100):
        step(spec, state, 1e-3, n_proj_iters=50)

    reactions = joint_reactions(spec, state)
    force_on_child = reactions["rod"][0]
    # Reaction on child from parent must balance gravity: upward force ~ m*g.
    assert force_on_child[2] == pytest.approx(spec["mass_kg"] * GRAVITY, rel=0.10)


# ---------------------------------------------------------------------------
# Muscle lane: external torque channel + derived-gain PD controller
# ---------------------------------------------------------------------------
def _free_link_spec() -> dict[str, Any]:
    """One floating rod, no joints: the cleanest torque-injection probe."""
    links = {
        "rod": _mklink(
            "rod", None, np.zeros(3), np.array([0.0, 0.0, 1.0]),
            2.0, np.array([0.2, 0.2, 0.01]),
        ),
    }
    return {
        "links": links,
        "joints": {},
        "ligaments": [],
        "contacts": {"L": [], "R": []},
        "lam": 1.0,
        "mass_kg": 2.0,
    }


def test_ext_torque_channel_obeys_euler():
    """A known torque on a free link gives dw = I^-1 @ tau * dt, exactly."""
    from LightEngine.kinematic.muscle_controller import MuscleController  # noqa: F401
    spec = _free_link_spec()
    state = init_state(spec)
    n = len(state["link_names"])
    state["ext_force"] = np.zeros((n, 3))
    state["ext_torque"] = np.zeros((n, 3))
    tau = np.array([0.0, 1.5, 0.0])
    dt = 1e-3
    # One tick: local frame is identity, so I^-1 @ tau = tau / I_yy.
    state["ext_torque"][0] = tau
    step(spec, state, dt, n_proj_iters=5)
    expected = dt * tau[1] / state["inertia_diag_local"][0][1]
    assert state["ang_vel"][0][1] == pytest.approx(expected, rel=1e-9)
    # No force channel engaged: linear velocity must be gravity-only.
    assert state["lin_vel"][0][2] == pytest.approx(-dt * GRAVITY, rel=1e-12)


def test_zero_ext_channel_is_a_no_op():
    """Explicit zero ext arrays reproduce the unactuated trajectory bitwise."""
    spec = _hinge_spec()
    s1 = init_state(spec)
    for _ in range(50):
        step(spec, s1, 1e-3, n_proj_iters=20)

    s2 = init_state(spec)
    n = len(s2["link_names"])
    s2["ext_force"] = np.zeros((n, 3))
    s2["ext_torque"] = np.zeros((n, 3))
    for _ in range(50):
        step(spec, s2, 1e-3, n_proj_iters=20)

    assert np.array_equal(s1["pos"], s2["pos"])
    assert np.array_equal(s1["quat"], s2["quat"])
    assert np.array_equal(s1["ang_vel"], s2["ang_vel"])


def test_controller_holds_inverted_hinge():
    """The derived-gain PD holds an inverted hinge upright; unactuated it falls.

    The hinge rig's rod starts vertical (COM above the joint): an inverted
    pendulum.  With the controller attached the y-dof is closed; without it
    the rod falls.  Rotation locks stay ON here -- the rig tests the one free
    dof, the other two are the test fixture.
    """
    from LightEngine.kinematic.muscle_controller import MuscleController

    spec = _hinge_spec()
    dt = 1e-3
    # Seed with an initial angular velocity: exactly vertical + exactly zero
    # velocity is the unstable fixed point itself, and fp noise alone takes
    # far longer than 2 s to grow.  The kick is an initial condition, not a
    # tuned constant -- far below the toppling energy barrier.
    kick = 0.5  # rad/s about the free (y) axis

    # Control: unactuated falls.  The rod swings (pendulum), so the meter is
    # the MINIMUM height over the run, not the endpoint.
    s_fall = init_state(spec)
    rod_f = s_fall["name_to_idx"]["rod"]
    s_fall["ang_vel"][rod_f][1] = kick
    com_z_min_fell = math.inf
    for _ in range(2000):
        step(spec, s_fall, dt, n_proj_iters=20)
        com_z_min_fell = min(com_z_min_fell, float(s_fall["pos"][rod_f][2]))
    assert com_z_min_fell < 0.4, "unactuated inverted hinge must fall"

    # Main: actuated holds.
    s_hold = init_state(spec)
    s_hold["ang_vel"][s_hold["name_to_idx"]["rod"]][1] = kick
    ctrl = MuscleController(spec, s_hold, physiology={"rod": (30.0, 0.05)})
    assert len(ctrl.actuators) == 1, "hinge rig must yield exactly one actuator"
    rod = s_hold["name_to_idx"]["rod"]
    com_z0 = float(s_hold["pos"][rod][2])
    com_z_min_held = math.inf
    for _ in range(2000):
        ctrl.apply(s_hold)
        step(spec, s_hold, dt, n_proj_iters=20)
        com_z_min_held = min(com_z_min_held, float(s_hold["pos"][rod][2]))
    assert com_z_min_held > com_z0 - 0.01, (
        f"actuated hinge must hold: z {com_z0:.4f} -> min {com_z_min_held:.4f}"
    )


def test_controller_motor_commands_sane(spec):
    """Motor rows: shapes, finite targets, lmax = torque cap x dt.

    The net external wrench is zero BY CONSTRUCTION (motor rows are angular
    pairs inside the constraint solve), so the measurables are the command
    arrays themselves and one bounded tick after a disturbance.
    """
    from LightEngine.kinematic.muscle_controller import MuscleController

    state = init_state(spec)
    dt = 1e-3
    ctrl = MuscleController(spec, state, dt=dt)
    state["ang_vel"] += 0.05
    ctrl.apply(state)
    n = len(ctrl.actuators)
    assert state["motor_axis"].shape == (n, 3)
    assert state["motor_target"].shape == (n,)
    assert np.all(np.isfinite(state["motor_target"]))
    for mi, a in enumerate(ctrl.actuators):
        assert state["motor_lmax"][mi] == pytest.approx(
            a["torque_limit_Nm"] * dt, rel=1e-12)
        assert np.linalg.norm(state["motor_axis"][mi]) == pytest.approx(
            1.0, rel=1e-9)
    step(spec, state, dt, n_proj_iters=20)
    assert np.max(np.linalg.norm(state["ang_vel"], axis=1)) < 20.0
    assert state["motor_impulses"].shape == (n,)


def test_controller_determinism(spec):
    """Two actuated runs of 200 ticks produce identical trajectories."""
    from LightEngine.kinematic.muscle_controller import MuscleController

    pos_runs = []
    for _ in range(2):
        state = init_state(spec)
        ctrl = MuscleController(spec, state)
        for _ in range(200):
            ctrl.apply(state)
            step(spec, state, 1e-3, n_proj_iters=20)
        pos_runs.append(state["pos"].copy())
    assert np.array_equal(pos_runs[0], pos_runs[1])
