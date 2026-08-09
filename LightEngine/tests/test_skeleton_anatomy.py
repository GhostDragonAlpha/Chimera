"""
test_skeleton_anatomy.py — RULE 27 upper-body interface membrane instrument.

Verifies that the derived body (body_style="derived") matches its ANATOMY-DATUM
within ±2% of stature for every audited segment, and that the legacy body
(body_style="legacy", the default) remains bit-identical to the pre-build
geometry.

FINDINGS 1–11 from docs/RULE27_AUDIT.md are test rows.  Finding 12 (foot
geometry) is carried from JOINT_ATLAS.md and out of scope for this build.

Membrane (RULE 0):
  STATEMENT: the upper-body interface membrane is derived from measured joint
  centers and segment fractions that close the derivation chain to ANSUR II
  and the bone table.
  PREDICTION: after re-derivation, all twelve findings show |diff| ≤ 2% of
  stature against the bone table, hip height matches ANSUR II (0.512 H) or
  notes its inherent offset, hand link matches ANSUR (0.110 H), and the spine
  regionality closes to lumbar 0.08 / thoracic 0.16 / cervical 0.08 within
  ±0.005 H each.
  FALSIFIER: any segment still deviates >2% from its ANATOMY-DATUM or
  >2σ from ANSUR II without a compensating derivation.
"""

from __future__ import annotations

import numpy as np
import pytest

from LightEngine import skeleton_scaling
from LightEngine.rope_network import DERIVED_VERTEBRAL_CENTERS
from LightEngine.skeleton_structures import _joint_dict


# ---------------------------------------------------------------------------
# Test params (must match the audit's scale)
# ---------------------------------------------------------------------------
H_M = 1.80
MASS_KG = 80.0
TOLERANCE_H = 0.02  # ±2% of stature in H units


@pytest.fixture(scope="module")
def lam():
    _, l, *_ = skeleton_scaling.scale_skeleton(H_M, MASS_KG)
    return l


@pytest.fixture(scope="module")
def legacy(lam):
    return _joint_dict(H_M / lam, foot_style="legacy", body_style="legacy")


@pytest.fixture(scope="module")
def derived(lam):
    return _joint_dict(H_M / lam, foot_style="legacy", body_style="derived")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _seg_h(j: dict[str, np.ndarray], a: str, b: str, lam: float) -> float:
    """Diagonal segment length in H units."""
    return float(np.linalg.norm(j[a] - j[b]) / (H_M / lam))


# ---------------------------------------------------------------------------
# Legacy body: bit-identical to pre-build geometry
# ---------------------------------------------------------------------------
class TestLegacyBitIdentical:
    """The legacy default must produce the original hardcoded geometry."""

    def test_upper_arm_0180(self, legacy, lam):
        # Finding 1: upper arm was -0.180 z-drop → diagonal ~0.1812 H
        assert abs(_seg_h(legacy, "shoulder_L", "elbow_L", lam) - 0.1812) < 0.002

    def test_forearm_0130(self, legacy, lam):
        # Finding 2: forearm was -0.130 z-drop → diagonal ~0.1312 H
        assert abs(_seg_h(legacy, "elbow_L", "wrist_L", lam) - 0.1312) < 0.002

    def test_hand_with_phantom_tip(self, legacy, lam):
        # Finding 3: hand link spans wrist→hand_tip (phantom segment present)
        assert "hand_tip_L" in legacy
        diag = _seg_h(legacy, "wrist_L", "hand_tip_L", lam)
        assert diag > 0.11  # phantom tip makes it longer than ANSUR 0.110
        assert diag < 0.13

    def test_femur_0270(self, legacy, lam):
        # Finding 4: femur was 0.2709 H (hip 0.530 - knee 0.260)
        assert abs(_seg_h(legacy, "hip_L", "knee_L", lam) - 0.2709) < 0.002

    def test_tibia_0222(self, legacy, lam):
        # Finding 5: tibia was 0.2223 H (knee 0.260 - ankle 0.040)
        assert abs(_seg_h(legacy, "knee_L", "ankle_L", lam) - 0.2223) < 0.002

    def test_hip_height_0530(self, legacy, lam):
        # Finding 6: hip was hardcoded at 0.530 H
        hip_z = legacy["hip_L"][2] / (H_M / lam)
        assert abs(hip_z - 0.530) < 0.002

    def test_c1_below_c2_inverted(self, legacy):
        # Finding 10: C1 z < C2 z in the original (inversion bug).
        # Vertebral centers are midline (x, 0, z), so use index [2] for z.
        assert legacy["C1"][2] < legacy["C2"][2]

    def test_skull_short(self, legacy, lam):
        # Finding 11: skull was 0.045 H (suture 0.985 - C1 0.940)
        # Both coordinates are z (index [2]) since vertebrae sit on the midline.
        skull_span = (legacy["skull_suture"][2] - legacy["C1"][2]) / (H_M / lam)
        assert abs(skull_span - 0.045) < 0.002


