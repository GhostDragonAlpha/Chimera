"""L7 — proof and replay reuse: the evidence cache with SEMANTIC-DEPENDENCY
invalidation, and the REPLAY-REUSE certificate (agent/cl-L7-reuse-20260921).

THE L7 THEORY (preregistration, tools/science_funnel/validation/
cl_L7_20260921/preregistration.md — written before this file): a cached
verification result (e.g. "record set S on baseline B reproduces trace T
bit-exact") is reusable EXACTLY while its SEMANTIC dependency closure is
unchanged, and that closure is COMPUTED from record content and the declared
boundary — never inferred from names, text, or full-content digests alone
(metadata is not semantics: a citation cannot change a bit).

Dependency classes (each a digest; ANY semantic delta invalidates):
  records/producers  per-record full content digest + SEMANTIC digest, plus
                     the transitive producer closure over record-input reads
                     (the one-defining-writer map; the `via` quantities are
                     recorded — the exact composition edges)
  reset              the reset event + every expanded initial (the reset rule)
  numeric_policy     dtype/IEEE/FP-flags/comparison convention/arith order
  domain             scene digest, externals binding, tick convention
  horizon            tick count + stop condition
  baseline           source-tree identity the claim was measured against

Invalidation is VALIDATION, not suspicion: identity drift (full digest
changed, semantic digest equal) is RECORDED, never fatal — F-OVER-INVALIDATE
guards the dual failure (a false invalidation is the bottleneck un-fixed).

THE REPLAY-REUSE CERTIFICATE (the narrow result): complete lossless replay
match (every boundary output + state transition, floats by uint64 bits, never
decimals) + physics-unchanged + measured determinism => same-trajectory-by-
induction, recorded with its EXACT assumptions. It entitles skipping a full
re-run ONLY while every assumption holds; otherwise the waiver is REFUSED and
the firing falsifier NAMED: F-STALE-CERTIFICATE (reuse after a semantic
dependency changed) or F-UNJUSTIFIED-RERUN-SKIP (rerun waived without the
certificate's assumptions holding).

FALSIFIERS:
  F-STALE-CERTIFICATE      a result reused after a semantic dependency changed
  F-UNJUSTIFIED-RERUN-SKIP a full rerun waived without the assumptions holding
  F-OVER-INVALIDATE        a result invalidated by a metadata-only change

Run: python -m unittest tools.constraint_ledger.tests_reuse -v
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from .schema import Record, RecordError, content_digest, effects, expand

F_STALE_CERTIFICATE = 'F-STALE-CERTIFICATE'
F_UNJUSTIFIED_RERUN_SKIP = 'F-UNJUSTIFIED-RERUN-SKIP'
F_OVER_INVALIDATE = 'F-OVER-INVALIDATE'


class ReuseError(ValueError):
    pass


def _sha(obj) -> str:
    """sha256 of canonical JSON (sort_keys, compact) — the store convention."""
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def digest_of(obj) -> str:
    """Public canonical-JSON digest (the store convention)."""
    return _sha(obj)


# ── semantics vs metadata ────────────────────────────────────────────────────
# The whitelist IS the theory: these record fields can change a computed bit.
# Everything else (provenance, falsifier, lane, notes) is citation — recorded
# as identity, never allowed to invalidate.
_SEMANTIC_FIELDS = ('name', 'kind', 'params', 'quantities', 'assign',
                    'constants', 'initial')
_SEMANTIC_EXTRA = ('invariant_expr',)   # semantics-carrying `extra` keys


def semantic_content(rec: Record) -> dict:
    """The semantics-carrying subset of a record's content (the digest input
    for dependency purposes). Provenance/falsifier/lane are METADATA here."""
    out = {k: rec.content()[k] for k in _SEMANTIC_FIELDS}
    for k in _SEMANTIC_EXTRA:          # extra keys land in rec.extra (schema)
        if k in rec.extra:
            out[k] = rec.extra[k]
    return out


def semantic_digest(rec: Record) -> str:
    return _sha(semantic_content(rec))


def record_set_digest(records: list[Record]) -> str:
    """Digest over the SET (sorted by name, deduplicated by semantic digest):
    the cache key input for 'record set S'."""
    seen = {}
    for r in records:
        seen[r.name] = semantic_digest(r)
    return _sha([[n, seen[n]] for n in sorted(seen)])


# ── the dependency calculator ────────────────────────────────────────────────
NUMERIC_POLICY_PILOT = {
    'dtype': 'binary64 (IEEE-754 double) at the controller boundary',
    'ieee': '754-2019',
    'comparison': 'uint64 bit patterns, NEVER decimals (a %.17g decimal is '
                  'only round-trip evidence, never the compared artifact)',
    'fp_flags': '/fp:precise (no fast-math in the gait targets)',
    'arith_order': 'chimpl mirrors the source operation order bit-for-bit',
    'threads': 'single-threaded sequential tick loop (structural, measured)',
    'substeps': 'none at the controller boundary (one decision per tick)',
}

RESET_EVENT_PILOT = {
    'event': {'reset': True},
    'at': 'GaitWalker::configure, once, before tick 0',
    'effect': 'reset() zeroes hind_step_mode_/t_/plant_y_, held=false, '
              'clear_tick=-1, touching_prev_=false,false, phi_={0,0.5}',
}

TICK_CONVENTION_PILOT = ('row j of a trace = status AFTER step j-1; dump(0) '
                         'is the reset row; decisions at row j read tick-start '
                         'values from row j-1 plus same-tick ordered writes')


@dataclass
class DependencySet:
    """The closure of what a result depended on. Frozen at cache time;
    compared class-by-class at reuse time."""
    records: dict            # template name -> {content_sha, semantic_sha}
    producers: dict          # template name -> {semantic_sha, via: [quantities]}
    reset: str               # reset-rule digest (event + all expanded initials)
    numeric_policy: str
    domain: str
    horizon: str
    baseline: str = ''       # source-tree identity (empty = not claimed)
    digest: str = ''         # over everything above

    def canonical(self) -> dict:
        return {'records': self.records, 'producers': self.producers,
                'reset': self.reset, 'numeric_policy': self.numeric_policy,
                'domain': self.domain, 'horizon': self.horizon,
                'baseline': self.baseline}

    def seal(self) -> 'DependencySet':
        self.digest = _sha(self.canonical())
        return self


def producer_closure(records: list[Record]) -> dict[str, list[str]]:
    """Transitive producer closure over record-input reads: for every record,
    the set of record-input quantities it reads, resolved through the
    one-defining-writer map to the producing record; producers are visited
    transitively. Returns template name -> sorted `via` quantities (empty for
    records with no record-input reads). A record-input with no producer IN
    THE SET is a named gap and refuses (never a silent under-approximation —
    an under-approximated closure is a stale certificate waiting to fire)."""
    writers: dict[str, str] = {}
    for rec in records:
        for inst in expand(rec):
            wx, _, _ = effects(inst)
            for q in wx:
                if q in writers and writers[q] != inst.name:
                    raise ReuseError(
                        f'two defining writers for {q!r}: {writers[q]!r} '
                        f'and {inst.name!r} (I1)')
                writers[q] = inst.name
    via: dict[str, set] = {}
    frontier = list(records)
    while frontier:
        rec = frontier.pop()
        if rec.name in via:
            continue
        via[rec.name] = set()
        for inst in expand(rec):
            _, delayed, same = effects(inst)
            for q in sorted(delayed | same):
                decl = inst.quantities.get(q)
                if decl is None or decl.role != 'record-input':
                    continue
                if q not in writers:
                    raise ReuseError(
                        f'{rec.name}: record-input {q!r} has no producer '
                        f'in the set (named gap, refusal)')
                via[rec.name].add(q)
                tmpl = writers[q].split('[')[0]
                if tmpl not in via:
                    for other in records:
                        if other.name == tmpl:
                            frontier.append(other)
                            break
                    else:
                        raise ReuseError(
                            f'producer template {tmpl!r} not in the set')
    return {name: sorted(qs) for name, qs in via.items()}


def _reset_digest(records: list[Record], reset_event: dict) -> str:
    """The reset rule: the event AND every expanded concrete initial. A reset
    is part of the transition function; changing either half changes it."""
    initials = {}
    for rec in records:
        for inst in expand(rec):
            for q, v in inst.initial.items():
                if q in initials and initials[q] != v:
                    raise ReuseError(f'conflicting initials for {q!r}')
                initials[q] = v
    return _sha({'event': reset_event,
                 'state_quantities': sorted(initials),
                 'initials': initials})


def compute_dependencies(records: list[Record], *, scene_digest: str,
                         externals_digest: str,
                         numeric_policy: dict = NUMERIC_POLICY_PILOT,
                         reset_event: dict = RESET_EVENT_PILOT,
                         tick_convention: str = TICK_CONVENTION_PILOT,
                         horizon: dict = {}, baseline: str = ''
                         ) -> DependencySet:
    """The closure of what a result over this record set depended on."""
    recs = {}
    for r in records:
        recs[r.name] = {'content_sha': content_digest(r),
                        'semantic_sha': semantic_digest(r)}
    closure = producer_closure(records)
    prods = {}
    for name, via in sorted(closure.items()):
        prods[name] = {'semantic_sha': semantic_digest(
            next(r for r in records if r.name == name)), 'via': via}
    domain = _sha({'scene_sha256': scene_digest,
                   'externals_sha256': externals_digest,
                   'tick_convention': tick_convention})
    return DependencySet(
        records=recs, producers=prods,
        reset=_reset_digest(records, reset_event),
        numeric_policy=_sha(numeric_policy),
        domain=domain,
        horizon=_sha(horizon),
        baseline=_sha({'source_tree': baseline}) if baseline else '',
    ).seal()


# ── the invalidation check ───────────────────────────────────────────────────
DEP_CLASSES = ('records', 'producers', 'reset', 'numeric_policy', 'domain',
               'horizon', 'baseline')


@dataclass
class Validity:
    status: str               # VALID | INVALIDATED
    reasons: list = field(default_factory=list)     # semantic deltas (fatal)
    identity_drift: list = field(default_factory=list)  # metadata-only (noted)
    falsifier: str = ''       # set when a STALE REUSE is attempted


def check_validity(cached: DependencySet, current: DependencySet) -> Validity:
    """Valid only while EVERY semantic dependency is unchanged. Identity drift
    (content_sha changed, semantic_sha equal) is recorded, never fatal."""
    reasons, drift = [], []
    for name, old in cached.records.items():
        if name not in current.records:
            reasons.append(f'record {name!r} removed from the set')
            continue
        new = current.records[name]
        if old['semantic_sha'] != new['semantic_sha']:
            reasons.append(f'record {name!r} SEMANTIC change '
                           f'({old["semantic_sha"][:8]} -> {new["semantic_sha"][:8]})')
        elif old['content_sha'] != new['content_sha']:
            drift.append({'record': name, 'kind': 'metadata-only',
                          'old_content_sha': old['content_sha'][:8],
                          'new_content_sha': new['content_sha'][:8]})
    for name in current.records:
        if name not in cached.records:
            reasons.append(f'record {name!r} added to the set')
    if cached.producers != current.producers:
        for name in sorted(set(cached.producers) | set(current.producers)):
            o, n = cached.producers.get(name), current.producers.get(name)
            if o != n:
                reasons.append(f'producer closure edge for {name!r} changed: '
                               f'{(o or {}).get("via")} -> {(n or {}).get("via")}')
    for cls in ('reset', 'numeric_policy', 'domain', 'horizon', 'baseline'):
        if getattr(cached, cls) != getattr(current, cls):
            reasons.append(f'{cls} dependency changed '
                           f'({getattr(cached, cls)[:8]} -> {getattr(current, cls)[:8]})')
    # F-OVER-INVALIDATE guard: an invalidation with NO semantic delta is the
    # falsifier, structurally impossible here but asserted, never silent.
    if reasons and not any('SEMANTIC' in r or 'changed' in r or 'removed' in r
                           or 'added' in r for r in reasons):
        reasons.append(F_OVER_INVALIDATE + ': invalidation without a named '
                       'semantic delta')
    return Validity('VALID' if not reasons else 'INVALIDATED',
                    reasons=reasons, identity_drift=drift)


# ── the evidence cache ───────────────────────────────────────────────────────
class EvidenceCache:
    """Append-only JSONL of cached results, each sealed with its
    DependencySet. Reuse is a CHECK, never an assumption."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[dict] = []
        if self.path.exists():
            for ln in self.path.read_text(encoding='utf-8').splitlines():
                if ln.strip():
                    self._entries.append(json.loads(ln))

    def put(self, key: str, result: dict, deps: DependencySet,
            certificate: dict | None = None) -> dict:
        entry = {'key': key, 'result': result,
                 'deps': deps.canonical() | {'digest': deps.digest},
                 'deps_digest': deps.digest,
                 'certificate': certificate,
                 'sealed_at': time.strftime('%Y-%m-%dT%H:%M:%S')}
        self._entries.append(entry)
        with open(self.path, 'a', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(entry, sort_keys=True, separators=(',', ':')) + '\n')
        return entry

    def lookup(self, key: str, current: DependencySet) -> Validity:
        """The reuse verdict for `key` against the CURRENT dependency set.
        MISS / VALID / INVALIDATED; an INVALIDATED hit names the falsifier
        that a reuse at this moment would fire."""
        hits = [e for e in self._entries if e['key'] == key]
        if not hits:
            return Validity('MISS')
        entry = hits[-1]
        cached = DependencySet(**{k: entry['deps'][k] for k in DEP_CLASSES}).seal()
        if cached.digest != entry['deps_digest']:
            return Validity('INVALIDATED',
                            reasons=['cache entry tampered: sealed digest '
                                     'does not recompute (I3)'],
                            falsifier=F_STALE_CERTIFICATE)
        verdict = check_validity(cached, current)
        if verdict.status == 'INVALIDATED':
            verdict.falsifier = F_STALE_CERTIFICATE
        return verdict

    def entries(self) -> list[dict]:
        return list(self._entries)


