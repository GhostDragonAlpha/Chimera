"""L5 — TRANSITIVE interference THROUGH THE PHYSICS (constraint-ledger lane
agent/cl-L5-transitive-20260921; pre-registration:
tools/science_funnel/validation/cl_L5_20260921/preregistration.json).

The pilot's interference.py is FIRST-ORDER: quantity-set overlap between two
records' own writes and reads. This module adds the closed PHYSICS loop the
spec says pure controller graphs miss:

    law --write--> force output --accumulate--> net force (the SHARED CARRIER)
        --integrate--> body state --guard--> contact guard --sense--> sensor
        --read--> later law --write--> ...   (the loop closes)

NEW FILES ONLY: no existing module is edited (concurrent lanes share this
tree class). schema/expr/interference are imported READ-ONLY.

Node classes (PropGraph.nodes, kind -> what it is):
    law               a concrete (expanded) record with expression effects
    quantity          a typed quantity, subclassed by `qclass`:
        force-output    declared into force accumulation (PhysicsModel)
        body-state      declared integrated from the accumulated net force
        contact-guard   declared evaluated from body state
        sensor          declared sensed from body state / guards
        carrier         a physics stage anchor (phys.net_force)
        controller-sink law-written, consumed by NO physics stage and NO
                        record read (a terminal output)
        external-opaque declared external-input and NOT claimed by any
                        physics stage: unknown code can write it
    (constants are NOT nodes: a fixed constant carries no influence; the
    counterfactual machinery perturbs a law's constant and observes the
    TWIN, which is ground truth for the synthetic universe)

Edge classes (PropGraph.edges, kind):
    write             law -> quantity (the assignment target)
    read-delayed      quantity -> law (bare chimpl read, value at tick start)
    read-sametick     quantity -> law (`now:` read, same-tick ordered)
    physics-flow      quantity -> quantity, carrying a STAGE tag
                      (force-accumulation | body-state | contact-guard |
                       sensor) and the declared summary that licensed it

Influence fixpoint (reach, with EVIDENCE PATHS): a law's reach is its writes
closed under (a) absorption — any OTHER record reading a reached quantity
contributes ITS writes (the controller-expression graph), and (b) the
declared physics-flow edges (the plant), and (c) the conservative opaque
rule — reading an EXTERNAL-OPAQUE quantity means unknown code can steer the
record, so its reach is the FULL universe (the spec: unknown externals
conservatively reach everything). Every reached quantity carries one
witnessed PATH of hops, so an interaction can show HOW influence travels.

Interaction2 verdict per pair (X, Y), asymmetric like the pilot:
    carrier q for direction X->Y  :=  q in reach[X] ∩ (reads_Y ∪ writes_Y)
    class 'direct'  — q in W_X (the pilot's first-order classes:
                      write-write | combinational | stateful)
    class 'physics-carried'    — the witness path used a physics-flow hop
    class 'controller-carried' — the witness path is record reads only
Independent iff NO carrier in EITHER direction. A shared READ is never a
carrier (R_X ∩ R_Y does not appear), so the read/read-only pair stays
independent while the shared-force-carrier pair is flagged THROUGH the
physics edges, not by any direct write.

Falsifier support:
    collapse_stats  — per record set, the fraction of laws whose reach is
        the FULL universe, SPLIT into structural collapse vs opaque-driven
        collapse. F-VACUOUS-CONE fires iff EVERY distinct fixture collapses;
        a full graph is CONSERVATIVE (sound), not useful.
    counterfactual_cover — compares a replayed perturbation's changed-
        observable set against a predicted cone. F-MISSED-COUPLING fires
        iff changed - cone is nonempty (the cone UNDER-approximates: a
        soundness failure). See l5_fixtures.py for the replayable twin and
        l5_real_trace.py for the real-trace leg.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import interference as I1          # the frozen first-order core
from .schema import Record, effects, expand

STAGES = ('force-accumulation', 'body-state', 'contact-guard', 'sensor')
CARRIER = 'phys.net_force'                # the accumulated net force node


class PhysicsError(ValueError):
    pass


# ── declared physics summaries ─────────────────────────────────────────────
@dataclass(frozen=True)
class PhysicsEdge:
    src: str
    dst: str
    stage: str                 # one of STAGES
    kind: str                  # accumulate | integrate | guard | sense
    summary: str = ''          # the declared summary that licensed the edge


@dataclass
class PhysicsModel:
    """The DECLARED physics summaries: which declared quantities flow
    through force accumulation, body-state integration, contact guards,
    sensors — the explicit loop model. Anything external-input NOT claimed
    here is EXTERNAL-OPAQUE (unknown code writable; conservatively reaches
    everything)."""
    force_outputs: tuple = ()
    body_states: tuple = ()
    contact_guards: tuple = ()
    sensors: tuple = ()
    opaque_externals: tuple = ()
    extra_edges: tuple = ()    # additional (src, dst, stage, kind, summary)

    def edges(self) -> list[PhysicsEdge]:
        """The canonical loop edges, explicitly modeled:
        force output -> net force -> body state -> guard -> sensor."""
        out = []
        for f in self.force_outputs:
            out.append(PhysicsEdge(f, CARRIER, 'force-accumulation', 'accumulate',
                                   'declared force output feeds accumulation'))
        for b in self.body_states:
            out.append(PhysicsEdge(CARRIER, b, 'body-state', 'integrate',
                                   'accumulated net force integrates into body state'))
        for g in self.contact_guards:
            for b in self.body_states:
                out.append(PhysicsEdge(b, g, 'contact-guard', 'guard',
                                       'guard evaluated from body state'))
        for s in self.sensors:
            # the sensor senses the GUARDED state (the canonical route:
            # body -> guard -> sensor); with no declared guard it reads the
            # body state directly (the summary must say which)
            for g in self.contact_guards:
                out.append(PhysicsEdge(g, s, 'sensor', 'sense',
                                       'sensor reads the contact guard'))
            if not self.contact_guards:
                for b in self.body_states:
                    out.append(PhysicsEdge(b, s, 'sensor', 'sense',
                                           'sensor reads body state '
                                           '(no guard declared)'))
        for src, dst, stage, kind, summary in self.extra_edges:
            if stage not in STAGES:
                raise PhysicsError(f'extra edge stage {stage!r} not in STAGES')
            out.append(PhysicsEdge(src, dst, stage, kind, summary))
        return out

    def claims(self, q: str) -> bool:
        return (q in self.force_outputs or q in self.body_states
                or q in self.contact_guards or q in self.sensors)


# ── the propagation graph ──────────────────────────────────────────────────
@dataclass(frozen=True)
class Node:
    kind: str                  # 'law' | 'quantity'
    name: str
    qclass: str = ''           # quantity subclass (see module docstring)


@dataclass(frozen=True)
class Edge:
    src: str                   # node name
    dst: str                   # node name
    kind: str                  # write | read-delayed | read-sametick | physics-flow
    stage: str = ''            # physics-flow only
    summary: str = ''


@dataclass
class PropGraph:
    records: list              # concrete (expanded) Records
    physics: PhysicsModel
    nodes: dict = field(default_factory=dict)    # name -> Node
    edges: list = field(default_factory=list)
    reads: dict = field(default_factory=dict)    # law -> (delayed, same-tick)
    writes: dict = field(default_factory=dict)   # law -> set
    opaque: set = field(default_factory=set)
    universe: set = field(default_factory=set)   # influence-capable quantities
    reach: dict = field(default_factory=dict)    # law -> {q: path tuple}
    steered: set = field(default_factory=set)    # laws reading an opaque q

    def path_uses_physics(self, rec_name: str, q: str) -> bool:
        return any(hop[0] == 'physics' for hop in self.reach[rec_name].get(q, ()))

    def path_stages(self, rec_name: str, q: str) -> tuple:
        return tuple(hop[2] for hop in self.reach[rec_name].get(q, ())
                     if hop[0] == 'physics')


def _effects_of(rec: Record):
    return effects(rec)


def build_graph(records: list, physics: PhysicsModel) -> PropGraph:
    """Concrete records (expand before calling) + declared physics ->
    the propagation graph with the influence fixpoint (paths included)."""
    g = PropGraph(records=list(records), physics=physics)
    phys_edges = physics.edges()
    phys_qs = set()
    for e in phys_edges:
        phys_qs.add(e.src)
        phys_qs.add(e.dst)

    for r in records:
        w, rd, rs = _effects_of(r)
        g.writes[r.name] = set(w)
        g.reads[r.name] = (set(rd), set(rs))
        g.nodes[r.name] = Node('law', r.name)

    all_reads = set()
    for rd, rs in g.reads.values():
        all_reads |= rd | rs

    # quantity nodes + their classes
    declared_external = set()
    for r in records:
        for qn, q in r.quantities.items():
            declared_external.add(qn) if q.role == 'external-input' else None
            if qn in g.nodes:
                continue
            if qn == CARRIER or (qn in phys_qs and qn.startswith('phys.')):
                g.nodes[qn] = Node('quantity', qn, 'carrier')
            elif qn in physics.force_outputs:
                g.nodes[qn] = Node('quantity', qn, 'force-output')
            elif qn in physics.body_states:
                g.nodes[qn] = Node('quantity', qn, 'body-state')
            elif qn in physics.contact_guards:
                g.nodes[qn] = Node('quantity', qn, 'contact-guard')
            elif qn in physics.sensors:
                g.nodes[qn] = Node('quantity', qn, 'sensor')
            elif q.role == 'external-input':
                g.nodes[qn] = Node('quantity', qn, 'external-opaque')
            elif qn in all_reads:
                g.nodes[qn] = Node('quantity', qn, 'controller-carrier')
            else:
                g.nodes[qn] = Node('quantity', qn, 'controller-sink')
    for qn in phys_qs:
        if qn not in g.nodes:
            if qn == CARRIER:
                g.nodes[qn] = Node('quantity', qn, 'carrier')
            elif qn in physics.force_outputs:
                g.nodes[qn] = Node('quantity', qn, 'force-output')
            elif qn in physics.body_states:
                g.nodes[qn] = Node('quantity', qn, 'body-state')
            elif qn in physics.contact_guards:
                g.nodes[qn] = Node('quantity', qn, 'contact-guard')
            elif qn in physics.sensors:
                g.nodes[qn] = Node('quantity', qn, 'sensor')
            else:
                g.nodes[qn] = Node('quantity', qn, 'external-opaque')

    # the conservative opaque set: declared opaque_externals PLUS every
    # external-input quantity no physics stage claims (unknown code writes
    # anything the summaries do not explain)
    g.opaque = set(physics.opaque_externals)
    for qn in declared_external:
        if not physics.claims(qn) and qn not in phys_qs:
            g.opaque.add(qn)
    for qn in g.opaque:
        if qn in g.nodes and g.nodes[qn].qclass not in ('carrier',):
            g.nodes[qn] = Node('quantity', qn, 'external-opaque')

    # edges
    for r in records:
        w = g.writes[r.name]
        rd, rs = g.reads[r.name]
        for q in sorted(w):
            g.edges.append(Edge(r.name, q, 'write'))
        for q in sorted(rd):
            g.edges.append(Edge(q, r.name, 'read-delayed'))
        for q in sorted(rs):
            g.edges.append(Edge(q, r.name, 'read-sametick'))
    for e in phys_edges:
        g.edges.append(Edge(e.src, e.dst, 'physics-flow', e.stage, e.summary))

    g.universe = {n.name for n in g.nodes.values() if n.kind == 'quantity'}

    # ── the influence fixpoint, with witness paths ────────────────────────
    def absorb_path(via_q, reader, base_path):
        return base_path + (('absorb', reader, via_q),)

    reach: dict[str, dict[str, tuple]] = {}
    for r in records:
        rd, rs = g.reads[r.name]
        opaque_hits = sorted((rd | rs) & g.opaque)
        if opaque_hits:
            # the conservative rule, at seed time: reading an EXTERNAL-OPAQUE
            # quantity means unknown code can steer this record, so its
            # influence is the FULL universe (every path is tagged 'opaque')
            tag = opaque_hits[0]
            reach[r.name] = {u: (('opaque', tag, '*'),)
                             for u in sorted(g.universe)}
        else:
            reach[r.name] = {q: (('write', r.name, q),)
                             for q in sorted(g.writes[r.name])}

    changed = True
    while changed:
        changed = False
        for r in records:
            cur = reach[r.name]
            frontier = list(cur.items())
            add: dict[str, tuple] = {}
            for q, path in frontier:
                if q in g.opaque:
                    # unknown code steers this record: conservative FULL cone
                    for u in g.universe:
                        if u not in cur and u not in add:
                            add[u] = path + (('opaque', q, '*'),)
                    continue
                # (a) absorption: another record reading q contributes its writes
                for other in records:
                    if other.name == r.name:
                        continue
                    rd_o, rs_o = g.reads[other.name]
                    if q in rd_o or q in rs_o:
                        for wq in sorted(g.writes[other.name]):
                            if wq not in cur and wq not in add:
                                add[wq] = absorb_path(q, other.name, path)
                # (b) physics-flow hops from q
                for e in phys_edges:
                    if e.src == q:
                        hop = ('physics', f'{e.src}->{e.dst}', e.stage, e.kind)
                        if e.dst not in cur and e.dst not in add:
                            add[e.dst] = path + (hop,)
            if add:
                cur.update(add)
                changed = True
    g.reach = reach

    # steering census (diagnostic): laws reading any opaque quantity
    for r in records:
        rd, rs = g.reads[r.name]
        if (rd | rs) & g.opaque:
            g.steered.add(r.name)
    return g


# ── the transitive interaction verdict ─────────────────────────────────────
@dataclass
class Interaction2:
    a: str
    b: str
    carriers: dict = field(default_factory=dict)
    # q -> {'directions': [...], 'classes': [...], 'path_a_to_b': tuple|None,
    #       'path_b_to_a': tuple|None, 'stages_a_to_b': tuple, ...}

    @property
    def independent(self) -> bool:
        return not self.carriers

    @property
    def direct_write_quantities(self) -> set:
        return {q for q, d in self.carriers.items() if 'direct' in d['classes']}


def _first_order_classes(x, y, q) -> list:
    """The pilot's classes when q is in W_X (direct write involvement)."""
    wx, rxd, rxs = _effects_of(x)
    wy, ryd, rys = _effects_of(y)
    out = []
    if q in wx and q in wy:
        out.append('write-write')
    if q in wx and q in rys:
        out.append('combinational')
    if q in wx and q in ryd:
        out.append('stateful')
    return out