# ---------------------------------------------------------------------------
# Derived body: every audited segment within ±2% of stature
# ---------------------------------------------------------------------------
class TestDerivedAnatomy:
    """body_style="derived" must close every FINDING 1–11 gap."""

    def test_upper_arm_within_2pct(self, derived, lam):
        """FINDING 1: upper arm 0.1912 H vs datum 0.190 H → diff 0.6%."""
        actual = _seg_h(derived, "shoulder_L", "elbow_L", lam)
        assert abs(actual - 0.190) <= TOLERANCE_H, f"upper arm {actual:.4f} H"

    def test_forearm_within_2pct(self, derived, lam):
        """FINDING 2: forearm 0.1412 H vs datum 0.140 H → diff 0.9%."""
        actual = _seg_h(derived, "elbow_L", "wrist_L", lam)
        assert abs(actual - 0.140) <= TOLERANCE_H, f"forearm {actual:.4f} H"

    def test_hand_ansur_0110(self, derived, lam):
        """FINDING 3: hand link = ANSUR 0.110 H; phantom tip removed."""
        assert "hand_tip_L" not in derived, "phantom hand_tip must be removed"
        actual = _seg_h(derived, "wrist_L", "hand_L", lam)
        assert abs(actual - 0.110) < 1e-6, f"hand {actual:.4f} H vs ANSUR 0.110"

    def test_femur_within_2pct(self, derived, lam):
        """FINDING 4: femur 0.246 H vs datum 0.245 H → diff 0.4%."""
        actual = _seg_h(derived, "hip_L", "knee_L", lam)
        assert abs(actual - 0.245) <= TOLERANCE_H, f"femur {actual:.4f} H"

    def test_tibia_within_2pct(self, derived, lam):
        """FINDING 5: tibia 0.252 H vs datum 0.250 H → diff 0.8%."""
        actual = _seg_h(derived, "knee_L", "ankle_L", lam)
        assert abs(actual - 0.250) <= TOLERANCE_H, f"tibia {actual:.4f} H"

    def test_hip_height_ansur_crosscheck(self, derived, lam):
        """FINDING 6: hip derived from bone table; notes inherent offset."""
        hip_z = derived["hip_L"][2] / (H_M / lam)
        # Bone-table derivation gives 0.535 H; ANSUR says 0.512 H.
        assert abs(hip_z - 0.535) < 0.002, f"hip z {hip_z:.3f} H"
        ansur_hip = 0.5121
        deviation_cm = (hip_z - ansur_hip) * H_M * 100
        assert deviation_cm > 3.0, "hip should be above ANSUR due to ankle offset"

    def test_lumbar_per_level_within_2pct(self):
        """FINDING 7: each lumbar vertebra ~0.016 H (±2% of stature)."""
        for i in range(5):
            lvl = f"L{5 - i}"
            # Prev (below) level: S1 under L5, then L5→L4→L3→L2.
            prev = f"L{6 - i}" if i > 0 else "S1"
            actual = (DERIVED_VERTEBRAL_CENTERS[lvl][1] -
                      DERIVED_VERTEBRAL_CENTERS[prev][1])
            assert abs(actual - 0.016) < TOLERANCE_H, f"{lvl} {actual:.4f} H"

    def test_thoracic_per_level_within_2pct(self):
        """FINDING 8: each thoracic vertebra ~0.0133 H (±2% of stature)."""
        expected = 0.16 / 12
        for i in range(12):
            lvl = f"T{12 - i}"
            prev = f"T{13 - i}" if i > 0 else "L1"
            actual = (DERIVED_VERTEBRAL_CENTERS[lvl][1] -
                      DERIVED_VERTEBRAL_CENTERS[prev][1])
            assert abs(actual - expected) < TOLERANCE_H, f"{lvl} {actual:.4f} H"

    def test_cervical_per_level_within_2pct(self):
        """FINDING 9: each cervical vertebra ~0.0114 H (±2% of stature)."""
        expected = 0.08 / 7
        for i in range(7):
            lvl = f"C{7 - i}"
            prev = f"C{8 - i}" if i > 0 else "T1"
            actual = (DERIVED_VERTEBRAL_CENTERS[lvl][1] -
                      DERIVED_VERTEBRAL_CENTERS[prev][1])
            assert abs(actual - expected) < TOLERANCE_H, f"{lvl} {actual:.4f} H"

    def test_c1_above_c2(self):
        """FINDING 10: C1 z > C2 z (inversion fixed)."""
        assert DERIVED_VERTEBRAL_CENTERS["C1"][1] > DERIVED_VERTEBRAL_CENTERS["C2"][1]

    def test_skull_full_012H(self, derived, lam):
        """FINDING 11: skull link = 0.12 H per bone table datum."""
        c1_z = DERIVED_VERTEBRAL_CENTERS["C1"][1]
        suture_z_h = derived["skull_suture"][2] / (H_M / lam)
        span = suture_z_h - c1_z
        assert abs(span - 0.120) < 1e-6, f"skull span {span:.4f} H vs datum 0.120"

    def test_upper_joints_above_floor(self, derived, lam):
        """Upper-body and leg major joints above floor (z >= 0)."""
        # Foot chain joints (tarsal, met_base, mtp, forefoot) are intentionally
        # below floor in legacy mode (Finding 12); skip them.
        check_keys = [
            "ankle_L", "knee_L", "hip_L", "shoulder_L",
            "C1", "C7", "T1", "L1", "L5", "S1",
            "skull_suture", "skull_center",
        ]
        for key in check_keys:
            if key not in derived:
                continue
            z = derived[key][2] / (H_M / lam)
            assert z >= 0.0, f"{key} z={z:.4f} H below floor"

    def test_shoulder_from_trunk_chain(self, derived, lam):
        """Shoulder z = T1_z (top of thoracic cage), not a bare constant."""
        shoulder_z_h = derived["shoulder_L"][2] / (H_M / lam)
        t1_z = DERIVED_VERTEBRAL_CENTERS["T1"][1]
        assert abs(shoulder_z_h - t1_z) < 1e-6, \
            f"shoulder {shoulder_z_h:.4f} H != T1 {t1_z:.4f} H"


