"""Independent reference model of the INTENDED catalogue-discovery contract.

Card GOV-06 "Discovery and roadmap evolution" (holodeck-gov-06). Stdlib
only; imports NOTHING from the repository. This is the contract the CARD
promises - append-only proposal/contradiction/supersession workflow,
dependency-DAG frontier discovery, and a promotion gate that refuses to let
a speculative idea become a certified production claim - not a copy of the
deployed source (that comparison lives in controls/run_controls.py).

Intended semantics fixed in PREREGISTRATION.txt (R1-R5):
  - imports are lead-gated, echo-checked (stale), validated, idempotent
    (duplicate), digested from the PAYLOAD (caller digest never trusted)
    and the ledger is APPEND-ONLY history.
  - catalogue_next is a pure read: the frontier is the PROPOSED cards
    whose ids are neither live nor done and whose EVERY dependency is
    satisfied by an INTEGRATED realization. Satisfaction is PROVENANCE
    based: a task realizes a card via its `realized_from` field (the
    fleet's convention derives realization ids as 'holodeck-' + card-id
    lowercase, so raw string identity can never be the contract).
  - supersede()/promote() append workflow records and REFUSE
    (speculative_not_certifiable) unless a lead-authorized trail exists:
    an INTEGRATED task realized from the card. A catalogue record is
    planning data: it never creates, claims, admits or mutates a task.
"""
from __future__ import annotations

import hashlib
import json


