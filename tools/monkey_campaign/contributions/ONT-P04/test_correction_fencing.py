"""ONT-P04 correction regressions: evidence fencing + restore-config law.

Written failing-first (2026-09-26) against the operational lead's reproduced
falsifier (queue-check-20260926, PR #158 CHANGES_REQUIRED): a foreign enrolled
gamer identity could mutate the training task's drain evidence
(checkpoint_preserved, model_unload) and unload accepted a restoration config
DIFFERENT from the registered one. Frozen in the correction prereg addendum
BEFORE the post-fix probe runs; first-run (failing) outputs preserved under
first_run_failures/.

Regression groups (frozen):
  F1 foreign-mutation refusal: a non-owner enrolled identity (and any stale
     foreign claim) is refused by name on every state/evidence mutation of a
     live handoff request; supervisor authority stays legal.
  F2 stale-generation refusal: mutations pinned to a non-live generation -
     explicitly, or via a request whose generation is no longer the task's
     live claim - are refused by the pinned controller's claim law.
  F3 restore-config law: unload only accepts the REGISTERED restoration
     configuration; a different/unregistered one is refused by name and the
     registered configuration is retained exactly.

Records profile: CPU-only, isolated temporary registries, no GPU, no live
process. Identical fixture style to test_gpu_handoff.py.
"""
import sys
import tempfile
import unittest
from pathlib import Path

WS = Path(__file__).resolve().parent
PINNED = WS / 'pinned' / 'tools' / 'agent_fleet'
sys.path.insert(0, str(PINNED))
sys.path.insert(0, str(WS))

from control import Refusal                     # noqa: E402
from gpu_handoff import HandoffControl          # noqa: E402

BASE = 'f' * 40
CFG = {'artifact': 'qwen-local', 'context': 119296, 'offload': 'cpu',
       'workers': ['bionic']}
GAME = dict(executable='C:/games/forest-demo.exe', pid=4242,
            start_time='2026-09-26T10:00:00Z')


class Harness:
    """Isolated HandoffControl registry; three enrolled agents."""

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
                        evidence='ONT-P04 fencing fixture')
        self.c.call('offer_lead', self.tok['lead'], epoch=0,
                    checkpoint='ONT-P04 fencing; no foreign work')
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

    def draining(self, close_gate=True):
        """A live DRAINING training request owned by trainer; returns rid."""
        ep = self.epoch()
        self.call('create_task', task='game', epoch=ep, base=BASE,
                  scopes=['docs/evidence/game'], packet='p')
        self.call('create_task', task='training', epoch=self.epoch(),
                  base=BASE, scopes=['docs/evidence/training'], packet='p')
        self.call('claim', actor='gamer', task='game')
        self.call('claim', actor='trainer', task='training')
        self.call('resource_request', actor='gamer', task='game',
                  generation=1, wants=[{'name': 'rtx4090'}])
        self.call('resource_request', actor='trainer', task='training',
                  generation=1, wants=[{'name': 'rtx4090'}])
        rid = self.call('handoff_request', 'trainer', task='training',
                        generation=1, evidence='training brief',
                        derivation_gate_receipt='gate-receipt-1',
                        vram_required_mb=1000,
                        expected_duration_minutes=30)['request']
        self.call('handoff_register_model', 'SUP', instance='qwen-local',
                  restoration_config=dict(CFG))
        self.call('handoff_register_game', 'SUP', name='forest-demo', **GAME)
        self.call('handoff_admit', 'trainer', request=rid, task='training',
                  generation=1)
        if close_gate:
            self.call('handoff_gate_close', 'trainer', task='training')
        return rid

    def drain_record(self, rid):
        return self.snap()['handoff']['requests'][rid]['drain']


