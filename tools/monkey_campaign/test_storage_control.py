"""Storage-control self-tests for task_package.py (wk-storage wave, 2026-10-01).

One test per tasked item:
  A1 space reservation BEFORE admission
  A2 per-job AND aggregate limits
  A3 active-job leases, lease identity checked on cleanup
  A4 explicit evidence pins (declared hashed, undeclared disposable)
  A5 automatic cleanup on success / failure / timeout (interruption via A3+A6)
  A6 recovery of abandoned scratch after restart (stale job identity)
  A7 receipt byte-accounting adds up (created == retained + reclaimed)
  A8 holds ledger with owner, reason, next action, date
  A9 directory separation policy: protected evidence / regenerable cache /
     temporary scratch; unknown paths never touched

Deterministic and CPU-only. Admissions are pinned by patching free_bytes and
available_memory so host load cannot flake a verdict.
"""
from contextlib import ExitStack, contextmanager
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

CAND = os.environ.get('TASK_PACKAGE_DIR') or str(Path(__file__).resolve().parent)
sys.path.insert(0, CAND)
import task_package as t
import runner_resources as r


@contextmanager
def admitted(free=None):
    """Pin memory admission; optionally pin free disk bytes."""
    with ExitStack() as st:
        st.enter_context(patch.object(r, 'available_memory', return_value=64*1024**3))
        if free is not None:
            st.enter_context(patch.object(t, 'free_bytes', return_value=free))
        yield


class StorageControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name).resolve()
        self.src = self.root/'source'; self.src.mkdir()
        t.git(self.src, 'init'); t.git(self.src, 'config', 'user.name', 'fixture')
        t.git(self.src, 'config', 'user.email', 'fixture@example.invalid')
        (self.src/'mod').mkdir()
        (self.src/'mod/code.py').write_text('original\n')
        t.git(self.src, 'add', '.'); t.git(self.src, 'commit', '-m', 'base')
        self.base = t.git(self.src, 'rev-parse', 'HEAD').decode().strip()
        self.pkg = self.root/'package'
        t.create(self.src, self.base, self.pkg, 'wk-storage', 'storage-control', [], ['mod'])
        self.runner = self.root/'runner'

    def tearDown(self):
        def writable(fn, p, exc): os.chmod(p, 0o700); fn(p)
        shutil.rmtree(self.root, onerror=writable); self.temp.cleanup()

    def sealed(self): return Path(t.seal(self.pkg)['sealed'])

    # A1: space reservation BEFORE admission.
    def test_a1_space_reserved_before_admission(self):
        s = self.sealed()
        with admitted(free=1*1024**3):
            out = t.run(s, [sys.executable, '-c', 'pass'], root=self.runner, slot=0)
        self.assertEqual(out['state'], 'BUSY', out)
        self.assertEqual(out['reason'], 'disk_space_reserve')
        self.assertFalse((self.runner/'slot-0/scratch').exists())
        self.assertFalse((self.runner/'slot-0/lease.json').exists())
        self.assertEqual(list((self.runner/'results').glob('*')), [])
        with admitted(free=10*1024**3):
            out = t.run(s, [sys.executable, '-c', 'pass'], root=self.runner, slot=0)
        self.assertEqual(out['state'], 'PASSED', out)
        self.assertGreaterEqual(out['space_admission']['free_bytes'],
                                out['space_admission']['required_bytes'])
        self.assertEqual(out['space_admission']['incoming_bytes'],
                         out['declared_budget_bytes']+t.OUTPUT_LIMIT)

    # A2: per-job AND aggregate limits.
    def test_a2_per_job_and_aggregate_limits(self):
        s = self.sealed()
        # Aggregate: a stale lease on slot-1 reserves 6 GiB against the shared store.
        (self.runner/'slot-1').mkdir(parents=True)
        (self.runner/'slot-1/lease.json').write_text(json.dumps(
            dict(schema=t.LEASE_SCHEMA, job='a'*32, declared_bytes=6*1024**3)))
        with admitted(free=8*1024**3):
            out = t.run(s, [sys.executable, '-c', 'pass'], root=self.runner, slot=0)
        self.assertEqual(out['state'], 'BUSY', out)
        self.assertEqual(out['reason'], 'disk_space_reserve')
        self.assertEqual(out['space']['reserved_bytes'], 6*1024**3)
        with admitted(free=9*1024**3):
            out = t.run(s, [sys.executable, '-c', 'pass'], root=self.runner, slot=0)
        self.assertEqual(out['state'], 'PASSED', out)
        self.assertEqual(out['space_admission']['reserved_bytes'], 6*1024**3)
        # Per-job: exceeding the declared budget fails the job; cleanup still verified.
        with admitted():
            out = t.run(s, [sys.executable, '-c',
                            "from pathlib import Path;import time;Path('huge').write_bytes(b'x'*10000);time.sleep(5)"],
                        root=self.runner, slot=0, job_limit=5000)
        self.assertEqual(out['state'], 'FAILED', out)
        self.assertIn('storage_budget', out['error'])
        self.assertTrue(out['cleanup_verified'])
        self.assertEqual(out['declared_budget_bytes'], 5000)
        self.assertFalse((self.runner/'slot-0/scratch').exists())

    # A3: active-job lease; lease identity checked on cleanup.
    def test_a3_lease_identity_checked_on_cleanup(self):
        s = self.sealed()
        # A foreign lease is refused instead of deleting anything.
        slot = self.runner/'slot-0'; slot.mkdir(parents=True)
        (slot/'lease.json').write_text(json.dumps(
            dict(schema=t.LEASE_SCHEMA, job='b'*32, pid=1, declared_bytes=1)))
        with self.assertRaisesRegex(ValueError, 'lease_identity_mismatch'):
            t.verify_lease(slot, 'c'*32)
        shutil.rmtree(slot)
        # A live job can read its own lease while running...
        lease = self.runner/'slot-0/lease.json'
        code = ("from pathlib import Path\n"
                "Path('outputs/lease_snapshot.json').write_text(Path("+repr(str(lease))+").read_text())")
        with admitted():
            out = t.run(s, [sys.executable, '-c', code], ['outputs/lease_snapshot.json'],
                        root=self.runner, slot=0)
        self.assertEqual(out['state'], 'PASSED', out)
        snap = json.loads((Path(out['result_directory'])/'artifacts/outputs/lease_snapshot.json').read_text())
        self.assertEqual(snap['schema'], t.LEASE_SCHEMA)
        self.assertEqual(snap['job'], out['job'])
        self.assertEqual(snap['declared_bytes'], out['declared_budget_bytes'])
        # ...and after cleanup the lease and scratch are gone together.
        self.assertFalse(lease.exists())
        self.assertFalse((self.runner/'slot-0/scratch').exists())
        # If the lease does not match at cleanup, nothing is deleted and a hold is recorded.
        with admitted(), patch.object(t, 'verify_lease',
                                      side_effect=ValueError('lease_identity_mismatch_preserved')):
            out = t.run(s, [sys.executable, '-c', 'pass'], root=self.runner, slot=0)
        self.assertEqual(out['state'], 'BLOCKED', out)
        self.assertIn('lease_identity_mismatch', out.get('cleanup_error', ''))
        self.assertTrue((self.runner/'slot-0/scratch').exists())
        holds = t.read_holds(self.runner)['holds']
        self.assertTrue(any(h['kind'] == 'scratch_preserved' and 'cleanup_failed' in h['reason']
                            for h in holds), holds)

    # A4: explicit evidence pins; undeclared files are disposable.
    def test_a4_evidence_pins_declared_hashed_undeclared_disposable(self):
        s = self.sealed()
        with admitted():
            out = t.run(s, [sys.executable, '-c',
                            "from pathlib import Path;"
                            "Path('outputs/evidence.json').write_text('{\"ok\": 1}');"
                            "Path('scratch_junk.bin').write_bytes(b'j'*4096)"],
                        ['outputs/evidence.json'], root=self.runner)
        self.assertEqual(out['state'], 'PASSED', out)
        self.assertEqual(sorted(out['artifacts']), ['outputs/evidence.json', 'runner.log'])
        kept = Path(out['result_directory'])/'artifacts/outputs/evidence.json'
        self.assertEqual(out['artifacts']['outputs/evidence.json'], t.sha(kept.read_bytes()))
        self.assertFalse((self.runner/'slot-0/scratch').exists())
        self.assertFalse(list(Path(out['result_directory']).rglob('scratch_junk.bin')))

    # A5: automatic cleanup per outcome: success, nonzero failure, timeout.
    # Interruption (killed runner) is covered by A6 plus the existing suite's
    # crashed-runner recovery test.
    def test_a5_cleanup_on_success_failure_timeout(self):
        s = self.sealed()
        cases = [("from pathlib import Path;Path('outputs/o').write_text('x')", 600, 'PASSED'),
                 ("raise SystemExit(3)", 600, 'FAILED'),
                 ("import time;time.sleep(30)", .2, 'FAILED')]
        for code, timeout, expect in cases:
            with admitted():
                out = t.run(s, [sys.executable, '-c', code], timeout=timeout, root=self.runner)
            self.assertEqual(out['state'], expect, out)
            self.assertTrue(out['cleanup_verified'], out)
            self.assertFalse((self.runner/'slot-0/scratch').exists())

    # A6: abandoned scratch + stale job identity recovered on next use.
    def test_a6_abandoned_scratch_recovered_after_restart(self):
        s = self.sealed()
        slot = self.runner/'slot-0'; scratch = slot/'scratch'
        scratch.mkdir(parents=True)
        jid = 'd'*32
        result = self.runner/'results'/jid; result.mkdir(parents=True)
        (scratch/'.chimera-runner-id').write_text(jid)
        (scratch/'outputs').mkdir(); (scratch/'outputs/abandoned.json').write_text('{"recovered": true}')
        (slot/'job.json').write_text(json.dumps(dict(
            schema=t.JOB_SCHEMA, job=jid, sealed='x', keep=['outputs/abandoned.json'],
            result=str(result))))
        (slot/'lease.json').write_text(json.dumps(dict(
            schema=t.LEASE_SCHEMA, job=jid, pid=999999, declared_bytes=1024)))
        with admitted():
            out = t.run(s, [sys.executable, '-c', 'pass'], root=self.runner)
        self.assertEqual(out['state'], 'PASSED', out)
        recs = list((self.runner/'results').glob('*/recovery.json'))
        self.assertEqual(len(recs), 1)
        rec = json.loads(recs[0].read_text())
        self.assertEqual(rec['state'], 'INTERRUPTED_RECOVERED')
        self.assertTrue(rec['cleanup_verified'])
        self.assertEqual(rec['job'], jid)
        self.assertEqual(json.loads((recs[0].parent/'artifacts/outputs/abandoned.json').read_text()),
                         {'recovered': True})
        rb = rec['bytes']
        self.assertEqual(rb['scratch_at_cleanup_bytes'], rb['retained_bytes']+rb['reclaimed_bytes'])
        self.assertFalse(scratch.exists())
        self.assertFalse((slot/'lease.json').exists())  # stale lease consumed with recovery

    # A7: receipt byte accounting: created == retained + reclaimed.
    def test_a7_receipt_byte_accounting_adds_up(self):
        s = self.sealed()
        with admitted():
            out = t.run(s, [sys.executable, '-c',
                            "from pathlib import Path;"
                            "Path('outputs/kept.bin').write_bytes(b'k'*10000);"
                            "Path('junk.bin').write_bytes(b'j'*3000)"],
                        ['outputs/kept.bin'], root=self.runner)
        self.assertEqual(out['state'], 'PASSED', out)
        b = out['bytes']
        self.assertEqual(b['schema'], t.BYTES_SCHEMA)
        self.assertEqual(b['units'], 'bytes')
        self.assertEqual(b['scratch_at_cleanup_bytes'], b['retained_bytes']+b['reclaimed_bytes'])
        artifacts = Path(out['result_directory'])/'artifacts'
        retained = sum(p.stat().st_size for p in artifacts.rglob('*') if p.is_file())
        self.assertEqual(b['retained_bytes'], retained)
        self.assertGreaterEqual(b['scratch_peak_bytes'], b['scratch_at_cleanup_bytes'])
        self.assertGreaterEqual(b['reclaimed_bytes'], 3000)
        self.assertEqual(b['declared_budget_bytes'], out['declared_budget_bytes'])

    # A8: holds ledger: owner, reason, next action, date for indefinite holds.
    def test_a8_holds_ledger_records_indefinite_preserves(self):
        s = self.sealed()
        slot = self.runner/'slot-0'; (slot/'scratch').mkdir(parents=True)
        (slot/'scratch/mystery').write_text('not ours')
        with self.assertRaisesRegex(ValueError, 'slot_recovery_required'):
            t.run(s, [sys.executable, '-c', 'pass'], root=self.runner)
        self.assertTrue((slot/'scratch/mystery').exists())  # preserved, never guessed disposable
        ledger = t.read_holds(self.runner)
        self.assertEqual(ledger['schema'], t.HOLDS_SCHEMA)
        self.assertGreaterEqual(len(ledger['holds']), 1)
        for key in ('date', 'kind', 'owner', 'reason', 'next_action'):
            self.assertTrue(ledger['holds'][-1][key])
        self.assertEqual(ledger['holds'][-1]['kind'], 'scratch_preserved')
        entry = t.record_hold(self.runner, 'results_preserved', 'campaign',
                              'results_budget_exceeded', 'anchor then retire', 'results')
        again = t.read_holds(self.runner)
        self.assertEqual(entry['index'], len(again['holds'])-1)
        self.assertEqual(again['holds'][entry['index']]['owner'], 'campaign')

    # A9: directory separation policy enforced by admission checks.
    def test_a9_directory_separation_enforced(self):
        self.assertEqual(t.classify_runner(self.runner, self.runner/'results'/'x'), 'protected_evidence')
        self.assertEqual(t.classify_runner(self.runner, self.runner/'slot-0'/'scratch'), 'temporary_scratch')
        self.assertEqual(t.classify_runner(self.runner, self.runner/'slot-0'/'job.json'), 'runner_metadata')
        self.assertEqual(t.classify_runner(self.runner, self.runner/'slot-0'/'lease.json'), 'runner_metadata')
        self.assertEqual(t.classify_runner(self.runner, self.runner/'slot-0'/'scratch-falsifiers'), 'unknown')
        self.assertEqual(t.classify_package(self.pkg, self.pkg/'files'), 'regenerable_cache')
        self.assertEqual(t.classify_package(self.pkg, self.pkg/'sealed'), 'pinned_package_history')
        slot = self.runner/'slot-0'; (slot/'cache').mkdir(parents=True)
        for victim in (slot/'cache', self.runner/'results'/'x', slot/'job.json'):
            with self.assertRaisesRegex(ValueError, 'not_runner_owned_scratch'):
                t.remove_owned(victim, slot)


if __name__ == '__main__':
    unittest.main()
