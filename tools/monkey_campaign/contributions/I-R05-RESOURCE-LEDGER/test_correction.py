"""test_correction.py -- I-R05-RESOURCE-LEDGER correction (failing-first).

The lead's reproducer must FAIL on BASE (recorded) and PASS after the fix.
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from resource_ledger import ResourceLedger, LedgerRefusal  # noqa: E402


class LeadReproducer(unittest.TestCase):
    def test_late_acquire_to_closed_generation(self):
        ledger = ResourceLedger()
        ledger.acquire("res", "owner", 0)
        ledger.release("res", "owner", 0)
        ledger.close_generation(0)
        with self.assertRaises(LedgerRefusal) as ctx:
            ledger.acquire("late", "owner", 0)
        self.assertIn("acquire_generation_closed", str(ctx.exception)
                      or getattr(ctx.exception, "reason", ""))
        result = ledger.close()
        self.assertEqual(result["live_now"], 0)
        self.assertTrue(result["passed"])


class FinalCloseNeverPassesWithLive(unittest.TestCase):
    def test_live_record_in_closed_generation_fails_close(self):
        # white-box regression guard for the defense-in-depth path: a live
        # record in an already-closed generation (creatable only pre-fix)
        # must make the final close FAIL, never pass
        ledger = ResourceLedger()
        ledger.acquire("res", "owner", 0)
        ledger.release("res", "owner", 0)
        ledger.close_generation(0)
        from resource_ledger import AcquireRecord
        ledger._live["late"] = AcquireRecord("late", "owner", 0, 99, 1000)
        result = ledger.close()
        self.assertFalse(result["passed"])
        self.assertEqual(result["live_now"], 0)
        kinds = [f["code"] for f in ledger.failures()]
        self.assertIn("ledger_live_at_close", kinds)


if __name__ == "__main__":
    unittest.main(verbosity=2)
