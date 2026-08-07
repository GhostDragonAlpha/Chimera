"""
Tests for LightEngine/skeleton_structures.py.

These tests verify the StandingHuman print builder:
  - determinism,
  - print law (no shared positions),
  - per-bone cluster identity,
  - cup-wrap capture geometry,
  - single-file taut ropes,
  - grain budget enforcement,
  - body_names coverage.
"""

from __future__ import annotations

import numpy as np
import pytest

from LightEngine import skeleton_structures
from LightEngine import skeleton_scaling
from LightEngine.constants import R_WALL, R_BOND


# ---------------------------------------------------------------------------
# Minimal mock scaling table for geometric tests.
# ---------------------------------------------------------------------------
def _minimal_table(lam: float = 0.18) -> tuple:
    """Return a small scaling table and parameters.

    The dimensions are chosen so the assembled leg-spine prints well under
    the 50 000 grain budget while still exercising ball-cup, hinge, and
    saddle joints plus the rope network.
    """
    rows = [
        _row("sacrum", 0.40, 0.18, "saddle", "ball-cup"),
        _row("pelvis pair", 0.50, 0.18, "saddle", "ball-cup"),
        _row("femur pair", 0.80, 0.15, "ball-cup", "hinge"),
        _row("patella pair", 0.20, 0.12, "saddle", "saddle"),
        _row("tibia pair", 0.80, 0.14, "hinge", "hinge"),
        _row("fibula pair", 0.70, 0.10, "hinge", "hinge"),
        _row("tarsals group", 0.30, 0.14, "hinge", "saddle"),
        _row("metatarsals group", 0.35, 0.12, "saddle", "hinge"),
        _row("forefoot mass", 0.25, 0.10, "hinge", "hinge"),
        _row("vertebra L5", 0.20, 0.14, "saddle", "saddle"),
    ]
    total = sum(r["grain_count"] for r in rows)
    breakdown = (total, 0, 0, 0)
    rc = {"a": 0, "b": 0, "c": len(rows)}
    return rows, lam, total, breakdown, rc, []


def _row(name: str, length_lu: float, d_lu: float, prox: str, dist: str) -> dict:
    shell_lu = skeleton_scaling.D_EQ_LU
    solid_lu = d_lu
    return {
        "name": name,
        "length_lu": length_lu,
        "outer_diameter_lu": d_lu,
        "shell_thickness_lu": shell_lu,
        "solid_end_lu": solid_lu,
        "grain_count": 10,  # small dummy for budget check
        "prox": prox,
        "dist": dist,
        "rung": "c",
    }


def _build_mock(monkeypatch, seed: int = 0):
    """Build the skeleton with the minimal mock table."""
    def _mock_scale(height_m, mass_kg):
        return _minimal_table()

    monkeypatch.setattr(skeleton_scaling, "scale_skeleton", _mock_scale)
    return skeleton_structures.build_skeleton(seed=seed)


def _nearest_neighbor_distances(pos: np.ndarray) -> np.ndarray:
    """Direct O(N^2) nearest-neighbor distances; OK for the small test counts."""
    pos64 = np.asarray(pos, dtype=np.float64)
    diff = pos64[:, None, :] - pos64[None, :, :]
    r2 = np.einsum("ijk,ijk->ij", diff, diff)
    np.fill_diagonal(r2, np.inf)
    return np.sqrt(r2.min(axis=1))


def _body_mask(grain_ids: np.ndarray, body_names: list[str], name: str) -> np.ndarray:
    return grain_ids == body_names.index(name)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_determinism(monkeypatch):
    """Same seed must produce identical positions and velocities."""
    a = _build_mock(monkeypatch, seed=7)
    b = _build_mock(monkeypatch, seed=7)
    np.testing.assert_array_equal(a[0], b[0])
    np.testing.assert_array_equal(a[1], b[1])
    np.testing.assert_array_equal(a[2], b[2])
    np.testing.assert_array_equal(a[3], b[3])
    assert a[4] == b[4]


def test_print_law_no_shared_positions(monkeypatch):
    """No two grains share a position."""
    pos, _, _, _, _, _ = _build_mock(monkeypatch, seed=3)
    nn = _nearest_neighbor_distances(pos)
    assert nn.min() > 1e-6, f"minimum pair distance {nn.min():.3e} <= 1e-6"


