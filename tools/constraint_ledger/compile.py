"""The fragment compiler (amendment-1 item 4).

Takes a record SET (the accepted snapshot manifest's selection) and lowers it
to a deterministic tick-step function:

  * acyclic within a tick over same-tick (`now:`) edges;
  * explicit delayed state: bare reads are previous-tick values, carried by
    the fragment's own state — never reset from the reference mid-run;
  * ONE defining writer per quantity-version: a second writer is REJECTED
    (alternatives are selected by a manifest before compilation, never
    silently overwritten; contributions to a declared combination operator
    are successor-lane machinery);
  * unspecified initial state or underdetermined outputs are REJECTED;
  * quantity phase (tick-start vs decision) fixes the row alignment of every
    external read (the tick convention the P2 replay tests against).

Definitions execute; invariants are assertions carried alongside (checked
elsewhere, never silently turned into equations).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import expr as X
from .schema import Record, RecordError, effects, expand


@dataclass
class Fragment:
    instances: list[Record]                    # deterministic execution order
    externals: dict[str, dict]                 # qname -> decl (with phase)
    constants: dict[str, float]
    initial: dict[str, object]
    order_report: list[str] = field(default_factory=list)

    def state_keys(self) -> list[str]:
        return sorted(self.initial)


def _assign_order(rec: Record) -> list:
    """Topological order of a record's own assignments over same-tick edges."""
    writes = {}
    for idx, a in enumerate(rec.assignments):
        for q in {a.write}:
            writes.setdefault(q, []).append(idx)
    edges = [set() for _ in rec.assignments]
    for i, a in enumerate(rec.assignments):
        _, same = X.reads(a.ast)
        for q in same:
            for j in writes.get(q, ()):
                if j != i:
                    edges[j].add(i)     # j must run before i
    order, done = [], set()

    def visit(idx, stack):
        if idx in done:
            return
        if idx in stack:
            raise RecordError(f'{rec.name}: instantaneous cycle through assignments '
                              f'{sorted(stack)}')
        stack.add(idx)
        for nxt in sorted(edges[idx]):
            visit(nxt, stack)
        stack.discard(idx)
        done.add(idx)
        order.append(idx)

    for i in range(len(rec.assignments)):
        visit(i, set())
    return [rec.assignments[i] for i in order]


def compile_fragment(records: list[Record], externals: dict[str, dict],
                     global_constants: dict[str, float]) -> Fragment:
    """records: CONCRETE (expanded) definition instances selected by the
    manifest. externals: qname -> {entity, frame, unit, dtype, phase, role}
    for every externally produced quantity the fragment reads."""
    instances = []
    all_quantities: dict[str, dict] = {}
    writers: dict[str, str] = {}
    initial: dict[str, object] = {}
    constants = dict(global_constants)

    for spec in records:
        for inst in expand(spec):
            instances.append(inst)

    # declaration merge: same name, same declared shape. A producer's own
    # role (state/external-input) is canonical; consumers declare the same
    # quantity as record-input — identical otherwise is ACCEPTED.
    def _canon(d):
        d = dict(d)
        return d

    for inst in instances:
        for qname, decl in inst.quantities.items():
            d = decl.as_decl()
            if qname in all_quantities:
                prev = all_quantities[qname]
                roles = {prev['role'], d['role']}
                shallow = {k: (None if k == 'role' else d[k]) for k in d}
                prev_shallow = {k: (None if k == 'role' else prev[k]) for k in prev}
                if shallow != prev_shallow or not (
                        roles <= {'state', 'record-input'}
                        or roles <= {'external-input', 'record-input'}):
                    raise RecordError(f'quantity {qname!r} declared twice with '
                                      f'different types: {prev} vs {d}')
                if d['role'] != 'record-input':   # producer's decl wins
                    all_quantities[qname] = d
            else:
                all_quantities[qname] = d
    # writers: one defining writer per quantity-version
    for inst in instances:
        wx, _, _ = effects(inst)
        for q in wx:
            if q in writers:
                raise RecordError(f'ambiguous writers for {q!r}: {writers[q]!r} and '
                                  f'{inst.name!r} (select alternatives by manifest)')
            writers[q] = inst.name
    # reads resolve; state initials collected; per-record constants merged
    for inst in instances:
        for cname, cval in inst.constants.items():
            v = cval['value'] if isinstance(cval, dict) else cval
            if cname in constants and float(constants[cname]) != float(v):
                raise RecordError(f'constant conflict on {cname!r}: '
                                  f'{constants[cname]!r} vs {v!r}')
            constants[cname] = v
    for inst in instances:
        wx, rd, rs = effects(inst)
        for name in rd | rs:
            if name in inst.quantities or name in constants or name in externals \
                    or name == 'control.step':
                continue
            raise RecordError(f'{inst.name}: read of undeclared quantity {name!r}')
        for w in wx:
            if w in externals and externals[w].get('role') == 'external-input':
                raise RecordError(f'{inst.name}: writes external input {w!r}')
        for qname, val in inst.initial.items():
            if qname in initial and initial[qname] != val:
                raise RecordError(f'initial conflict on {qname!r}')
            initial[qname] = val
        for a in inst.assignments:
            if a.ast is None:
                a.ast = X.parse(a.src)
        inst.__dict__['_ordered'] = _assign_order(inst)
    # same-tick dependency edges between instances -> deterministic topo order
    dep = {inst.name: set() for inst in instances}
    by_write = {}
    for inst in instances:
        wx, _, _ = effects(inst)
        for q in wx:
            by_write.setdefault(q, set()).add(inst.name)
    for inst in instances:
        _, _, rs = effects(inst)
        for q in rs:
            for producer in by_write.get(q, ()):
                if producer != inst.name:
                    dep[inst.name].add(producer)   # producer before reader
    order: list[Record] = []
    temp: set[str] = set()
    seen: set[str] = set()

    def visit(name: str):
        if name in seen:
            return
        if name in temp:
            raise RecordError(f'instantaneous cycle in fragment at {name!r} '
                              f'(same-tick edges {sorted(dep)})')
        temp.add(name)
        for d in sorted(dep[name]):
            visit(d)
        temp.discard(name)
        seen.add(name)
        order.append(next(i for i in instances if i.name == name))

    for inst in instances:
        visit(inst.name)
    report = [i.name for i in order]
    return Fragment(instances=order, externals=externals,
                    constants=constants, initial=initial, order_report=report)


def outputs_of(frag: Fragment, state: dict, row_prev: dict, row_now: dict,
               step_index: int) -> tuple[dict, dict]:
    """(same-tick computed values, next state) — the observation tuple used by
    the replay and the witness search. Alignment: phase 'tick-start' externals
    read row_prev; phase 'decision' read row_now (the registered tick
    convention). Record-carried state is the fragment's OWN memory — never
    reset from the reference mid-run."""
    delayed: dict = dict(state)
    same: dict = {}
    delayed['control.step'] = step_index
    for qname, decl in frag.externals.items():
        row = row_now if decl.get('phase') == 'decision' else row_prev
        if qname in row:
            delayed[qname] = row[qname]
    for a_rec in frag.instances:
        for a in a_rec.__dict__['_ordered']:
            same[a.write] = X.evaluate(a.ast, delayed, same, frag.constants)
    next_state = dict(state)
    for qname in frag.state_keys():
        if qname in same:
            next_state[qname] = same[qname]
    return same, next_state


def tick(frag: Fragment, state: dict, row_prev: dict, row_now: dict,
         step_index: int) -> dict:
    """Advance one tick; returns the fragment's next state."""
    _, next_state = outputs_of(frag, state, row_prev, row_now, step_index)
    return next_state