# ── the replay-reuse certificate ─────────────────────────────────────────────
INDUCTION_CLAIM = (
    'same-trajectory-by-induction: base — row 0 equals the declared reset/'
    'initial state (measured in the ledger); step — the transition function '
    '(record set + physics + numeric policy) is UNCHANGED and DETERMINISTIC, '
    'and every boundary output and state transition matched BIT-EXACT '
    '(uint64, never decimals) across the certified horizon on the registered '
    'lossless trace; therefore, on the same inputs (the recorded domain), the '
    'trajectory is identical at every tick. SCOPE: in-domain only, certified '
    'horizon only — no claim beyond either.')

REQUIRED_PHYSICS_FIELDS = ('source_tree_digest', 'numeric_policy_sha',
                           'toolchain')
REQUIRED_DETERMINISM_FIELDS = ('double_run_byte_identical', 'rng',
                               'env_or_clock_inputs')


@dataclass
class ReplayMatchLedger:
    """The measured replay match. Floats are compared as uint64 bits; a
    decimal is only round-trip evidence and never the compared artifact."""
    rows: int
    boundary_outputs_checked: int
    state_transitions_checked: int
    bit_pairs_checked: int
    mismatches: list
    lossless: bool
    row0_matches_declared_initial: bool
    horizon_covered: dict          # e.g. {'walk_ticks': 300, 'stop': '...'}

    def complete(self, expected_horizon: dict) -> tuple[bool, list]:
        why = []
        if self.rows <= 0:
            why.append('no rows replayed')
        if self.mismatches:
            why.append(f'{len(self.mismatches)} mismatch(es), first: '
                       f'{self.mismatches[0]}')
        if not self.lossless:
            why.append('match is not lossless (decimal-rounded comparison)')
        if self.boundary_outputs_checked <= 0:
            why.append('no boundary outputs checked')
        if self.state_transitions_checked <= 0:
            why.append('no state transitions checked')
        if self.bit_pairs_checked <= 0:
            why.append('no float bit-pairs checked')
        if not self.row0_matches_declared_initial:
            why.append('row 0 does not equal the declared initial state '
                       '(the induction base)')
        if self.horizon_covered != expected_horizon:
            why.append(f'horizon covered {self.horizon_covered} != '
                       f'expected {expected_horizon}')
        return (not why), why