def interaction2(x: Record, y: Record, g: PropGraph) -> Interaction2:
    """Transitive verdict for the pair on the graph g. Carriers for X->Y are
    reach[X] ∩ (reads_Y ∪ writes_Y); class 'direct' iff the carrier is X's
    OWN write (then the pilot's first-order subclass), else carried, split
    by whether the witness path used the physics."""
    ix = Interaction2(x.name, y.name)
    rx = g.reach.get(x.name, {})
    ry = g.reach.get(y.name, {})
    _, rxd, rxs = _effects_of(x)
    _, ryd, rys = _effects_of(y)
    touches_y = set(ryd) | set(rys) | set(g.writes.get(y.name, ()))
    touches_x = set(rxd) | set(rxs) | set(g.writes.get(x.name, ()))

    def one_dir(src: Record, dst: Record, reach_src, touches_dst, fwd):
        wx = set(g.writes[src.name])
        for q in sorted(reach_src.keys() & touches_dst):
            if q not in ix.carriers:
                ix.carriers[q] = {'directions': [], 'classes': [],
                                  'path_a_to_b': None, 'path_b_to_a': None,
                                  'stages_a_to_b': (), 'stages_b_to_a': ()}
            entry = ix.carriers[q]
            d = 'X->Y' if fwd else 'Y->X'
            entry['directions'].append(d)
            if q in wx:
                entry['classes'].append('direct')
                for c in (_first_order_classes(x, y, q) if fwd
                          else _first_order_classes(y, x, q)):
                    entry['classes'].append(f'direct:{c}')
            else:
                path = reach_src[q]
                if any(hop[0] == 'opaque' for hop in path):
                    entry['classes'].append('opaque-conservative')
                elif any(hop[0] == 'physics' for hop in path):
                    entry['classes'].append('physics-carried')
                else:
                    entry['classes'].append('controller-carried')
            key_p = 'path_a_to_b' if fwd else 'path_b_to_a'
            key_s = 'stages_a_to_b' if fwd else 'stages_b_to_a'
            if entry[key_p] is None:
                entry[key_p] = reach_src[q]
                entry[key_s] = tuple(h[2] for h in path if h[0] == 'physics')

    one_dir(x, y, rx, touches_y, True)
    one_dir(y, x, ry, touches_x, False)
    for q in list(ix.carriers):
        e = ix.carriers[q]
        e['directions'] = list(dict.fromkeys(e['directions']))
        e['classes'] = list(dict.fromkeys(e['classes']))
    return ix


