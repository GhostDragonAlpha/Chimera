"""fleet-slot-expansion-03: slots materialize on demand, like worktrees.

The registry dict IS the state. Fresh registries still initialize 5 slots
(migration no-op); growth is additive via supervisor slot_spawn / claim
auto-spawn; free unprovisioned slots retire via slot_retire (slot 1 is the
immortal integration slot); SLOT_MAX (64) is a safety fuse, not a ceiling.
The scale probe records the first latency/spawn-cost data for the
operator's I/O-limit hypothesis.
"""
import json
from pathlib import Path
import statistics
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control import Control, Refusal
from layout import SLOT_MAX, slot_layout

BASE = 'a' * 40


def _spin(root):
    """Fresh registry with an elected lead; returns (control, lead_token)."""
    c = Control(root / 'state.sqlite', 'super-secret', 'enroll-secret',
                root / 'slots')
    tok = c.call('enroll', 'enroll-secret', agent='lead', label='lead')['result']['session_token']
    c.call('qualify', 'super-secret', agent='lead', capabilities=['cpu'],
           max_tasks=5, can_lead=True, rank=1, evidence='fixture lead')
    c.call('offer_lead', tok, epoch=0, checkpoint='fixture')
    c.call('elect', 'super-secret')
    return c, tok


def _worker(c, aid, caps=('cpu',), max_tasks=1):
    tok = c.call('enroll', 'enroll-secret', agent=aid, label=aid)['result']['session_token']
    c.call('qualify', 'super-secret', agent=aid, capabilities=list(caps),
           max_tasks=max_tasks, can_lead=False, rank=0, evidence='fixture worker')
    return tok


def _task(c, tok, tid, epoch, scopes=None):
    return c.call('create_task', tok, task=tid, epoch=epoch, base=BASE,
                  scopes=scopes or ['tools/labs/' + tid], kind='worker',
                  packet='statement / prediction / falsifier')['result']


class SlotExpansionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    # --- 1. migration is a no-op on existing registries -------------------
    def test_reopen_existing_registry_changes_nothing(self):
        c, tok = _spin(self.root)
        before = json.dumps(c.call('snapshot', tok)['result']['slots'],
                            sort_keys=True)
        c2 = Control(self.root / 'state.sqlite', 'super-secret',
                     'enroll-secret', self.root / 'slots')
        after = json.dumps(c2.call('snapshot', tok)['result']['slots'],
                           sort_keys=True)
        self.assertEqual(before, after)
        self.assertEqual(len(json.loads(after)), 5)

    # --- 2. supervisor spawn/retire with named refusals --------------------
    def test_slot_spawn_and_retire_roundtrip_with_refusals(self):
        c, tok = _spin(self.root)
        w = _worker(c, 'w1')
        r = c.call('slot_spawn', 'super-secret')['result']
        self.assertEqual(r['slot'], '6')
        self.assertEqual(r['kind'], 'worker')
        self.assertEqual(r['path'], str(self.root / 'slots' / 'slot-06'))
        self.assertEqual(slot_layout(self.root, 6)['engine']['port_candidate'],
                         8106)
        # slot 1 is the UNIQUE integration slot: a second one refuses by name
        with self.assertRaisesRegex(Refusal, 'integration_slot_unique'):
            c.call('slot_spawn', 'super-secret', kind='integration')
        # refusals by name
        for args, err in ((dict(kind='gpu'), 'invalid_slot_kind'),
                          (dict(), 'supervisor_only')):
            actor = w if err == 'supervisor_only' else 'super-secret'
            with self.assertRaisesRegex(Refusal, err):
                c.call('slot_spawn', actor, **args)
        # retire: busy refusal on a bound spawned slot, then clean roundtrip
        ep = c.call('snapshot', tok)['result']['epoch']
        c.call('create_task', tok, task='busy0', epoch=ep, base=BASE,
               scopes=['tools/labs/busy0'], kind='worker', packet='fixture')
        w2 = _worker(c, 'w2')
        t = c.call('claim', w2, task='busy0')['result']
        with self.assertRaisesRegex(Refusal, 'slot_busy'):
            c.call('slot_retire', 'super-secret', slot=t['slot'])
        c.call('claim_abandon', 'super-secret', task='busy0',
               generation=t['generation'],
               preservation_evidence='fixture preservation',
               drain_evidence='fixture drain')
        c.call('slot_retire', 'super-secret', slot=t['slot'], evidence='retire freed slot')
        self.assertNotIn(t['slot'], c.call('snapshot', tok)['result']['slots'])
        for args, err in ((dict(slot='1'), 'integration_slot_immortal'),
                          (dict(slot='99'), 'unknown_slot'),
                          (dict(), 'supervisor_only')):
            actor = w if err == 'supervisor_only' else 'super-secret'
            with self.assertRaisesRegex(Refusal, err):
                c.call('slot_retire', actor, **args)
        # retired ids are NEVER reused (persisted high-water mark) and slots
        # with preserved history refuse to retire
        sub = self.root / 'r2'; sub.mkdir()
        c2, tok2 = _spin(sub)
        ra = c2.call('slot_spawn', 'super-secret')['result']      # id 6
        rb = c2.call('slot_spawn', 'super-secret')['result']      # id 7
        self.assertEqual(rb['slot'], '7')
        c2.call('slot_retire', 'super-secret', slot='7', evidence='hwm test')
        rc = c2.call('slot_spawn', 'super-secret')['result']
        self.assertEqual(rc['slot'], '8')  # NOT 7 - high-water held
        # preserved history blocks retire
        con = c2.connect(); con.execute('BEGIN IMMEDIATE')
        s = json.loads(con.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
        s['slots']['8']['engine']['preserved_provisions'] = [{'reason': 'x'}]
        con.execute('UPDATE state SET body=? WHERE id=1', (json.dumps(s),))
        con.execute('COMMIT'); con.close()
        with self.assertRaisesRegex(Refusal, 'slot_has_preserved_history'):
            c2.call('slot_retire', 'super-secret', slot='8', evidence='blocked')
        # integration task never auto-spawns when slot 1 is busy
        ep2 = c2.call('snapshot', tok2)['result']['epoch']
        c2.call('create_task', tok2, task='ilead', epoch=ep2, base=BASE,
                scopes=['tools/labs/ilead'], kind='integration', packet='f')
        c2.call('claim', tok2, task='ilead')  # takes slot 1
        c2.call('create_task', tok2, task='ilead2', epoch=ep2, base=BASE,
                scopes=['tools/labs/ilead2'], kind='integration', packet='f')
        with self.assertRaisesRegex(Refusal, 'integration_slot_busy'):
            c2.call('claim', tok2, task='ilead2')

        # guard fuse: spawn until the named refusal fires (ids grow past
        # retired slots, so the refusal may arrive before the count hits
        # SLOT_MAX - exactly the id-space binding the guard now enforces)
        hit = False
        while True:
            try:
                c.call('slot_spawn', 'super-secret')
            except Refusal as e:
                self.assertIn('slot_guard_reached', str(e))
                hit = True
                break
        self.assertTrue(hit)

    # --- 3. claim auto-spawn end-to-end; stale-provision NOT masked -------
    def test_claim_auto_spins_slot_and_preserves_stale_refusal(self):
        c, tok = _spin(self.root)
        w = _worker(c, 'w1', max_tasks=5)
        ep = c.call('snapshot', tok)['result']['epoch']
        tids = ['t%d' % i for i in range(4)]
        for tid in tids:
            _task(c, tok, tid, ep)
        heads = {}
        for tid in tids:  # fill all 4 worker slots (slot 1 is integration-kind)
            t = c.call('claim', w, task=tid)['result']
            heads[tid] = t['generation']
        self.assertEqual(sorted(k for k, v in
                                c.call('snapshot', tok)['result']['slots'].items()
                                if v['task']), ['2', '3', '4', '5'])
        # 5th claim finds no free worker slot -> AUTO-SPINS slot 6 end-to-end
        _task(c, tok, 't4', ep)
        t6 = c.call('claim', w, task='t4')['result']
        self.assertEqual(t6['slot'], '6')
        r = c.call('checkpoint', w, task='t4', generation=t6['generation'],
                   checkpoint='on a spawned slot')['result']
        self.assertTrue(r['saved'])
        # stale-provision masking: free slot 2 (submit its task) then fake a
        # stale provision on it; a new claim must REFUSE, not spawn past it
        # stale provision on it; a new claim must REFUSE, not spawn past it.
        # claim_abandon (base-plane op) frees the unprovisioned claim and its
        # slot, returning the task to READY at gen+1.
        c.call('claim_abandon', 'super-secret', task='t0',
               generation=heads['t0'],
               preservation_evidence='fixture preservation',
               drain_evidence='fixture drain')
        # simulate an ACTIVE stale provision on the now-free slot 2
        con = c.connect()
        con.execute('BEGIN IMMEDIATE')
        s = json.loads(con.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
        s['slots']['2']['engine']['provisioned'] = True
        s['slots']['2']['engine']['provision_task'] = 't0'
        s['slots']['2']['engine']['provision_generation'] = 99
        con.execute('UPDATE state SET body=? WHERE id=1', (json.dumps(s),))
        con.execute('COMMIT')
        con.close()
        _task(c, tok, 't6', ep)
        with self.assertRaisesRegex(Refusal, 'stale_provision_requires_recovery'):
            c.call('claim', w, task='t6')['result']
        self.assertEqual(len(c.call('snapshot', tok)['result']['slots']), 6)

    # --- 4. scale probe: lock errors + latency percentiles + spawn cost ---
    def test_scale_probe_lock_errors_and_latency(self):
        c, tok = _spin(self.root)
        w = [_worker(c, 'w%d' % i) for i in range(8)]
        ep = c.call('snapshot', tok)['result']['epoch']
        for i in range(24):
            _task(c, tok, 'p%d' % i, ep, scopes=['tools/labs/p%d' % i])
        lat = []
        errs = []
        stop = time.monotonic() + 20.0
        lock_err = 0

        def churn(i):
            # MIXED load per the prediction: 4 reads per 1 write cycle
            # (fleet-realistic; workers poll snapshots far more often than
            # they write).
            nonlocal lock_err
            n = 0
            while time.monotonic() < stop:
                t0 = time.monotonic()
                try:
                    for _ in range(4):
                        c.call('snapshot', w[i])
                    tid = 'p%d' % (n % 24)
                    t = c.call('claim', w[i], task=tid)['result']
                    c.call('checkpoint', w[i], task=tid,
                           generation=t['generation'],
                           checkpoint='probe n%d' % n)
                    c.call('claim_abandon', 'super-secret', task=tid,
                           generation=t['generation'],
                           preservation_evidence='probe preservation',
                           drain_evidence='probe drain')
                except Refusal as e:
                    errs.append(str(e))
                    if 'database is locked' in str(e):
                        lock_err += 1
                except Exception as e:  # noqa: BLE001 - probe counts everything
                    errs.append('%s:%s' % (type(e).__name__, e))
                    if 'locked' in str(e).lower():
                        lock_err += 1
                lat.append(time.monotonic() - t0)
                n += 1

        threads = [threading.Thread(target=churn, args=(i,)) for i in range(8)]
        t_start = time.monotonic()
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        wall = time.monotonic() - t_start
        spawn_t0 = time.monotonic()
        spawned = 0
        while spawned < 20:
            before = len(c.call('snapshot', tok)['result']['slots'])
            c.call('slot_spawn', 'super-secret')
            spawned += 1
            assert len(c.call('snapshot', tok)['result']['slots']) == before + 1
        spawn_cost = (time.monotonic() - spawn_t0) / spawned
        lat.sort()
        pct = lambda q: lat[min(len(lat) - 1, int(q * len(lat)))]
        summary = {
            'threads': 8, 'duration_s': round(wall, 1), 'ops': len(lat),
            'p50_ms': round(pct(0.50) * 1000, 1),
            'p95_ms': round(pct(0.95) * 1000, 1),
            'p99_ms': round(pct(0.99) * 1000, 1),
            'max_ms': round(lat[-1] * 1000, 1),
            'lock_errors': lock_err,
            'other_refusals': len(errs) - lock_err,
            'spawn_cost_ms': round(spawn_cost * 1000, 1),
        }
        print('SCALE_PROBE_MIXED ' + json.dumps(summary))
        self.assertEqual(lock_err, 0, 'lock errors: %s' % summary)
        self.assertLess(summary['p95_ms'], 1000.0, summary)
        # SATURATED phase (writes only, no reads): recorded as boundary data
        # for the operator I/O hypothesis; lock errors are REPORTED, not
        # asserted - this is the deliberate overload profile.
        sat_lat, sat_lock = [], 0
        stop_sat = time.monotonic() + 5.0
        def saturate(i):
            nonlocal sat_lock
            n = 0
            while time.monotonic() < stop_sat:
                t0 = time.monotonic()
                try:
                    tid = 'p%d' % (n % 24)
                    t = c.call('claim', w[i], task=tid)['result']
                    c.call('claim_abandon', 'super-secret', task=tid,
                           generation=t['generation'],
                           preservation_evidence='sat', drain_evidence='sat')
                except Refusal as e:
                    if 'database is locked' in str(e) or 'slot_guard' in str(e):
                        if 'database is locked' in str(e):
                            sat_lock += 1
                except Exception:
                    sat_lock += 1
                sat_lat.append(time.monotonic() - t0)
                n += 1
        ths = [threading.Thread(target=saturate, args=(i,)) for i in range(8)]
        for th in ths: th.start()
        for th in ths: th.join()
        sat_lat.sort()
        sat = {'ops': len(sat_lat), 'lock_or_err': sat_lock,
               'p50_ms': round(sat_lat[len(sat_lat)//2]*1000, 1),
               'p95_ms': round(sat_lat[int(0.95*len(sat_lat))]*1000, 1),
               'max_ms': round(sat_lat[-1]*1000, 1)}
        print('SCALE_PROBE_SATURATED ' + json.dumps(sat))

    # --- 5. layout + inventory parameterization ---------------------------
    def test_layout_bounds_and_inventory_default(self):
        self.assertEqual(slot_layout(self.root, 64)['engine']['port_candidate'], 8164)
        with self.assertRaises(ValueError):
            slot_layout(self.root, 65)
        import inventory
        plan5 = inventory.plan(self.root, BASE)
        self.assertEqual(len(plan5['slots']), 5)
        plan8 = inventory.plan(self.root, BASE, 8)
        self.assertEqual(len(plan8['slots']), 8)
        self.assertEqual(plan8['slots'][7]['engine']['port_candidate'], 8108)


if __name__ == '__main__':
    unittest.main(verbosity=2)
