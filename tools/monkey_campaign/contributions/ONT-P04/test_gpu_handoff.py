"""ONT-P04 correction probes: GPU-A handoff authority/state machine.

Records profile (offline, CPU-only, isolated temporary registries). Frozen in
PREREGISTRATION.md of attempt 4f4df57ef3d54c0996cf969e8a599d1b BEFORE any run.
Every probe runs against `pinned/tools/agent_fleet` extracted byte-exactly from
attempt head c525b82c7c3ce0128565424764293a3c85811ab3 plus the new additive
subclass gpu_handoff.HandoffControl. No GPU, no live registry, no real process:
"drained"/"graceful" evidence strings are records inside fixtures.

Probe groups (frozen):
  H1 legal chain: the six-state sequence with registry facts at each edge
  H2 illegal-transition refusal matrix: exact refusal names
  H3 idempotent re-request and fair arrival-order serialization
  H4 crash-recovery reconstruction (restart, corruption, replay)
  H5 supervisor-only invariants (graceful release, never force-kill,
     never release a protected run on timer/silence)
  H6 inference admission gate (RESOURCE_WAIT, timeout stays closed, bypass
     refused, open only on the restore path)
"""
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

WS = Path(__file__).resolve().parent
PINNED = WS / 'pinned' / 'tools' / 'agent_fleet'
sys.path.insert(0, str(PINNED))
sys.path.insert(0, str(WS))

from control import Control, Refusal            # noqa: E402
from gpu_handoff import HandoffControl          # noqa: E402

BASE = 'a' * 40
CFG = {'artifact': 'qwen-local', 'context': 119296, 'offload': 'cpu',
       'workers': ['bionic']}
GAME = dict(executable='C:/games/forest-demo.exe', pid=4242,
            start_time='2026-09-26T10:00:00Z')


