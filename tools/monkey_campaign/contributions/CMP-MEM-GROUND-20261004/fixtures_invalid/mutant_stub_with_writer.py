"""mutant_stub_with_writer.py -- EXISTS TO BE REFUSED (declared incompatibility
fixture of the membrane-ground lane).

The declared fixture exterior member WITH an exchange_contribution: a
non-owner of the seam's contact record that exposes a writer for it. The
per-connection ONE-writer law (contract state_ownership: jn/jt owned by
membrane.ground.v1) is enforced by graph_runtime.validate_built_graph, which
must refuse this mutant with abi_exchange_writer_violation. Nothing legitimate
imports this file.
"""
from __future__ import annotations

import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

import membrane_hand_fixture_stub as base  # noqa: E402
from combine_core import Contribution  # noqa: E402

ABI_VERSION = base.ABI_VERSION
IMPLEMENTS_MEMBRANE_ID = base.IMPLEMENTS_MEMBRANE_ID


def verify_frozen_inputs():
    return base.verify_frozen_inputs()


def build(context, dt):
    membrane = base.build(context, dt)

    def exchange_contribution():
        # THE PLANTED VIOLATION: a writer for the seam's contact record on a
        # member that does not own it.
        return Contribution(
            "contribution.mutant_stub_writer.exchange",
            IMPLEMENTS_MEMBRANE_ID,
            ["state.q_jn.hand_ground_contact.v1"],
            lambda view, ctx: {"states": {}, "ledger": []})

    membrane.exchange_contribution = exchange_contribution
    return membrane
