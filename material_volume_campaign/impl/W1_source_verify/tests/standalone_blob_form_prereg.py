"""W1 failing-first artifact: the NEW battery test (decision M01-F1), written
BEFORE the battery edit, run against the PRE-CHANGE battery. The method body
below is the exact body that is then appended to
tools/material_volume_export_proof_verify.py as
test_blob_form_reproduction_of_saved_example_report (append-style; the
materialized-file check stays separate, labeled, with the original
checkout-dependent failure and its explanation preserved).

Run against the pre-change battery (receipts/03_...txt) and re-run post-change
as an unchanged-behavior control (receipts/06b_...txt).
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

TOOLS = Path("E:/ChimeraWork/mvc-20260924/tools")
sys.path.insert(0, str(TOOLS))
import material_volume_export_proof_verify as battery  # pre-change bytes first run
import material_volume_body_export as exporter


class BlobFormReproductionPreChange(unittest.TestCase):
    def test_blob_form_reproduction_of_saved_example_report(self):
        # BLOB-FORM IDENTITY (portable) — added per decision M01-F1.
        # Portable reproduction: the exporter CLI's LF stdout must equal the git
        # blob bytes of the saved example report and the canonical serialization
        # of its parsed content. Unlike the materialized-file check, this
        # identity does not depend on the checkout's EOL smudge (B4 law: disk
        # bytes are a checkout materialization; blob bytes are the portable
        # materialization identity; canonical JSON is the content identity).
        try:
            root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                  cwd=str(battery.ROOT), capture_output=True,
                                  check=True)
            toplevel = root.stdout.decode("utf-8", "replace").strip()
            blob = subprocess.run(
                ["git", "cat-file", "blob",
                 "HEAD:tools/material_volume_body_export_example_report.json"],
                cwd=toplevel, capture_output=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"blob-form identity unavailable (no git/blob): {error!r}")
        code, out = battery.run_cli(
            "material_volume_body_export_manifest_example.json",
            "material_volume_body_export_partition_example.json",
            "material_volume_body_export_groups_example.json")
        self.assertEqual(code, 0)
        lf_stdout = out.replace(b"\r\n", b"\n")
        self.assertEqual(
            lf_stdout, blob,
            "LF(CLI stdout) must reproduce the saved example report's git blob "
            "bytes (portable blob-form identity)")
        parsed = json.loads(blob)
        self.assertEqual(
            blob, exporter.canonical_json(parsed).encode("ascii"),
            "the saved example report blob must be the exporter's canonical "
            "serialization (C-1)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
