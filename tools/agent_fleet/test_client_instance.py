"""fleet-client-instance-01: distinct durable client instance identities.

The fence is TASK-CENTRIC: a claim binds the claiming instance; only that
instance (of that agent) mutates the claimed task. Legacy sessions stay
admitted in compat mode with an explicit `legacy-unfenced` audit marker;
enforced mode refuses instance-less claims. Instance secrets appear nowhere
in state (only sha256 fingerprints), snapshot, events, or logs.
"""
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control import Control, Refusal
from service import Server
from client import call as http_call

BASE = 'a' * 40


class ClientInstanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / 'state.sqlite'
        self.c = Control(self.db, 'super-secret', 'enroll-secret', self.root / 'slots')
        self._spin()  # leader election so tasks can be created
        self.call('create_task', 'lead', task='probe', epoch=self.snap()['epoch'],
                  base=BASE, scopes=['tools/labs/probe'], kind='worker',
                  packet='statement / prediction / falsifier')

    def tearDown(self):
        self.tmp.cleanup()

    # --- harness ----------------------------------------------------------
    def _spin(self):
        tok = self.c.call('enroll', 'enroll-secret', agent='lead', label='lead')['result']['session_token']
        self.lead_tok = tok
        self.c.call('qualify', 'super-secret', agent='lead', capabilities=['cpu'],
                    max_tasks=2, can_lead=True, rank=1, evidence='fixture lead')
        self.c.call('offer_lead', tok, epoch=0, checkpoint='fixture')
        self.c.call('elect', 'super-secret')

    def enroll_instance_agent(self, aid='wk', with_instance=True):
        args = {'agent': aid, 'label': aid}
        instance = None
        if with_instance:
            instance = {'id': aid + '-inst-1', 'secret': 'INSTSECRET-' + aid + '-0123456789abcdef'}
            args['instance'] = instance
        out = self.c.call('enroll', 'enroll-secret', **args)['result']
        self.c.call('qualify', 'super-secret', agent=aid, capabilities=['cpu'],
                    max_tasks=2, can_lead=False, evidence='fixture worker')
        return out['session_token'], instance

    def call(self, op, actor_token, _instance=None, **p):
        tok = self.lead_tok if actor_token == 'lead' else actor_token
        return self.c.call(op, tok, _instance=_instance, **p)['result']

    def snap(self):
        return self.c.call('snapshot', self.lead_tok)['result']

    def claim_probe(self, token, instance=None):
        return self.call('claim', token, _instance=instance, task='probe')

    # --- 1. baseline: legacy compat admits both writers (before-picture) --
    def test_baseline_two_legacy_clients_both_admitted_unfenced(self):
        tok, _ = self.enroll_instance_agent(with_instance=False)
        t = self.claim_probe(tok)
        # Two clients sharing the bearer, no instance headers (feedback
        # 4a1e631e scenario): both admitted, audit lacks instance identity.
        a = self.call('checkpoint', tok, task='probe', generation=t['generation'],
                      checkpoint='client A writes')
        b = self.call('checkpoint', tok, task='probe', generation=t['generation'],
                      checkpoint='client B writes')
        self.assertTrue(a['saved'] and b['saved'])
        events = self.c.call('events', self.lead_tok, since=0)['result']['events']
        ours = [e for e in events if e.get('task') == 'probe' and e['kind'] == 'checkpoint']
        self.assertEqual(len(ours), 2)
        self.assertTrue(all(e.get('instance') == 'legacy-unfenced' for e in ours))
        # retained as the documented gap: nothing in this PR rewrites history.

    # --- 2. the fence: only the bound instance mutates the claimed task ---
    def test_bound_task_refuses_second_instance_and_header_less_caller(self):
        tok, inst = self.enroll_instance_agent()
        t = self.claim_probe(tok, instance=inst)
        self.assertEqual(t['owner_instance'], inst['id'])
        # wrong secret -> named refusal at authentication
        forged = {'id': inst['id'], 'secret': 'INSTSECRET-wrong-0123456789abcdef'}
        with self.assertRaisesRegex(Refusal, 'instance_secret_mismatch'):
            self.call('checkpoint', tok, _instance=forged, task='probe',
                      generation=t['generation'], checkpoint='forged')
        # same bearer, no instance header -> fence refusal on the bound task
        with self.assertRaisesRegex(Refusal, 'instance_not_bound'):
            self.call('checkpoint', tok, task='probe',
                      generation=t['generation'], checkpoint='header-less twin')
        # the bound instance succeeds
        r = self.call('checkpoint', tok, _instance=inst, task='probe',
                      generation=t['generation'], checkpoint='bound instance writes')
        self.assertTrue(r['saved'])
        # resource mutation paths are fenced the same way
        with self.assertRaisesRegex(Refusal, 'instance_not_bound'):
            self.call('resource_acquire', tok, task='probe',
                      generation=t['generation'], resource='rtx4090')
        events = self.c.call('events', self.lead_tok, since=0)['result']['events']
        bound = [e for e in events if e.get('instance') == inst['id']]
        self.assertTrue(bound)

    # --- 3. secrets never surface in state, snapshot, or events -----------
    def test_instance_secret_absent_from_snapshot_events_and_state(self):
        tok, inst = self.enroll_instance_agent()
        t = self.claim_probe(tok, instance=inst)
        self.call('checkpoint', tok, _instance=inst, task='probe',
                  generation=t['generation'], checkpoint='scan me')
        snap_text = json.dumps(self.snap())
        events_text = json.dumps(self.c.call('events', self.lead_tok, since=0)['result'])
        import sqlite3
        con = sqlite3.connect(self.db)
        state_text = con.execute('SELECT body FROM state WHERE id=1').fetchone()[0]
        events_table = con.execute('SELECT body FROM events').fetchall()
        con.close()
        for surface in (snap_text, events_text, state_text,
                        json.dumps([r[0] for r in events_table])):
            self.assertNotIn(inst['secret'], surface)
        # fingerprint stored, ids visible in snapshot without hashes
        self.assertIn(inst['id'], snap_text)
        self.assertNotIn('secret_hash', snap_text)

    # --- 4. restart preserves bindings and the fence ----------------------
    def test_fence_survives_reopen_on_same_store(self):
        tok, inst = self.enroll_instance_agent()
        t = self.claim_probe(tok, instance=inst)
        c2 = Control(self.db, 'super-secret', 'enroll-secret', self.root / 'slots')
        with self.assertRaisesRegex(Refusal, 'instance_not_bound'):
            c2.call('checkpoint', tok, task='probe',
                    generation=t['generation'], checkpoint='after restart, twin')['result']
        r = c2.call('checkpoint', tok, _instance=inst, task='probe',
                    generation=t['generation'], checkpoint='after restart, bound')['result']
        self.assertTrue(r['saved'])

    # --- 5. enforced mode refuses instance-less claims --------------------
    def test_enforced_mode_requires_instance_for_new_claims(self):
        legacy_tok, _ = self.enroll_instance_agent('legacy1', with_instance=False)
        itok, inst = self.enroll_instance_agent('fenced1')
        r = self.call('instance_fencing_set', 'super-secret', mode='enforced')
        self.assertEqual(r['instance_fencing'], 'enforced')
        with self.assertRaisesRegex(Refusal, 'instance_binding_required'):
            self.claim_probe(legacy_tok)
        t = self.claim_probe(itok, instance=inst)
        self.assertEqual(t['owner_instance'], inst['id'])
        # supervisor can return to compat (staged migration both ways)
        self.call('instance_fencing_set', 'super-secret', mode='compat')
        # flip to enforced without any instance-bearing agent is refused
        c3 = Control(self.root / 'fresh.sqlite', 'super-secret', 'enroll-secret',
                     self.root / 'slots3')
        with self.assertRaisesRegex(Refusal, 'no_instance_bearing_agents'):
            c3.call('instance_fencing_set', 'super-secret', mode='enforced')

    # --- 6. transport: malformed header refused by name -------------------
    def test_transport_malformed_instance_header_refused(self):
        tok, inst = self.enroll_instance_agent()
        t = self.claim_probe(tok, instance=inst)
        server = Server(('127.0.0.1', 0), self.c)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = {'endpoint': 'http://127.0.0.1:%d/v1/action' % server.server_port}
            # the client library sends the header from the session file
            session = {**base, 'token': tok, 'instance': inst}
            r = http_call(session, 'checkpoint', {'task': 'probe',
                         'generation': t['generation'], 'checkpoint': 'via header'})
            self.assertTrue(r['result']['saved'])
            # malformed header (no colon) -> named refusal, nothing executed
            import urllib.request
            import urllib.error
            body = json.dumps({'operation': 'snapshot', 'arguments': {}}).encode()
            req = urllib.request.Request(base['endpoint'], data=body, headers={
                'Authorization': 'Bearer ' + tok,
                'Content-Type': 'application/json',
                'X-Chimera-Instance': 'nocolon'})
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=10)
            with ctx.exception:
                body_text = ctx.exception.read().decode()
            self.assertIn('invalid_instance_header', body_text)
        finally:
            server.shutdown(); server.server_close(); thread.join()

    # --- 7. supervisor ops carry no instance marker -----------------------
    def test_supervisor_events_have_no_instance_marker(self):
        tok, inst = self.enroll_instance_agent()
        t = self.claim_probe(tok, instance=inst)
        self.call('checkpoint', tok, _instance=inst, task='probe',
                  generation=t['generation'], state='BLOCKED', checkpoint='blocked for guard test')
        # supervisor release paths stay instance-free by design
        events = self.c.call('events', self.lead_tok, since=0)['result']['events']
        sup = [e for e in events if e.get('actor') == 'SUPERVISOR' and 'task' in e]
        self.assertTrue(all('instance' not in e for e in sup))


if __name__ == '__main__':
    unittest.main(verbosity=2)