@dataclass
class ReplayReuseCertificate:
    claim: str
    deps: DependencySet
    match: ReplayMatchLedger
    physics: dict
    determinism: dict
    induction: str
    digest: str = ''

    def canonical(self) -> dict:
        return {'claim': self.claim,
                'deps': self.deps.canonical() | {'digest': self.deps.digest},
                'match': vars(self.match), 'physics': self.physics,
                'determinism': self.determinism, 'induction': self.induction}

    def seal(self) -> 'ReplayReuseCertificate':
        self.digest = _sha(self.canonical())
        return self


def issue_certificate(deps: DependencySet, match: ReplayMatchLedger,
                      physics: dict, determinism: dict,
                      expected_horizon: dict) -> ReplayReuseCertificate:
    """Issue ONLY on a complete lossless match + recorded physics +
    recorded determinism. Anything less refuses (never issues soft)."""
    ok, why = match.complete(expected_horizon)
    if not ok:
        raise ReuseError('certificate REFUSED, match incomplete: ' + '; '.join(why))
    for f in REQUIRED_PHYSICS_FIELDS:
        if not physics.get(f):
            raise ReuseError(f'certificate REFUSED: physics field {f!r} empty '
                             '(the assumption must be recorded, not implied)')
    for f in REQUIRED_DETERMINISM_FIELDS:
        if f not in determinism:
            raise ReuseError(f'certificate REFUSED: determinism field {f!r} '
                             'missing (the assumption must be recorded)')
    if determinism.get('double_run_byte_identical') is not True:
        raise ReuseError('certificate REFUSED: determinism not measured '
                         '(double-run byte identity false/absent)')
    if not deps.digest:
        raise ReuseError('certificate REFUSED: dependency set unsealed')
    return ReplayReuseCertificate(
        claim=INDUCTION_CLAIM, deps=deps, match=match, physics=dict(physics),
        determinism=dict(determinism), induction=INDUCTION_CLAIM).seal()