# ---------------------------------------------------------------------------
# Spine total span sanity
# ---------------------------------------------------------------------------
class TestSpineSpan:
    """Total vertebral column must equal 0.32 H (C1–S1)."""

    def test_total_spine_span(self):
        total = DERIVED_VERTEBRAL_CENTERS["C1"][1] - DERIVED_VERTEBRAL_CENTERS["S1"][1]
        assert abs(total - 0.32) < 1e-9, f"spine span {total:.4f} H != 0.32"

    def test_lumbar_region_center_to_center(self):
        span = DERIVED_VERTEBRAL_CENTERS["L1"][1] - DERIVED_VERTEBRAL_CENTERS["L5"][1]
        assert abs(span - 4 * 0.016) < 1e-6

    def test_thoracic_region_center_to_center(self):
        span = DERIVED_VERTEBRAL_CENTERS["T1"][1] - DERIVED_VERTEBRAL_CENTERS["T12"][1]
        assert abs(span - 11 * (0.16 / 12)) < 1e-6

    def test_cervical_region_center_to_center(self):
        span = DERIVED_VERTEBRAL_CENTERS["C1"][1] - DERIVED_VERTEBRAL_CENTERS["C7"][1]
        assert abs(span - 6 * (0.08 / 7)) < 1e-6
