"""
Tests for LightEngine/kinematic (Lane K1).

Verifies the 77-link spec, zero-pose forward kinematics, DoF enforcement,
known rotations, CCD inverse kinematics, and determinism.
"""

from __future__ import annotations

import numpy as np
import pytest

from LightEngine import skeleton_scaling, skeleton_structures
from LightEngine.kinematic import build_spec, forward_kinematics, ik
from LightEngine.kinematic import transforms
from LightEngine.kinematic.skeleton_spec import BALL_CUP, SADDLE, HINGE, SUTURE


HEIGHT_M = 1.80
MASS_KG = 80.0


@pytest.fixture(scope="module")
def spec():
    """Shared spec built once per test module."""
    return build_spec(HEIGHT_M, MASS_KG)


@pytest.fixture(scope="module")
def instances():
    """Concrete body instances from the structure lane."""
    table, lam, *_ = skeleton_scaling.scale_skeleton(HEIGHT_M, MASS_KG)
    height_lu = HEIGHT_M / lam
    return skeleton_structures._body_instances(table, height_lu)


# ---------------------------------------------------------------------------
# Spec integrity
# ---------------------------------------------------------------------------
def test_spec_has_77_links(spec):
    """The spec must cover exactly the 77 body instances."""
    assert len(spec["links"]) == 77


def test_spec_mass_normalization(spec):
    """Link masses must sum to the input body mass."""
    total = sum(link["mass_kg"] for link in spec["links"].values())
    assert total == pytest.approx(MASS_KG, abs=1e-9)


def test_spec_tree_integrity(spec):
    """Exactly one root, no cycles, every non-root link reachable."""
    links = spec["links"]
    joints = spec["joints"]

    roots = [name for name, link in links.items() if link["parent_name"] is None]
    assert len(roots) == 1
    root = roots[0]

    # Every joint references existing links.
    for joint in joints.values():
        assert joint["parent_link"] in links
        assert joint["child_link"] in links

    # Every non-root link is a child in exactly one joint and has a parent.
    child_links = {joint["child_link"] for joint in joints.values()}
    non_roots = {name for name, link in links.items() if link["parent_name"] is not None}
    assert child_links == non_roots

    # No cycles: following parents from any link must reach the root.
    for name in links:
        seen = set()
        cur = name
        while cur is not None:
            assert cur not in seen, f"cycle detected involving {name!r}"
            seen.add(cur)
            cur = links[cur]["parent_name"]
        assert root in seen

    # Reachability from root via children.
    children_of = {name: [] for name in links}
    for joint in joints.values():
        children_of[joint["parent_link"]].append(joint["child_link"])
    reached = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if node in reached:
            continue
        reached.add(node)
        stack.extend(children_of[node])
    assert reached == set(links.keys())


def test_spec_dof_classes_are_legal(spec):
    """All joint DoF classes must be one of the four encoded classes."""
    legal = {BALL_CUP, SADDLE, HINGE, SUTURE}
    for joint in spec["joints"].values():
        assert joint["dof_class"] in legal


def test_spec_ligament_count(spec):
    """The 43 ropes from rope_network.py become ligaments."""
    assert len(spec["ligaments"]) == 43


# ---------------------------------------------------------------------------
# Forward kinematics: zero pose
# ---------------------------------------------------------------------------
def test_fk_zero_pose_matches_instances(spec, instances):
    """Zero angles must reproduce the printed pose exactly."""
    poses = forward_kinematics(spec, {})
    instances_by_name = {inst["name"]: inst for inst in instances}

    for name, inst in instances_by_name.items():
        pose_pos = poses[name][0]
        expected = np.asarray(inst["prox"], dtype=np.float64)
        np.testing.assert_allclose(pose_pos, expected, atol=1e-9,
                                   err_msg=f"zero-pose mismatch for {name}")


# ---------------------------------------------------------------------------
# Forward kinematics: known rotation
# ---------------------------------------------------------------------------
def test_fk_knee_hinge_90_degrees(spec):
    """A 90-degree knee hinge moves the ankle by the derived amount.

    DERIVED-GEOMETRY: the ankle is the distal endpoint of tibia_L.  Rotating
    the knee hinge (parent femur_L's local y-axis) by +pi/2 must leave the
    knee-to-ankle distance unchanged and place the ankle at
        ankle = knee + R_axis(pi/2) @ (ankle0 - knee).
    """
    poses0 = forward_kinematics(spec, {})
    angles = {"tibia_L": np.pi / 2.0}
    poses = forward_kinematics(spec, angles)

    knee0 = poses0["tibia_L"][0]
    ankle0 = poses0["tarsals_L"][0]
    ankle = poses["tarsals_L"][0]

    # Distance from knee to ankle is preserved.
    d0 = float(np.linalg.norm(ankle0 - knee0))
    d1 = float(np.linalg.norm(ankle - knee0))
    assert d1 == pytest.approx(d0, abs=1e-9)

    # Expected ankle using the spec-derived hinge axis in world coordinates.
    joint = spec["joints"]["tibia_L"]
    parent_q0 = poses0["femur_L"][1]
    axis_world = transforms.rotate(parent_q0, joint["axes"][0])
    expected = knee0 + transforms.rotate(
        transforms.from_axis_angle(axis_world, np.pi / 2.0),
        ankle0 - knee0,
    )
    np.testing.assert_allclose(ankle, expected, atol=1e-9)


