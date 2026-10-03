"""mutant_ground_drifted_pin.py -- EXISTS TO BE REFUSED (declared
incompatibility fixture of the membrane-ground lane).

The ground membrane module with ONE planted pin drift: its pinned spec
sha256 is replaced by a wrong digest. The frozen-input contract must refuse
the build with spec_pinned_input_drift before anything is constructed.
Nothing legitimate imports this file.
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from combine_core import CombineRefusal  # noqa: E402
import membrane_ground as base  # noqa: E402

ABI_VERSION = base.ABI_VERSION
IMPLEMENTS_MEMBRANE_ID = base.IMPLEMENTS_MEMBRANE_ID

DRIFTED_PINS = dict(base.PINNED_INPUTS)
DRIFTED_PINS["spec/ground_walk_contact.spec.v1.json"] = "0" * 64  # THE PLANTED DRIFT


def verify_frozen_inputs():
    for rel, want in sorted(DRIFTED_PINS.items()):
        path = base._HERE / rel
        if not path.is_file():
            raise CombineRefusal("spec_pinned_input_drift", {
                "path": rel, "expected": want, "law": "pinned input missing"})
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != want:
            raise CombineRefusal("spec_pinned_input_drift", {
                "path": rel, "expected": want, "observed": got,
                "law": "pinned bytes drifted (the planted drift)"})
    return dict(DRIFTED_PINS)


def build(context, dt):
    verify_frozen_inputs()
    return base.build(context, dt)
