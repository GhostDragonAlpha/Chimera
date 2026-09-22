"""policy_compat: the Astra round-5 COMPATIBILITY CERTIFICATE gate.

A policy trained on physics build N must never silently degrade on build N+1.
Enforcement: (policy bundle, physics build, runtime profile, body/domain, test
suite) -> COMPATIBILITY CERTIFICATE; a missing or invalidated certificate BLOCKS
deployment. Preregistration of record:
tools/science_funnel/validation/upgrade_gate_20260920/receipt.json (frozen
rule_0 sha 4c27fc7fd78f75357bdb015c11e58807028ca996111557d1520e44294b100ed2).
"""
from __future__ import annotations

SCHEMA_VERSION = "chimera.policy_compat/1.0.0"