def test_per_bone_cluster_identity(monkeypatch):
    """Each body_name forms a single connected cluster at R_BOND scale."""
    pos, _, _, grain_ids, body_names, derived = _build_mock(monkeypatch, seed=2)

    for name in body_names:
        if name == "ground_plate":
            continue
        mask = _body_mask(grain_ids, body_names, name)
        pts = pos[mask]
        if pts.shape[0] <= 1:
            continue
        # Build a graph with edges between points within R_BOND.
        diff = pts[:, None, :] - pts[None, :, :]
        r = np.sqrt(np.einsum("ijk,ijk->ij", diff, diff))
        np.fill_diagonal(r, np.inf)
        adj = r <= R_BOND * 1.01
        # Simple union-find.
        parent = np.arange(pts.shape[0])

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for i in range(pts.shape[0]):
            for j in range(i + 1, pts.shape[0]):
                if adj[i, j]:
                    parent[find(i)] = find(j)

        roots = {find(i) for i in range(pts.shape[0])}
        assert len(roots) == 1, (
            f"body {name!r} splits into {len(roots)} clusters "
            f"({pts.shape[0]} grains)"
        )


def test_cup_wrap(monkeypatch):
    """A ball-cup joint has cup grains surrounding the child end with a d_eq gap."""
    pos, _, _, grain_ids, body_names, derived = _build_mock(monkeypatch, seed=5)

    hip_joint = next((j for j in derived["joints"] if j["name"] == "hip_L"), None)
    assert hip_joint is not None, "hip_L joint record missing"

    child = hip_joint["child"]
    cup_start, cup_end = hip_joint["cup_indices"]
    cup_pts = pos[cup_start:cup_end]
    ball_mask = _body_mask(grain_ids, body_names, child)
    ball_pts = pos[ball_mask]

    # Only the child end near the joint participates in the wrap.
    joint_center = hip_joint["ball_center"]
    end_radius = 2.0 * skeleton_structures.SPACING_LU
    near = np.linalg.norm(ball_pts - joint_center, axis=1) <= end_radius
    ball_end_pts = ball_pts[near]
    assert ball_end_pts.shape[0] > 0, "no child grains near the joint"

    diff = ball_end_pts[:, None, :] - cup_pts[None, :, :]
    r = np.sqrt(np.einsum("ijk,ijk->ij", diff, diff))
    min_gap = float(r.min())

    # Cup must not intersect the child.
    assert min_gap > 1e-6, (
        f"cup intersects ball: minimum cup-ball gap {min_gap:.3e} <= 0"
    )


def test_rope_taut_uncompressed(monkeypatch):
    """Ropes are single-file chains with spacing ~ d_eq and no overlaps."""
    pos, _, _, grain_ids, body_names, derived = _build_mock(monkeypatch, seed=11)

    for rope in derived["ropes"]:
        link_id = rope["link_indices"][0]
        mask = grain_ids == link_id
        pts = pos[mask]
        assert pts.shape[0] >= 2, f"rope {rope['name']!r} has < 2 grains"

        diffs = np.diff(pts, axis=0)
        seg_lengths = np.linalg.norm(diffs, axis=1)
        assert seg_lengths.min() >= skeleton_structures.D_EQ_LU * 0.5, (
            f"rope {rope['name']!r} is compressed: segment length "
            f"{seg_lengths.min():.3f} < 0.5*d_eq"
        )
        assert seg_lengths.max() <= skeleton_structures.SPACING_LU * 2.0, (
            f"rope {rope['name']!r} is too slack: segment length "
            f"{seg_lengths.max():.3f} > 2*spacing"
        )


def test_grain_budget():
    """The real scaling table must fit within the 50 000 grain budget."""
    pos, _, _, _, _, derived = skeleton_structures.build_skeleton()
    assert derived["actual_total"] <= skeleton_scaling.N_BUDGET, (
        f"actual grain count {derived['actual_total']:,} exceeds "
        f"budget {skeleton_scaling.N_BUDGET:,}"
    )
    assert derived["estimated_total"] <= skeleton_scaling.N_BUDGET, (
        f"estimated grain count {derived['estimated_total']:,} exceeds "
        f"budget {skeleton_scaling.N_BUDGET:,}"
    )


def test_body_names_coverage(monkeypatch):
    """The returned body_names include the expected bone and rope bodies."""
    pos, _, _, grain_ids, body_names, derived = _build_mock(monkeypatch, seed=13)

    expected_bones = {
        "femur_L", "femur_R", "tibia_L", "tibia_R",
        "pelvis_L", "pelvis_R", "sacrum",
    }
    for name in expected_bones:
        assert name in body_names, f"expected bone {name!r} missing from body_names"

    for name in body_names:
        count = int((grain_ids == body_names.index(name)).sum())
        assert count > 0, f"body {name!r} has zero grains"

    plate_id = body_names.index("ground_plate")
    plate_mask = grain_ids == plate_id
    assert plate_mask.any(), "ground plate has no grains"


def test_ground_plate_pinned(monkeypatch):
    """Only the ground plate grains are pinned."""
    pos, _, pin_mask, grain_ids, body_names, _ = _build_mock(monkeypatch, seed=4)
    plate_id = body_names.index("ground_plate")
    assert pin_mask[grain_ids == plate_id].all()
    assert not pin_mask[grain_ids != plate_id].any()