class F1ForeignMutationRefusalTests(Harness, unittest.TestCase):
    """The lead's falsifier, as frozen regressions: a foreign enrolled gamer
    identity must be refused BY NAME on every state/evidence mutation, and
    the drain record must stay untouched."""

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def test_foreign_gamer_cannot_mutate_drain_evidence(self):
        rid = self.draining()
        self.refused('handoff_checkpoint_preserved', 'gamer',
                     'handoff_mutation_not_authorized', task='training',
                     evidence='foreign assertion', workers=['bionic'])
        self.refused('handoff_model_unload', 'gamer',
                     'handoff_mutation_not_authorized', task='training',
                     instance='qwen-local', restoration_config=dict(CFG))
        self.refused('handoff_game_release', 'gamer',
                     'handoff_mutation_not_authorized', task='training',
                     name='forest-demo', pid=GAME['pid'],
                     start_time=GAME['start_time'],
                     evidence='foreign save/quit',
                     observed_free_vram_mb=2000)
        self.refused('handoff_gate_close', 'gamer',
                     'handoff_mutation_not_authorized', task='training')
        # nothing the foreign identity attempted landed in the drain record
        self.assertEqual(self.drain_record(rid), {})
        # the owner's legal flow is preserved after the refused attempts
        self.call('handoff_checkpoint_preserved', 'trainer', task='training',
                  evidence='preserved', workers=['bionic'])
        self.assertEqual(self.drain_record(rid)['checkpoint_preserved'],
                         'preserved')

    def test_lead_falsifier_foreign_unload_wrong_config_refused(self):
        rid = self.draining()
        # the exact falsifier call: foreign actor AND unregistered config
        self.refused('handoff_model_unload', 'gamer',
                     'handoff_mutation_not_authorized', task='training',
                     instance='qwen-local',
                     restoration_config={'artifact': 'DIFFERENT',
                                         'context': 1})
        self.assertEqual(self.drain_record(rid), {},
                         'the foreign mutation must not land')
        self.assertEqual(self.drain_record(rid).get('unloaded'), None)

    def test_lead_falsifier_foreign_checkpoint_refused(self):
        rid = self.draining()
        self.refused('handoff_checkpoint_preserved', 'gamer',
                     'handoff_mutation_not_authorized', task='training',
                     evidence='foreign assertion', workers=['bionic'])
        self.assertEqual(self.drain_record(rid), {})
        self.assertEqual(self.drain_record(rid).get('checkpoint_preserved'),
                         None)

    def test_stale_foreign_claim_via_wrong_owner_is_refused(self):
        rid = self.draining()
        # the enrolled lead identity is not the request owner either
        self.refused('handoff_checkpoint_preserved', 'lead',
                     'handoff_mutation_not_authorized', task='training',
                     evidence='lead is foreign here', workers=['bionic'])
        self.assertEqual(self.drain_record(rid), {})

    def test_supervisor_authority_stays_legal(self):
        rid = self.draining()
        out = self.call('handoff_checkpoint_preserved', 'SUP',
                        task='training', evidence='supervisor-delegated '
                        'preservation record', workers=['bionic'])
        self.assertEqual(out['preserved'], True)
        self.assertEqual(self.drain_record(rid)['checkpoint_preserved'],
                         'supervisor-delegated preservation record')


class F2StaleGenerationRefusalTests(Harness, unittest.TestCase):
    """Mutations pinned to a non-live generation are refused by the pinned
    controller's claim law (stale_or_foreign_claim)."""

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def test_owner_with_stale_generation_pin_refused(self):
        self.draining()
        # live claim is generation 1; a pinned generation 9 is stale
        self.refused('handoff_checkpoint_preserved', 'trainer',
                     'stale_or_foreign_claim', task='training',
                     generation=9, evidence='stale pin', workers=['bionic'])
        self.refused('handoff_model_unload', 'trainer',
                     'stale_or_foreign_claim', task='training',
                     generation=9, instance='qwen-local',
                     restoration_config=dict(CFG))

    def test_request_generation_stale_after_claim_advance_refused(self):
        rid = self.draining()
        # supervisor advances the live claim: abandon (gen 2) + re-claim
        # (gen 3), same owner; the request still carries generation 1
        self.call('claim_abandon', 'SUP', task='training',
                  preservation_evidence='state preserved',
                  drain_evidence='processes drained')
        self.call('claim', actor='trainer', task='training')
        live = self.snap()['tasks']['training']['generation']
        self.assertEqual(live, 3)
        # the owner's own token can no longer mutate through the stale
        # request: its generation is no longer the live claim generation
        self.refused('handoff_checkpoint_preserved', 'trainer',
                     'stale_or_foreign_claim', task='training',
                     evidence='stale request', workers=['bionic'])
        self.refused('handoff_checkpoint_preserved', 'trainer',
                     'stale_or_foreign_claim', task='training',
                     generation=1, evidence='explicit stale generation',
                     workers=['bionic'])
        self.refused('handoff_model_unload', 'trainer',
                     'stale_or_foreign_claim', task='training',
                     instance='qwen-local', restoration_config=dict(CFG))
        self.assertEqual(self.drain_record(rid), {},
                         'no evidence lands through a stale request')
        # a fresh resource request at the LIVE generation, then the honest
        # re-request path (the abandon dropped the stale queue entry)
        self.call('resource_request', actor='trainer', task='training',
                  generation=3, wants=[{'name': 'rtx4090'}])
        rid2 = self.call('handoff_request', 'trainer', task='training',
                         generation=3, evidence='training brief regen',
                         derivation_gate_receipt='gate-receipt-3',
                         vram_required_mb=1000,
                         expected_duration_minutes=30)['request']
        self.assertNotEqual(rid2, rid)
        self.assertEqual(self.snap()['handoff']['requests'][rid2]['phase'],
                         'REQUESTED')


