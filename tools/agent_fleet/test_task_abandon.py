"""fleet-task-abandon-01: task_abandon + claim_abandon controller contract.

Isolated tests over a temp registry root (the test_control.py harness
pattern): every test builds its own Control store, enrolls/qualifies fixture
agents, elects a lead, and drives the real controller state machine. No live
service, no deployed store, no filesystem mutation by the ops under test.
Covers both positive paths, all named refusals (the two claim_abandon slot
arms that are unreachable by design are documented and their invariant
pinned instead of driven -- see
test_claim_abandon_slot_refusals_pinned_unreachable_by_design), reopen
invariants, audit events, no session revocation, and the untouched
yield -> recover path.
"""
import json
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from control import Control, Refusal
from master_catalogue import build_records, payload_digest

BASE='a'*40
HEAD='b'*40
MERGED='c'*40
PRESERVED='worktree preserved at recorded head; no dirty source files'
DRAINED='no live writer process; no runtime; resources released'

class TaskAbandonTests(unittest.TestCase):
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
    def abandon(self,tid,**kw):
        p=dict(task=tid,reason='stale READY record superseded by the amended plan',
               evidence='master amendment disposition, third wave 2026-09-11')
        p.update(kw);return self.call('task_abandon','super-secret',**p)
    def claim_abandon(self,tid,_actor='super-secret',**kw):
        p=dict(task=tid,preservation_evidence=PRESERVED,drain_evidence=DRAINED)
        p.update(kw);return self.call('claim_abandon',_actor,**p)
    def events(self,since=0):return self.call('events',since=since)['events']

    # ---- task_abandon: positive path -------------------------------------
    def test_task_abandon_retires_ready_task_with_audit_record(self):
        self.task('stale-one')
        r=self.abandon('stale-one')
        self.assertEqual(r['state'],'ABANDONED');self.assertFalse(r['filesystem_touched'])
        s=self.snap();t=s['tasks']['stale-one']
        self.assertEqual(t['state'],'ABANDONED')
        self.assertEqual(t['abandon']['reason'],'stale READY record superseded by the amended plan')
        self.assertIn('master amendment disposition',t['abandon']['evidence'])
        self.assertEqual(t['abandon']['actor'],'SUPERVISOR')
        # READY invariants preserved: never held a slot; generation untouched.
        self.assertIsNone(t['slot']);self.assertIsNone(t['owner']);self.assertEqual(t['generation'],0)
        ev=[e for e in self.events(since=0) if e['kind']=='task_abandon']
        self.assertEqual(len(ev),1)
        self.assertEqual(ev[0]['task'],'stale-one')
        self.assertEqual(ev[0]['reason'],t['abandon']['reason'])
        self.assertEqual(ev[0]['actor'],'SUPERVISOR')
    def test_task_abandon_never_touches_the_filesystem(self):
        # The op is registry-state only: the entire temp store tree is
        # byte-for-byte unchanged by the op (no file created, written or
        # removed anywhere under the root).
        self.task('paper-one')
        before=sorted((str(p),p.stat().st_size) for p in self.root.rglob('*'))
        r=self.abandon('paper-one')
        self.assertFalse(r['filesystem_touched'])
        after=sorted((str(p),p.stat().st_size) for p in self.root.rglob('*'))
        self.assertEqual(before,after)

    # ---- task_abandon: refusals ------------------------------------------
    def test_task_abandon_refuses_non_supervisor_actors(self):
        self.task('stale-two')
        for actor in ('worker','other','lead'):
            with self.assertRaisesRegex(Refusal,'supervisor_only'):
                self.call('task_abandon',actor,task='stale-two',reason='r',evidence='e')
        s=self.snap();self.assertEqual(s['tasks']['stale-two']['state'],'READY')
    def test_task_abandon_refuses_unknown_task(self):
        with self.assertRaisesRegex(Refusal,'unknown_task'):self.abandon('no-such-task')
    def test_task_abandon_refuses_inactive_states(self):
        # RUNNING
        self.task('live');t=self.claim('live')
        with self.assertRaisesRegex(Refusal,'task_not_ready'):self.abandon('live')
        # BLOCKED
        self.call('checkpoint','worker',task='live',generation=t['generation'],state='BLOCKED',checkpoint='blocked on dependency')
        with self.assertRaisesRegex(Refusal,'task_not_ready'):self.abandon('live')
        # RECOVERY_HOLD
        self.call('fail','super-secret',agent='worker',reason='PROCESS_EXIT',evidence='trusted runner exited handle record')
        with self.assertRaisesRegex(Refusal,'task_not_ready'):self.abandon('live')
        self.call('recover','super-secret',task='live',evidence='preserved hash, clean directory, stopped writer')
        # READY again -> abandon -> ABANDONED (also sets up the next refusals)
        self.abandon('live')
        # ABANDONED: a terminal state; double abandon refused.
        with self.assertRaisesRegex(Refusal,'task_not_ready'):self.abandon('live')
        # REVIEW
        self.task('reviewed');rt=self.claim('reviewed','other')
        self.call('submit_review','other',task='reviewed',generation=rt['generation'],branch=rt['branch'],head=HEAD,evidence='tests and independent review links')
        with self.assertRaisesRegex(Refusal,'task_not_ready'):self.abandon('reviewed')
        # INTEGRATED (terminal acceptance)
        r=self.call('integration_request',task='reviewed',head=HEAD,branch=rt['branch'],expected_base=BASE,epoch=self.snap()['epoch'],review='independent source and evidence review')
        self.call('ack_integration','super-secret',request=r['request'],base_branch='astra/gait-capture',expected_base=BASE,commit=MERGED,evidence='trusted publisher GitHub verification')
        with self.assertRaisesRegex(Refusal,'task_not_ready'):self.abandon('reviewed')
    def test_task_abandon_requires_reason_and_evidence(self):
        self.task('stale-three')
        # Named refusals (PR #62 review F3, landed by followups-batch-02):
        # text() validates reason FIRST and evidence SECOND, so each blank
        # case names its exact missing_* arm instead of a bare Refusal.
        for p,name in (({'evidence':'e'},'missing_abandon_reason'),
                       ({'reason':'','evidence':'e'},'missing_abandon_reason'),
                       ({'reason':'  ','evidence':'e'},'missing_abandon_reason'),
                       ({'reason':'r'},'missing_abandon_evidence'),
                       ({'reason':'r','evidence':''},'missing_abandon_evidence'),
                       ({'reason':'r','evidence':'  '},'missing_abandon_evidence')):
            with self.assertRaisesRegex(Refusal,name):
                self.call('task_abandon','super-secret',task='stale-three',**p)
        self.assertEqual(self.snap()['tasks']['stale-three']['state'],'READY')

    # ---- ABANDONED coherence across every state switch --------------------
    def test_abandoned_id_is_permanent_scope_freed_and_dependency_blocking(self):
        self.task('gone',scopes=['tools/shared'])
        self.abandon('gone')
        # The id is retired permanently: re-creating it is refused, so the
        # audit history of the retired record can never be rewritten.
        with self.assertRaisesRegex(Refusal,'invalid_or_duplicate_task'):
            self.task('gone')
        # Retired = not active: an overlapping-scope task claims freely.
        # (Scope strings stay extension-free: the doc-lint pointer pass
        # treats <root-dir>/.../*.ext tokens in staged files as file refs.)
        self.task('fresh',scopes=['tools/shared/sub'])
        self.claim('fresh','other')
        # Not claimable, and satisfies NO dependency.
        with self.assertRaisesRegex(Refusal,'task_not_ready'):self.claim('gone')
        self.task('dependent',dependencies=['gone'])
        with self.assertRaisesRegex(Refusal,'dependencies_not_integrated'):self.claim('dependent','other')
        self.assertEqual(self.snap()['tasks']['dependent']['state'],'READY')
    def test_abandoned_task_not_counted_as_owner_capacity_or_active(self):
        # An abandoned READY task never counted toward capacity (owner None);
        # pin that the active-state enumerations exclude ABANDONED by
        # abandoning and then claiming other tasks with the same agent.
        self.task('cap-one');self.abandon('cap-one')
        self.task('cap-two');self.claim('cap-two')
        self.assertEqual(self.snap()['tasks']['cap-two']['state'],'RUNNING')
    def test_abandoned_card_is_reproposable_in_catalogue_next(self):
        card={'id':'STALE-CARD','domain':'fixture','title':'Fixture card',
              'status':'PROPOSED','depends_on':[]}
        payload=build_records(catalog_text=json.dumps({'tasks':[card]}),master_text='')
        digest=payload_digest(payload)
        self.call('catalogue_import',epoch=self.snap()['epoch'],payload=payload,digest=digest,evidence='fixture import')
        self.task('stale-card')
        nxt=self.call('catalogue_next',digest=digest)
        self.assertIn('stale-card',nxt['live_tasks'])
        self.assertNotIn('STALE-CARD',nxt['candidates'])
        self.abandon('stale-card')
        nxt=self.call('catalogue_next',digest=digest)
        self.assertNotIn('stale-card',nxt['live_tasks'])
        self.assertIn('STALE-CARD',nxt['candidates'])

    # ---- claim_abandon: positive path -------------------------------------
    def test_claim_abandon_returns_ready_at_new_generation_without_revoking_session(self):
        self.task('stuck');cl=self.claim('stuck')
        r=self.claim_abandon('stuck')
        self.assertEqual(r['state'],'READY');self.assertEqual(r['generation'],cl['generation']+1)
        self.assertEqual(r['slot_freed'],cl['slot'])
        self.assertFalse(r['owner_session_revoked']);self.assertFalse(r['filesystem_touched'])
        s=self.snap();t=s['tasks']['stuck']
        self.assertEqual(t['state'],'READY');self.assertIsNone(t['owner']);self.assertIsNone(t['slot'])
        self.assertIsNone(t['owner_instance'])
        self.assertIn('preservation: '+PRESERVED,t['checkpoint'])
        self.assertIn('drain: '+DRAINED,t['checkpoint'])
        # The owner session is intact and keeps its remaining capacity.
        self.assertTrue(s['agents']['worker']['alive'])
        # The slot was freed and never carried an ACTIVE provision, so no
        # preserved-provision record was fabricated for it.
        self.assertFalse(s['slots'][cl['slot']]['engine'].get('provisioned'))
        self.assertEqual(s['slots'][cl['slot']]['task'],None)
        self.assertEqual(s['slots'][cl['slot']]['engine'].get('preserved_provisions',[]),[])
        # Reopen: any qualified agent can re-claim; generation advances again.
        recl=self.claim('stuck','other')
        self.assertEqual(recl['generation'],cl['generation']+2)
        ev=[e for e in self.events(since=0) if e['kind']=='claim_abandon']
        self.assertEqual(len(ev),1);self.assertEqual(ev[0]['task'],'stuck');self.assertEqual(ev[0]['actor'],'SUPERVISOR')
    def test_yield_recover_path_still_works_alongside_claim_abandon(self):
        # The legacy path stays available and unchanged: yield ends the
        # session (by design) and holds the task for supervisor recovery.
        self.task('legacy');t=self.claim('legacy')
        self.call('yield','worker',checkpoint='work and files preserved')
        s=self.snap()
        self.assertEqual(s['tasks']['legacy']['state'],'RECOVERY_HOLD')
        self.assertFalse(s['agents']['worker']['alive'])
        self.call('recover','super-secret',task='legacy',evidence='preserved hash, clean directory, stopped writer')
        self.assertEqual(self.snap()['tasks']['legacy']['state'],'READY')
        # claim_abandon, by contrast, never ends a session (pinned above).

    # ---- claim_abandon: refusals ------------------------------------------
    def test_claim_abandon_refuses_non_supervisor_and_wrong_states(self):
        self.task('one');t=self.claim('one')
        for actor in ('worker','other','lead'):
            with self.assertRaisesRegex(Refusal,'supervisor_only'):self.claim_abandon('one',_actor=actor)
        with self.assertRaisesRegex(Refusal,'unknown_task'):self.claim_abandon('absent')
        # READY task: not running, and holds no slot at all.
        self.task('two')
        with self.assertRaisesRegex(Refusal,'task_not_running'):self.claim_abandon('two')
        # REVIEW task.
        self.call('submit_review','worker',task='one',generation=t['generation'],branch=t['branch'],head=HEAD,evidence='review links')
        with self.assertRaisesRegex(Refusal,'task_not_running'):self.claim_abandon('one')
        # RECOVERY_HOLD.
        self.call('fail','super-secret',agent='worker',reason='PROCESS_EXIT',evidence='exited handle record')
        with self.assertRaisesRegex(Refusal,'task_not_running'):self.claim_abandon('one')
        # A refused op never mutates state.
        self.assertEqual(self.snap()['tasks']['one']['state'],'RECOVERY_HOLD')
    def test_claim_abandon_refuses_active_provision_naming_slot_rebind(self):
        self.task('prov');t=self.claim('prov')
        self.call('provision_slot','super-secret',task='prov',worktree_head=HEAD,evidence='lead provisioned worktree at head')
        with self.assertRaisesRegex(Refusal,'provision_active_use_slot_rebind'):self.claim_abandon('prov')
        s=self.snap()
        self.assertEqual(s['tasks']['prov']['state'],'RUNNING')
        self.assertTrue(s['slots'][t['slot']]['engine']['provisioned'])
        self.assertEqual(s['slots'][t['slot']]['task'],'prov')
    def test_claim_abandon_slot_refusals_pinned_unreachable_by_design(self):
        # PR #62 review F2/F3 (landed by followups-batch-02): the
        # `task_has_no_slot` and `slot_binding_mismatch` refusal arms have NO
        # executable refusal test because they are UNREACHABLE BY DESIGN, and
        # faking a state to reach them would mean corrupting the registry by
        # hand -- exactly what the arms exist to catch. Why they cannot fire
        # through any legal op sequence: a task enters RUNNING only through
        # claim, which binds a free slot and writes slot['task']=task_id in
        # the SAME single-writer transaction; every slot-freeing op
        # (claim_abandon, recover, slot_rebind, release_review_slot) clears
        # both sides together. So a RUNNING task can never have slot=None
        # (task_has_no_slot) and slots[task.slot].task can never name another
        # task (slot_binding_mismatch). The arms stay in control.py as
        # defense-in-depth; the honest coverage is pinning the INVARIANT that
        # makes them unreachable, asserted here through the public snapshot:
        self.task('bound');self.claim('bound')
        s=self.snap()
        self.assertIsNotNone(s['tasks']['bound']['slot'])
        self.assertEqual(s['slots'][s['tasks']['bound']['slot']]['task'],'bound')
        # ...and it still holds for the SECOND claimer on the same slot
        # family after the first claim is abandoned back to READY:
        self.claim_abandon('bound');self.claim('bound','other')
        s=self.snap()
        self.assertIsNotNone(s['tasks']['bound']['slot'])
        self.assertEqual(s['slots'][s['tasks']['bound']['slot']]['task'],'bound')
    def test_claim_abandon_refuses_while_resources_still_held(self):
        # recover's exact guard, mirrored: a claim that ITSELF holds a
        # resource cannot be retired until the holder drains it.
        self.task('gpu-one');a=self.claim('gpu-one')
        self.call('resource_acquire','worker',task='gpu-one',generation=a['generation'],resource='rtx4090')
        with self.assertRaisesRegex(Refusal,'resources_still_held'):
            self.claim_abandon('gpu-one',preservation_evidence=PRESERVED,drain_evidence=DRAINED)
        self.assertEqual(self.snap()['tasks']['gpu-one']['state'],'RUNNING')
        self.call('resource_release','worker',task='gpu-one',generation=a['generation'],resource='rtx4090',evidence='drained')
        self.claim_abandon('gpu-one')
        self.assertEqual(self.snap()['tasks']['gpu-one']['state'],'READY')
    def test_claim_abandon_requires_both_attestations(self):
        self.task('attest');self.claim('attest')
        # Named refusals (PR #62 review F3, landed by followups-batch-02):
        # preservation is validated FIRST, drain SECOND, so each blank case
        # names its exact missing_* arm instead of a bare Refusal.
        for p,name in (({'drain_evidence':DRAINED},'missing_preservation_evidence'),
                       ({'preservation_evidence':'','drain_evidence':DRAINED},'missing_preservation_evidence'),
                       ({'preservation_evidence':'  ','drain_evidence':DRAINED},'missing_preservation_evidence'),
                       ({'preservation_evidence':PRESERVED},'missing_drain_evidence'),
                       ({'preservation_evidence':PRESERVED,'drain_evidence':''},'missing_drain_evidence')):
            with self.assertRaisesRegex(Refusal,name):
                self.call('claim_abandon','super-secret',task='attest',**p)
        s=self.snap()
        self.assertEqual(s['tasks']['attest']['state'],'RUNNING');self.assertIsNotNone(s['tasks']['attest']['slot'])
    def test_claim_abandon_drops_queued_resource_requests(self):
        self.task('holder');self.task('waiter',scopes=['tools/waiting-lab'])
        a=self.claim('holder');b=self.claim('waiter','other')
        self.call('resource_acquire','worker',task='holder',generation=a['generation'],resource='rtx4090')
        self.call('resource_request','other',task='waiter',generation=b['generation'],
                  wants=[{'name':'rtx4090'}],priority=5)
        q=self.snap()['resource_queues']
        self.assertEqual(len([x for x in q if not x['served']]),1)
        self.claim_abandon('waiter')
        q=self.snap()['resource_queues']
        dropped=[x for x in q if x['task']=='waiter']
        self.assertEqual(len(dropped),1)
        self.assertTrue(dropped[0]['served']);self.assertEqual(dropped[0]['dropped_reason'],'claim_abandoned')
        self.assertFalse(dropped[0].get('granted'))
        # The holder's claim is untouched by the other task's retirement.
        self.assertEqual(self.snap()['tasks']['holder']['state'],'RUNNING')

    # ---- reopen invariants and audit --------------------------------------
    def test_stale_generation_refused_after_claim_abandon(self):
        self.task('reopen');t=self.claim('reopen')
        self.claim_abandon('reopen')
        with self.assertRaisesRegex(Refusal,'stale_or_foreign_claim'):
            self.call('checkpoint','worker',task='reopen',generation=t['generation'],checkpoint='zombie write')
        with self.assertRaisesRegex(Refusal,'stale_or_foreign_claim'):
            self.call('submit_review','worker',task='reopen',generation=t['generation'],branch=t['branch'],head=HEAD,evidence='zombie review')
    def test_refusals_leave_revision_and_audit_untouched(self):
        self.task('quiet')
        before=self.snap()['revision'];events_before=self.events(since=0)
        with self.assertRaises(Refusal):self.abandon('quiet',reason='',evidence='e')
        with self.assertRaisesRegex(Refusal,'supervisor_only'):
            self.call('task_abandon','worker',task='quiet',reason='r',evidence='e')
        with self.assertRaisesRegex(Refusal,'unknown_task'):self.claim_abandon('absent')
        self.assertEqual(before,self.snap()['revision'])
        self.assertEqual(events_before,self.events(since=0))
    def test_audit_trail_append_only_and_token_free(self):
        self.task('aud');t=self.claim('aud')
        self.claim_abandon('aud')
        self.claim('aud','other')  # RUNNING again at a new generation
        with self.assertRaisesRegex(Refusal,'task_not_ready'):
            self.abandon('aud')    # refused: RUNNING -> no event, no rewrite
        self.task('legacy');self.claim('legacy')
        self.call('yield','worker',checkpoint='work and files preserved')
        self.call('recover','super-secret',task='legacy',evidence='preserved; writer stopped')
        all_events=self.events(since=0)
        seqs=[e['sequence'] for e in all_events]
        self.assertEqual(seqs,sorted(seqs));self.assertEqual(len(seqs),len(set(seqs)))
        kinds=[e['kind'] for e in all_events]
        self.assertIn('claim_abandon',kinds);self.assertIn('recover',kinds)
        self.assertEqual(kinds.count('task_abandon'),0)  # the RUNNING abandon was refused
        body=json.dumps(self.snap())+json.dumps(all_events)
        for token in self.tokens.values():self.assertNotIn(token,body)
        self.assertNotIn('token_hash',body)

if __name__=='__main__':unittest.main(verbosity=2)