# ---------------------------------------------------------------------------
# DoF enforcement
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("joint_name,bad_angle", [
    ("tibia_L", np.array([0.1, 0.2])),      # hinge expects scalar
    ("tibia_L", np.array([0.1, 0.2, 0.3])), # hinge expects scalar
    ("femur_L", np.array([0.1])),           # ball-cup expects 3 or 4
    ("femur_L", np.array([0.1, 0.2])),      # ball-cup expects 3 or 4
    ("femur_L", np.array([0.1, 0.2, 0.3, 0.4, 0.5])),  # ball-cup expects 3 or 4
    ("pelvis_L", np.array([0.1])),          # saddle expects 2
    ("pelvis_L", np.array([0.1, 0.2, 0.3])), # saddle expects 2
])
def test_fk_rejects_bad_angle_size(spec, joint_name, bad_angle):
    """FK must raise when the angle vector size does not match the DoF class."""
    with pytest.raises(ValueError):
        forward_kinematics(spec, {joint_name: bad_angle})


# ---------------------------------------------------------------------------
# Inverse kinematics
# ---------------------------------------------------------------------------
def _end_effector(spec, poses, link_name):
    """Return the distal endpoint of a link."""
    p, q = poses[link_name]
    length = spec["links"][link_name]["length_lu"]
    return p + transforms.rotate(q, np.array([0.0, 0.0, length]))


def test_ik_reachable_target(spec):
    """CCD reaches a small perturbation of the foot position."""
    poses0 = forward_kinematics(spec, {})
    end_link = "tarsals_L"
    end0 = _end_effector(spec, poses0, end_link)
    target = end0 + np.array([1.0, 0.0, 1.0])

    angles = ik(spec, {}, end_link, target, max_iter=1000, tol=1e-6)
    poses = forward_kinematics(spec, angles)
    end_pos = _end_effector(spec, poses, end_link)
    assert float(np.linalg.norm(end_pos - target)) < 1e-5


def test_ik_unreachable_target_does_not_explode(spec):
    """An unreachable far target terminates without error."""
    poses0 = forward_kinematics(spec, {})
    end_link = "tarsals_L"
    end0 = _end_effector(spec, poses0, end_link)
    # A target far outside the leg workspace.
    target = end0 + np.array([1000.0, 0.0, 1000.0])

    angles = ik(spec, {}, end_link, target, max_iter=20, tol=1e-6)
    # No exception is the passing condition; angles remain finite quaternions.
    for name, value in angles.items():
        arr = np.asarray(value, dtype=np.float64)
        assert np.all(np.isfinite(arr))


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------
def test_fk_determinism(spec):
    """Same inputs produce identical FK outputs."""
    angles = {
        "tibia_L": 0.3,
        "femur_L": np.array([0.2, 0.1, -0.1]),
    }
    a = forward_kinematics(spec, angles)
    b = forward_kinematics(spec, angles)
    for name in a:
        np.testing.assert_array_equal(a[name][0], b[name][0])
        np.testing.assert_array_equal(a[name][1], b[name][1])


def test_ik_determinism(spec):
    """Same inputs produce identical IK outputs."""
    poses0 = forward_kinematics(spec, {})
    end_link = "tarsals_L"
    target = _end_effector(spec, poses0, end_link) + np.array([0.5, 0.0, 0.5])
    a = ik(spec, {}, end_link, target, max_iter=200, tol=1e-6)
    b = ik(spec, {}, end_link, target, max_iter=200, tol=1e-6)
    for name in a:
        np.testing.assert_array_almost_equal(a[name], b[name])


# ---------------------------------------------------------------------------
# Transform helpers
# ---------------------------------------------------------------------------
def test_quaternion_rotate_matches_matrix():
    """q.rotate(v) must equal R(q) @ v."""
    q = transforms.normalize(np.array([0.8, 0.2, 0.3, 0.4]))
    v = np.array([1.0, 2.0, 3.0])
    R = transforms.to_matrix(q)
    np.testing.assert_allclose(transforms.rotate(q, v), R @ v, atol=1e-12)


def test_from_axis_angle_90_degrees():
    """A +90-degree rotation around z maps x to y."""
    q = transforms.from_axis_angle(np.array([0.0, 0.0, 1.0]), np.pi / 2.0)
    v = transforms.rotate(q, np.array([1.0, 0.0, 0.0]))
    np.testing.assert_allclose(v, np.array([0.0, 1.0, 0.0]), atol=1e-12)


def test_homogeneous_invert():
    """compose(T, invert(T)) is the identity."""
    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = transforms.to_matrix(
        transforms.from_axis_angle(np.array([1.0, 2.0, 3.0]), 0.5)
    )
    T[:3, 3] = np.array([1.0, 2.0, 3.0])
    I = transforms.compose(T, transforms.invert(T))
    np.testing.assert_allclose(I, np.eye(4), atol=1e-12)