class F3RestoreConfigRegistrationTests(Harness, unittest.TestCase):
    """Unload requires the REGISTERED restoration configuration; a different
    or unregistered one is refused by name; the registered configuration is
    retained exactly."""

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def test_unload_with_different_artifact_refused(self):
        rid = self.draining()
        self.refused('handoff_model_unload', 'trainer',
                     'restoration_config_mismatch', task='training',
                     instance='qwen-local',
                     restoration_config={'artifact': 'DIFFERENT',
                                         'context': 1})
        self.assertEqual(self.drain_record(rid).get('unloaded'), None,
                         'a refused config must never land in the record')

    def test_unload_with_mutated_context_or_offload_refused(self):
        rid = self.draining()
        self.refused('handoff_model_unload', 'trainer',
                     'restoration_config_mismatch', task='training',
                     instance='qwen-local',
                     restoration_config=dict(CFG, context=1))
        self.refused('handoff_model_unload', 'trainer',
                     'restoration_config_mismatch', task='training',
                     instance='qwen-local',
                     restoration_config=dict(CFG, offload='gpu'))
        self.assertIsNone(self.drain_record(rid).get('unloaded'),
                          'a refused config must never land in the record')

    def test_unregistered_instance_and_config_still_refused(self):
        self.draining()
        self.refused('handoff_model_unload', 'trainer', 'unknown_instance',
                     task='training', instance='never-registered',
                     restoration_config=dict(CFG))
        self.refused('handoff_model_unload', 'trainer',
                     'restoration_config_required', task='training',
                     instance='qwen-local', restoration_config=None)

    def test_registered_config_retained_exactly_through_restore(self):
        rid = self.draining()
        self.call('handoff_checkpoint_preserved', 'trainer', task='training',
                  evidence='preserved', workers=['bionic'])
        out = self.call('handoff_model_unload', 'trainer', task='training',
                        instance='qwen-local',
                        restoration_config=dict(CFG))
        self.assertEqual(out['restoration_config'], CFG,
                         'exactly the registered configuration is retained')
        self.assertEqual(self.drain_record(rid)['unloaded']['qwen-local'],
                         CFG)
        self.call('handoff_game_release', 'trainer', task='training',
                  name='forest-demo', pid=GAME['pid'],
                  start_time=GAME['start_time'], evidence='save/quit',
                  observed_free_vram_mb=2000)
        self.call('resource_release', 'gamer', task='game', generation=1,
                  resource='rtx4090', evidence='graceful exit drained')
        self.call('handoff_ready', 'trainer', task='training', generation=1)
        self.call('handoff_launch', 'trainer', task='training',
                  generation=1, evidence='authorized start, once')
        self.call('handoff_cessation', 'trainer', task='training',
                  generation=1, observed=True, evidence='exit observed',
                  preserved_receipts_evidence='kept')
        self.call('resource_release', 'trainer', task='training',
                  generation=1, resource='rtx4090',
                  evidence='training drained; preserved')
        # the restore law compares against the RETAINED registered config
        self.refused('handoff_restore', 'trainer',
                     'restoration_config_mismatch', task='training',
                     generation=1,
                     reloads=[{'instance': 'qwen-local',
                               'restoration_config': dict(CFG, context=1),
                               'health_evidence': 'healthy'}],
                     resumes=['bionic'])
        res = self.call('handoff_restore', 'trainer', task='training',
                        generation=1,
                        reloads=[{'instance': 'qwen-local',
                                  'restoration_config': dict(CFG),
                                  'health_evidence': 'healthy'}],
                        resumes=['bionic'])
        self.assertEqual(res['phase'], 'AVAILABLE')


if __name__ == '__main__':
    unittest.main(verbosity=2)