class Refusal(Exception):
    """Named refusal, mirroring the controller's require() convention."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


VALID_STATES = ('READY', 'RUNNING', 'BLOCKED', 'REVIEW', 'RECOVERY_HOLD',
                'INTEGRATED', 'ABANDONED')


def payload_digest(payload):
    canonical = json.loads(json.dumps(payload, ensure_ascii=False))
    return hashlib.sha256(json.dumps(canonical, sort_keys=True,
                                     ensure_ascii=False).encode('utf-8')).hexdigest()


def validate_payload(payload):
    """Intended import validation. Returns None or an error string."""
    if not isinstance(payload, dict) or not isinstance(payload.get('cards'), list):
        return 'missing_cards'
    seen = set()
    for card in payload['cards']:
        if not isinstance(card, dict):
            return 'card_not_object'
        cid = card.get('id')
        if not isinstance(cid, str) or not cid.strip():
            return 'card_missing_id'
        if cid in seen:
            return 'duplicate_card_id:' + cid
        seen.add(cid)
        if not isinstance(card.get('status'), str) or not card['status']:
            return 'card_missing_status:' + cid
        deps = card.get('depends_on')
        if deps is None:
            deps = []
        if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
            return 'card_bad_depends:' + cid
    cards = {c['id']: c for c in payload['cards'] if isinstance(c, dict) and isinstance(c.get('id'), str)}
    for cid, card in cards.items():
        for dep in (card.get('depends_on') or []):
            if dep not in cards:
                return 'unknown_dependency:' + cid + '->' + dep
    # acyclicity (dependency DAG - card prediction: explicit integration
    # dependencies form a graph, and a cycle can never have a frontier)
    state = {}

    def visit(node):
        if state.get(node) == 1:
            return False
        if state.get(node) == 2:
            return True
        state[node] = 1
        for dep in (cards[node].get('depends_on') or []):
            if dep in cards and not visit(dep):
                return False
        state[node] = 2
        return True

    for cid in cards:
        if not visit(cid):
            return 'dependency_cycle:' + cid
    return None


class CatalogueModel:
    """Append-only proposal / contradiction / supersession workflow."""

    LEAD = 'lead'

    def __init__(self, revision=100, epoch=5):
        self.revision = revision
        self.epoch = epoch
        self.imports = []            # APPEND-ONLY ledger (no current payload)
        self.current = None          # {digest, payload, imported_revision, ...}
        self.tasks = {}              # id -> {state, realized_from}
        self.workflow = []           # APPEND-ONLY proposal/contradiction/supersession

    # -- lifecycle fixtures (the model does NOT create tasks; tests place
    #    them here exactly as the lead-authorized lifecycle would) --------
    def add_task(self, task_id, state, realized_from):
        assert state in VALID_STATES
        self.tasks[task_id] = {'state': state, 'realized_from': realized_from}

    # -- intended catalogue_import (R1/R2) --------------------------------
    def catalogue_import(self, actor, epoch, digest_echo, payload):
        if actor != self.LEAD or epoch != self.epoch:
            raise Refusal('lead_gate')
        if self.current is not None and digest_echo != self.current['digest']:
            raise Refusal('stale_catalogue_import')
        error = validate_payload(payload)
        if error is not None:
            raise Refusal('invalid_catalogue_payload:' + error)
        digest = payload_digest(payload)
        if self.current is not None and self.current['digest'] == digest:
            raise Refusal('duplicate_catalogue_import')
        self.revision += 1
        record = {'digest': digest, 'imported_revision': self.revision,
                  'epoch': self.epoch, 'leader': actor}
        self.current = {**record, 'payload': payload}
        self.imports.append(dict(record))   # append-only history
        return {'digest': digest, 'coverage': payload.get('coverage'),
                'imported_revision': self.revision}

    # -- intended catalogue_next (R3/R4) ----------------------------------
    def catalogue_next(self, digest):
        if self.current is None or digest != self.current['digest']:
            raise Refusal('unknown_catalogue_digest')
        done_cards = {t['realized_from'].casefold() for t in self.tasks.values()
                      if t['state'] == 'INTEGRATED' and t.get('realized_from')}
        live_cards = {t['realized_from'].casefold() for t in self.tasks.values()
                      if t['state'] not in ('INTEGRATED', 'ABANDONED')
                      and t.get('realized_from')}
        live_tasks = sorted(tid for tid, t in self.tasks.items()
                            if t['state'] not in ('INTEGRATED', 'ABANDONED'))
        candidates = []
        for card in self.current['payload'].get('cards', []):
            if not isinstance(card, dict) or not isinstance(card.get('id'), str):
                continue
            cid = card['id'].casefold()
            if cid in live_cards or cid in done_cards:
                continue
            if card.get('status') != 'PROPOSED':
                continue
            deps = card.get('depends_on') if isinstance(card.get('depends_on'), list) else []
            if all(str(d).casefold() in done_cards for d in deps):
                candidates.append(card['id'])
        return {'digest': digest, 'candidates': sorted(candidates),
                'live_tasks': live_tasks,
                'note': 'PLANNING CANDIDATES ONLY: catalogue records are not '
                        'claims, not READY tasks and grant no authority.'}

    # -- intended workflow: contradiction / supersession / promotion (R5) --
    def _realization(self, card_id):
        cid = card_id.casefold()
        for task in self.tasks.values():
            if task.get('realized_from', '').casefold() == cid:
                return task
        return None

    def supersede(self, actor, card_id, kind, note):
        """Append a workflow record. Promotion-grade records (SUPERSESSION
        of a card by its certified realization) require the trail: an
        INTEGRATED task realized from the card. Anything else is exactly
        the card falsifier and refuses by name."""
        if actor != self.LEAD:
            raise Refusal('speculative_not_certifiable')
        realization = self._realization(card_id)
        certified = realization is not None and realization['state'] == 'INTEGRATED'
        if kind in ('SUPERSESSION', 'PROMOTION') and not certified:
            raise Refusal('speculative_not_certifiable')
        self.workflow.append({'card': card_id, 'kind': kind, 'note': note,
                              'certified_trail': certified,
                              'revision': self.revision + 1})

    def contradict(self, actor, card_id, note):
        self.supersede(actor, card_id, 'CONTRADICTION', note)

    def promote(self, actor, card_id, note='promote to certified claim'):
        self.supersede(actor, card_id, 'PROMOTION', note)
