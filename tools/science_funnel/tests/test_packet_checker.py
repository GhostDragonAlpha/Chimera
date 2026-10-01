"""Packet completeness gate wired into the funnel suite (RULE 0, mechanical).

Every packet in docs/packets must pass tools/science_funnel/check_packet.py:
a packet naming no falsifier, no frozen bit-exact control, or no file change
list is not a packet. Read-only over the checkout; the checker itself never
writes, so this test is safe to run under any suite and is deterministic on a
fixed tree.
"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / "tools" / "science_funnel" / "check_packet.py"
PACKETS = ROOT / "docs" / "packets"


class PacketCompleteness(unittest.TestCase):
    def test_every_packet_names_falsifier_frozen_control_and_files(self):
        self.assertTrue(CHECKER.exists(), f"checker missing: {CHECKER}")
        self.assertTrue(PACKETS.is_dir(), "docs/packets missing: no packets exist")
        packets = sorted(PACKETS.glob("*.md"))
        self.assertTrue(packets, "docs/packets is empty: a packet lane shipped nothing")
        result = subprocess.run(
            [sys.executable, "-B", str(CHECKER)],
            capture_output=True, text=True, cwd=str(ROOT))
        self.assertEqual(
            result.returncode, 0,
            "check_packet refused:\n" + result.stdout + result.stderr)
        self.assertIn("ALL PACKETS COMPLETE", result.stdout)


if __name__ == "__main__":
    unittest.main()
