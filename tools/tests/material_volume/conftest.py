"""Landing shim for tools/tests/material_volume (W7 publication, 2026-09-24).

Path adaptation only: the reviewed suites were frozen in homes where the two
tools sat next to tests/ (impl/W5_diag_promo, impl/W6_validator). Landed, they
sit one level higher, in tools/. This shim puts tools/ on sys.path so
``import material_volume_diagnostic`` / ``import
rigid_body_mass_consumption_validator`` resolve to the landed, hash-pinned
modules without editing a single test import.

Bytecode guard: T9/F1 forbid any __pycache__ under the material-volume surface
of tools/; arm sys.dont_write_bytecode before any tools/ module is imported.
The canonical run command also sets PYTHONDONTWRITEBYTECODE=1 in the
environment (see README.md).
"""
import os
import sys

sys.dont_write_bytecode = True
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
