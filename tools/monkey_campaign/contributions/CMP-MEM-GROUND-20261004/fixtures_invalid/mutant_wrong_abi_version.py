"""mutant_wrong_abi_version.py -- EXISTS TO BE REFUSED (declared
incompatibility fixture of the membrane-ground lane).

A module whose ABI_VERSION string is not chimera.membrane_abi.v1.
membrane_abi.validate_module must refuse it with abi_version_mismatch.
Nothing legitimate imports this file.
"""
from __future__ import annotations

import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

import membrane_ground as base  # noqa: E402

ABI_VERSION = "chimera.membrane_abi.v0"  # THE PLANTED VIOLATION
IMPLEMENTS_MEMBRANE_ID = base.IMPLEMENTS_MEMBRANE_ID


def verify_frozen_inputs():
    return base.verify_frozen_inputs()


def build(context, dt):
    return base.build(context, dt)
