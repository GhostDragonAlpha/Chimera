"""fleet-catalogue-realization-matching-01: catalogue_next must bind cards
to their realizations through the task PROVENANCE field (realized_from),
with the original id-string matching kept as the fallback for tasks that
carry no provenance.

Production gap measured by holodeck-gov-06 (PR #84): exact-casefold
id matching never binds card GOV-0X to realized task holodeck-gov-0X, so
the realized root is perpetually re-proposed and every dependent is
permanently blocked.

ORACLE: the preregistered intended model (gov06_reference_model.py,
holodeck-gov-06 / PR #84; outputs retained verbatim in that lane's
checks/r3_r4_frontier.txt). PR #84 was not yet merged at this branch's
base, so the oracle EXPECTED SETS are embedded below as constants sourced
from those retained checks; PR #84 remains the provenance.

The old-era tests (P2) assert the EXACT pre-fix outputs; they pass at
BOTH heads with identical expectations - that is the byte-identity proof
for the fallback.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control import Control, Refusal
from master_catalogue import build_records, payload_digest

BASE = 'a' * 40
HEAD = 'b' * 40
MERGED = 'c' * 40

# Retained fixture: the GOV+MATH subgraph of the real 240-card graph at
# 62b8e357 (holodeck-gov-06 lane; docs/roadmap/holodeck_tasks.json
# sha256 d5c7aa8b...fcd8). GOV-01 is the unique root.
GOV_CARDS = [
    {'id': 'GOV-01', 'domain': 'GOV', 'status': 'PROPOSED', 'depends_on': []},
    {'id': 'GOV-02', 'domain': 'GOV', 'status': 'PROPOSED', 'depends_on': ['GOV-01']},
    {'id': 'GOV-03', 'domain': 'GOV', 'status': 'PROPOSED', 'depends_on': ['GOV-01']},
    {'id': 'GOV-04', 'domain': 'GOV', 'status': 'PROPOSED', 'depends_on': ['GOV-01']},
    {'id': 'GOV-05', 'domain': 'GOV', 'status': 'PROPOSED', 'depends_on': ['GOV-01']},
    {'id': 'GOV-06', 'domain': 'GOV', 'status': 'PROPOSED', 'depends_on': ['GOV-01']},
    {'id': 'MATH-01', 'domain': 'MATH', 'status': 'PROPOSED', 'depends_on': ['GOV-01']},
]
MINI_MASTER = '# Mini master\n\n| # | id | task |\n|---|----|------|\n'


def gov_payload():
    return build_records(catalog_text=json.dumps({'tasks': GOV_CARDS}),
                         master_text=MINI_MASTER)


def realize_via_lifecycle(call, tid, card_id, final='INTEGRATED'):
    """Create a task citing its card, then drive it through the
    lead-authorized lifecycle to `final` (RUNNING or INTEGRATED)."""
    call('create_task', task=tid, epoch=call('snapshot')['epoch'], base=BASE,
         scopes=['tools/labs/' + tid], packet='statement / prediction / falsifier',
         kind='worker', realized_from=card_id)
    claimed = call('claim', 'worker', task=tid)
    call('checkpoint', 'worker', task=tid, generation=claimed['generation'],
         checkpoint='realization underway')
    if final == 'RUNNING':
        return claimed
    call('submit_review', 'worker', task=tid, generation=claimed['generation'],
         branch=claimed['branch'], head=HEAD, evidence='exact review evidence')
    request = call('integration_request', task=tid, head=HEAD,
                   branch=claimed['branch'], expected_base=BASE,
                   epoch=call('snapshot')['epoch'],
                   review='independent review')
    call('ack_integration', 'super-secret', request=request['request'],
         base_branch='astra/gait-capture', expected_base=BASE, commit=MERGED,
         evidence='publisher verified remote head')
    return claimed


class CatalogueRealizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.c = Control(self.root / 'state.sqlite', 'super-secret',
                         'enroll-secret', self.root / 'slots')
        self.tokens = {}
        for aid in ('lead', 'worker', 'other'):
            self.tokens[aid] = self.c.call('enroll', 'enroll-secret', agent=aid,
                label=aid)['result']['session_token']
            self.c.call('qualify', 'super-secret', agent=aid,
                capabilities=['cpu', 'docs'], max_tasks=5,
                can_lead=aid == 'lead', rank=10 if aid == 'lead' else 1,
                evidence='fixture qualification')
        self.c.call('offer_lead', self.tokens['lead'], epoch=0,
                    checkpoint='fixture leader ready')
        self.c.call('elect', 'super-secret')
        self.payload = gov_payload()
        self.digest = payload_digest(self.payload)
        self.call('catalogue_import', payload=self.payload, digest=self.digest,
                  epoch=self.epoch(), evidence='fixture import evidence')

    def tearDown(self):
        self.tmp.cleanup()

    # --- harness ----------------------------------------------------------
    def call(self, op, actor='lead', **p):
        return self.c.call(op, self.tokens.get(actor, actor), **p)['result']

    def epoch(self):
        return self.call('snapshot')['epoch']

    def frontier(self):
        return self.call('catalogue_next', digest=self.digest)['candidates']

    def next_raw(self):
        return self.call('catalogue_next', digest=self.digest)

    # --- P1: the retained gov-06 oracle fixtures --------------------------
    def test_s1_integrated_root_offers_dependents(self):
        realize_via_lifecycle(self.call, 'holodeck-gov-01', 'GOV-01')
        self.assertEqual(self.call('snapshot')['tasks']['holodeck-gov-01']['state'],
                         'INTEGRATED')
        # oracle (gov06_reference_model): the realized root is never
        # re-proposed and its dependents open.
        self.assertEqual(self.frontier(),
                         ['GOV-02', 'GOV-03', 'GOV-04', 'GOV-05', 'GOV-06', 'MATH-01'])

    def test_s2_active_realizations_narrow_frontier(self):
        realize_via_lifecycle(self.call, 'holodeck-gov-01', 'GOV-01')
        realize_via_lifecycle(self.call, 'holodeck-gov-02', 'GOV-02',
                              final='RUNNING')
        # the retained oracle fixture has GOV-03/04/05 live in mixed
        # active states (READY/REVIEW/BLOCKED all count as active);
        # READY created-and-citing tasks are the same provenance class
        for extra in ('GOV-03', 'GOV-04', 'GOV-05'):
            self.call('create_task', task='holodeck-' + extra.lower(),
                      epoch=self.epoch(), base=BASE,
                      scopes=['tools/labs/holodeck-' + extra.lower()],
                      packet='statement / prediction / falsifier', kind='worker',
                      realized_from=extra)
        realize_via_lifecycle(self.call, 'holodeck-gov-06', 'GOV-06',
                              final='RUNNING')
        self.assertEqual(self.frontier(), ['MATH-01'])

    def test_s3_abandonment_reproposes_card_and_blocks_dependents(self):
        # A READY attempt still cites the card: GOV-01 is active, not
        # re-proposed. Retiring the attempt (task_abandon -> ABANDONED,
        # terminal) re-proposes the card while satisfying no dependency.
        self.call('create_task', task='holodeck-gov-01', epoch=self.epoch(),
                  base=BASE, scopes=['tools/labs/holodeck-gov-01'],
                  packet='statement / prediction / falsifier', kind='worker',
                  realized_from='GOV-01')
        self.assertNotIn('GOV-01', self.frontier())
        self.assertEqual(self.frontier(), [])
        self.c.call('task_abandon', 'super-secret', task='holodeck-gov-01',
                    reason='realization attempt retired',
                    evidence='fixture abandonment evidence')
        ready = self.call('snapshot')['tasks']['holodeck-gov-01']
        self.assertEqual(ready['state'], 'ABANDONED')
        self.assertEqual(self.frontier(), ['GOV-01'])

    # --- P2: old-era fallback is byte-identical ---------------------------
    def test_old_era_no_provenance_resolves_exactly_as_before(self):
        # Legacy task with NO realized_from: the id matching cannot bind
        # 'GOV-01' to 'holodeck-gov-01' - the pre-fix output for this exact
        # fixture is ['GOV-01'], and the fix must not change it by one byte.
        realize_via_lifecycle(self.call, 'holodeck-gov-01', None)
        self.assertIsNone(self.call('snapshot')['tasks']['holodeck-gov-01']
                          .get('realized_from'))
        self.assertEqual(self.frontier(), ['GOV-01'])

    def test_legacy_exact_id_realization_still_satisfies(self):
        # Original import era: a task NAMED like the card (casefold) is a
        # realization by id matching alone; the fallback must keep working.
        realize_via_lifecycle(self.call, 'gov-01', None)
        self.assertEqual(self.frontier(),
                         ['GOV-02', 'GOV-03', 'GOV-04', 'GOV-05', 'GOV-06', 'MATH-01'])

    # --- P3: provenance carry ---------------------------------------------
    def test_create_task_carries_realized_from(self):
        self.call('create_task', task='cites-card', epoch=self.epoch(), base=BASE,
                  scopes=['tools/labs/cites-card'],
                  packet='statement / prediction / falsifier', kind='worker',
                  realized_from='GOV-06')
        self.assertEqual(self.call('snapshot')['tasks']['cites-card']['realized_from'],
                         'GOV-06')
        self.call('create_task', task='no-card', epoch=self.epoch(), base=BASE,
                  scopes=['tools/labs/no-card'],
                  packet='statement / prediction / falsifier', kind='worker')
        self.assertIsNone(self.call('snapshot')['tasks']['no-card']['realized_from'])
        with self.assertRaisesRegex(Refusal, 'invalid_realized_from'):
            self.call('create_task', task='bad-card', epoch=self.epoch(), base=BASE,
                      scopes=['tools/labs/bad-card'],
                      packet='statement / prediction / falsifier', kind='worker',
                      realized_from='   ')

    # --- P4: gates unchanged ----------------------------------------------
    def test_unknown_digest_and_status_gate_and_pure_read(self):
        with self.assertRaisesRegex(Refusal, 'unknown_catalogue_digest'):
            self.c.call('catalogue_next', self.tokens['lead'], digest='0' * 64)
        before = json.dumps(self.call('snapshot'), sort_keys=True)
        raw = self.next_raw()
        self.assertIn('PLANNING CANDIDATES ONLY', raw['note'])
        after = json.dumps(self.call('snapshot'), sort_keys=True)
        self.assertEqual(before, after)  # pure read
        # importing a new catalogue rotates the digest: the old one refuses
        payload = build_records(
            catalog_text=json.dumps({'tasks': [
                {'id': 'Z-01', 'domain': 'Z', 'status': 'SUPERSEDED',
                 'depends_on': []}]}),
            master_text=MINI_MASTER)
        dig = payload_digest(payload)
        self.call('catalogue_import', payload=payload, digest=self.digest,
                  epoch=self.epoch(), evidence='superseded import')
        with self.assertRaisesRegex(Refusal, 'unknown_catalogue_digest'):
            self.c.call('catalogue_next', self.tokens['lead'], digest=self.digest)
        # a SUPERSEDED card is never offered, even with satisfied deps
        self.assertEqual(self.call('catalogue_next', digest=dig)['candidates'], [])


if __name__ == '__main__':
    unittest.main()
