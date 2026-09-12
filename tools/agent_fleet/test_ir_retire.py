"""fleet-followups-batch-04: ir_retire controller contract.

Isolated tests over a temp registry root (the test_task_abandon.py harness
pattern): every test builds its own Control store, enrolls/qualifies fixture
agents, elects a lead, drives a task to REVIEW, and files a real
integration_request before exercising ir_retire. No live service, no deployed
store, no filesystem mutation by the ops under test. Covers the positive
retirement path with its audit record, every named refusal (supervisor_only,
unknown_integration_request, request_not_pending firing for BOTH ACKNOWLEDGED
and already-RETIRED requests, and the missing_retire_reason /
missing_retire_evidence text arms), the ack-path invariants in both
directions (a retired request can never be acknowledged; an untouched pending
request still acknowledges), refusal atomicity, and the event whitelist
(request + reason enter the audit event, evidence never does).
"""
import json
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from control import Control, Refusal

BASE='a'*40
HEAD='b'*40
MERGED='c'*40
REVIEW='independent source and evidence review'
REASON='orphaned PENDING request: PR merged through another path; broker never deployed'


class IrRetireTests(unittest.TestCase):
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
    def request(self,tid,claimer='other'):
        """Drive a task to REVIEW and file a pending integration request."""
        t=self.task(tid);cl=self.claim(tid,claimer)
        self.call('submit_review',claimer,task=tid,generation=cl['generation'],
                  branch=cl['branch'],head=HEAD,evidence='tests and review links')
        r=self.call('integration_request',task=tid,head=HEAD,branch=cl['branch'],
                    expected_base=BASE,epoch=self.snap()['epoch'],review=REVIEW)
        return r['request'],cl
    def claim(self,tid,actor='worker'):return self.call('claim',actor,task=tid)
    def retire(self,rid,**kw):
        p=dict(request=rid,reason=REASON,
               evidence='snapshot shows the request PENDING_EXTERNAL_BROKER while its PR is merged')
        p.update(kw);return self.call('ir_retire','super-secret',**p)
    def ack(self,rid):
        return self.call('ack_integration','super-secret',request=rid,
                         base_branch='astra/gait-capture',expected_base=BASE,
                         commit=MERGED,evidence='trusted publisher GitHub verification')
    def events(self,since=0):return self.call('events',since=since)['events']

    # ---- ir_retire: positive path -----------------------------------------
    def test_ir_retire_retires_pending_request_with_audit_record(self):
        rid,_=self.request('gone-pr')
        r=self.retire(rid)
        self.assertEqual(r['state'],'RETIRED_ORPHANED');self.assertFalse(r['filesystem_touched'])
        self.assertEqual(r['task'],'gone-pr')
        s=self.snap();rec=s['requests'][rid]
        self.assertEqual(rec['state'],'RETIRED_ORPHANED')  # retained, not deleted
        self.assertEqual(rec['retire']['reason'],REASON)
        self.assertIn('snapshot shows',rec['retire']['evidence'])
        self.assertEqual(rec['retire']['actor'],'SUPERVISOR')
        ev=[e for e in self.events(since=0) if e['kind']=='ir_retire']
        self.assertEqual(len(ev),1)
        self.assertEqual(ev[0]['request'],rid)
        self.assertEqual(ev[0]['reason'],REASON)
        self.assertEqual(ev[0]['actor'],'SUPERVISOR')
    def test_ir_retire_never_touches_the_filesystem(self):
        rid,_=self.request('paper-pr')
        before=sorted((str(p),p.stat().st_size) for p in self.root.rglob('*'))
        r=self.retire(rid)
        self.assertFalse(r['filesystem_touched'])
        after=sorted((str(p),p.stat().st_size) for p in self.root.rglob('*'))
        self.assertEqual(before,after)

    # ---- ir_retire: refusals ----------------------------------------------
    def test_ir_retire_refuses_non_supervisor_actors(self):
        rid,_=self.request('open-pr')
        for actor in ('worker','other','lead'):
            with self.assertRaisesRegex(Refusal,'supervisor_only'):
                self.call('ir_retire',actor,request=rid,reason='r',evidence='e')
        self.assertEqual(self.snap()['requests'][rid]['state'],'PENDING_EXTERNAL_BROKER')
    def test_ir_retire_refuses_unknown_request(self):
        with self.assertRaisesRegex(Refusal,'unknown_integration_request'):
            self.retire('0'*24)
    def test_ir_retire_refuses_acknowledged_request(self):
        rid,_=self.request('acked-pr')
        self.ack(rid)
        self.assertEqual(self.snap()['requests'][rid]['state'],'ACKNOWLEDGED')
        with self.assertRaisesRegex(Refusal,'request_not_pending'):self.retire(rid)
    def test_ir_retire_refuses_already_retired_request(self):
        rid,_=self.request('twice-pr')
        self.retire(rid)
        with self.assertRaisesRegex(Refusal,'request_not_pending'):self.retire(rid)
        self.assertEqual(self.snap()['requests'][rid]['state'],'RETIRED_ORPHANED')
    def test_ir_retire_requires_reason_and_evidence(self):
        rid,_=self.request('attested-pr')
        # text() validates reason FIRST and evidence SECOND, so each blank
        # case names its exact missing_* arm instead of a bare Refusal.
        for p,name in (({'evidence':'e'},'missing_retire_reason'),
                       ({'reason':'','evidence':'e'},'missing_retire_reason'),
                       ({'reason':'  ','evidence':'e'},'missing_retire_reason'),
                       ({'reason':'r'},'missing_retire_evidence'),
                       ({'reason':'r','evidence':''},'missing_retire_evidence'),
                       ({'reason':'r','evidence':'  '},'missing_retire_evidence')):
            with self.assertRaisesRegex(Refusal,name):
                self.call('ir_retire','super-secret',request=rid,**p)
        self.assertEqual(self.snap()['requests'][rid]['state'],'PENDING_EXTERNAL_BROKER')

    # ---- the ack path is intact in both directions -------------------------
    def test_retired_request_cannot_be_acknowledged(self):
        rid,_=self.request('retired-ack-pr')
        self.retire(rid)
        # ack_integration's existing state guard names the same refusal it
        # always has for a non-PENDING request; no un-retire op exists.
        with self.assertRaisesRegex(Refusal,'integration_already_acknowledged'):
            self.ack(rid)
        self.assertEqual(self.snap()['tasks']['retired-ack-pr']['state'],'REVIEW')
    def test_pending_request_still_acknowledges(self):
        rid,_=self.request('healthy-pr')
        r=self.ack(rid)
        self.assertEqual(r['state'],'INTEGRATED')
        self.assertEqual(self.snap()['requests'][rid]['state'],'ACKNOWLEDGED')
        self.assertEqual(self.snap()['tasks']['healthy-pr']['state'],'INTEGRATED')

    # ---- refusal atomicity and audit hygiene -------------------------------
    def test_refusals_leave_revision_and_audit_untouched(self):
        rid,_=self.request('quiet-pr')
        before=self.snap()['revision'];events_before=self.events(since=0)
        with self.assertRaisesRegex(Refusal,'missing_retire_reason'):
            self.retire(rid,reason='',evidence='e')
        with self.assertRaisesRegex(Refusal,'supervisor_only'):
            self.call('ir_retire','worker',request=rid,reason='r',evidence='e')
        with self.assertRaisesRegex(Refusal,'unknown_integration_request'):self.retire('0'*24)
        self.assertEqual(before,self.snap()['revision'])
        self.assertEqual(events_before,self.events(since=0))
    def test_audit_event_carries_request_and_reason_not_evidence(self):
        rid,_=self.request('aud-pr')
        evidence='secret-free but payload-bearing: never enters the event stream'
        self.retire(rid,evidence=evidence)
        ev=[e for e in self.events(since=0) if e['kind']=='ir_retire'][0]
        self.assertEqual(ev['request'],rid);self.assertIn('orphaned',ev['reason'])
        self.assertNotIn(evidence,json.dumps(ev))
        # The stored request record keeps the evidence; the event never does.
        self.assertEqual(self.snap()['requests'][rid]['retire']['evidence'],evidence)
        body=json.dumps(self.events(since=0))
        for token in self.tokens.values():self.assertNotIn(token,body)

if __name__=='__main__':unittest.main(verbosity=2)
