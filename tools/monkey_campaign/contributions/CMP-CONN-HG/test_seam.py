"""test_seam.py -- the runner command for the CMP-CONN-HG seam packet.

Runs the four acceptance checks T.CONN_counted_once / T.CONN_friction_pair /
T.CONN_release / T.CONN_ledger as run-time falsifiers on constructed triggers
(see conn_seam.py + PREREGISTRATION.md) and writes outputs/seam_result.json.
Exit 0 iff every fatal prereg window holds and every refusal probe bites.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import conn_seam  # noqa: E402

conn_seam.main()