def matrix2(records: list, g: PropGraph) -> list[Interaction2]:
    out = []
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            out.append(interaction2(records[i], records[j], g))
    return out


# ── usefulness vs soundness instrumentation ────────────────────────────────
def collapse_stats(g: PropGraph) -> dict:
    """F-VACUOUS-CONE instrumentation, per record set. A law is FULL when its
    reach is the whole quantity universe. The REASON is split: a law is
    opaque-driven when some path to fullness used the opaque rule — that is
    the conservative rule doing its job, not a structural claim. A full
    graph is conservative (sound); it is a USEFULNESS failure only when
    every fixture collapses (fired by the caller across fixtures)."""
    n = len(g.records)
    full, opaque_full = [], []
    for r in g.records:
        if set(g.reach.get(r.name, {})) >= g.universe:
            full.append(r.name)
            if any(hop[0] == 'opaque' for path in g.reach[r.name].values()
                   for hop in path):
                opaque_full.append(r.name)
    return {'n_laws': n, 'full': full, 'opaque_full': opaque_full,
            'collapse_fraction': (len(full) / n) if n else 0.0,
            'structural_collapse_fraction':
                ((len(full) - len(opaque_full)) / n) if n else 0.0,
            'steered': sorted(g.steered)}


def external_cone(q: str, g: PropGraph) -> dict:
    """Influence cone of a PERTURBED EXTERNAL (or initial) quantity q: every
    record reading it (delayed/same) joins, its writes with paths, then the
    same closure as reach — plus, conservatively, every opaque quantity
    (unknown code can couple anything the summaries do not explain)."""
    cone: dict[str, tuple] = {q: (('external', q),)}
    changed = True
    while changed:
        changed = False
        for r in g.records:
            rd, rs = g.reads[r.name]
            hits = (rd | rs) & set(cone)
            if not hits:
                continue
            best = min((cone[h] for h in hits), key=len)
            for wq in sorted(g.writes[r.name]):
                if wq not in cone:
                    cone[wq] = best + (('absorb', r.name, sorted(hits)[0]),)
                    changed = True
            for e in g.physics.edges():
                if e.src in cone and e.dst not in cone:
                    cone[e.dst] = cone[e.src] + (
                        ('physics', f'{e.src}->{e.dst}', e.stage, e.kind),)
                    changed = True
        for o in sorted(g.opaque):
            if o not in cone:
                cone[o] = (('opaque', o),)
                changed = True
    return cone


def cone_covers(cone: dict, changed: set) -> tuple[bool, set]:
    """F-MISSED-COUPLING discharge: (covered, misses). Fires iff misses."""
    misses = set(changed) - set(cone)
    return (not misses), misses


# ── frozen-interface compatibility shim ────────────────────────────────────
def physics_edges_of(physics: PhysicsModel) -> list[tuple[str, str]]:
    """The declared summaries flattened to the pilot's (src, dst) form, so
    the frozen interference.build_cone can consume the same declarations."""
    return [(e.src, e.dst) for e in physics.edges()]


def v1_cone(records: list) -> dict:
    """The FIRST-ORDER cone (pilot build_cone, NO physics edges): the
    soundness contrast the lane exists to measure."""
    return I1.build_cone(records, physics_edges=[]).reach
