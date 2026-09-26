from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent_slots import Registry, check_instruction_revision


def registration(i,adopt=True):
    return {'agent_id':f'agent-{i}','task_id':f'campaign-W{i}',
            'ownership_reference':'existing assigned task brief, fixture only','workspace':'fixture workspace',
            'checkpoint':'implementation','next_action':'implement assigned change','phase':'implement',
            'instruction_revision':'astra-0001','instruction_bundle_sha256':'a'*64,
            'adopt_existing':adopt}


class AgentSlotTests(unittest.TestCase):
    def test_live_registration_rejects_stale_policy_without_claiming_slot(self):
        self.r.reconcile({'expected_registered_agents':0,'live_inventory_reference':'fixture'})
        current={'revision_id':'astra-0010','bundle_sha256':'b'*64}
        with patch('agent_slots.DEFAULT_ROOT',Path(self.temp.name)), patch('instruction_state.inspect',return_value=current):
            with self.assertRaisesRegex(ValueError,'LEAD_UPDATE_REQUIRED'):
                self.r.register(registration(1,False))
            self.assertEqual(self.r.snapshot()['registered_agents'],0)
            a=registration(1,False)
            a.update(instruction_revision=current['revision_id'],instruction_bundle_sha256=current['bundle_sha256'])
            self.assertEqual(self.r.register(a)['agent_id'],'agent-1')
            self.assertEqual(self.r.instruction_notice()['revision_id'],'astra-0010')

    def test_live_stale_existing_worker_can_still_finish_and_release(self):
        slot=self.r.register(registration(1))
        with patch('agent_slots.DEFAULT_ROOT',Path(self.temp.name)), patch('instruction_state.inspect',return_value={'revision_id':'astra-0010','bundle_sha256':'b'*64}):
            a={**registration(1),'slot':slot['slot'],'generation':slot['generation'],'phase':'finished','last_action':'completed'}
            self.r.report(a)
            self.r.release({**a,'worker_finished_confirmed':True,'preservation_reference':'durable fixture report'})
            self.assertEqual(self.r.snapshot()['registered_agents'],0)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.r=Registry(self.temp.name);self.r.initialize()

    def test_bootstrap_does_not_invent_active_agents(self):
        state=self.r.snapshot()
        self.assertEqual(state['registered_agents'],0)
        self.assertEqual(len(state['slots']),10)
        self.assertEqual(state['mode'],'AWAITING_RECONCILIATION')
        with self.assertRaisesRegex(ValueError,'reconcile_existing'):
            self.r.register(registration(1,False))

    def test_concurrent_registration_unique_slots_and_capacity(self):
        with ThreadPoolExecutor(max_workers=10) as pool:
            slots=list(pool.map(lambda i:Registry(self.temp.name).register(registration(i)),range(10)))
        self.assertEqual(len({s['slot'] for s in slots}),10)
        with self.assertRaisesRegex(ValueError,'all_ten'):self.r.register(registration(11))
        disk=json.loads((Path(self.temp.name)/'STATUS.json').read_text())
        self.assertEqual(disk['registered_agents'],10)

    def test_reconciliation_reports_release_and_stale_generation(self):
        a=self.r.register(registration(1))
        with self.assertRaisesRegex(ValueError,'count_mismatch'):
            self.r.reconcile({'expected_registered_agents':7,'live_inventory_reference':'fixture'})
        self.r.reconcile({'expected_registered_agents':1,'live_inventory_reference':'fixture'})
        report={**a,'phase':'visual','last_action':'capture queued','next_action':'await reserved GPU'}
        self.r.report(report)
        with self.assertRaisesRegex(ValueError,'completion_confirmation'):
            self.r.release({**a,'worker_finished_confirmed':True,'preservation_reference':'fixture'})
        self.r.report({**report,'phase':'finished'})
        self.r.release({**a,'worker_finished_confirmed':True,'preservation_reference':'fixture preserved'})
        b=self.r.register(registration(2,False))
        self.assertEqual(b['slot'],a['slot']);self.assertGreater(b['generation'],a['generation'])
        with self.assertRaisesRegex(ValueError,'stale_or_wrong'):
            self.r.report(report)

    def test_duplicate_agent_and_safe_reinitialization(self):
        self.r.register(registration(1))
        with self.assertRaisesRegex(ValueError,'already_registered'):self.r.register(registration(1))
        self.assertEqual(self.r.initialize()['registered_agents'],1)

    def test_coordinator_report_has_next_action(self):
        data={'coordinator_id':'coordinator','checkpoint':'review','last_action':'read receipt',
              'next_action':'review then refill','evidence_reference':'fixture'}
        out=self.r.coordinator(data)
        self.assertEqual(out['coordinator_report']['next_action'],'review then refill')

    def test_top_of_hour_deadline_not_rolling_and_report_does_not_renew(self):
        clock=[2*3600+40*60] # 02:40 -> 03:00 deadline, not 03:40.
        registry=Registry(self.temp.name,clock=lambda:clock[0])
        a=registry.register({**registration(1),'memory':{'resume':'finish scoped patch'}})
        self.assertEqual(a['deadline_unix'],3*3600)
        clock[0]=3*3600-1
        registry.report({**a,'last_action':'checkpoint preserved','next_action':'verify'})
        self.assertEqual(registry.snapshot()['slots'][0]['deadline_unix'],3*3600)
        clock[0]=3*3600
        out=registry.snapshot()
        self.assertEqual(out['slots'][0]['lease_state'],'EXPIRED_RECOVERY_REQUIRED')
        self.assertEqual(out['registered_agents'],1)
        with self.assertRaisesRegex(ValueError,'assignment_expired'):
            registry.report({**a,'last_action':'late','next_action':'keep writing'})
        with self.assertRaisesRegex(ValueError,'completion_confirmation'):
            registry.release({**a,'preservation_reference':'saved'})
        out=registry.release({**a,'worker_finished_confirmed':True,'preservation_reference':'saved checkpoint'})
        self.assertEqual(out['slots'][0]['last_handoff']['memory']['resume'],'finish scoped patch')
        b=registry.register(registration(2))
        self.assertEqual(b['deadline_unix'],4*3600)
        self.assertGreater(b['generation'],a['generation'])

    def test_existing_agents_are_not_extended_by_idempotent_init(self):
        clock=[3599]
        registry=Registry(self.temp.name,clock=lambda:clock[0])
        registry.register(registration(1))
        clock[0]=3600
        out=registry.initialize()
        self.assertEqual(out['slots'][0]['deadline_unix'],3600)
        self.assertEqual(out['slots'][0]['lease_state'],'EXPIRED_RECOVERY_REQUIRED')


if __name__=='__main__':unittest.main(verbosity=2)