def grant_rerun_waiver(cert: ReplayReuseCertificate, current: DependencySet,
                       current_physics: dict,
                       expected_horizon: dict) -> dict:
    """The ONLY gate through which a full re-run may be skipped. Every
    SEMANTIC assumption must hold NOW; otherwise REFUSED with the firing
    falsifier NAMED: F-STALE-CERTIFICATE (a semantic dependency changed) or
    F-UNJUSTIFIED-RERUN-SKIP (an assumption does not hold). Identity drift
    (metadata-only) is recorded in the waiver, never fatal — the same rule
    the cache obeys (F-OVER-INVALIDATE's dual)."""
    reasons = []
    current.seal()
    drift: list = []
    if current.digest != cert.deps.digest:
        verdict = check_validity(cert.deps, current)
        if verdict.status == 'INVALIDATED':
            return {'granted': False, 'falsifier': F_STALE_CERTIFICATE,
                    'reasons': ['reuse after a semantic dependency changed '
                                f'({cert.deps.digest[:8]} -> '
                                f'{current.digest[:8]})'],
                    'details': verdict.reasons, 'identity_drift': []}
        drift = verdict.identity_drift      # VALID: metadata-only drift
    for f in REQUIRED_PHYSICS_FIELDS:
        if current_physics.get(f) != cert.physics.get(f):
            reasons.append(f'physics {f!r} changed: {cert.physics.get(f)!r} '
                           f'-> {current_physics.get(f)!r}')
    ok, why = cert.match.complete(expected_horizon)
    if not ok:
        reasons.extend(f'certified match no longer covers: {w}' for w in why)
    if not cert.determinism.get('double_run_byte_identical'):
        reasons.append('certificate determinism unproven')
    if not cert.claim or not cert.induction:
        reasons.append('certificate assumptions not recorded')
    if reasons:
        return {'granted': False, 'falsifier': F_UNJUSTIFIED_RERUN_SKIP,
                'reasons': reasons, 'details': reasons,
                'identity_drift': drift}
    return {'granted': True, 'falsifier': None, 'reasons': [],
            'details': ['every certificate assumption holds: complete lossless '
                        'match, physics unchanged, determinism measured, '
                        'semantic dependencies unchanged, horizon covered'],
            'identity_drift': drift}
