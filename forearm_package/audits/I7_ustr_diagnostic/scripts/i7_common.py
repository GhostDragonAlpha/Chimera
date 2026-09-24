"""i7_common — shared setup for the I7 isolated U-STR B4 diagnostic.

Reuses the B4 gate machinery verbatim: this module imports B4's `b4_common` so every
tolerance constant (ROLL_EPS, JOINT_EPS, reconstruction bound, orthonormality tiers,
det tolerance, degenerate floors, scale band) is THE protocol's frozen value —
inherited, never re-declared, never weakened (challenge_protocol.md §2 stands).

Authorization executed here (handoff memo §5, verbatim):
  "Authorize the isolated U-STR B4 diagnostic without requiring the hand-scoped O2
   gate to pass. This authorization is for source-kinematic fidelity diagnostics only.
   Retain the anatomical falsifier outcome from R1; do not relabel source convention
   as anatomical evidence. No production radius supersession, hand fit, or
   training-body change is authorized by that diagnostic. Preserve old radius and all
   failed alternatives. Return the existing B4 criteria, exact proposed radius effects
   and resulting defined/undefined tendon coverage. A diagnostic PASS does not close
   A03 or authorize mechanically qualified grasp."

Scope: CPU-only; no fitting search; no production mapping; no supersession execution;
no training-body change; no moment-arm/path-length/tendon-length computation anywhere
in the gate scripts (T6). Writes ONLY inside audits/I7_ustr_diagnostic/ plus the
append-only addendum to USTR_DIAGNOSTIC_RECEIPT.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

I7 = Path(r"E:/PythonChimera/forearm_package/audits/I7_ustr_diagnostic")
B4 = Path(r"E:/PythonChimera/forearm_package/audits/B4_correspondence_challenge")
RECEIPTS = I7 / "receipts"
RECEIPTS.mkdir(exist_ok=True)

# The B4 gate machinery: constants + loaders + onb + verdict/save helpers.
sys.path.insert(0, str(B4 / "scripts"))
import b4_common as C  # noqa: E402  (B4's own module; tolerances inherited as-is)

SNAP = C.SNAP
XML_PATH = C.XML_PATH
PACKET_PATH = C.PACKET_PATH
MESH_PATH = C.MESH_PATH
PACK_PATH = C.PACK_PATH

# The candidate under test (declared, frozen in receipts/00_candidate_declaration.json)
CANDIDATE_BODIES = ("ulna", "ulna_l")
ROLL_SOURCE_SITE = {"ulna": "TRIlat-P5", "ulna_l": "TRIlat_l-P5"}

# O1's resolved sign law (audits/O1_ulna_orientation/report.md §5, receipt
# o1_combine_sign.json): a declared pair (source site s, target witness q) carries the
# correct sign iff az_target(q) = az_source(s) + 90 deg (mod 360).
O1_LAW = "az_target(q) = az_source(s) + 90 deg (mod 360)"
O1_WITNESS_B_PRIME_AZ_DEG = -111.86515772931568  # receipt o1_combine_sign.json inputs
O1_RESIDUALS_DEG = {"ECU-P2": 63.61229795664599,
                    "ANC-P2": 17.552772577400333,
                    "TRIlat-P5": 0.15353092426937565}

# I6 candidate constants (ANATOMICAL_DECISION_TABLE.md §1 U-STR column; R1 §5.3)
BODY_SCALE_RADIUS = 0.22170679566544982  # the known-good radius body scale (packet)


def load_candidate() -> dict:
    with open(RECEIPTS / "00_candidate_declaration.json", "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_packet() -> dict:
    return C.load_packet()


def save_receipt(name: str, payload: dict) -> Path:
    """I7-scoped override: b4_common.save_receipt writes into the B4 receipts dir;
    the diagnostic's write scope is audits/I7_ustr_diagnostic/receipts ONLY."""
    def enc(o):
        if isinstance(o, np.ndarray):
            return o.tolist()
        return float(o)

    p = RECEIPTS / name
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=enc)
    return p


def verdict(name: str, ok: bool, detail: str = "") -> str:
    return C.verdict(name, ok, detail)
