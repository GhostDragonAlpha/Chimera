import copy
import os
from pathlib import Path
import tempfile
import unittest

import campaign as c


def fixture(n=3,slots=10):
    tasks=[{'id':f'W{i:02d}','title':f'Work {i}','scope':'core','depends_on':[],
            'done_when':'Receipt-backed implementation'} for i in range(1,n+1)]
    ctl={f't{i}':{'state':'READY','kind':'worker','scopes':[f'owned/{i}'],
                 'dependencies':[],'generation':1} for i in range(1,n+1)}
    envelope={'captured_at_unix':1000,'snapshot':{'tasks':ctl,'slots':{
        str(i):{'task':None,'kind':'worker'} for i in range(slots)}}}
    bindings={'schema':'chimera-monkey-controller-bindings-v1','bindings':{
        f'W{i:02d}':{'controller_tasks':[f't{i}'],'mapping_receipt':'review.md',
                     'additional_peak_bytes':c.GIB} for i in range(1,n+1)}}
    return {'tasks':tasks},envelope,bindings


def run_plan(parts, **kwargs):
    defaults=dict(harness_limit=10,active_subagents=0,free_bytes=500*c.GIB,now=1000)
    defaults.update(kwargs)
    return c.plan(*parts,**defaults)


class CampaignPolicyTests(unittest.TestCase):
    def test_unique_missing_and_cyclic_dependencies(self):
        a,_,_=fixture()
        for change in ('duplicate','missing','cycle'):
            b=copy.deepcopy(a)
            if change=='duplicate':b['tasks'].append(copy.deepcopy(b['tasks'][0]))
            elif change=='missing':b['tasks'][0]['depends_on']=['W99']
            else:
                b['tasks'][0]['depends_on']=['W02'];b['tasks'][1]['depends_on']=['W01']
            with self.subTest(change=change),self.assertRaises(c.Refusal):c.validate_catalog(b)

    def test_limit_respects_harness_active_and_controller(self):
        parts=fixture(15,4)
        out=run_plan(parts,harness_limit=10,active_subagents=7)
        self.assertEqual(len(out['new_dispatch_recommendations']),3)
        self.assertEqual(len(run_plan(parts,harness_limit=20)['new_dispatch_recommendations']),4)
        self.assertFalse(out['goal_complete'])

    def test_campaign_ceiling(self):
        self.assertEqual(len(run_plan(fixture(15,15),harness_limit=30)['new_dispatch_recommendations']),10)

    def test_stale_and_future_snapshot_refused(self):
        for now in (1121,994):
            with self.subTest(now=now),self.assertRaises(c.Refusal):run_plan(fixture(),now=now)

    def test_dependency_needs_integrated_receipt(self):
        parts=fixture(2);parts[0]['tasks'][1]['depends_on']=['W01']
        t=parts[1]['snapshot']['tasks']['t1'];t['state']='INTEGRATED'
        self.assertEqual(run_plan(parts)['new_dispatch_recommendations'],[])
        t['integration']={'commit':'a'*40,'evidence':'real integration receipt'}
        self.assertEqual(run_plan(parts)['new_dispatch_recommendations'][0]['planning_task'],'W02')

    def test_complete_requires_every_selected_task(self):
        parts=fixture()
        for t in parts[1]['snapshot']['tasks'].values():
            t.update(state='INTEGRATED',integration={'commit':'b'*40,'evidence':'receipt'})
        self.assertTrue(run_plan(parts)['goal_complete'])
        parts[1]['snapshot']['tasks']['t3'].pop('integration')
        self.assertFalse(run_plan(parts)['goal_complete'])

    def test_unbound_is_reconcile_not_duplicate(self):
        parts=fixture();parts[2]['bindings'].pop('W01')
        out=run_plan(parts)
        self.assertIn('W01',out['unreconciled'])
        self.assertEqual(len(out['new_dispatch_recommendations']),2)

    def test_blocked_does_not_block_independent_work(self):
        parts=fixture();t=parts[1]['snapshot']['tasks']['t1'];t['state']='BLOCKED'
        parts[2]['active_growth_forecasts']={'t1':{'generation':1,'remaining_bytes':0,'evidence':'parked receipt'}}
        self.assertEqual(len(run_plan(parts)['new_dispatch_recommendations']),2)

    def test_active_unknown_forecasts_refuse_new_admission(self):
        parts=fixture();parts[1]['snapshot']['tasks']['t1']['state']='RUNNING'
        self.assertEqual(run_plan(parts)['new_dispatch_recommendations'],[])

    def test_aggregate_disk_forecast_and_reserve(self):
        out=run_plan(fixture(3),free_bytes=102*c.GIB)
        self.assertEqual(len(out['new_dispatch_recommendations']),2)
        self.assertEqual(out['disk']['new_batch_forecast_bytes'],2*c.GIB)
        self.assertEqual(run_plan(fixture(),free_bytes=99*c.GIB)['new_dispatch_recommendations'],[])

    def test_active_reservations_are_subtracted(self):
        parts=fixture();parts[1]['snapshot']['tasks']['t1']['state']='RUNNING'
        parts[2]['active_growth_forecasts']={'t1':{'generation':1,'remaining_bytes':2*c.GIB,'evidence':'forecast'}}
        self.assertEqual(run_plan(parts,free_bytes=102*c.GIB)['new_dispatch_recommendations'],[])

    def test_missing_forecast_not_assumed_zero(self):
        parts=fixture();parts[2]['bindings']['W01'].pop('additional_peak_bytes')
        self.assertEqual(run_plan(parts)['waiting']['W01']['reason'],'DISK_FORECAST_REQUIRED')

    def test_scope_conflicts_in_same_batch(self):
        parts=fixture();parts[1]['snapshot']['tasks']['t2']['scopes']=['OWNED/1/child.py']
        self.assertEqual(len(run_plan(parts)['new_dispatch_recommendations']),2)

    def test_live_scope_conflict(self):
        parts=fixture();t=parts[1]['snapshot']['tasks']['t1'];t['state']='RUNNING'
        parts[1]['snapshot']['tasks']['t2']['scopes']=['owned/1/test.py']
        parts[2]['active_growth_forecasts']={'t1':{'generation':1,'remaining_bytes':0,'evidence':'forecast'}}
        self.assertEqual(len(run_plan(parts)['new_dispatch_recommendations']),1)

    def test_unknown_state_and_bindings_refused(self):
        parts=fixture();parts[1]['snapshot']['tasks']['t1']['state']='DONE'
        with self.assertRaises(c.Refusal):run_plan(parts)
        parts=fixture();parts[2]['bindings']['X99']=parts[2]['bindings']['W01']
        with self.assertRaises(c.Refusal):run_plan(parts)

    def test_selected_scope_keeps_decisions_and_excludes_conditional(self):
        parts=fixture();parts[0]['tasks'][2]['scope']='conditional'
        self.assertEqual(run_plan(parts)['selected_tasks'],2)
        self.assertEqual(run_plan(parts,conditional=True)['selected_tasks'],3)

    def test_storage_is_bounded_and_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'keep.txt').write_text('preserve')
            (root/'sub').mkdir();(root/'sub'/'more.txt').write_text('more')
            out=c.scan_storage(root)
            self.assertTrue(out['complete']);self.assertEqual(out['logical_bytes'],12)
            self.assertFalse(c.scan_storage(root,1)['complete'])
            self.assertEqual((root/'keep.txt').read_text(),'preserve')
            self.assertFalse(c.scan_storage(root/'absent')['complete'])

    def test_symlink_not_followed_when_host_allows_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);target=root/'target';target.mkdir();(target/'secret').write_text('x')
            try:os.symlink(target,root/'link',target_is_directory=True)
            except OSError:self.skipTest('Host does not permit creating symlinks')
            out=c.scan_storage(root/'link')
            self.assertEqual(out['logical_bytes'],0);self.assertFalse(out['complete'])
            self.assertEqual(out['links_skipped'],1)

    def test_plan_does_not_mutate_inputs(self):
        parts=fixture();before=copy.deepcopy(parts);run_plan(parts)
        self.assertEqual(parts,before)


if __name__=='__main__':unittest.main(verbosity=2)
