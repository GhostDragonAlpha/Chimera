import concurrent.futures
import json
from pathlib import Path
import tempfile
import threading
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from control import Control, Refusal
from service import Server
from client import call as http_call
from inventory import inspect, plan

BASE='a'*40
HEAD='b'*40
MERGED='c'*40

class ControlTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.c=Control(self.root/'state.sqlite','super-secret','enroll-secret',self.root/'slots')
        self.tokens={}
        for aid in ('lead','standby','worker','other'):
            self.tokens[aid]=self.c.call('enroll','enroll-secret',agent=aid,label=aid)['result']['session_token']
            self.c.call('qualify','super-secret',agent=aid,capabilities=['cpu','gpu'],max_tasks=5,
                can_lead=aid in ('lead','standby'),rank=10 if aid=='lead' else 1,evidence='fixture qualification record')
        self.c.call('offer_lead',self.tokens['lead'],epoch=0,checkpoint='ready; no foreign work')
        self.c.call('elect','super-secret')
    def tearDown(self):self.tmp.cleanup()
    def call(self,op,actor='lead',**p):return self.c.call(op,self.tokens.get(actor,actor),**p)['result']
    def snap(self):return self.call('snapshot')
    def task(self,tid,**kw):
        p=dict(task=tid,epoch=self.snap()['epoch'],base=BASE,scopes=['tools/labs/'+tid],packet='statement / prediction / falsifier',kind='worker')
        p.update(kw);return self.call('create_task',**p)
    def claim(self,tid,actor='worker'):return self.call('claim',actor,task=tid)
    def standby(self):self.call('offer_lead','standby',epoch=self.snap()['epoch'],checkpoint='recovered current state; ready to lead')
    def faillead(self):return self.call('fail','super-secret',agent='lead',reason='PROCESS_EXIT',evidence='trusted runner exited handle record')
    def feedback(self,**kw):
        args={'source':'HUMAN','categories':['APPEARANCE'],'text':'The centre is not visible.',
              'evidence':'operator input reference','tasks':[]};args.update(kw)
        return self.call('feedback_add','super-secret',**args)
    def test_human_feedback_cannot_be_forged_by_worker(self):
        with self.assertRaisesRegex(Refusal,'trusted_human_adapter_required'):
            self.call('feedback_add','worker',source='HUMAN',categories=['INTENT'],text='invented',evidence='fake')
    def test_feedback_retains_original_and_appends_dispositions(self):
        f=self.feedback();original={k:v for k,v in f.items() if k!='dispositions'}
        for status in ['INVESTIGATE','ADDRESSED']:
            self.call('feedback_disposition',epoch=self.snap()['epoch'],feedback=f['id'],status=status,reason='measured cause',evidence='retained comparison')
        after=self.snap()['feedback'][f['id']]
        self.assertEqual(original,{k:v for k,v in after.items() if k!='dispositions'})
        self.assertEqual([x['status'] for x in after['dispositions']],['INVESTIGATE','ADDRESSED'])
    def test_feedback_does_not_accept_task(self):
        self.task('one');f=self.feedback(tasks=['one'])
        self.call('feedback_disposition',epoch=self.snap()['epoch'],feedback=f['id'],status='ADDRESSED',reason='example',evidence='review reference')
        self.assertEqual(self.snap()['tasks']['one']['state'],'READY')
    def test_feedback_unknown_category_and_task_refused(self):
        for args in [{'categories':['MAGIC']},{'tasks':['absent']}]:
            with self.assertRaises(Refusal):self.feedback(**args)
    def test_stop_feedback_preserves_authority_requirement(self):
        f=self.feedback(categories=['STOP'],text='Stop this engine.')
        self.assertTrue(f['authority_action_required'])
        self.assertEqual(f['acceptance'],'NOT_CLAIMED')
    def test_old_lead_cannot_disposition_feedback(self):
        f=self.feedback();epoch=self.snap()['epoch'];self.standby();self.faillead()
        with self.assertRaises(Refusal):
            self.call('feedback_disposition',epoch=epoch,feedback=f['id'],status='ADDRESSED',reason='stale',evidence='stale')

    def test_five_slots_and_sixth_refusal(self):
        self.task('integrate',kind='integration');self.claim('integrate','lead')
        for i in range(4):self.task('w'+str(i));self.claim('w'+str(i))
        self.task('sixth')
        with self.assertRaisesRegex(Refusal,'no_free_slot'):self.claim('sixth','other')
        self.assertEqual(sum(x['task'] is not None for x in self.snap()['slots'].values()),5)
    def test_same_agent_multiple_tasks_distinct_slots(self):
        self.task('one');self.task('two');a=self.claim('one');b=self.claim('two')
        self.assertNotEqual(a['worktree'],b['worktree'])
        self.assertEqual(a['owner'],b['owner'])
    def test_claim_capacity(self):
        self.call('qualify','super-secret',agent='worker',capabilities=['cpu'],max_tasks=1,evidence='capacity one')
        self.task('one');self.task('two');self.claim('one')
        with self.assertRaisesRegex(Refusal,'capacity'):self.claim('two')
    def test_concurrent_claim_one_winner(self):
        self.task('race')
        def take(a):
            try:self.claim('race',a);return True
            except Refusal:return False
        with concurrent.futures.ThreadPoolExecutor(2) as pool:r=list(pool.map(take,['worker','other']))
        self.assertEqual(sum(r),1)
    def test_scope_conflict_casefold(self):
        self.task('one',scopes=['tools/Foo']);self.task('two',scopes=['tools/foo/sub.py']);self.claim('one')
        with self.assertRaisesRegex(Refusal,'write_scope_conflict'):self.claim('two','other')
    def test_foreign_and_stale_claim_refused_without_revision(self):
        self.task('one');t=self.claim('one');before=self.snap()['revision']
        for actor,gen in [('other',t['generation']),('worker',0)]:
            with self.assertRaises(Refusal):self.call('checkpoint',actor,task='one',generation=gen,checkpoint='bad')
        self.assertEqual(before,self.snap()['revision'])
    def test_silence_suspicion_does_not_elect(self):
        before=self.snap()
        for _ in range(4):self.call('suspect','worker',agent='lead',reason='no recent progress; investigate')
        after=self.snap();self.assertEqual(before['leader'],after['leader']);self.assertEqual(before['epoch'],after['epoch'])
    def test_confirmed_failure_elects_qualified_standby(self):
        self.standby();old=self.snap()['epoch'];r=self.faillead()
        self.assertEqual(r['leader'],'standby');self.assertEqual(r['epoch'],old+1)
        with self.assertRaisesRegex(Refusal,'session_revoked'):self.call('create_task',epoch=old,task='late')
    def test_no_ready_successor_leaves_vacancy(self):
        self.faillead()
        self.assertIsNone(self.call('snapshot','worker')['leader'])
    def test_agent_cannot_accuse_to_take_over(self):
        with self.assertRaisesRegex(Refusal,'trusted_failure'):self.call('fail','worker',agent='lead',reason='PROCESS_EXIT',evidence='I think so')
    def test_unqualified_agent_cannot_offer_or_claim(self):
        token=self.c.call('enroll','enroll-secret',agent='new',label='unqualified')['result']['session_token']
        for op,p in [('offer_lead',{'epoch':1,'checkpoint':'hello'}),('claim',{'task':'x'})]:
            with self.assertRaises(Refusal):self.c.call(op,token,**p)
    def test_failure_holds_task_and_resources(self):
        self.task('one');t=self.claim('one')
        self.call('resource_acquire','worker',task='one',generation=t['generation'],resource='rtx4090')
        self.call('fail','super-secret',agent='worker',reason='PROVIDER_TERMINAL_ERROR',evidence='runner provider refusal')
        s=self.snap();self.assertEqual(s['tasks']['one']['state'],'RECOVERY_HOLD');self.assertIn('rtx4090',s['resources'])
        with self.assertRaisesRegex(Refusal,'resources_still_held'):self.call('recover','super-secret',task='one',evidence='not enough')
    def test_recovery_requires_attestation_and_new_generation(self):
        self.task('one');t=self.claim('one');self.call('fail','super-secret',agent='worker',reason='PROCESS_EXIT',evidence='exited')
        with self.assertRaises(Refusal):self.call('recover','other',task='one',evidence='mine now')
        self.call('recover','super-secret',task='one',evidence='preserved hash, clean directory, stopped writer')
        n=self.claim('one','other');self.assertGreater(n['generation'],t['generation'])
    def test_gpu_exclusive_even_same_agent_two_tasks(self):
        self.task('one');self.task('two');a=self.claim('one');b=self.claim('two')
        self.call('resource_acquire','worker',task='one',generation=a['generation'],resource='rtx4090')
        with self.assertRaisesRegex(Refusal,'resource_not_available'):self.call('resource_acquire','worker',task='two',generation=b['generation'],resource='rtx4090')
    def test_dyad_reserves_gpu_and_release_order(self):
        self.task('one');t=self.claim('one');args=dict(task='one',generation=t['generation'])
        with self.assertRaises(Refusal):self.call('resource_acquire','worker',resource='dyad_eye',**args)
        self.call('resource_acquire','worker',resource='rtx4090',**args);self.call('resource_acquire','worker',resource='dyad_eye',**args)
        with self.assertRaises(Refusal):self.call('resource_release','worker',resource='rtx4090',evidence='drained',**args)
    def review(self):
        self.task('one');t=self.claim('one')
        self.call('submit_review','worker',task='one',generation=t['generation'],branch=t['branch'],head=HEAD,evidence='tests and independent review links')
        return t
    def request(self,t):return self.call('integration_request',task=t['id'],head=HEAD,branch=t['branch'],expected_base=BASE,epoch=self.snap()['epoch'],review='source and evidence review')
    def test_review_not_acceptance_or_free_slot(self):
        t=self.review();s=self.snap();self.assertEqual(s['tasks']['one']['state'],'REVIEW');self.assertEqual(s['slots'][t['slot']]['task'],'one')
    def test_integration_request_stale_after_failover(self):
        t=self.review();r=self.request(t);self.standby();self.faillead()
        with self.assertRaisesRegex(Refusal,'stale_integration_epoch'):
            self.call('ack_integration','super-secret',request=r['request'],base_branch='astra/gait-capture',expected_base=BASE,commit=MERGED,evidence='must not pass')
    def test_integration_ack_and_explicit_slot_release(self):
        t=self.review();r=self.request(t)
        self.call('ack_integration','super-secret',request=r['request'],base_branch='astra/gait-capture',expected_base=BASE,commit=MERGED,evidence='trusted publisher GitHub verification')
        self.assertIsNotNone(self.snap()['tasks']['one']['slot'])
        self.call('release_slot','super-secret',task='one',evidence='preserved files; no dirty files; no processes')
        self.assertIsNone(self.snap()['slots'][t['slot']]['task'])
    def test_master_base_refused(self):
        t=self.review();r=self.request(t)
        with self.assertRaisesRegex(Refusal,'wrong_integration_base'):
            self.call('ack_integration','super-secret',request=r['request'],base_branch='master',expected_base=BASE,commit=MERGED,evidence='bad')
    def test_task_branch_wrong_refused(self):
        self.task('one');t=self.claim('one')
        with self.assertRaisesRegex(Refusal,'wrong_task_branch'):
            self.call('submit_review','worker',task='one',generation=t['generation'],branch='astra/gait-capture',head=HEAD,evidence='bad')
    def test_dependency_waits_for_integration(self):
        self.task('one');self.task('two',dependencies=['one']);self.claim('one')
        with self.assertRaisesRegex(Refusal,'dependencies_not_integrated'):self.claim('two','other')
    def test_protected_and_traversal_scope(self):
        for s in ['ChimeraEngine/engine/build','ChimeraEngine/engine','../other','E:/outside','.git/config']:
            with self.assertRaises(Refusal):self.task('bad',scopes=[s])
    def test_master_list_claim_lead_only(self):
        self.task('ledger',scopes=['docs/THE_MASTER_LIST.md'])
        with self.assertRaisesRegex(Refusal,'master_list_lead_only'):self.claim('ledger')
    def test_restart_retains_identity_and_claims(self):
        self.task('one');self.claim('one');before=self.snap()
        c=Control(self.root/'state.sqlite','super-secret','enroll-secret',self.root/'slots')
        self.assertEqual(before,c.call('snapshot',self.tokens['lead'])['result'])
        with self.assertRaisesRegex(Refusal,'service_identity_mismatch'):Control(self.root/'state.sqlite','different','enroll-secret',self.root/'slots')
    def test_snapshot_and_events_do_not_expose_tokens(self):
        body=json.dumps(self.snap())+json.dumps(self.call('events',since=0))
        for token in self.tokens.values():self.assertNotIn(token,body)
        self.assertNotIn('token_hash',body)
    def test_wrong_epoch_current_lead_refused(self):
        with self.assertRaisesRegex(Refusal,'stale_or_nonleader'):self.task('bad',epoch=0)
    def test_explicit_yield_uses_same_recovery_rules(self):
        self.standby();r=self.call('yield',checkpoint='work and files preserved')
        self.assertEqual(r['leader'],'standby')
    def test_real_http_roundtrip_and_refusal(self):
        server=Server(('127.0.0.1',0),self.c);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            session={'endpoint':f'http://127.0.0.1:{server.server_port}/v1/action','token':self.tokens['worker']}
            self.assertEqual(http_call(session,'snapshot',{})['result']['leader'],'lead')
            with self.assertRaises(ValueError):http_call(session,'create_task',{'task':'forbidden'})
        finally:server.shutdown();server.server_close();thread.join()
    def test_each_slot_has_its_own_engine_plan(self):
        slots=self.snap()['slots']
        roots=[];ports=[]
        for slot in slots.values():
            engine=slot['engine'];ports.append(engine['port_candidate'])
            self.assertFalse(engine['provisioned']);self.assertFalse(engine['port_reserved'])
            for key in ('build_root','runtime_root','evidence_root'):
                p=Path(engine[key]);self.assertTrue(p.is_relative_to(Path(slot['path'])))
                self.assertNotIn('ChimeraEngine/engine/build',p.as_posix())
                roots.append(str(p))
        self.assertEqual(len(set(roots)),15);self.assertEqual(len(set(ports)),5)
        self.task('engine-check');claim=self.claim('engine-check')
        self.assertEqual(claim['engine'],slots[claim['slot']]['engine'])
        inventory=plan(self.root/'slots',BASE)
        self.assertEqual(inventory['slots'][int(claim['slot'])-1]['engine'],claim['engine'])

    def test_inventory_is_read_only_and_bounded(self):
        root=self.root/'scan';root.mkdir();f=root/'a';f.write_bytes(b'abc')
        r=inspect(root);self.assertEqual(r['logical_bytes'],3);self.assertTrue(r['complete']);self.assertEqual(f.read_bytes(),b'abc')
        self.assertFalse(inspect(root,max_entries=1)['complete'])
        self.assertFalse(inspect(self.root/'missing')['complete'])
        self.assertEqual(len(plan(self.root,BASE)['slots']),5)

if __name__=='__main__':unittest.main(verbosity=2)