class Harness:
    """Shared fixture: isolated HandoffControl registry, three agents."""

    def setup(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / 'state.sqlite'
        self.c = HandoffControl(self.db, 'SUP', 'ENR', self.root / 'slots',
                                memory_budget_mb=8192)
        self.tok = {}
        for aid in ('lead', 'gamer', 'trainer'):
            self.tok[aid] = self.c.call('enroll', 'ENR', agent=aid,
                                        label=aid)['result']['session_token']
            self.c.call('qualify', 'SUP', agent=aid, capabilities=['cpu', 'gpu'],
                        max_tasks=3, can_lead=aid == 'lead',
                        rank=5 if aid == 'lead' else 1,
                        evidence='ONT-P04 correction fixture')
        self.c.call('offer_lead', self.tok['lead'], epoch=0,
                    checkpoint='ONT-P04 correction; no foreign work')
        self.c.call('elect', 'SUP')

    def teardown(self):
        self.tmp.cleanup()

    def call(self, op, actor='lead', **p):
        return self.c.call(op, self.tok.get(actor, actor), **p)['result']

    def refused(self, op, actor, error, **p):
        with self.assertRaisesRegex(Refusal, error):
            self.call(op, actor, **p)

    def snap(self):
        return self.call('snapshot', 'SUP')

    def epoch(self):
        return self.snap()['epoch']

    def task_pair(self, game='game', training='training'):
        ep = self.epoch()
        self.call('create_task', task=game, epoch=ep, base=BASE,
                  scopes=['docs/evidence/' + game], packet='p')
        self.call('create_task', task=training, epoch=self.epoch(), base=BASE,
                  scopes=['docs/evidence/' + training], packet='p')
        self.call('claim', actor='gamer', task=game)
        claimed = self.call('claim', actor='trainer', task=training)
        self.call('resource_request', actor='gamer', task=game, generation=1,
                  wants=[{'name': 'rtx4090'}])
        self.call('resource_request', actor='trainer', task=training,
                  generation=1, wants=[{'name': 'rtx4090'}])
        return claimed

    def request(self, training='training', actor='trainer', **over):
        p = dict(task=training, generation=1, evidence='training brief',
                 derivation_gate_receipt='gate-receipt-1',
                 vram_required_mb=1000, expected_duration_minutes=30)
        p.update(over)
        return self.call('handoff_request', actor, **p)

    def register_fixtures(self):
        self.call('handoff_register_model', 'SUP', instance='qwen-local',
                  restoration_config=dict(CFG))
        self.call('handoff_register_game', 'SUP', name='forest-demo', **GAME)

    def drain(self, rid, training='training', release_game_holder=True):
        """Drive DRAINING: gate, checkpoint, named unload, graceful release."""
        self.call('handoff_gate_close', 'trainer', task=training)
        self.call('handoff_checkpoint_preserved', 'trainer', task=training,
                  evidence='session/tool/child state preserved', workers=['bionic'])
        self.call('handoff_model_unload', 'trainer', task=training,
                  instance='qwen-local', restoration_config=dict(CFG))
        self.call('handoff_game_release', 'trainer', task=training,
                  name='forest-demo', pid=GAME['pid'],
                  start_time=GAME['start_time'],
                  evidence='application save/quit confirmed',
                  observed_free_vram_mb=2000)
        if release_game_holder:
            self.call('resource_release', 'gamer', task='game', generation=1,
                      resource='rtx4090', evidence='graceful exit drained')

    def full_chain(self, training='training'):
        claimed = self.task_pair(training=training)
        rid = self.request(training=training)['request']
        self.register_fixtures()
        self.call('handoff_admit', 'trainer', request=rid, task=training,
                  generation=1)
        self.drain(rid, training=training)
        self.call('handoff_ready', 'trainer', task=training, generation=1)
        run = self.call('handoff_launch', 'trainer', task=training,
                        generation=1, evidence='authorized start, once')
        self.call('handoff_cessation', 'trainer', task=training, generation=1,
                  observed=True, evidence='process + children exit observed',
                  preserved_receipts_evidence='receipts/checkpoints preserved')
        self.call('resource_release', 'trainer', task=training, generation=1,
                  resource='rtx4090',
                  evidence='training drained; receipts preserved first')
        self.call('handoff_restore', 'trainer', task=training, generation=1,
                  reloads=[{'instance': 'qwen-local',
                            'restoration_config': dict(CFG),
                            'health_evidence': 'reload health confirmed'}],
                  resumes=['bionic'])
        return rid, run


class H1LegalChainTests(Harness, unittest.TestCase):

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def test_six_state_sequence_with_registry_facts(self):
        claimed = self.task_pair()
        rid = self.request()['request']
        self.assertEqual(self.snap()['handoff']['requests'][rid]['phase'],
                         'REQUESTED')
        # the gaming holder is real and recorded on the request
        self.assertEqual(self.snap()['resources']['rtx4090']['task'], 'game')
        self.assertEqual(self.snap()['handoff']['requests'][rid]
                         ['existing_training_owner']['task'], 'game')
        self.register_fixtures()
        self.assertEqual(self.call('handoff_admit', 'trainer', request=rid,
                                   task='training', generation=1)['phase'],
                         'DRAINING')
        self.assertEqual(self.call('handoff_gate_close', 'trainer',
                                   task='training')['gate'], 'CLOSED')
        self.assertEqual(self.call('handoff_checkpoint_preserved', 'trainer',
                                   task='training',
                                   evidence='preserved', workers=['bionic'])
                         ['preserved'], True)
        self.assertEqual(self.call('handoff_model_unload', 'trainer',
                                   task='training', instance='qwen-local',
                                   restoration_config=dict(CFG))['unloaded'],
                         'qwen-local')
        self.assertEqual(self.call('handoff_game_release', 'trainer',
                                   task='training', name='forest-demo',
                                   pid=GAME['pid'],
                                   start_time=GAME['start_time'],
                                   evidence='save/quit',
                                   observed_free_vram_mb=2000)['method'],
                         'graceful_save_quit')
        # the gaming holder keeps the GPU until its own evidenced release
        self.assertEqual(self.snap()['resources']['rtx4090']['task'], 'game')
        self.call('resource_release', 'gamer', task='game', generation=1,
                  resource='rtx4090', evidence='graceful exit drained')
        # the grant transferred through the controller's atomic promotion
        self.assertEqual(self.snap()['resources']['rtx4090']['task'],
                         'training')
        self.assertEqual(self.snap()['resources']['rtx4090']['generation'], 1)
        self.assertEqual(self.call('handoff_ready', 'trainer', task='training',
                                   generation=1)['phase'], 'READY')
        run = self.call('handoff_launch', 'trainer', task='training',
                        generation=1, evidence='authorized start, once')
        self.assertEqual(run['phase'], 'TRAINING')
        self.assertTrue(run['run_id'])
        self.assertEqual(run['launched'], 'exactly_once')
        self.assertEqual(self.snap()['resources']['rtx4090']['task'],
                         'training')
        self.assertEqual(self.call('handoff_cessation', 'trainer',
                                   task='training', generation=1, observed=True,
                                   evidence='exit observed',
                                   preserved_receipts_evidence='kept')
                         ['phase'], 'RESTORING')
        # C3 carry-forward: the hold persists until the owner's evidenced
        # release, even after observed cessation is recorded
        self.assertEqual(self.snap()['resources']['rtx4090']['task'],
                         'training')
        self.call('resource_release', 'trainer', task='training', generation=1,
                  resource='rtx4090', evidence='drained after observed exit')
        out = self.call('handoff_restore', 'trainer', task='training',
                        generation=1,
                        reloads=[{'instance': 'qwen-local',
                                  'restoration_config': dict(CFG),
                                  'health_evidence': 'healthy'}],
                        resumes=['bionic'])
        self.assertEqual(out['phase'], 'AVAILABLE')
        self.assertEqual(out['gate'], 'OPEN')
        self.assertEqual(out['resumed_workers'], ['bionic'])
        self.assertIs(out['games_relaunched'], False)
        self.assertNotIn('rtx4090', self.snap()['resources'])
        state = self.call('handoff_state', 'SUP')
        self.assertEqual(state['queue'], [], 'terminal request leaves the queue')

    def test_machine_plane_visible_through_controller_snapshot_and_journal(self):
        rid, run = self.full_chain()
        plane = self.snap()['handoff']
        self.assertEqual(plane['requests'][rid]['phase'], 'AVAILABLE')
        ops = [j['op'] for j in plane['journal']]
        self.assertEqual(ops, ['handoff_request', 'handoff_admit',
                               'handoff_gate_close',
                               'handoff_checkpoint_preserved',
                               'handoff_model_unload', 'handoff_game_release',
                               'handoff_ready', 'handoff_launch',
                               'handoff_cessation', 'handoff_restore'])
        chain = [(j['from'], j['to']) for j in plane['journal']]
        self.assertEqual(chain, [(None, 'REQUESTED'),
                                 ('REQUESTED', 'DRAINING'),
                                 ('DRAINING', 'DRAINING'),
                                 ('DRAINING', 'DRAINING'),
                                 ('DRAINING', 'DRAINING'),
                                 ('DRAINING', 'DRAINING'),
                                 ('DRAINING', 'READY'),
                                 ('READY', 'TRAINING'),
                                 ('TRAINING', 'RESTORING'),
                                 ('RESTORING', 'AVAILABLE')])
        state = self.call('handoff_state', 'SUP')
        self.assertTrue(state['journal_tail'])


class H2IllegalTransitionTests(Harness, unittest.TestCase):
    """Every non-legal op from every phase is refused by its frozen name."""

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def seeded(self, phase):
        """Drive a fresh request to the requested phase; return rid."""
        self.task_pair()
        rid = self.request()['request']
        self.register_fixtures()
        if phase == 'REQUESTED':
            return rid
        self.call('handoff_admit', 'trainer', request=rid, task='training',
                  generation=1)
        if phase == 'DRAINING_OPEN_GATE':
            return rid
        self.call('handoff_gate_close', 'trainer', task='training')
        return rid

    def test_requested_phase_refusals(self):
        rid = self.seeded('REQUESTED')
        self.refused('handoff_ready', 'trainer', 'handoff_not_draining',
                     task='training', generation=1)
        self.refused('handoff_launch', 'trainer', 'handoff_not_ready',
                     task='training', generation=1, evidence='x')
        self.refused('handoff_cessation', 'trainer', 'handoff_not_training',
                     task='training', generation=1, observed=True,
                     evidence='x', preserved_receipts_evidence='y')
        self.refused('handoff_restore', 'trainer', 'handoff_not_restoring',
                     task='training', generation=1, reloads=[], resumes=[])
        self.refused('handoff_gate_close', 'trainer', 'handoff_not_draining',
                     task='training')
        self.refused('handoff_force_kill', 'trainer', 'force_kill_refused',
                     task='training', name='forest-demo')
        # a follower request already queued cannot be admitted out of order
        self.call('create_task', task='train-b', epoch=self.epoch(),
                  base=BASE, scopes=['docs/evidence/b'], packet='p')
        self.call('claim', actor='lead', task='train-b')
        self.call('resource_request', actor='lead', task='train-b',
                  generation=1, wants=[{'name': 'rtx4090'}], priority=9)
        rid_b = self.request('train-b', actor='lead')['request']
        self.refused('handoff_admit', 'lead', 'handoff_queue_jump_refused',
                     request=rid_b, task='train-b', generation=1)

    def test_draining_phase_refusals(self):
        self.seeded('DRAINING_OPEN_GATE')
        self.refused('handoff_admit', 'trainer', 'handoff_not_requested',
                     request=self.snap()['handoff']['queue'][0],
                     task='training', generation=1)
        self.refused('handoff_launch', 'trainer', 'handoff_not_ready',
                     task='training', generation=1, evidence='x')
        self.refused('handoff_cessation', 'trainer', 'handoff_not_training',
                     task='training', generation=1, observed=True,
                     evidence='x', preserved_receipts_evidence='y')
        self.refused('handoff_restore', 'trainer', 'handoff_not_restoring',
                     task='training', generation=1, reloads=[], resumes=[])
        self.call('handoff_gate_close', 'trainer', task='training')
        self.refused('handoff_reload_attempt', 'gamer',
                     'inference_admission_closed')
        self.refused('handoff_force_kill', 'trainer', 'force_kill_refused',
                     task='training', name='forest-demo')
        # ready is refused by each missing drain piece, by name, in order
        self.refused('handoff_ready', 'trainer', 'preservation_evidence_required',
                     task='training', generation=1)
        self.call('handoff_checkpoint_preserved', 'trainer', task='training',
                  evidence='preserved', workers=['bionic'])
        self.refused('handoff_ready', 'trainer', 'model_instances_still_loaded',
                     task='training', generation=1)
        self.call('handoff_model_unload', 'trainer', task='training',
                  instance='qwen-local', restoration_config=dict(CFG))
        self.refused('handoff_ready', 'trainer', 'game_not_released',
                     task='training', generation=1)
        self.call('handoff_game_release', 'trainer', task='training',
                  name='forest-demo', pid=GAME['pid'],
                  start_time=GAME['start_time'], evidence='save/quit',
                  observed_free_vram_mb=10)
        self.refused('handoff_ready', 'trainer', 'insufficient_vram_evidence',
                     task='training', generation=1,
                     observed_free_vram_mb=999)
        # a second release with a mismatched identity is refused
        self.refused('handoff_game_release', 'trainer', 'game_identity_mismatch',
                     task='training', name='forest-demo', pid=1,
                     start_time='x', evidence='e2', observed_free_vram_mb=10)

    def test_ready_and_training_phase_refusals(self):
        self.task_pair()
        rid = self.request()['request']
        self.register_fixtures()
        self.call('handoff_admit', 'trainer', request=rid, task='training',
                  generation=1)
        self.drain(rid)
        self.call('handoff_ready', 'trainer', task='training', generation=1)
        self.refused('handoff_ready', 'trainer', 'handoff_not_draining',
                     task='training', generation=1)
        self.refused('handoff_cessation', 'trainer', 'handoff_not_training',
                     task='training', generation=1, observed=True,
                     evidence='x', preserved_receipts_evidence='y')
        run = self.call('handoff_launch', 'trainer', task='training',
                        generation=1, evidence='authorized start, once')
        self.refused('handoff_launch', 'trainer', 'already_launched',
                     task='training', generation=1, evidence='replay')
        self.refused('handoff_restore', 'trainer', 'handoff_not_restoring',
                     task='training', generation=1, reloads=[], resumes=[])
        self.refused('handoff_gate_close', 'trainer', 'handoff_not_draining',
                     task='training')
        # release on timer/silence is refused; preservation before release
        self.refused('handoff_cessation', 'trainer',
                     'release_requires_observed_cessation', task='training',
                     generation=1, observed=False, evidence='hourly lease expired',
                     preserved_receipts_evidence='kept')
        self.refused('handoff_cessation', 'trainer',
                     'preservation_required_before_release', task='training',
                     generation=1, observed=True, evidence='exit observed',
                     preserved_receipts_evidence='')
        # a protected run cannot be preempted even by the follower
        self.call('create_task', task='train-b', epoch=self.epoch(),
                  base=BASE, scopes=['docs/evidence/b'], packet='p')
        self.call('claim', actor='lead', task='train-b')
        r = self.call('resource_request', actor='lead', task='train-b',
                      generation=1, wants=[{'name': 'rtx4090'}], priority=9)
        self.assertFalse(r['granted'])
        rid_b = self.request('train-b', actor='lead')['request']
        self.refused('handoff_admit', 'lead', 'handoff_queue_jump_refused',
                     request=rid_b, task='train-b', generation=1)

    def test_protected_run_active_survives_queue_surgery(self):
        rid, run = None, None
        self.task_pair()
        rid = self.request()['request']
        self.register_fixtures()
        self.call('handoff_admit', 'trainer', request=rid, task='training',
                  generation=1)
        self.drain(rid)
        self.call('handoff_ready', 'trainer', task='training', generation=1)
        self.call('handoff_launch', 'trainer', task='training', generation=1,
                  evidence='authorized start, once')
        self.call('create_task', task='train-b', epoch=self.epoch(),
                  base=BASE, scopes=['docs/evidence/b'], packet='p')
        self.call('claim', actor='lead', task='train-b')
        self.call('resource_request', actor='lead', task='train-b',
                  generation=1, wants=[{'name': 'rtx4090'}], priority=9)
        rid_b = self.request('train-b', actor='lead')['request']
        # surgery on the ISOLATED fixture registry: remove the protected
        # request from the queue so the queue-jump guard cannot shadow the
        # protected-run guard underneath it
        con = self.c.connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            s = json.loads(con.execute('SELECT body FROM state WHERE id=1')
                           .fetchone()[0])
            s['handoff']['queue'].remove(rid)
            con.execute('UPDATE state SET body=? WHERE id=1', (json.dumps(s),))
            con.execute('COMMIT')
        finally:
            con.close()
        self.refused('handoff_admit', 'lead', 'protected_run_active',
                     request=rid_b, task='train-b', generation=1)

    def test_restoring_and_available_phase_refusals(self):
        claimed = self.task_pair()
        rid = self.request()['request']
        self.register_fixtures()
        self.call('handoff_admit', 'trainer', request=rid, task='training',
                  generation=1)
        self.drain(rid)
        self.call('handoff_ready', 'trainer', task='training', generation=1)
        self.call('handoff_launch', 'trainer', task='training', generation=1,
                  evidence='authorized start, once')
        self.call('handoff_cessation', 'trainer', task='training',
                  generation=1, observed=True, evidence='exit observed',
                  preserved_receipts_evidence='kept')
        # the training hold must be released by owner evidence first
        self.refused('handoff_restore', 'trainer', 'training_hold_not_released',
                     task='training', generation=1,
                     reloads=[{'instance': 'qwen-local',
                               'restoration_config': dict(CFG),
                               'health_evidence': 'healthy'}],
                     resumes=['bionic'])
        self.call('resource_release', 'trainer', task='training', generation=1,
                  resource='rtx4090', evidence='drained; receipts kept')
        self.refused('handoff_restore', 'trainer', 'unknown_instance',
                     task='training', generation=1,
                     reloads=[{'instance': 'other',
                               'restoration_config': dict(CFG),
                               'health_evidence': 'h'}],
                     resumes=['bionic'])
        self.refused('handoff_restore', 'trainer', 'restoration_config_mismatch',
                     task='training', generation=1,
                     reloads=[{'instance': 'qwen-local',
                               'restoration_config': {'artifact': 'WRONG',
                                                      'context': 1},
                               'health_evidence': 'h'}],
                     resumes=['bionic'])
        self.refused('handoff_restore', 'trainer', 'restore_incomplete',
                     task='training', generation=1,
                     reloads=[{'instance': 'qwen-local',
                               'restoration_config': dict(CFG),
                               'health_evidence': 'healthy'}],
                     resumes=[])
        self.refused('handoff_restore', 'trainer', 'worker_already_resumed',
                     task='training', generation=1,
                     reloads=[{'instance': 'qwen-local',
                               'restoration_config': dict(CFG),
                               'health_evidence': 'healthy'}],
                     resumes=['bionic', 'bionic'])
        self.refused('handoff_cessation', 'trainer', 'handoff_not_training',
                     task='training', generation=1, observed=True,
                     evidence='x', preserved_receipts_evidence='y')
        out = self.call('handoff_restore', 'trainer', task='training',
                        generation=1,
                        reloads=[{'instance': 'qwen-local',
                                  'restoration_config': dict(CFG),
                                  'health_evidence': 'healthy'}],
                        resumes=['bionic'])
        self.assertEqual(out['phase'], 'AVAILABLE')
        # terminal: the completed request is no longer addressable
        self.refused('handoff_launch', 'trainer', 'unknown_handoff_request',
                     task='training', generation=1, evidence='x')
        self.refused('handoff_cessation', 'trainer', 'unknown_handoff_request',
                     task='training', generation=1, observed=True,
                     evidence='x', preserved_receipts_evidence='y')
        # a new cycle is a new request: with the GPU free again the gamer
        # re-acquires it, the trainer's fresh controller request queues
        # (contended), and the machine accepts the new handoff request
        self.call('resource_request', 'gamer', task='game', generation=1,
                  wants=[{'name': 'rtx4090'}])
        self.assertEqual(self.snap()['resources']['rtx4090']['task'], 'game')
        self.call('resource_request', 'trainer', task='training', generation=1,
                  wants=[{'name': 'rtx4090'}])
        rid2 = self.request()['request']
        self.assertNotEqual(rid2, rid)
        self.assertEqual(self.call('handoff_infer_wait', 'gamer')['status'],
                         'OPEN')

    def test_only_supervisor_registers_identities(self):
        self.task_pair()
        self.refused('handoff_register_model', 'trainer', 'supervisor_only',
                     instance='m', restoration_config=dict(CFG))
        self.refused('handoff_register_game', 'trainer', 'supervisor_only',
                     name='g', **GAME)
        self.refused('handoff_recover', 'trainer', 'supervisor_only',
                     request='missing')

    def test_model_unload_rules(self):
        self.seeded('DRAINING_OPEN_GATE')
        self.call('handoff_gate_close', 'trainer', task='training')
        self.refused('handoff_model_unload', 'trainer',
                     'model_unload_all_refused', task='training',
                     instance='--all', restoration_config=dict(CFG))
        self.refused('handoff_model_unload', 'trainer', 'unknown_instance',
                     task='training', instance='never-registered',
                     restoration_config=dict(CFG))
        self.refused('handoff_model_unload', 'trainer',
                     'restoration_config_required', task='training',
                     instance='qwen-local', restoration_config=None)
        self.call('handoff_model_unload', 'trainer', task='training',
                  instance='qwen-local', restoration_config=dict(CFG))
        self.refused('handoff_model_unload', 'trainer',
                     'instance_already_unloaded', task='training',
                     instance='qwen-local', restoration_config=dict(CFG))

    def test_game_release_rules_and_graceful_failure_holds(self):
        self.seeded('DRAINING_OPEN_GATE')
        self.call('handoff_gate_close', 'trainer', task='training')
        self.refused('handoff_game_release', 'trainer',
                     'unregistered_game_identity', task='training',
                     name='unknown-game', pid=1, start_time='t',
                     evidence='e', observed_free_vram_mb=10)
        self.refused('handoff_game_release', 'trainer',
                     'game_identity_mismatch', task='training',
                     name='forest-demo', pid=99, start_time=GAME['start_time'],
                     evidence='e', observed_free_vram_mb=10)
        self.refused('handoff_game_release', 'trainer',
                     'graceful_release_required', task='training',
                     name='forest-demo', pid=GAME['pid'],
                     start_time=GAME['start_time'], evidence='',
                     observed_free_vram_mb=10)
        self.refused('handoff_game_release', 'trainer',
                     'insufficient_vram_evidence', task='training',
                     name='forest-demo', pid=GAME['pid'],
                     start_time=GAME['start_time'], evidence='e')
        self.call('handoff_game_release', 'trainer', task='training',
                  name='forest-demo', pid=GAME['pid'],
                  start_time=GAME['start_time'], evidence='save/quit ok',
                  observed_free_vram_mb=2000)
        # force-kill does not exist in ANY phase, for ANY actor
        self.refused('handoff_force_kill', 'trainer', 'force_kill_refused',
                     task='training', name='forest-demo')
        self.refused('handoff_force_kill', 'SUP', 'force_kill_refused',
                     task='training', name='forest-demo')


class H3IdempotentReRequestTests(Harness, unittest.TestCase):

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def test_duplicate_request_is_the_same_record(self):
        self.task_pair()
        first = self.request()
        plane = self.snap()['handoff']
        journal_len = len(plane['journal'])
        self.assertEqual(len(plane['queue']), 1)
        second = self.request()
        self.assertEqual(second['request'], first['request'])
        self.assertTrue(second['idempotent_replay'])
        plane = self.snap()['handoff']
        self.assertEqual(len(plane['queue']), 1, 'no second queue entry')
        self.assertEqual(len(plane['journal']), journal_len,
                         'idempotent replay writes no journal entry')

    def test_re_request_during_drain_does_not_restart_the_drain(self):
        self.task_pair()
        rid = self.request()['request']
        self.register_fixtures()
        self.call('handoff_admit', 'trainer', request=rid, task='training',
                  generation=1)
        self.call('handoff_gate_close', 'trainer', task='training')
        self.call('handoff_checkpoint_preserved', 'trainer', task='training',
                  evidence='preserved', workers=['bionic'])
        before = self.snap()['handoff']['requests'][rid]
        replay = self.request()
        self.assertEqual(replay['request'], rid)
        self.assertEqual(replay['phase'], 'DRAINING')
        after = self.snap()['handoff']['requests'][rid]
        self.assertEqual(after['drain'], before['drain'])
        self.assertEqual(after['phase'], before['phase'])

    def test_arrival_order_not_priority_governs_admission(self):
        self.task_pair()
        first = self.request()['request']
        self.call('create_task', task='train-b', epoch=self.epoch(),
                  base=BASE, scopes=['docs/evidence/b'], packet='p')
        self.call('claim', actor='lead', task='train-b')
        self.call('resource_request', actor='lead', task='train-b',
                  generation=1, wants=[{'name': 'rtx4090'}], priority=9)
        second = self.request('train-b', actor='lead',
                              vram_required_mb=10)['request']
        self.assertLess(self.snap()['handoff']['queue'].index(first),
                        self.snap()['handoff']['queue'].index(second))
        # the priority-9 later request cannot jump the priority-1 earlier one
        self.refused('handoff_admit', 'lead', 'handoff_queue_jump_refused',
                     request=second, task='train-b', generation=1)
        self.assertEqual(self.call('handoff_admit', 'trainer', request=first,
                                   task='training',
                                   generation=1)['phase'], 'DRAINING')


class H4CrashRecoveryTests(Harness, unittest.TestCase):

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def to_ready_launched(self):
        self.task_pair()
        rid = self.request()['request']
        self.register_fixtures()
        self.call('handoff_admit', 'trainer', request=rid, task='training',
                  generation=1)
        self.drain(rid)
        self.call('handoff_ready', 'trainer', task='training', generation=1)
        run = self.call('handoff_launch', 'trainer', task='training',
                        generation=1, evidence='authorized start, once')
        return rid, run

    def restart(self):
        """Simulate a supervisor process restart: a NEW authority object over
        the SAME persisted registry."""
        self.c = HandoffControl(self.db, 'SUP', 'ENR', self.root / 'slots',
                                memory_budget_mb=8192)

    def test_restart_during_training_keeps_the_run_protected(self):
        rid, run = self.to_ready_launched()
        self.restart()
        rec = self.call('handoff_recover', 'SUP', request=rid)
        self.assertEqual(rec['phase'], 'TRAINING')
        self.assertEqual(rec['run_id'], run['run_id'])
        self.assertTrue(rec['grant_live'])
        # the protected run still cannot be preempted after the restart
        self.call('create_task', task='train-b', epoch=self.epoch(),
                  base=BASE, scopes=['docs/evidence/b'], packet='p')
        self.call('claim', actor='lead', task='train-b')
        self.call('resource_request', actor='lead', task='train-b',
                  generation=1, wants=[{'name': 'rtx4090'}], priority=9)
        rid_b = self.request('train-b', actor='lead')['request']
        self.refused('handoff_admit', 'lead', 'handoff_queue_jump_refused',
                     request=rid_b, task='train-b', generation=1)
        self.assertNotEqual(self.snap()['resources']['rtx4090']['task'],
                            'train-b')
        # a replayed launch across the restart is refused: launch exactly once
        self.refused('handoff_launch', 'trainer', 'already_launched',
                     task='training', generation=1, evidence='replay')

    def test_ready_with_foreign_holder_refuses_recovery(self):
        self.task_pair()
        rid = self.request()['request']
        self.register_fixtures()
        self.call('handoff_admit', 'trainer', request=rid, task='training',
                  generation=1)
        self.drain(rid)
        self.call('handoff_ready', 'trainer', task='training', generation=1)
        # surgery on the ISOLATED fixture registry: a foreign holder appears
        con = self.c.connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            s = json.loads(con.execute('SELECT body FROM state WHERE id=1')
                           .fetchone()[0])
            s['resources']['rtx4090'] = {
                'task': 'game', 'owner': 'gamer', 'generation': 1,
                'class': 'gpu_functionality', 'since_revision': s['revision'] + 1,
                'memory_mb': None}
            con.execute('UPDATE state SET body=? WHERE id=1', (json.dumps(s),))
            con.execute('COMMIT')
        finally:
            con.close()
        self.refused('handoff_recover', 'SUP', 'resources_still_held',
                     request=rid)
        self.refused('handoff_launch', 'trainer', 'gpu_not_held_by_training_task',
                     task='training', generation=1, evidence='x')

    def test_hold_then_recover_without_evidence_stays_held(self):
        rid, run = self.to_ready_launched()
        self.call('handoff_hold', 'SUP', task='training',
                  reason='uncertain transition', evidence='host crash')
        # the grant disappears (owner evidenced release) with NO cessation
        # evidence supplied to the machine: silence is not a release record
        self.call('resource_release', 'trainer', task='training',
                  generation=1, resource='rtx4090',
                  evidence='owner drained while hold recorded')
        self.restart()
        out = self.call('handoff_recover', 'SUP', request=rid)
        self.assertEqual(out['phase'], 'RECOVERY_HOLD')
        self.assertEqual(out['note'], 'recovery_evidence_insufficient')
        # never fabricates READY from a hold; a run id was recorded, so any
        # launch attempt is already_launched (launch exactly once, forever)
        self.refused('handoff_launch', 'trainer', 'already_launched',
                     task='training', generation=1, evidence='x')
        self.refused('handoff_recover', 'SUP', 'cannot_fabricate_ready',
                     request=rid, resume_to='READY')

    def test_recover_completes_interrupted_transition_with_observed_cessation(self):
        rid, run = self.to_ready_launched()
        self.call('handoff_hold', 'SUP', task='training',
                  reason='uncertain transition', evidence='host crash')
        # the owner's evidenced release happens while held (C3 law: release
        # still requires the owner + live generation + drained evidence)
        self.call('resource_release', 'trainer', task='training',
                  generation=1, resource='rtx4090',
                  evidence='drained after observed exit; receipts kept')
        out = self.call('handoff_recover', 'SUP', request=rid,
                        cessation_observed=True, evidence='exit observed',
                        preserved_receipts_evidence='receipts kept')
        self.assertEqual(out['phase'], 'RESTORING')

    def test_recover_from_live_training_resume(self):
        rid, run = self.to_ready_launched()
        self.call('handoff_hold', 'SUP', task='training',
                  reason='uncertain transition', evidence='host crash')
        out = self.call('handoff_recover', 'SUP', request=rid)
        self.assertEqual(out['phase'], 'TRAINING',
                         'the grant is still live: protection resumes')
        self.assertEqual(out['run_id'], run['run_id'])

    def test_corrupt_phase_stays_recovery_hold(self):
        rid, run = self.to_ready_launched()
        con = self.c.connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            s = json.loads(con.execute('SELECT body FROM state WHERE id=1')
                           .fetchone()[0])
            s['handoff']['requests'][rid]['phase'] = 'MANGLED'
            con.execute('UPDATE state SET body=? WHERE id=1', (json.dumps(s),))
            con.execute('COMMIT')
        finally:
            con.close()
        self.restart()
        out = self.call('handoff_recover', 'SUP', request=rid)
        self.assertEqual(out['phase'], 'RECOVERY_HOLD')
        self.assertEqual(out['note'], 'unknown_state_stays_recovery_hold')
        for op, kwargs in (
                ('handoff_restore', dict(task='training', generation=1,
                                         reloads=[], resumes=[])),
                ('handoff_cessation', dict(task='training', generation=1,
                                           observed=True, evidence='x',
                                           preserved_receipts_evidence='y'))):
            self.refused(op, 'trainer', 'unknown_state_stays_recovery_hold',
                         **kwargs)
        self.refused('handoff_recover', 'SUP', 'cannot_fabricate_ready',
                     request=rid, resume_to='READY')

    def test_hold_from_any_phase_is_recorded(self):
        self.task_pair()
        rid = self.request()['request']
        out = self.call('handoff_hold', 'trainer', task='training',
                        reason='failed gate', evidence='uncertain state')
        self.assertEqual(out['phase'], 'RECOVERY_HOLD')
        self.assertEqual(out['from_phase'], 'REQUESTED')
        plane = self.snap()['handoff']
        self.assertEqual(plane['requests'][rid]['phase'], 'RECOVERY_HOLD')
        self.assertIn(rid, plane['queue'], 'a held request stays serialized')


class H5SupervisorInvariantTests(Harness, unittest.TestCase):

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def launched(self):
        self.task_pair()
        rid = self.request()['request']
        self.register_fixtures()
        self.call('handoff_admit', 'trainer', request=rid, task='training',
                  generation=1)
        self.drain(rid)
        self.call('handoff_ready', 'trainer', task='training', generation=1)
        run = self.call('handoff_launch', 'trainer', task='training',
                        generation=1, evidence='authorized start, once')
        return rid, run

    def test_supervisor_clear_still_needs_actual_drain_evidence(self):
        self.launched()
        self.refused('resource_clear', 'trainer', 'supervisor_only',
                     resource='rtx4090', evidence='not the supervisor')
        self.refused('resource_clear', 'SUP',
                     'actual_process_drained_evidence', resource='rtx4090',
                     evidence='')
        self.assertEqual(self.snap()['resources']['rtx4090']['task'],
                         'training',
                         'a protected run is never force-cleared by name alone')

    def test_authorized_stop_records_hold_and_clear(self):
        rid, run = self.launched()
        self.call('handoff_hold', 'SUP', task='training',
                  reason='operator-authorized stop', evidence='explicit stop')
        self.assertEqual(self.snap()['handoff']['requests'][rid]['phase'],
                         'RECOVERY_HOLD')
        self.call('resource_clear', 'SUP', resource='rtx4090',
                  evidence='actual process + children drain observed')
        self.assertNotIn('rtx4090', self.snap()['resources'])

    def test_hold_is_owner_or_supervisor_only(self):
        self.task_pair()
        self.request()
        self.refused('handoff_hold', 'gamer', 'handoff_hold_not_authorized',
                     task='training', reason='x', evidence='y')
        self.assertEqual(self.call('handoff_hold', 'trainer', task='training',
                                   reason='r', evidence='e')['phase'],
                         'RECOVERY_HOLD')

    def test_non_supervisor_recover_and_registration_refused(self):
        rid, run = self.launched()
        self.refused('handoff_recover', 'trainer', 'supervisor_only',
                     request=rid)
        self.refused('handoff_register_model', 'trainer', 'supervisor_only',
                     instance='m2', restoration_config=dict(CFG))


class H6InferenceGateTests(Harness, unittest.TestCase):

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def draining_with_gate(self, deadline_revision=None):
        self.task_pair()
        rid = self.request()['request']
        self.call('handoff_admit', 'trainer', request=rid, task='training',
                  generation=1)
        self.call('handoff_gate_close', 'trainer', task='training',
                  deadline_revision=deadline_revision)

    def test_requests_wait_not_refused_and_never_fall_through(self):
        self.draining_with_gate()
        out = self.call('handoff_infer_wait', 'gamer')
        self.assertEqual(out['status'], 'RESOURCE_WAIT')
        out2 = self.call('handoff_infer_wait', 'lead', kind='judge')
        self.assertEqual(out2['status'], 'RESOURCE_WAIT')
        self.assertEqual(self.call('handoff_state', 'SUP')['waiters'], 2)

    def test_timeout_leaves_gate_closed_with_waiters(self):
        revision = self.snap()['revision']
        self.draining_with_gate(deadline_revision=revision + 2)
        self.call('handoff_infer_wait', 'gamer')
        self.call('handoff_infer_wait', 'gamer')
        out = self.call('handoff_gate_check', 'SUP')
        self.assertEqual(out['status'], 'GATE_TIMEOUT')
        self.assertEqual(out['gate'], 'CLOSED')
        self.assertEqual(out['note'], 'gate_timeout_gate_stays_closed')
        self.assertEqual(self.call('handoff_state', 'SUP')['waiters'], 2)
        self.assertEqual(self.call('handoff_gate_check', 'SUP')['gate'],
                         'CLOSED')

    def test_bypass_and_early_open_refused(self):
        self.draining_with_gate()
        self.refused('handoff_reload_attempt', 'gamer',
                     'inference_admission_closed')
        self.refused('handoff_gate_open', 'trainer',
                     'inference_gate_open_not_allowed', task='training')

    def test_gate_opens_only_on_the_restore_path(self):
        rid, run = None, None
        self.task_pair()
        rid = self.request()['request']
        self.register_fixtures()
        self.call('handoff_admit', 'trainer', request=rid, task='training',
                  generation=1)
        self.drain(rid)
        self.call('handoff_ready', 'trainer', task='training', generation=1)
        self.call('handoff_launch', 'trainer', task='training', generation=1,
                  evidence='authorized start, once')
        self.refused('handoff_gate_open', 'trainer',
                     'inference_gate_open_not_allowed', task='training')
        self.call('handoff_cessation', 'trainer', task='training',
                  generation=1, observed=True, evidence='exit observed',
                  preserved_receipts_evidence='kept')
        self.call('resource_release', 'trainer', task='training',
                  generation=1, resource='rtx4090',
                  evidence='drained; receipts kept')
        # during RESTORING the gate may be opened explicitly...
        self.assertEqual(self.call('handoff_gate_open', 'trainer',
                                   task='training')['gate'], 'OPEN')
        # ...and handoff_restore completes with the gate open on AVAILABLE
        out = self.call('handoff_restore', 'trainer', task='training',
                        generation=1,
                        reloads=[{'instance': 'qwen-local',
                                  'restoration_config': dict(CFG),
                                  'health_evidence': 'healthy'}],
                        resumes=['bionic'])
        self.assertEqual(out['phase'], 'AVAILABLE')
        self.assertEqual(self.call('handoff_infer_wait', 'gamer')['status'],
                         'OPEN')


if __name__ == '__main__':
    unittest.main(verbosity=2)
