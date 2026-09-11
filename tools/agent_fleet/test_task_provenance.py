"""fleet-task-provenance-backfill-01: the task_provenance_set contract.

Isolated tests over a temp registry root (the test_task_abandon.py
harness pattern): every test builds its own Control store, enrolls/
qualifies fixture agents, elects a lead, imports a fixture catalogue,
and drives the real controller state machine. No live service, no
deployed store, no filesystem mutation by the ops under test.

The gap under test is MEASURED LIVE (snapshot 2026-09-11): every
pre-existing holodeck task carries realized_from=None (the field
postdates them; PR #92's additive migration setdefaults None), so
live_cards/done_cards are empty and the id-fallback never binds GOV-0X
to holodeck-gov-0X - catalogue_next keeps offering [GOV-01]. The fix is
a supervisor-only BACKFILL op; catalogue_next matching rules are NOT
touched (PR #92 semantics hold verbatim, including: ABANDONED citations
satisfy nothing and re-propose the card).

The S1 fixture (GOV_CARDS + oracle frontier set) is retained verbatim
from fleet-catalogue-realization-matching-01 (PR #92,
test_catalogue_realization.py) - here it must pass through BACKFILL
(op-set provenance) instead of create-time citation.
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
BACKFILL='backfill evidence: card citation from the integrated draft (docs/evidence, PR-recorded)'

# Retained S1 fixture verbatim from fleet-catalogue-realization-matching-01
# (test_catalogue_realization.py): the GOV+MATH subgraph of the real
# 240-card graph. GOV-01 is the unique root.
GOV_CARDS=[
    {'id':'GOV-01','domain':'GOV','status':'PROPOSED','depends_on':[]},
    {'id':'GOV-02','domain':'GOV','status':'PROPOSED','depends_on':['GOV-01']},
    {'id':'GOV-03','domain':'GOV','status':'PROPOSED','depends_on':['GOV-01']},
    {'id':'GOV-04','domain':'GOV','status':'PROPOSED','depends_on':['GOV-01']},
    {'id':'GOV-05','domain':'GOV','status':'PROPOSED','depends_on':['GOV-01']},
    {'id':'GOV-06','domain':'GOV','status':'PROPOSED','depends_on':['GOV-01']},
    {'id':'MATH-01','domain':'MATH','status':'PROPOSED','depends_on':['GOV-01']},
]
# The faithful eight-task rehearsal graph: GOV_CARDS plus the real
# dependency shapes MATH-02 dep GOV-01+MATH-01 and MAT-01 dep
# MATH-01+GOV-03 (docs/roadmap/holodeck_tasks.json at this base).
BACKFILL_CARDS=GOV_CARDS+[
    {'id':'MATH-02','domain':'MATH','status':'PROPOSED','depends_on':['GOV-01','MATH-01']},
    {'id':'MAT-01','domain':'MAT','status':'PROPOSED','depends_on':['MATH-01','GOV-03']},
]
MINI_MASTER='# Mini master\n\n| # | id | task |\n|---|----|------|\n'
S1_ORACLE=['GOV-02','GOV-03','GOV-04','GOV-05','GOV-06','MATH-01']

class TaskProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.c=Control(self.root/'state.sqlite','super-secret','enroll-secret',self.root/'slots')
        self.tokens={}
        for aid in ('lead','standby','worker','other'):
            self.tokens[aid]=self.c.call('enroll','enroll-secret',agent=aid,label=aid)['result']['session_token']
            self.c.call('qualify','super-secret',agent=aid,capabilities=['cpu','docs'],max_tasks=5,
                can_lead=aid=='lead',rank=10 if aid=='lead' else 1,evidence='fixture qualification record')
        self.c.call('offer_lead',self.tokens['lead'],epoch=0,checkpoint='ready; no foreign work')
        self.c.call('elect','super-secret')
    def tearDown(self):self.tmp.cleanup()

    # --- harness -----------------------------------------------------------
    def call(self,op,actor='lead',**p):return self.c.call(op,self.tokens.get(actor,actor),**p)['result']
    def snap(self):return self.call('snapshot')
    def epoch(self):return self.snap()['epoch']
    def import_cards(self,cards):
        payload=build_records(catalog_text=json.dumps({'tasks':cards}),master_text=MINI_MASTER)
        dig=payload_digest(payload)
        self.call('catalogue_import',payload=payload,digest=dig,epoch=self.epoch(),
                  evidence='fixture import evidence')
        return dig
    def task(self,tid,**kw):
        p=dict(task=tid,epoch=self.epoch(),base=BASE,scopes=['tools/labs/'+tid],
               packet='statement / prediction / falsifier',kind='worker')
        p.update(kw);return self.call('create_task',**p)
    def setprov(self,tid,card,**kw):
        _actor=kw.pop('_actor','super-secret')
        p=dict(task=tid,realized_from=card,evidence=BACKFILL)
        p.update(kw);return self.call('task_provenance_set',_actor,**p)
    def drive(self,tid,final='INTEGRATED'):
        """Create a LEGACY task (NO realized_from - the pre-field era) and
        drive it through the lead-authorized lifecycle to `final`."""
        self.task(tid)
        claimed=self.call('claim','worker',task=tid)
        self.call('checkpoint','worker',task=tid,generation=claimed['generation'],
                  checkpoint='realization underway')
        if final=='RUNNING':return claimed
        self.call('submit_review','worker',task=tid,generation=claimed['generation'],
                  branch=claimed['branch'],head=HEAD,evidence='exact review evidence')
        if final=='REVIEW':return claimed
        request=self.call('integration_request',task=tid,head=HEAD,branch=claimed['branch'],
                          expected_base=BASE,epoch=self.epoch(),review='independent review')
        self.call('ack_integration','super-secret',request=request['request'],
                  base_branch='astra/gait-capture',expected_base=BASE,commit=MERGED,
                  evidence='publisher verified remote head')
        return claimed
    def frontier(self,digest):return self.call('catalogue_next',digest=digest)['candidates']
    def events(self,since=0):return self.call('events',since=since)['events']

    # --- P1: the retained S1 fixture passes through BACKFILL ---------------
    def test_s1_fixture_passes_with_backfilled_provenance(self):
        digest=self.import_cards(GOV_CARDS)
        self.drive('holodeck-gov-01')
        self.assertEqual(self.snap()['tasks']['holodeck-gov-01']['state'],'INTEGRATED')
        self.assertIsNone(self.snap()['tasks']['holodeck-gov-01'].get('realized_from'))
        # The measured live gap, in miniature: the id-fallback cannot bind
        # GOV-01 to holodeck-gov-01, so the realized root is re-proposed.
        self.assertEqual(self.frontier(digest),['GOV-01'])
        # Backfill via the supervisor op; NO matching rule changed.
        self.setprov('holodeck-gov-01','GOV-01')
        self.assertEqual(self.snap()['tasks']['holodeck-gov-01']['realized_from'],'GOV-01')
        # S1 oracle set, byte-identical to the PR #92 fixture expectation.
        self.assertEqual(self.frontier(digest),S1_ORACLE)

    # --- P2: the eight-task rehearsal (mirrors the live registry) ----------
    def test_eight_task_backfill_offers_true_frontier(self):
        digest=self.import_cards(BACKFILL_CARDS)
        for tid in ('holodeck-gov-01','holodeck-gov-02','holodeck-gov-03',
                    'holodeck-gov-04','holodeck-gov-05','holodeck-math-01',
                    'holodeck-mat-01'):
            self.drive(tid)                       # INTEGRATED
        self.drive('holodeck-gov-06',final='REVIEW')  # live registry: REVIEW
        s=self.snap()
        for tid in ('holodeck-gov-01','holodeck-gov-02','holodeck-gov-03',
                    'holodeck-gov-04','holodeck-gov-05','holodeck-math-01',
                    'holodeck-mat-01'):
            self.assertEqual(s['tasks'][tid]['state'],'INTEGRATED')
        self.assertEqual(s['tasks']['holodeck-gov-06']['state'],'REVIEW')
        # Pre-backfill: the gap - GOV-01 offered although realized.
        self.assertEqual(self.frontier(digest),['GOV-01'])
        # The backfill: eight op calls (seven terminal + one active).
        for tid,card in (('holodeck-gov-01','GOV-01'),('holodeck-gov-02','GOV-02'),
                         ('holodeck-gov-03','GOV-03'),('holodeck-gov-04','GOV-04'),
                         ('holodeck-gov-05','GOV-05'),('holodeck-gov-06','GOV-06'),
                         ('holodeck-math-01','MATH-01'),('holodeck-mat-01','MAT-01')):
            self.setprov(tid,card)
        # True frontier: the realized root is NOT re-proposed; the only
        # uncited card whose dependencies are certified is MATH-02.
        self.assertEqual(self.frontier(digest),['MATH-02'])

    # --- P3: forward path unchanged; a present citation is never rewritten -
    def test_forward_path_create_task_citation_needs_no_op(self):
        # Baseline that is green at BOTH heads (the op never fires here):
        # PR #92's create-time citation resolves the frontier by itself.
        digest=self.import_cards(GOV_CARDS)
        self.task('holodeck-gov-01',realized_from='GOV-01')
        claimed=self.call('claim','worker',task='holodeck-gov-01')
        self.call('submit_review','worker',task='holodeck-gov-01',
                  generation=claimed['generation'],branch=claimed['branch'],head=HEAD,
                  evidence='exact review evidence')
        request=self.call('integration_request',task='holodeck-gov-01',head=HEAD,
                          branch=claimed['branch'],expected_base=BASE,epoch=self.epoch(),
                          review='independent review')
        self.call('ack_integration','super-secret',request=request['request'],
                  base_branch='astra/gait-capture',expected_base=BASE,commit=MERGED,
                  evidence='publisher verified remote head')
        self.assertEqual(self.frontier(digest),S1_ORACLE)
    def test_provenance_set_refuses_when_citation_already_present(self):
        digest=self.import_cards(GOV_CARDS)
        self.drive('holodeck-gov-01')
        self.setprov('holodeck-gov-01','GOV-01')
        with self.assertRaisesRegex(Refusal,'provenance_already_set'):
            self.setprov('holodeck-gov-01','GOV-02')
        self.assertEqual(self.snap()['tasks']['holodeck-gov-01']['realized_from'],'GOV-01')
        # A forward-cited task (create_task practice) is likewise closed:
        self.task('cited-at-create',realized_from='GOV-01')
        with self.assertRaisesRegex(Refusal,'provenance_already_set'):
            self.setprov('cited-at-create','GOV-06')
        self.assertEqual(self.snap()['tasks']['cited-at-create']['realized_from'],'GOV-01')

    # --- active and terminal states ----------------------------------------
    def test_provenance_set_on_active_running_task(self):
        digest=self.import_cards(GOV_CARDS)
        self.drive('holodeck-gov-01',final='RUNNING')
        before=self.snap()['revision']
        self.setprov('holodeck-gov-01','GOV-01')
        t=self.snap()['tasks']['holodeck-gov-01']
        self.assertEqual(t['state'],'RUNNING')
        self.assertEqual(t['realized_from'],'GOV-01')
        self.assertEqual(t['provenance_set']['actor'],'SUPERVISOR')
        self.assertEqual(t['provenance_set']['realized_from'],'GOV-01')
        self.assertIn('integrated draft',t['provenance_set']['evidence'])
        self.assertEqual(t['provenance_set']['revision'],before+1)
        # An ACTIVE citation already excludes the card (live_cards).
        self.assertNotIn('GOV-01',self.frontier(digest))
    def test_provenance_set_on_review_task_mirrors_live_registry(self):
        digest=self.import_cards(GOV_CARDS)
        self.drive('holodeck-gov-06',final='REVIEW')
        self.setprov('holodeck-gov-06','GOV-06')
        t=self.snap()['tasks']['holodeck-gov-06']
        self.assertEqual(t['state'],'REVIEW')
        self.assertEqual(t['realized_from'],'GOV-06')
        self.assertNotIn('GOV-06',self.frontier(digest))
    def test_provenance_set_on_abandoned_task_satisfies_nothing(self):
        # ABANDONED is terminal, so the citation backfills (factual history),
        # but PR #92 semantics hold untouched: an ABANDONED citation
        # satisfies no dependency and RE-PROPOSES the card.
        digest=self.import_cards(GOV_CARDS)
        self.task('holodeck-gov-01')
        self.call('task_abandon','super-secret',task='holodeck-gov-01',
                  reason='attempt retired',evidence='fixture abandonment evidence')
        self.setprov('holodeck-gov-01','GOV-01')
        t=self.snap()['tasks']['holodeck-gov-01']
        self.assertEqual(t['state'],'ABANDONED')
        self.assertEqual(t['realized_from'],'GOV-01')
        self.assertEqual(self.frontier(digest),['GOV-01'])

    # --- P4: refusals, all named -------------------------------------------
    def test_refuses_non_supervisor_actors(self):
        self.task('legacy-one')
        for actor in ('worker','other','lead','standby'):
            with self.assertRaisesRegex(Refusal,'supervisor_only'):
                self.setprov('legacy-one','GOV-01',_actor=actor)
        self.assertEqual(self.snap()['tasks']['legacy-one']['state'],'READY')
    def test_refuses_unknown_task(self):
        with self.assertRaisesRegex(Refusal,'unknown_task'):
            self.setprov('no-such-task','GOV-01')
    def test_refuses_ready_and_recovery_hold(self):
        digest=self.import_cards(GOV_CARDS)
        self.task('pending')
        with self.assertRaisesRegex(Refusal,'task_not_terminal_or_active'):
            self.setprov('pending','GOV-01')
        self.assertEqual(self.snap()['tasks']['pending']['realized_from'],None)
        self.assertEqual(self.frontier(digest),['GOV-01'])  # unchanged
        t=self.call('claim','worker',task='pending')
        self.call('fail','super-secret',agent='worker',reason='PROCESS_EXIT',
                  evidence='trusted runner exited handle record')
        self.assertEqual(self.snap()['tasks']['pending']['state'],'RECOVERY_HOLD')
        with self.assertRaisesRegex(Refusal,'task_not_terminal_or_active'):
            self.setprov('pending','GOV-01')
        self.assertEqual(self.snap()['tasks']['pending']['realized_from'],None)
    def test_state_gate_precedes_id_validation(self):
        # A READY task with a malformed id names the STATE arm: the state
        # gate runs before the id gates (task_abandon ordering precedent).
        self.task('ready-bad')
        with self.assertRaisesRegex(Refusal,'task_not_terminal_or_active'):
            self.setprov('ready-bad','gov-01')
    def test_refuses_missing_and_malformed_card_ids(self):
        digest=self.import_cards(GOV_CARDS)
        self.drive('holodeck-gov-01')
        for bad,name in ((None,'missing_realized_from'),('','missing_realized_from'),
                         ('   ','missing_realized_from'),(42,'missing_realized_from'),
                         ('gov-01','malformed_realized_from'),
                         ('GOV1','malformed_realized_from'),
                         ('GOV-','malformed_realized_from'),
                         ('GOV-01A','malformed_realized_from'),
                         ('GOV-01 ','malformed_realized_from'),
                         ('GOV-01-X','malformed_realized_from'),
                         ('GOV_01','malformed_realized_from'),
                         ('holodeck-gov-01','malformed_realized_from')):
            with self.assertRaisesRegex(Refusal,name):
                self.setprov('holodeck-gov-01',bad)
        self.assertIsNone(self.snap()['tasks']['holodeck-gov-01']['realized_from'])
        self.assertEqual(self.frontier(digest),['GOV-01'])  # still the gap
    def test_evidence_gate_after_id_gate(self):
        self.drive('holodeck-gov-01')
        with self.assertRaisesRegex(Refusal,'missing_provenance_evidence'):
            self.setprov('holodeck-gov-01','GOV-01',evidence='')
        with self.assertRaisesRegex(Refusal,'missing_provenance_evidence'):
            self.setprov('holodeck-gov-01','GOV-01',evidence='   ')
        t=self.snap()['tasks']['holodeck-gov-01']
        self.assertIsNone(t['realized_from'])
        self.assertNotIn('provenance_set',t)
        # The op accepts then requires: valid id + evidence writes both.
        self.setprov('holodeck-gov-01','GOV-01')
        self.assertEqual(self.snap()['tasks']['holodeck-gov-01']['realized_from'],'GOV-01')

    # --- P5: audit parity with task_abandon ---------------------------------
    def test_audit_event_and_task_record(self):
        self.drive('holodeck-gov-01')
        before=self.snap()['revision']
        self.setprov('holodeck-gov-01','GOV-01')
        self.assertEqual(self.snap()['revision'],before+1)
        ev=[e for e in self.events(since=0) if e['kind']=='task_provenance_set']
        self.assertEqual(len(ev),1)
        self.assertEqual(ev[0]['task'],'holodeck-gov-01')
        self.assertEqual(ev[0]['actor'],'SUPERVISOR')
        # Audit parity: the payload (evidence + citation) lives on the task
        # record, not in the event - exactly like task_abandon's evidence.
        self.assertNotIn('evidence',ev[0])
        self.assertNotIn('realized_from',ev[0])
        rec=self.snap()['tasks']['holodeck-gov-01']['provenance_set']
        self.assertEqual(rec['realized_from'],'GOV-01')
        self.assertIn('integrated draft',rec['evidence'])
        self.assertEqual(rec['actor'],'SUPERVISOR')
        self.assertEqual(rec['revision'],before+1)
    def test_refusals_leave_revision_and_audit_untouched(self):
        self.task('quiet')
        before=self.snap()['revision'];events_before=self.events(since=0)
        with self.assertRaisesRegex(Refusal,'supervisor_only'):
            self.setprov('quiet','GOV-01',_actor='worker')
        with self.assertRaisesRegex(Refusal,'unknown_task'):
            self.setprov('absent','GOV-01')
        with self.assertRaisesRegex(Refusal,'task_not_terminal_or_active'):
            self.setprov('quiet','GOV-01')
        with self.assertRaisesRegex(Refusal,'malformed_realized_from'):
            self.setprov('quiet','gov-01')
        self.assertEqual(before,self.snap()['revision'])
        self.assertEqual(events_before,self.events(since=0))
        self.assertIsNone(self.snap()['tasks']['quiet']['realized_from'])
    def test_op_is_registry_state_only_never_touches_the_filesystem(self):
        digest=self.import_cards(GOV_CARDS)
        self.drive('holodeck-gov-01')
        before=sorted((str(p),p.stat().st_size) for p in self.root.rglob('*'))
        self.setprov('holodeck-gov-01','GOV-01')
        after=sorted((str(p),p.stat().st_size) for p in self.root.rglob('*'))
        self.assertEqual(before,after)

if __name__=='__main__':unittest.main(verbosity=2)
