"""Tests for theSpine v2 structure builder."""

from __future__ import annotations

import math
import numpy as np
import pytest

from LightEngine import spine_structures
from LightEngine.constants import S_WALL, R_C


def _build(control: bool = False, seed: int = 7):
    return spine_structures.spine(control=control, seed=seed)


def test_counts():
    pos, vel, pin_mask, grain_ids, derived = _build()
    assert pos.shape == vel.shape
    assert grain_ids.shape[0] == pos.shape[0]
    assert pin_mask.shape[0] == pos.shape[0]
    assert derived["n_plate"] == 36
    # v2 tapered sacrum: bottom rings solid 4x4 (16 grains), top ring hollow (12)
    expected_sacrum = sum(derived["sacrum_ring_counts"])
    assert derived["n_sacrum"] == expected_sacrum
    assert derived["n_sacrum"] > 8 * 12  # more grains than v1 hollow tube
    assert derived["n_lumbar"] == 8 * 12
    assert derived["n_droplet"] == 64
    assert derived["n_load"] == 64
    assert derived["n_rope"] >= 2
    # grain ids present
    assert set(grain_ids) == {-1, 0, 1, 2, 3, 4, 5}


def test_tapered_sacrum_profile():
    pos, vel, pin_mask, grain_ids, derived = _build()
    counts = derived["sacrum_ring_counts"]
    layers = derived["sacrum_layers"]
    assert len(counts) == layers
    assert counts[0] == 16  # base ring solid 4x4
    assert counts[-1] == 12  # top ring hollow shell
    assert all(12 <= c <= 16 for c in counts)
    # non-increasing from base to top (moment decreases with height)
    assert all(counts[i] >= counts[i + 1] for i in range(len(counts) - 1))
    # total grain count matches the actual sacrum grains
    assert sum(counts) == derived["n_sacrum"]
    # derivation numbers are present and physically sane
    assert derived["F_tip"] > 0.0
    assert derived["M_max"] > 0.0
    assert derived["taper_extra_needed_base"] >= 0.0


def test_pinned_bodies():
    pos, vel, pin_mask, grain_ids, derived = _build()
    assert pin_mask[grain_ids == -1].all()  # ground plate
    assert pin_mask[grain_ids == 1].all()   # saddle block+cheeks+lintel
    assert pin_mask[grain_ids == 3].all()   # droplet
    # lumbar, load, rope free
    assert not pin_mask[grain_ids == 2].any()
    assert not pin_mask[grain_ids == 5].any()
    assert not pin_mask[grain_ids == 4].any()
    # sacrum bottom face pinned, not the whole body
    sacrum_idx = np.flatnonzero(grain_ids == 0)
    bottom_z = derived["sacrum_bottom_z"]
    pinned_frac = (pin_mask[sacrum_idx]).mean()
    assert 0.0 < pinned_frac < 1.0
    # bottom ring is solid 4x4 = 16 grains; total sacrum is sum of ring counts
    expected_pinned_frac = 16.0 / derived["n_sacrum"]
    assert pinned_frac == pytest.approx(expected_pinned_frac, rel=0.2)


def test_box_capture_dimensions():
    pos, vel, pin_mask, grain_ids, derived = _build()
    # lintel underside derived from nominal lumbar top + corner rise + d_eq
    nominal_lumbar_bottom = derived["block_top_z"] + derived["d_eq"]
    nominal_lumbar_top = nominal_lumbar_bottom + (4 - 1) * derived["spacing"]
    expected_lintel = nominal_lumbar_top + derived["corner_rise"] + derived["d_eq"]
    assert derived["lintel_bottom_z"] == pytest.approx(expected_lintel, abs=1e-4)
    # cheek inner face gap = d_eq
    saddle = pos[grain_ids == 1]
    cheek_y = derived["cheek_y_center"]
    cheek_inner_y = cheek_y - 0.5 * derived["spacing"]  # one-grain-thick cheek
    lumbar = pos[grain_ids == 2]
    tube_half = (4 - 1) / 2.0 * derived["spacing"]
    side_face_y = np.max(np.abs(lumbar[:, 1]))
    assert side_face_y == pytest.approx(tube_half, abs=2e-3)
    assert cheek_inner_y - side_face_y == pytest.approx(derived["d_eq"], abs=2e-3)


