"""L6 — infeasibility and named cores (Astra spec L6, lane agent/cl-L6-cores-20260921).

Given a SELECTED set of records, the question L6 answers is: is the selection
FEASIBLE, and if not, WHICH NAMED RECORDS are implicated — an inclusion-minimal
set of record IDs whose constraints alone are already unsat in the exact
background.

Machinery (the spec):
  * every selected record is encoded as an ACTIVATION implication
        enabled_X  =>  constraint_X
    where constraint_X lowers the record into the solver language:
      - kind 'invariant'  -> its `invariant_expr` (chimpl) as a predicate;
      - kind 'definition' -> each assignment as an equation write == rhs
        (a static snapshot feasibility question: one valuation per quantity,
        so `now:` and delayed reads of the same name are the same variable —
        a cycle there is an execution-order refusal, owned by compile.py,
        not a satisfiability answer).
  * solving runs UNDER ACTIVATION ASSUMPTIONS (Z3 check-with-assumptions over
    the implication encoding, so a disabled record's constraint is OFF);
  * on unsat, the solver's raw core is SHRUNK by deletion-based minimization
    in SORTED RECORD-ID ORDER: for each member, recheck unsat after removing
    it; keep the removal only if still unsat. One pass. The result is
    inclusion-minimal (any later removal only shrinks the surviving set, and
    a subset of a satisfiable set is satisfiable), NOT minimum-cardinality.
  * the finding is NAMED by its interaction identity: sha256 over
    {core ids sorted, background-model digest, assumptions sorted, horizon}.

SOLVER CHOICE (honest): Z3 (z3-solver) is INSTALLED for this lane and is the
engine. Scope of the encoding, stated rather than hidden:
  * numeric quantities (dtype f64/int) are modeled as exact Z3 Reals — an
    f64 RELAXATION. Literals in the sealed fixtures are exactly representable
    in f64, and every SAT verdict is BRIDGE-CHECKED in true float64 by
    re-evaluating each record constraint with `expr.evaluate` on the model
    (a model that is not exactly f64-representable refuses the witness —
    it is never silently accepted). An UNSAT verdict is a Real-arithmetic
    fact; falsifier F-CORE-UNSOUND rechecks every reported core by DIRECT
    conjunction in a fresh solver with NO activation machinery.
  * nonlinear arithmetic may return z3.unknown: UNKNOWN IS NEVER CLEARANCE
    (F-FALSE-CLEARANCE's second face: unknown != feasible).
  * `control.step` has no binding in a single-state snapshot — a constraint
    reading it raises UnsupportedFragment, and the record set is reported
    UNKNOWN, never cleared.

RULE 0 PREREG (recorded verbatim in the L6 receipt BEFORE the run; also in
the lane report):
  STATEMENT: encoding each record as enabled_X => constraint_X under
    activation-literal assumptions makes every unsat explainable by an
    inclusion-minimal named set of record IDs whose constraints alone are
    unsat in the exact background theory.
  PREDICTION (unmeasured at prereg time): the triple fixture
    (x=y ^ y=z ^ x!=z) minimizes to exactly {r1,r2,r3} — every pair sat, the
    triple unsat — and the shrunk core rechecks unsat; satisfiable fixtures
    are never reported as cores.
  FALSIFIERS:
    F-CORE-UNSOUND      a reported core is satisfiable in the exact background
                        (direct conjunction, no activation literals, fresh
                        solver — must be unsat, else the lane is VOID);
    F-CORE-NONMINIMAL   a claimed minimal core stays unsat after removing a
                        member (for every member: core-minus-member must be
                        SAT, else minimality was faked);
    F-FALSE-CLEARANCE   an infeasible fixture marked feasible — including the
                        unknown-is-clearance cheat — fires if any sealed-unsat
                        fixture classifies as sat/unknown-clearance.

Run:   python -m tools.constraint_ledger.l6_cores          (writes the receipt)
Test:  python -m unittest tools.constraint_ledger.tests_l6 -v
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from . import expr as X
from .schema import Record, RecordError, content_digest, expand, load

try:
    import z3
    HAVE_Z3 = True
    Z3_VERSION = z3.get_version_string()
except ImportError:                                    # pragma: no cover
    HAVE_Z3 = False
    Z3_VERSION = None

LANE = 'agent/cl-L6-cores-20260921'
RECEIPT_DIR = Path('tools/science_funnel/validation/cl_L6_20260921')
DEFAULT_HORIZON = 'single-state-snapshot@0'
TRAILER = 'Agent: GLM 5.3'


class UnsupportedFragment(Exception):
    """A chimpl construct with no honest binding in the L6 snapshot fragment."""


# ── the background model ───────────────────────────────────────────────────
def background_of(records: list[Record]) -> dict:
    """The shared background: every quantity declaration and every named
    constant, from the record SET. Conflicting re-declarations (same name,
    different shape) refuse — the background must be one model, not a fight."""
    quantities: dict[str, dict] = {}
    constants: dict[str, object] = {}
    for rec in records:
        for inst in expand(rec):
            for qname, decl in inst.quantities.items():
                d = decl.as_decl()
                prev = quantities.get(qname)
                if prev is not None and prev != d:
                    # the L0 interface rule: a producer's own role is
                    # canonical; a consumer re-declaring the same shape as
                    # record-input is ACCEPTED (compile.py's declaration merge)
                    shallow = {k: (None if k == 'role' else d[k]) for k in d}
                    prev_shallow = {k: (None if k == 'role' else prev[k])
                                    for k in prev}
                    roles = {prev['role'], d['role']}
                    if shallow != prev_shallow or not (
                            roles <= {'state', 'record-input'}
                            or roles <= {'external-input', 'record-input'}):
                        raise RecordError(
                            f'background conflict on {qname!r}: '
                            f'{prev} vs {d}')
                    if d['role'] != 'record-input':   # producer's decl wins
                        quantities[qname] = d
                elif prev is None:
                    quantities[qname] = d
            for cname, cval in inst.constants.items():
                v = cval['value'] if isinstance(cval, dict) else cval
                if cname in constants and constants[cname] != v:
                    raise RecordError(f'background constant conflict on {cname!r}')
                constants[cname] = v
    bg = {'quantities': quantities, 'constants': constants,
          'sorts': {q: _sort_of(d['dtype']) for q, d in quantities.items()}}
    return bg


def background_digest(bg: dict) -> str:
    payload = json.dumps(bg, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(payload).hexdigest()


def _sort_of(dtype: str):
    if dtype in ('f64', 'int'):
        return 'real' if HAVE_Z3 else None    # exact-Real relaxation of f64
    if dtype == 'bool':
        return 'bool'
    raise RecordError(f'unknown dtype {dtype!r}')


# ── chimpl AST -> Z3 term ──────────────────────────────────────────────────
def _var(env: dict, name: str):
    if name not in env:
        raise UnsupportedFragment(f'quantity {name!r} not in the background '
                                  f'(unbound reads cannot be solved, only guessed)')
    return env[name]


def translate(ast, env: dict, constants: dict):
    """Lower a parsed chimpl AST to a Z3 term over the background env.
    Numeric quantity -> Real constant; bool quantity -> Bool constant;
    named constants -> inline literals (evaluate() resolves Qty->constants
    only when no delayed binding exists, so the variable wins on clash)."""
    def num(v):
        return z3.RealVal(v)

    def ev(e):
        if isinstance(e, X.Num):
            return num(e.value)
        if isinstance(e, X._BoolLit):
            return z3.BoolVal(e.value)
        if isinstance(e, X.Qty):
            if e.name == 'control.step':
                raise UnsupportedFragment('control.step has no binding in a '
                                          'single-state snapshot')
            if e.name in env:
                return _var(env, e.name)
            if e.name in constants:
                c = constants[e.name]
                return z3.BoolVal(bool(c)) if isinstance(c, bool) else num(c)
            raise UnsupportedFragment(f'unbound name {e.name!r}')
        if isinstance(e, X.NowQty):
            # single-state fragment: same-tick and delayed reads are the
            # same valuation (stated in the module docstring)
            return ev(X.Qty(e.name))
        if isinstance(e, X.Un):
            if e.op == 'not':
                return z3.Not(ev(e.a))
            if e.op == 'neg':
                return -ev(e.a)
            raise UnsupportedFragment(f'unary {e.op!r}')
        if isinstance(e, X.Bin):
            if e.op == 'and':
                return z3.And(ev(e.a), ev(e.b))
            if e.op == 'or':
                return z3.Or(ev(e.a), ev(e.b))
            a, b = ev(e.a), ev(e.b)
            if e.op == '==':
                return a == b
            if e.op == '!=':
                return a != b
            if e.op == '<':
                return a < b
            if e.op == '>':
                return a > b
            if e.op == '<=':
                return a <= b
            if e.op == '>=':
                return a >= b
            if e.op == '+':
                return a + b
            if e.op == '-':
                return a - b
            if e.op == '*':
                return a * b                     # nonlinear -> may be unknown
            if e.op == '/':
                return a / b
            raise UnsupportedFragment(f'binary {e.op!r}')
        if isinstance(e, X.If):
            return z3.If(ev(e.cond), ev(e.then), ev(e.other))
        if isinstance(e, X.Call):
            args = [ev(a) for a in e.args]
            if e.fn in ('min', 'max'):
                if not args:
                    raise UnsupportedFragment(f'{e.fn} of no arguments')
                out = args[0]
                for v in args[1:]:
                    out = z3.If(v < out, v, out) if e.fn == 'min' \
                        else z3.If(v > out, v, out)
                return out
            if e.fn == 'abs':
                a = args[0]
                return z3.If(a >= 0, a, -a)
            if e.fn == 'floor':
                return _floor_of(args[0])
            if e.fn == 'ceil':
                return -_floor_of(-args[0])       # ceil(r) = -floor(-r)
            raise UnsupportedFragment(f'builtin {e.fn!r}')
        raise UnsupportedFragment(f'AST node {e!r}')

    return ev(ast)


def _floor_of(a):
    """floor over the Reals: ToInt truncates toward zero; correct the sign."""
    t = z3.ToReal(z3.ToInt(a))
    return z3.If(a == t, t, z3.If(a > 0, t, t - 1))


# ── record -> constraint term ──────────────────────────────────────────────
def constraint_ast(rec: Record):
    """(kind, [(lhs_name, rhs_ast)]) — the record lowered to constraint form:
    invariants -> [(None, invariant_expr ast)]; definitions -> the assignment
    equations [(write, rhs ast), ...]. Duplicate writes inside one record
    refuse (the one-defining-writer law, mirrored at the record level)."""
    if rec.kind == 'invariant':
        src = rec.extra.get('invariant_expr')
        if not src:
            raise RecordError(f'{rec.name}: invariant record without invariant_expr')
        return 'invariant', [(None, X.parse(src))]
    if rec.kind == 'definition':
        seen = set()
        eqs = []
        for a in rec.assignments:
            if a.write in seen:
                raise RecordError(f'{rec.name}: second write of {a.write!r} '
                                  f'(one defining writer, even locally)')
            seen.add(a.write)
            eqs.append((a.write, X.parse(a.src)))
        return 'definition', eqs
    raise UnsupportedFragment(f'kind {rec.kind!r} carries no L6 constraint '
                              f'(only invariant/definition lower to predicates)')


# ── the activation encoding ────────────────────────────────────────────────
@dataclass
class Encoding:
    solver: object
    assumptions: dict            # record name -> z3 Bool (the enabled_X)
    env: dict                    # quantity name -> z3 const
    constants: dict
    bg: dict
    digest: str
    lowerings: dict              # record name -> (kind, eqs)


def encode(records: list[Record], horizon: str = DEFAULT_HORIZON) -> Encoding:
    """Background + one activation implication per record. The solver itself
    never sees a bare record constraint — only enabled_X => constraint_X."""
    if not HAVE_Z3:
        raise RuntimeError('z3-solver is not installed; L6 refuses to fake a '
                           'solver (the DPLL fallback was NOT needed: z3 5.1.0 '
                           'installed for this lane)')
    bg = background_of(records)
    env, constants = {}, dict(bg['constants'])
    for qname, d in sorted(bg['quantities'].items()):
        env[qname] = z3.Const('q.' + qname, z3.RealSort()
                              if d['dtype'] in ('f64', 'int') else z3.BoolSort())
    solver = z3.Solver()
    lowerings = {}
    for rec in records:
        kind, eqs = constraint_ast(rec)
        lowerings[rec.name] = (kind, eqs)
        enabled = z3.Const('enabled.' + rec.name, z3.BoolSort())
        body = []
        for lhs, rhs in eqs:
            term = translate(rhs, env, constants)
            body.append(term if lhs is None else env[lhs] == term)
        solver.add(z3.Implies(enabled, z3.And(*body)))
    # background sanity: with EVERY record disabled the model must be
    # satisfiable — otherwise cores are unattributable to records at all.
    if solver.check() != z3.sat:
        raise RecordError('background model is itself unsat; refusing to '
                          'attribute a conflict to any record')
    return Encoding(solver=solver, assumptions={}, env=env, constants=constants,
                    bg=bg, digest=background_digest(bg), lowerings=lowerings)


def _assumptions(enc: Encoding, records: list[Record]) -> list:
    return [z3.Const('enabled.' + r.name, z3.BoolSort()) for r in records]


# ── verdicts ───────────────────────────────────────────────────────────────
@dataclass
class Verdict:
    status: str                  # 'sat' | 'unsat' | 'unknown'
    fixture: str
    core: list | None = None     # inclusion-minimal, sorted record IDs
    raw_core: list | None = None
    witness: dict | None = None
    witness_checked: bool = False
    identity: str | None = None
    identity_full: str | None = None
    horizon: str = DEFAULT_HORIZON
    notes: list = field(default_factory=list)

    @property
    def cleared(self) -> bool:
        # UNKNOWN IS NEVER CLEARANCE — the only definition of clearance is a
        # witness-checked sat.
        return self.status == 'sat' and self.witness_checked


def interaction_identity(core_ids: list[str], background_digest_str: str,
                         assumptions: list[str], horizon: str,
                         full: bool = False) -> str:
    payload = {'core': sorted(core_ids), 'background': background_digest_str,
               'assumptions': sorted(assumptions), 'horizon': horizon}
    h = hashlib.sha256(json.dumps(payload, sort_keys=True,
                                  separators=(',', ':')).encode()).hexdigest()
    return h if full else h[:32]


def check(records: list[Record], horizon: str = DEFAULT_HORIZON,
          name: str = '<set>') -> Verdict:
    """The L6 question: solve under ALL activation assumptions; on unsat,
    extract the raw core and shrink it (deletion, sorted-ID order)."""
    enc = encode(records, horizon)
    names = [r.name for r in records]
    v = Verdict(status='unknown', fixture=name, horizon=horizon)
    assumps = _assumptions(enc, records)
    res = enc.solver.check(*assumps)
    if res == z3.sat:
        v.status = 'sat'
        v.witness = _witness(enc, records)
        _bridge_check_witness(v, enc, records)
        v.identity, v.identity_full = None, None   # a clearance names nothing
        return v
    if res == z3.unknown:
        v.status = 'unknown'                       # unknown != feasible
        v.notes.append('z3.unknown — reported UNKNOWN, never cleared')
        return v
    v.status = 'unsat'
    raw = sorted(str(l).split('.', 1)[1] for l in enc.solver.unsat_core())
    if not raw:
        # unreachable given the background-sanity gate, but REFUSE beats invent
        raise RecordError('unsat with an empty core — refusing to report')
    v.raw_core = raw
    core = _minimize(enc, records, raw, horizon)
    v.core = core
    v.identity, v.identity_full = interaction_identity(
        core, enc.digest, names, horizon), interaction_identity(
        core, enc.digest, names, horizon, full=True)
    return v


def _minimize(enc: Encoding, records: list[Record], core: list[str],
              horizon: str) -> list[str]:
    """Deletion-based minimization in SORTED RECORD-ID ORDER: for each member,
    recheck unsat after removing it (one pass; inclusion-minimal result)."""
    current = sorted(core)
    by_name = {r.name: r for r in records}
    for m in sorted(core):
        trial = [x for x in current if x != m]
        s = z3.Solver()
        _add_implications(s, enc, [by_name[n] for n in trial])
        if s.check(*[z3.Const('enabled.' + n, z3.BoolSort()) for n in trial]) \
                == z3.unsat:
            current = trial                        # dispensable: gone
    return current


def _add_implications(solver, enc: Encoding, records: list[Record]) -> None:
    env, constants = enc.env, enc.constants
    for rec in records:
        kind, eqs = enc.lowerings[rec.name]
        enabled = z3.Const('enabled.' + rec.name, z3.BoolSort())
        body = []
        for lhs, rhs in eqs:
            term = translate(rhs, env, constants)
            body.append(term if lhs is None else env[lhs] == term)
        solver.add(z3.Implies(enabled, z3.And(*body)))


# ── the exact-background falsifier harnesses ───────────────────────────────
def direct_conjunction_status(names: list[str], all_records: list[Record]) -> str:
    """NO activation machinery: plain conjunction of the named records'
    constraints over the same background. 'unsat' | 'sat' | 'unknown'."""
    enc = encode(all_records)
    s = z3.Solver()
    by_name = {r.name: r for r in all_records}
    for n in names:
        kind, eqs = enc.lowerings[n]
        for lhs, rhs in eqs:
            term = translate(rhs, enc.env, enc.constants)
            if lhs is None:
                s.add(term)
            else:
                s.add(enc.env[lhs] == term)
    res = s.check()
    if res == z3.sat:
        return 'sat'
    if res == z3.unsat:
        return 'unsat'
    return 'unknown'


def core_is_sound(core: list[str], all_records: list[Record]) -> bool:
    """F-CORE-UNSOUND: the reported core, conjoined DIRECTLY in the exact
    background, must be UNSAT. A sat (or unknown) core is a fabricated one."""
    return direct_conjunction_status(core, all_records) == 'unsat'


def core_is_minimal(core: list[str], all_records: list[Record]) -> bool:
    """F-CORE-NONMINIMAL: EVERY member must be indispensable — core minus any
    member, direct conjunction, must be SAT. A member whose removal leaves
    unsat means the minimizer lied."""
    return all(direct_conjunction_status([x for x in core if x != m],
                                         all_records) == 'sat'
               for m in core)


def _witness(enc: Encoding, records: list[Record]) -> dict:
    model = enc.solver.model()
    vals = {}
    for qname, const in enc.env.items():
        v = model.eval(const, model_completion=True)
        if z3.is_true(v):
            vals[qname] = True
        elif z3.is_false(v):
            vals[qname] = False
        elif z3.is_rational_value(v):
            den = v.denominator_as_long()
            if den != 1:
                raise UnsupportedFragment(
                    f'model value for {qname!r} is {v} — not f64-exact; '
                    f'witness refused, clearance NOT claimed')
            vals[qname] = float(v.numerator_as_long())
        else:
            raise UnsupportedFragment(f'model value for {qname!r} not concrete')
    return vals


def _bridge_check_witness(v: Verdict, enc: Encoding, records: list[Record]) -> None:
    """The float64 bridge: evaluate every record constraint through
    expr.evaluate (true Python float64 / bool semantics) on the model.
    Only a witness that survives THIS is clearance."""
    try:
        for rec in records:
            kind, eqs = constraint_ast(rec)
            for lhs, rhs in eqs:
                got = X.evaluate(rhs, v.witness, v.witness, enc.constants)
                if lhs is None:
                    if got is not True:
                        raise UnsupportedFragment(
                            f'{rec.name}: witness violates the invariant in '
                            f'true float64 (evaluate -> {got!r})')
                else:
                    want = v.get(lhs)
                    if want != got:
                        raise UnsupportedFragment(
                            f'{rec.name}: equation {lhs} == rhs fails in true '
                            f'float64 ({want!r} vs {got!r})')
        v.witness_checked = True
    except UnsupportedFragment as e:
        v.notes.append(f'witness refused ({e}); clearance NOT claimed')
        v.witness_checked = False


# ── sealed fixtures ────────────────────────────────────────────────────────
def _inv(name, expr_src, reads: dict, constants: dict | None = None,
         falsifier='L6 (F-CORE-UNSOUND/F-CORE-NONMINIMAL/F-FALSE-CLEARANCE)'):
    return {
        'name': name, 'kind': 'invariant', 'lane': LANE,
        'provenance': {'spec': 'Astra L6 (infeasibility and named cores)',
                       'lane': LANE},
        'falsifier': falsifier, 'params': {},
        'quantities': {q: dict(d) for q, d in reads.items()},
        'constants': constants or {}, 'initial': {}, 'assign': [],
        'invariant_expr': expr_src,
    }


def _ext(dtype='f64'):
    return {'entity': 'l6.fixture', 'frame': 'none', 'unit': '1',
            'dtype': dtype, 'phase': 'tick-start', 'role': 'external-input'}


def _def(name, write, expr_src, write_decl, reads: dict):
    return {
        'name': name, 'kind': 'definition', 'lane': LANE,
        'provenance': {'spec': 'Astra L6 (infeasibility and named cores)',
                       'lane': LANE},
        'falsifier': 'L6 (F-CORE-UNSOUND/F-CORE-NONMINIMAL/F-FALSE-CLEARANCE)',
        'params': {},
        'quantities': {**{write: write_decl}, **{q: dict(d) for q, d in reads.items()}},
        'constants': {}, 'initial': {write: 0.0},
        'assign': [{'write': write, 'expr': expr_src}],
    }


# the HIGHER-ORDER conflict the spec demands: every pair satisfiable, the
# triple not (x=y ^ y=z ^ x!=z).
_TRIPLE_Q = {'x': _ext(), 'y': _ext(), 'z': _ext()}


def fixtures() -> list[dict]:
    """The sealed fixture sets; `expect` and `expect_core` are the preregistered
    sealed verdicts the run is judged against."""
    return [
        {'name': 'l6_sat_band',
         'records': [
             _inv('l6_band_r1_y_nonneg', 'y >= 0', {'y': _ext()}),
             _inv('l6_band_r2_x_cap', 'x <= 10', {'x': _ext()}),
             _inv('l6_band_r3_sum', 'x + y <= 20', {'x': _ext(), 'y': _ext()}),
         ],
         'expect': 'sat', 'expect_core': None},
        {'name': 'l6_pair_bound',
         'records': [
             _inv('l6_pair_r1_lo', 'x <= 5', {'x': _ext()}),
             _inv('l6_pair_r2_hi', 'x >= 10', {'x': _ext()}),
         ],
         'expect': 'unsat', 'expect_core': ['l6_pair_r1_lo', 'l6_pair_r2_hi']},
        {'name': 'l6_triple_eq_neq',
         'records': [
             _inv('l6_triple_r1_xy', 'x == y', _TRIPLE_Q),
             _inv('l6_triple_r2_yz', 'y == z', _TRIPLE_Q),
             _inv('l6_triple_r3_xneqz', 'x != z', _TRIPLE_Q),
         ],
         'expect': 'unsat',
         'expect_core': ['l6_triple_r1_xy', 'l6_triple_r2_yz',
                         'l6_triple_r3_xneqz']},
        {'name': 'l6_herring',
         'records': [
             _inv('l6_herr_r1_noise', 'w >= 0', {'w': _ext()}),
             _inv('l6_herr_r2_lo', 'x <= 5', {'x': _ext()}),
             _inv('l6_herr_r3_hi', 'x >= 10', {'x': _ext()}),
         ],
         'expect': 'unsat', 'expect_core': ['l6_herr_r2_lo', 'l6_herr_r3_hi']},
        {'name': 'l6_def_gap',
         'records': [
             _def('l6_gap_d1_tsum', 't', 'a + b',
                  {'entity': 'l6.fixture', 'frame': 'none', 'unit': '1',
                   'dtype': 'f64', 'phase': 'decision', 'role': 'state'},
                  {'a': _ext(), 'b': _ext()}),
             _inv('l6_gap_i1_a', 'a <= 1', {'a': _ext()}),
             _inv('l6_gap_i2_b', 'b <= 2', {'b': _ext()}),
             _inv('l6_gap_i3_t', 't >= 5',
                  {'t': {'entity': 'l6.fixture', 'frame': 'none', 'unit': '1',
                         'dtype': 'f64', 'phase': 'decision',
                         'role': 'record-input'}}),
         ],
         'expect': 'unsat',
         'expect_core': ['l6_gap_d1_tsum', 'l6_gap_i1_a', 'l6_gap_i2_b',
                         'l6_gap_i3_t']},
    ]


def fixture_digest(fix: dict) -> str:
    recs = [load(spec) for spec in fix['records']]
    payload = json.dumps({
        'fixture': fix['name'],
        'records': sorted(r.digest for r in recs),
        'expect': fix['expect'], 'expect_core': fix['expect_core'],
        'horizon': DEFAULT_HORIZON,
    }, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(payload).hexdigest()


# ── the run + receipt ──────────────────────────────────────────────────────
PREREG = {
    'statement': 'encoding each record as enabled_X => constraint_X under '
                 'activation-literal assumptions makes every unsat explainable '
                 'by an inclusion-minimal named set of record IDs whose '
                 'constraints alone are unsat in the exact background theory',
    'prediction': 'the triple fixture (x=y ^ y=z ^ x!=z) minimizes to exactly '
                  '{r1,r2,r3} — every pair sat, the triple unsat — and the '
                  'shrunk core rechecks unsat; satisfiable fixtures are never '
                  'reported as cores',
    'falsifiers': {
        'F-CORE-UNSOUND': 'a reported core is satisfiable in the exact '
                          'background (direct conjunction, no activation '
                          'literals, fresh solver) — VOID if it fires',
        'F-CORE-NONMINIMAL': 'a claimed minimal core stays unsat after '
                             'removing a member (every member must be '
                             'indispensable: core-minus-member SAT)',
        'F-FALSE-CLEARANCE': 'an infeasible fixture marked feasible; unknown '
                             'is never clearance',
    },
}


def run_all() -> dict:
    """Run every sealed fixture, then the falsifier harness over everything
    reported. Returns the receipt payload (numbers included)."""
    results, falsifiers = [], {
        'F-CORE-UNSOUND': {'cores_rechecked': 0, 'violations': 0},
        'F-CORE-NONMINIMAL': {'members_rechecked': 0, 'violations': 0},
        'F-FALSE-CLEARANCE': {'sealed_unsat_fixtures': 0,
                              'false_clearances': 0,
                              'unknown_clearance_attempts': 0},
    }
    for fix in fixtures():
        recs = [load(spec) for spec in fix['records']]
        v = check(recs, name=fix['name'])
        row = {'fixture': fix['name'], 'sealed_digest': fixture_digest(fix),
               'expect': fix['expect'], 'expect_core': fix['expect_core'],
               'status': v.status, 'core': v.core, 'raw_core': v.raw_core,
               'n_records': len(recs), 'horizon': v.horizon,
               'witness_checked': v.witness_checked, 'notes': v.notes}
        if v.identity_full:
            row['identity'] = v.identity_full
        if fix['expect'] == 'unsat':
            falsifiers['F-FALSE-CLEARANCE']['sealed_unsat_fixtures'] += 1
            if v.cleared:
                falsifiers['F-FALSE-CLEARANCE']['false_clearances'] += 1
            if v.status == 'unknown':
                falsifiers['F-FALSE-CLEARANCE']['unknown_clearance_attempts'] += 1
        if v.core is not None:
            ok_sound = core_is_sound(v.core, recs)
            ok_min = core_is_minimal(v.core, recs)
            falsifiers['F-CORE-UNSOUND']['cores_rechecked'] += 1
            falsifiers['F-CORE-NONMINIMAL']['members_rechecked'] += len(v.core)
            if not ok_sound:
                falsifiers['F-CORE-UNSOUND']['violations'] += 1
            if not ok_min:
                falsifiers['F-CORE-NONMINIMAL']['violations'] += len(v.core)
            row['core_direct_conjunction_unsat'] = ok_sound
            row['every_member_indispensable'] = ok_min
        results.append(row)
    # the prediction, checked against the sealed triple
    triple = next(r for r in results if r['fixture'] == 'l6_triple_eq_neq')
    prediction_held = (triple['core'] == triple['expect_core']
                       and triple['core_direct_conjunction_unsat']
                       and triple['every_member_indispensable'])
    # pair-satisfiability of the triple: the spec's higher-order demand
    triple_records = {load(s).name: load(s) for s in
                      next(f for f in fixtures()
                           if f['name'] == 'l6_triple_eq_neq')['records']}
    pairs = {}
    ids = sorted(triple_records)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            pairs[f'{ids[i]}+{ids[j]}'] = direct_conjunction_status(
                [ids[i], ids[j]], list(triple_records.values()))
    return {
        'protocol': 'chimera-record-pilot-v1', 'lane': 'L6',
        'lane_branch': LANE, 'date': '2026-09-21',
        'base': 'agent/cl-L0-baseline-20260921 @ 7181b8ce',
        'prereg': PREREG,
        'solver': {'engine': 'z3 (z3-solver)', 'version': Z3_VERSION,
                   'installed_for_lane': HAVE_Z3,
                   'dpll_fallback': 'NOT NEEDED and NOT USED — z3 installed; '
                                    'stating so per spec'},
        'scope': 'numeric quantities are an exact-Real relaxation of f64/int; '
                 'every SAT verdict is bridge-checked in true float64 via '
                 'expr.evaluate (inexact models refuse the witness); UNSAT '
                 'cores are rechecked by DIRECT conjunction in the exact '
                 'background; unknown is never clearance',
        'fixtures': results,
        'triple_pair_satisfiability': pairs,
        'prediction_held': prediction_held,
        'falsifiers': falsifiers,
        'falsifiers_all_green': (
            falsifiers['F-CORE-UNSOUND']['violations'] == 0
            and falsifiers['F-CORE-NONMINIMAL']['violations'] == 0
            and falsifiers['F-FALSE-CLEARANCE']['false_clearances'] == 0
            and falsifiers['F-FALSE-CLEARANCE']['unknown_clearance_attempts'] == 0
            and prediction_held),
        'trailer': TRAILER,
    }


def main() -> Path:
    payload = run_all()
    out = Path(__file__).resolve().parents[2] / RECEIPT_DIR
    out.mkdir(parents=True, exist_ok=True)
    path = out / 'receipt.json'
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + '\n',
                    encoding='utf-8')
    print(f"L6 receipt: {path}")
    print(f"  falsifiers_all_green: {payload['falsifiers_all_green']}")
    for row in payload['fixtures']:
        print(f"  {row['fixture']}: {row['status']} core={row['core']} "
              f"(raw {row['raw_core']})")
    print(f"  triple pairs: {payload['triple_pair_satisfiability']}")
    return path


if __name__ == '__main__':
    main()
