"""The interference calculator (the math core, amendment-1 item 3).

ASYMMETRIC independence: X and Y are independent iff

    W_X ∩ (R_Y ∪ W_Y) = ∅   AND   W_Y ∩ (R_X ∪ W_X) = ∅

Shared reads are HARMLESS (R_X ∩ R_Y never appears). Overlap is a POTENTIAL
conflict, never proof of one: the operational discharge is a witness search,
∃s: Obs(F_X(F_Y(s))) != Obs(F_Y(F_X(s))) (Servois-style commutativity; here
fixture-based — SMT is successor lane L4). Every interfering pair carries its
NAMED interaction quantities and a per-quantity class:

    write-write        q in W_X ∩ W_Y
    combinational      q written by one and `now:`-read by the other
                       (a same-tick ordering edge — resolvable by the
                       fragment's declared dependency, which is a property of
                       the record SET, not of the append history)
    stateful           q written by one and delayed-read by the other
                       (explicit delayed state across ticks)

Transitive propagation walks declared dependency EDGES: controller-expression
edges (from the effects) PLUS registered physics edges (law → force → body
state → contact guard → load-share sensor → later law). Unknown externals are
conservatively opaque: they reach every quantity registered as externally
writable.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Interaction:
    a: str
    b: str
    quantities: dict          # qname -> class  (the named interaction term)
    directions: dict          # qname -> list of direction labels

    @property
    def independent(self) -> bool:
        return not self.quantities


def _fx(record):
    from .schema import effects  # local import: schema <-> interference leaf
    return effects(record)


def interaction(x, y) -> Interaction:
    """The asymmetric pairwise test on concrete (expanded) records."""
    wx, rxd, rxs = _fx(x)
    wy, ryd, rys = _fx(y)
    rx, ry = rxd | rxs, ryd | rys
    hit_a = wx & (ry | wy)    # x's writes feed y
    hit_b = wy & (rx | wx)    # y's writes feed x
    if not hit_a and not hit_b:
        return Interaction(x.name, y.name, {}, {})
    quantities, directions = {}, {}
    for q in sorted(hit_a | hit_b):
        cls = []
        dirs = []
        if q in wx and q in wy:
            cls.append('write-write')
            dirs.append('X<->Y')
        else:
            if q in wx and q in ry:
                cls.append('combinational' if q in rys else 'stateful')
                dirs.append('X->Y')
            if q in wx and q in wy:      # (already covered above)
                pass
            if q in wy and q in rx:
                cls.append('combinational' if q in rxs else 'stateful')
                dirs.append('Y->X')
        # de-duplicate preserving order
        quantities[q] = '+'.join(dict.fromkeys(cls))
        directions[q] = list(dict.fromkeys(dirs))
    return Interaction(x.name, y.name, quantities, directions)


def matrix(records: list) -> list[Interaction]:
    """All pairwise interactions (i<j); order-free — [X,Y] vs [Y,X] is the
    same named term with directions labeled."""
    out = []
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            out.append(interaction(records[i], records[j]))
    return out


# ── transitive cone (controller edges + registered physics edges) ──────────
@dataclass
class Cone:
    reach: dict = field(default_factory=dict)   # record name -> set of quantities it can influence

    def influenced(self, rec_name: str, q: str) -> bool:
        return q in self.reach.get(rec_name, set())


def build_cone(records: list, physics_edges: list[tuple[str, str]],
               externals: list[str] | None = None) -> Cone:
    """Fixpoint over: X writes q -> q; X now:-reads q' (same-tick, immediate)
    and delayed-reads q' (next tick, still reaches eventually) where q' is
    influenced by someone; plus the declared physics edges (force, body
    state, contact guards, sensors). Unknown externals (opaque writers) reach
    every quantity in `externals`."""
    writes = {}
    for r in records:
        wx, _, _ = _fx(r)
        for q in wx:
            writes.setdefault(q, set()).add(r.name)
    influence = {r.name: set(_fx(r)[0]) for r in records}     # own writes
    # opaque externals: any record reading them may be influenced arbitrarily
    external_qs = set(externals or ())
    changed = True
    while changed:
        changed = False
        for r in records:
            wx, rd, rs = _fx(r)
            cur = influence[r.name]
            add = set()
            for q in rd | rs:
                for other, reach in influence.items():
                    if other != r.name and q in reach:
                        add |= wx
                if q in external_qs:
                    add |= wx
            # physics edges: (src, dst) — an influenced src influences dst
            for src, dst in physics_edges:
                if src in cur or src in external_qs:
                    add.add(dst)
            new = cur | add
            if new != cur:
                influence[r.name] = new
                changed = True
    return Cone(reach=influence)


# ── witness search (fixture-based commutativity discharge) ────────────────
def commutativity_witness(step_x, step_y, fixtures: list[dict], observe) -> dict | None:
    """Search fixtures for s with Obs(F_X(F_Y(s))) != Obs(F_Y(F_X(s))).
    step_x/step_y: state -> state (the two records' staged updates);
    observe: state -> the comparison tuple (output AND next-state bits).
    Returns the witness fixture (with both observations) or None."""
    for s in fixtures:
        a = observe(step_x(step_y(dict(s))))
        b = observe(step_y(step_x(dict(s))))
        if a != b:
            return {'fixture': s, 'obs_x_after_y': a, 'obs_y_after_x': b}
    return None