def test_capture_gaps_at_print():
    pos, vel, pin_mask, grain_ids, derived = _build()
    saddle = pos[grain_ids == 1]
    lumbar = pos[grain_ids == 2]
    # perch gap
    saddle_top = saddle[derived["saddle_top_local"]]
    lumbar_contact = lumbar[derived["lumbar_contact_local"]]
    perch_gap = np.linalg.norm(
        saddle_top[:, None, :] - lumbar_contact[None, :, :], axis=2).min()
    assert S_WALL <= perch_gap <= 2 * derived["d_eq"]
    # lintel gap
    lintel = saddle[derived["lintel_local"]]
    lumbar_top = lumbar[derived["lumbar_top_local"]]
    lintel_gap = np.linalg.norm(
        lintel[:, None, :] - lumbar_top[None, :, :], axis=2).min()
    assert S_WALL <= lintel_gap <= 2 * derived["d_eq"]
    # cheek gap
    cheek = saddle[derived["cheek_inner_local"]]
    lumbar_side = lumbar[derived["lumbar_side_local"]]
    cheek_gap = np.linalg.norm(
        cheek[:, None, :] - lumbar_side[None, :, :], axis=2).min()
    assert S_WALL <= cheek_gap <= 2 * derived["d_eq"]


def test_rope_taut_at_print():
    pos, vel, pin_mask, grain_ids, derived = _build()
    rope = pos[grain_ids == 4]
    n_rope = derived["n_rope"]
    assert rope.shape[0] == n_rope
    # ordered from anchor to attach
    order = derived["rope_order_local"]
    assert len(order) == n_rope
    anchor = np.array([derived["muscle_tip_x"], 0.0,
                       derived["droplet_apex_z"] + derived["d_eq"]])
    # attach point is the underside center of the lumbar near end
    lumbar = pos[grain_ids == 2]
    near_end = lumbar[derived["muscle_face_local"]]
    attach = near_end.mean(axis=0)
    attach[2] = derived["lumbar_bottom_z"] - derived["d_eq"]
    # first grain near anchor, last near attach
    assert np.linalg.norm(rope[order[0]] - anchor) <= 0.5 * derived["spacing"]
    assert np.linalg.norm(rope[order[-1]] - attach) <= 0.5 * derived["spacing"]
    # consecutive spacing approximately spacing
    dists = np.linalg.norm(np.diff(rope[order], axis=0), axis=1)
    assert dists.min() > 0.0
    assert np.allclose(dists, dists.mean(), rtol=0.2)


def test_endstop_derivations():
    pos, vel, pin_mask, grain_ids, derived = _build()
    tr = derived["arc_trace"]
    assert tr["theta_muscle"] > 0.0
    assert tr["theta_load"] <= 0.0
    # muscle stop: near-end underside reaches droplet apex + d_eq
    cx = derived["contact_x"]
    cp_z = derived["block_top_z"]
    target_z = derived["droplet_apex_z"] + derived["d_eq"]
    theta_m = tr["theta_muscle"]
    z_m = cp_z - cx * math.sin(theta_m)
    assert z_m == pytest.approx(target_z, abs=1e-3)
    # load-side stop magnitude bounded by the capture/ground limits
    assert abs(tr["theta_load"]) <= math.radians(120.0)


def test_determinism():
    pos1, _, _, _, _ = _build(seed=42)
    pos2, _, _, _, _ = _build(seed=42)
    assert np.allclose(pos1, pos2, atol=1e-6)


def test_gate_trace_exists():
    pos, vel, pin_mask, grain_ids, derived = _build()
    tr = derived["arc_trace"]
    assert "thetas" in tr
    assert "R_taut" in tr
    assert "R_slack" in tr
    assert len(tr["thetas"]) == len(tr["R_taut"]) == len(tr["R_slack"])
    assert tr["thetas"][0] == pytest.approx(tr["theta_load"], abs=1e-6)
    assert tr["thetas"][-1] == pytest.approx(tr["theta_muscle"], abs=1e-6)
    assert math.isfinite(float(tr["R_taut"][0]))
    assert math.isfinite(float(tr["R_slack"][0]))
