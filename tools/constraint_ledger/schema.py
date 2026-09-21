"""The record schema (amendment-1): kinds, typed quantities, derived effects.

A record is NOT just a constraint. `kind` is fundamental:
  invariant      a requirement; conjoins: Models(R+{c}) = Models(R) ^ Models(c)
  definition     an executable law; causality + determinacy; composes as
                 STAGED updates (never simultaneous equations over one output)
  contribution   a term of a declared combination operator
  alternative    a competing candidate; stays in the store, selected by an
                 explicit snapshot manifest, never by overwriting
  measurement    a recorded number/series with provenance
  proof          a receipt/test letter

Quantities carry entity, frame, unit, dtype, phase, and role. Reads/writes
are DERIVED from the typed expression (expr.reads / assignment targets) and
CHECKED against the declarations -- a record whose effects escape its
declarations is refused, never silently widened.

Parameterized records declare `params` ({leg} holes); validation and the
calculator operate on EXPANDED concrete instances.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from . import expr as X

KINDS = ('invariant', 'definition', 'contribution', 'alternative', 'measurement', 'proof')
DTYPES = ('f64', 'int', 'bool')
PHASES = ('tick-start', 'decision')   # when the quantity's value is bound in a tick
ROLES = ('external-input', 'state', 'constant')


class RecordError(ValueError):
    pass


@dataclass
class Quantity:
    name: str
    entity: str      # which physical/logical object owns the value
    frame: str       # coordinate frame / reference
    unit: str
    dtype: str       # f64 | int | bool
    phase: str       # tick-start | decision
    role: str        # external-input | state | constant

    def as_decl(self) -> dict:
        return {'entity': self.entity, 'frame': self.frame, 'unit': self.unit,
                'dtype': self.dtype, 'phase': self.phase, 'role': self.role}


@dataclass
class Assignment:
    write: str       # concrete quantity name
    ast: object
    src: str


@dataclass
class Record:
    name: str
    kind: str
    lane: str
    provenance: dict
    falsifier: str
    params: dict                       # hole -> allowed bindings
    quantities: dict                   # template name -> Quantity decl
    assignments: list[Assignment]      # definitions only
    constants: dict                    # name -> {value, provenance}
    initial: dict                      # state quantity -> value
    extra: dict = field(default_factory=dict)
    digest: str = ''

    def content(self) -> dict:
        """The canonical record content (digest input; excludes the digest)."""
        return {
            'name': self.name, 'kind': self.kind, 'lane': self.lane,
            'provenance': self.provenance, 'falsifier': self.falsifier,
            'params': self.params,
            'quantities': {k: v.as_decl() for k, v in sorted(self.quantities.items())},
            'assign': [{'write': a.write, 'expr': a.src} for a in self.assignments],
            'constants': self.constants, 'initial': self.initial,
            **self.extra,
        }

    def canonical_bytes(self) -> bytes:
        return json.dumps(self.content(), sort_keys=True, separators=(',', ':')).encode()


def content_digest(rec: Record) -> str:
    return hashlib.sha256(rec.canonical_bytes()).hexdigest()


# ── parameter expansion ────────────────────────────────────────────────────
def _expand_bindings(params: dict) -> list[dict]:
    """Cartesian bindings of every declared hole (usually exactly one)."""
    if not params:
        return [{}]
    holes = sorted(params)
    combos = [{}]
    for h in holes:
        combos = [dict(c, **{h: b}) for c in combos for b in params[h]]
    return combos


def _subst(template: str, binding: dict) -> str:
    out = template
    for hole, val in binding.items():
        out = out.replace('{' + hole + '}', val)
    if '{' in out and '}' in out:
        raise RecordError(f'unexpanded parameter hole in {out!r} (binding {binding})')
    return out


# ── record construction + validation ──────────────────────────────────────
def load(spec: dict) -> Record:
    """Validate one record spec (template form, {holes} allowed) into a Record."""
    for key in ('name', 'kind', 'lane', 'provenance', 'falsifier'):
        if key not in spec:
            raise RecordError(f'record missing required field {key!r}')
    kind = spec['kind']
    if kind not in KINDS:
        raise RecordError(f'{spec["name"]}: unknown kind {kind!r}')
    quantities = {}
    for qname, d in spec.get('quantities', {}).items():
        for f in ('entity', 'frame', 'unit', 'dtype', 'phase', 'role'):
            if f not in d:
                raise RecordError(f'{spec["name"]}: quantity {qname} missing {f!r}')
        if d['dtype'] not in DTYPES:
            raise RecordError(f'{spec["name"]}: quantity {qname} bad dtype {d["dtype"]!r}')
        if d['phase'] not in PHASES:
            raise RecordError(f'{spec["name"]}: quantity {qname} bad phase {d["phase"]!r}')
        if d['role'] not in ROLES:
            raise RecordError(f'{spec["name"]}: quantity {qname} bad role {d["role"]!r}')
        quantities[qname] = Quantity(qname, d['entity'], d['frame'], d['unit'],
                                     d['dtype'], d['phase'], d['role'])
    assignments = []
    for a in spec.get('assign', []):
        if 'write' not in a or 'expr' not in a:
            raise RecordError(f'{spec["name"]}: assignment needs write+expr')
        assignments.append(Assignment(a['write'], None, a['expr']))
    if kind == 'definition' and not assignments:
        raise RecordError(f'{spec["name"]}: definition with no assignments')
    rec = Record(
        name=spec['name'], kind=kind, lane=spec['lane'],
        provenance=spec['provenance'], falsifier=spec['falsifier'],
        params=dict(spec.get('params', {})), quantities=quantities,
        assignments=assignments, constants=dict(spec.get('constants', {})),
        initial=dict(spec.get('initial', {})),
        extra={k: v for k, v in spec.items()
               if k not in ('name', 'kind', 'lane', 'provenance', 'falsifier',
                            'params', 'quantities', 'assign', 'constants', 'initial')},
    )
    rec.digest = content_digest(rec)
    return rec


def expand(rec: Record) -> list[Record]:
    """Expand parameter holes into concrete instances (a record is its set of
    instances for interference and compilation)."""
    out = []
    for binding in _expand_bindings(rec.params):
        q = {}
        for tname, decl in rec.quantities.items():
            q[_subst(tname, binding)] = Quantity(_subst(tname, binding), decl.entity,
                                                 decl.frame, decl.unit, decl.dtype,
                                                 decl.phase, decl.role)
        assignments = [Assignment(_subst(a.write, binding),
                                  X.parse(_subst(a.src, binding)),
                                  _subst(a.src, binding))
                       for a in rec.assignments]
        inst = Record(
            name=f'{rec.name}[{",".join(f"{k}={v}" for k, v in sorted(binding.items()))}]'
                 if binding else rec.name,
            kind=rec.kind, lane=rec.lane, provenance=rec.provenance,
            falsifier=rec.falsifier, params={}, quantities=q,
            assignments=assignments,
            constants={k: (v if isinstance(v, dict) else {'value': v})
                       for k, v in rec.constants.items()},
            initial={_subst(k, binding): v for k, v in rec.initial.items()},
            extra=dict(rec.extra),
        )
        inst.digest = rec.digest
        out.append(inst)
    return out


def effects(rec: Record) -> tuple[set, set, set]:
    """Derive (writes, delayed_reads, same_tick_reads) from the typed
    expressions. DEFINITIONS only; other kinds have no expression effects."""
    writes, delayed, same = set(), set(), set()
    for a in rec.assignments:
        if a.ast is None:
            a.ast = X.parse(a.src)
        writes.add(a.write)
        d, s = X.reads(a.ast)
        delayed |= d
        same |= s
    return writes, delayed, same


def check_declarations(rec: Record, externals: dict[str, Quantity] | None = None,
                       constants: set[str] | None = None) -> None:
    """Every derived read must resolve to a declared quantity, a declared
    constant, or (when provided) a registered external input; every declared
    `state` quantity written must have an initial value (explicit delayed
    state, amendment-1 item 4). Effects escaping declarations are REFUSED."""
    consts = set(rec.constants) | (constants or set())
    writes, delayed, same = effects(rec)
    known = dict(rec.quantities)
    if externals:
        for n, q in externals.items():
            known.setdefault(n, q)
    for name in delayed | same:
        if name not in known and name not in consts:
            raise RecordError(f'{rec.name}: read of undeclared quantity {name!r}')
    for w in writes:
        if w not in known:
            raise RecordError(f'{rec.name}: writes undeclared quantity {w!r}')
        q = known[w]
        if q.role == 'state' and w not in rec.initial:
            raise RecordError(f'{rec.name}: state write {w!r} without declared initial')
        if q.role == 'external-input':
            raise RecordError(f'{rec.name}: writes external-input quantity {w!r}')
    for qname, q in rec.quantities.items():
        if q.role == 'state':
            if qname not in rec.initial:
                raise RecordError(f'{rec.name}: state quantity {qname!r} lacks initial')
            if qname not in writes:
                raise RecordError(f'{rec.name}: state quantity {qname!r} never written')
    for cname, cval in rec.constants.items():
        if not isinstance(cval, dict) or 'value' not in cval:
            raise RecordError(f'{rec.name}: constant {cname!r} lacks value/provenance')
