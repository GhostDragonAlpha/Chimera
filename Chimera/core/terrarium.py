"""terrarium — STAGE 0. Grow an organism from a genome.

A pure function. No engine, no graph, no gate, no pipeline. Genome in, geometry
out. See docs/TERRARIUM_DESIGN.md.

The two rules that make this safe live HERE, in code, not in comments:

  RULE 2 — TOTALITY.     grow() is a `for` loop with a hard symbol cap. There is no
                         `while`, no recursion, and no genome — valid, malformed, or
                         adversarial — that can make it fail to terminate. Runaway
                         growth is not a bug we guard against; it is a state that
                         cannot be expressed. test_terrarium proves it with a genome
                         that *tries* to explode.

  RULE 3 — DETERMINISM.  grow(genome, seed) is pure: no clock, no global RNG, no
                         I/O. Same inputs -> byte-identical mesh. Every creature and
                         every bug is reproducible.

  RULE 1 — THE MEMBRANE. This module imports NOTHING from the studio: no
                         graphify_record, no world_store, no task_board, no capcom.
                         It cannot write to the studio's genome even by accident.
                         test_terrarium asserts the import list.

Zero dependencies in the core. numpy/skimage are used ONLY by the optional `blob`
mesher, because totality and determinism are far easier to *prove* over pure Python
than to argue about across a library upgrade.

THE GENOTYPE -> PHENOTYPE MAP is INDIRECT: the genome is a RECIPE (a rewriting
grammar), never a BLUEPRINT (a list of vertices). That is the single decision this
whole idea stands on. A human genome is ~750 MB and specifies ~37 trillion cells;
that is not storage, it is a generative rule set. If gene 17 meant "the position of
the left elbow" this would not scale, would not evolve, and would never surprise you.

CLI
---
    python -m core.terrarium seed  --out g.json
    python -m core.terrarium grow  --genome g.json --seed 7 --mesh tubes|blob
    python -m core.terrarium sheet --genome g.json --n 24     # Stage 1 preview
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass, asdict, field
from pathlib import Path

# --- THE WALLS (Rule 2). These are the reason runaway growth is unrepresentable. --
MAX_DEPTH = 12          # derivation iterations. A `for` bound. It cannot run a 13th.
MAX_SYMBOLS = 50_000    # phenotype complexity ceiling. Hard truncation.
MAX_BONES = 20_000      # belt-and-braces on the interpreter.
MAX_MIRRORS = 256       # bilateral expansions. Each pass removes one '(' — bounded.

# A bone may not be fatter than this fraction of its own length. Without it, '#'
# is a free-mass exploit: mass goes as r^2, so an optimiser inflates ONE bone into
# a boulder, hoists it up a pole, and calls it a body. (Observed 2026-07-14: the
# very first evolutionary run produced exactly that lollipop in three seconds.)
# Real bones have aspect ratios. So do these.
MAX_ASPECT = 0.35

# Phyllotaxis. The golden angle — exactly how a plant arranges leaves so that none
# shades another (core/fractal_spiral.py already places the studio's own features on
# this law). Applied as a roll on every branch, successive limbs never stack up.
#
# It is a PLANT law. A bilaterian must switch it OFF (branch_twist = 0): spiralling
# your limbs around the body axis is the one thing an animal must not do.
GOLDEN_ANGLE = 137.50776405003785

# Mirror across the sagittal plane: YAW and ROLL flip, PITCH does not. Down is down
# for both sides of an animal; left/right is what reverses.
_MIRROR = str.maketrans("+-<>", "-+><")


# --- genome ------------------------------------------------------------------

@dataclass(frozen=True)
class Genome:
    """A RECIPE. ~600 bytes of JSON that unfolds into a body.

    A TREE IS A RECURSION; A CREATURE IS A CASCADE. The default rules below say
    `A -> ...A` — A calls A — and self-similarity IS the definition of a plant:
    every branch is a smaller tree. It cannot make anything else.

    An animal is a finite staged program — C -> S1 -> S2 -> S3 -> tail — where each
    symbol fires ONCE and hands off to a DIFFERENT one. That is what Hox genes do:
    positional identity. Segment 3 knows it is segment 3, which is why a fly's
    thorax grows wings and its abdomen does not, from one genome. See Genome.quadruped().
    """
    axiom: str = "A"
    # symbol -> production, or a list of (production, weight) for stochastic rules.
    # Stochastic rules are what make `seed` mean something: one genome, a family of
    # individuals, exactly as development is noisy in a real organism.
    rules: dict = field(default_factory=lambda: {
        "A": [["F[+B]~!F[-B]~!A", 0.6], ["F[&B]~!F[^B]~!A", 0.4]],
        "B": [["F[+A]~!B", 0.5], ["F[^A]~!B", 0.5]],
    })
    depth: int = 6
    angle: float = 28.0          # yaw/pitch, degrees
    twist: float = GOLDEN_ANGLE  # roll applied by an explicit < or >
    length: float = 1.0
    decay: float = 0.82          # length multiplier applied by ~
    radius: float = 0.10
    radius_decay: float = 0.72   # radius multiplier applied by ! (and / by #)

    # --- body-plan parameters. Defaults reproduce the plant EXACTLY. ---------
    pitch0: float = 0.0          # initial pitch. 0 = grow up (a tree).
                                 # ~90 = a horizontal body axis (an animal).
    branch_twist: float = GOLDEN_ANGLE   # auto-roll on '['. 0 = bilateral, not spiral.
    branch_len: float = 0.82     # auto length mult on '['. 1.0 = limbs keep their length.
    branch_rad: float = 0.72     # auto radius mult on '['. 1.0 = limbs keep their girth.
    seg_taper: float = 0.0       # per-segment radius mult. 0 = derive from
                                 # radius_decay**0.5 — a plant BRANCH tapers to its
                                 # tip, and that assumption was baked into the
                                 # interpreter. 1.0 = no taper: a SPINE keeps its
                                 # girth. Girth becomes explicit (! thins, # thickens),
                                 # which is what lets a body have a fat torso and
                                 # thin legs instead of one monotonic cone.

    @staticmethod
    def quadruped() -> "Genome":
        """A CASCADE, not a recursion. Nothing here calls itself, so the program
        terminates on its own — MAX_DEPTH is a backstop, not the mechanism."""
        return Genome(
            axiom="C",
            rules={
                "C":  "T S",              # tail stub, then the spine
                "S":  "F F (G) F F (H) F N",   # spine: fore limbs, aft limbs, neck
                "G":  "++&&&!F K",        # fore limb: yaw OUT, pitch DOWN, thin
                "H":  "++&&&!F K",        # aft limb (same organ, different position)
                "K":  "&F P",             # knee
                "P":  "^^F",              # foot
                "N":  "^F # F",           # neck up, then a thicker head
                "T":  "!!F",              # tail
            },
            # The cascade is C->S->G->K->P: five levels. Give it room. Note what
            # a cascade buys you — once every symbol is terminal, FURTHER PASSES
            # CHANGE NOTHING. A fractal plant grows more detail forever; a body
            # finishes. Depth stops being a dial and becomes a backstop.
            depth=7,
            angle=26.0,
            length=0.9,
            radius=0.16,
            radius_decay=0.62,
            pitch0=90.0,        # lie the body down
            branch_twist=0.0,   # NO phyllotaxis — a bilaterian must not spiral
            branch_len=1.0,     # limbs keep their length
            branch_rad=1.0,     # limbs keep their girth (thinning is explicit, via !)
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @staticmethod
    def from_json(text: str) -> "Genome":
        return Genome(**json.loads(text))


@dataclass
class Bone:
    parent: int
    p0: tuple
    p1: tuple
    r0: float
    r1: float
    depth: int


# --- vector plumbing (pure python, so determinism is obvious) -----------------

def _sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def _add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def _mul(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def _dot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _norm(v):
    m = math.sqrt(_dot(v, v))
    return (0.0, 0.0, 1.0) if m < 1e-12 else (v[0]/m, v[1]/m, v[2]/m)


def _rot(v, axis, ang):
    """Rodrigues rotation of v about a unit axis."""
    c, s = math.cos(ang), math.sin(ang)
    return _add(_add(_mul(v, c), _mul(_cross(axis, v), s)),
                _mul(axis, _dot(axis, v) * (1.0 - c)))


# --- RULE 2: growth, and it is TOTAL -----------------------------------------

def _pick(prod, rng: random.Random) -> str:
    """A production may be a plain string or weighted alternatives."""
    if isinstance(prod, str):
        return prod
    total = sum(w for _, w in prod)
    x = rng.random() * total
    for s, w in prod:
        x -= w
        if x <= 0:
            return s
    return prod[-1][0]


def _rewrite(s: str, rules: dict, rng: random.Random) -> str:
    """One derivation pass. Bounded DURING the pass, not merely after it — a genome
    whose rules explode cannot even build the oversized intermediate string."""
    out, n = [], 0
    for ch in s:
        r = _pick(rules[ch], rng) if ch in rules else ch
        out.append(r)
        n += len(r)
        if n >= MAX_SYMBOLS:          # hard stop, mid-pass
            break
    return "".join(out)


def _expand_mirrors(s: str) -> str:
    """(X)  ->  [X][X-mirrored].  BILATERAL SYMMETRY, in one operator.

    Done as a pure string rewrite BEFORE interpretation, so the turtle never has to
    know that animals have two sides. Yaw and roll flip; pitch does not — down is
    down on both flanks, it is left/right that reverses.

    TOTAL: a `for` bounded by MAX_MIRRORS, and every pass strictly removes one '(',
    so it cannot iterate more times than the string has parentheses. Truncated at
    MAX_SYMBOLS, exactly like the derivation."""
    for _ in range(MAX_MIRRORS):
        j = s.rfind("(")                     # innermost pair first
        if j < 0:
            return s
        k = s.find(")", j)
        if k < 0:
            return s.replace("(", "")        # unbalanced genome: drop it, don't crash
        inner = s[j + 1:k]
        s = f"{s[:j]}[{inner}][{inner.translate(_MIRROR)}]{s[k + 1:]}"
        if len(s) >= MAX_SYMBOLS:
            return s[:MAX_SYMBOLS]
    return s.replace("(", "").replace(")", "")


def grow(g: Genome, seed: int) -> list:
    """genome -> skeleton. TOTAL: provably terminates for every possible input.

    No `while`. No recursion. Every loop is a `for` over a bounded range or over a
    string that is capped at MAX_SYMBOLS."""
    rng = random.Random(seed)

    s = g.axiom
    for _ in range(max(0, min(int(g.depth), MAX_DEPTH))):   # <= MAX_DEPTH. Full stop.
        s = _rewrite(s, g.rules, rng)
        if len(s) >= MAX_SYMBOLS:
            s = s[:MAX_SYMBOLS]
            break

    return _interpret(_expand_mirrors(s), g, rng)


def _interpret(s: str, g: Genome, rng: random.Random) -> list:
    """3D turtle. The symbol string becomes a SKELETON — a tree of frames.

    The skeleton is the intermediate representation, and that is the whole trick:
    physics wants it, animation wants it, and the mesh is grown FROM it. The genome
    never has to know what a triangle is."""
    ang = math.radians(g.angle)
    twist = math.radians(g.twist)
    btwist = math.radians(g.branch_twist)
    # 0 = the old plant behaviour (a branch tapers to its tip). >0 = explicit.
    taper = g.seg_taper if g.seg_taper > 0 else (g.radius_decay ** 0.5)

    pos = (0.0, 0.0, 0.0)
    H, L, U = (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)   # heading/left/up

    # pitch0 lays the body down. 0 -> grow UP (a trunk). ~90 -> a HORIZONTAL body
    # axis with 'up' still up, which is the whole difference between a plant and an
    # animal: limbs can now hang DOWN off a spine instead of reaching for the sun.
    if g.pitch0:
        p0 = math.radians(g.pitch0)
        H, U = _norm(_rot(H, L, p0)), _norm(_rot(U, L, p0))

    ln, rad, depth, parent = g.length, g.radius, 0, -1

    stack, bones = [], []

    for ch in s:
        if len(bones) >= MAX_BONES:      # belt and braces
            break

        if ch == "F":
            nxt = _add(pos, _mul(H, ln))
            cap = ln * MAX_ASPECT          # no boulders on sticks
            r0 = min(rad, cap)
            r1 = min(rad * taper, cap)
            bones.append(Bone(parent, pos, nxt, r0, r1, depth))
            parent = len(bones) - 1
            pos, rad = nxt, r1

        elif ch == "f":
            pos = _add(pos, _mul(H, ln))

        elif ch in "+-":                                  # yaw about U
            a = ang if ch == "+" else -ang
            H, L = _norm(_rot(H, U, a)), _norm(_rot(L, U, a))
        elif ch in "&^":                                  # pitch about L
            a = ang if ch == "&" else -ang
            H, U = _norm(_rot(H, L, a)), _norm(_rot(U, L, a))
        elif ch in "<>":                                  # roll about H
            a = twist if ch == "<" else -twist
            L, U = _norm(_rot(L, H, a)), _norm(_rot(U, H, a))

        elif ch == "!":
            rad *= g.radius_decay
        elif ch == "#":                                   # thicken — a torso, a skull
            rad /= g.radius_decay if g.radius_decay else 1.0
        elif ch == "~":
            ln *= g.decay
        elif ch == "|":                                   # about-face
            H, L = _norm(_rot(H, U, math.pi)), _norm(_rot(L, U, math.pi))

        elif ch == "[":
            stack.append((pos, H, L, U, ln, rad, depth, parent))
            # PHYLLOTAXIS on branch, IF the genome wants it. A plant rolls every
            # branch by the golden angle so successive limbs spiral and none shades
            # another (the same law core/fractal_spiral.py uses on the studio's own
            # features). A bilaterian sets branch_twist=0: spiralling your legs
            # around your spine is the one thing an animal must not do.
            if btwist:
                L, U = _norm(_rot(L, H, btwist)), _norm(_rot(U, H, btwist))
            ln, rad, depth = ln * g.branch_len, rad * g.branch_rad, depth + 1

        elif ch == "]":
            if stack:
                pos, H, L, U, ln, rad, depth, parent = stack.pop()

    return bones


# --- RULE 1 boundary check: mutation is local and bounded --------------------

_SYMBOLS = "F+-&^<>!~#"


def _mutate_string(s: str, rng: random.Random) -> str:
    """Mutate ONE production. Includes TOPOLOGY operators, not just symbol jitter:
    a mutation that can add or delete a whole MIRRORED LIMB PAIR reaches the body
    plan, where jittering a float never will."""
    op = rng.random()

    # --- topology: gain a bilateral pair. Wrap a balanced run in ( ). ---------
    if op < 0.16 and "(" not in s and len(s) < 34:
        starts = [i for i, c in enumerate(s) if c == "F"]
        if starts:
            i = rng.choice(starts)
            j = min(len(s), i + rng.randint(1, 4))
            seg = s[i:j]
            if seg.count("[") == seg.count("]"):
                return f"{s[:i]}({seg}){s[j:]}"

    # --- topology: lose a bilateral pair. ------------------------------------
    if op < 0.26 and "(" in s:
        i = s.index("(")
        k = s.find(")", i)
        if k > 0:
            return s[:i] + s[i + 1:k] + s[k + 1:]

    body = list(s)
    if op < 0.55 and body:                        # substitute a symbol
        j = rng.randrange(len(body))
        if body[j] in _SYMBOLS:
            body[j] = rng.choice(_SYMBOLS)
    elif op < 0.82 and len(body) < 40:            # insert a symbol
        body.insert(rng.randrange(len(body) + 1), rng.choice(_SYMBOLS))
    elif len(body) > 4:                           # delete a symbol
        j = rng.randrange(len(body))
        if body[j] not in "[]()":                 # never break the balance
            body.pop(j)
    return "".join(body)


def mutate(g: Genome, rng: random.Random, rate: float = 0.35) -> Genome:
    """A point mutation. Small, local, and it CANNOT breach the walls: depth is
    re-clamped, and MAX_SYMBOLS still bounds whatever the new rules try to say."""
    d = asdict(g)

    def jitter(v, frac, lo, hi):
        return max(lo, min(hi, v * (1.0 + rng.uniform(-frac, frac))))

    d["angle"] = jitter(d["angle"], rate, 5.0, 80.0)
    d["decay"] = jitter(d["decay"], rate * 0.4, 0.55, 0.98)
    d["radius"] = jitter(d["radius"], rate, 0.02, 0.4)
    d["radius_decay"] = jitter(d["radius_decay"], rate * 0.4, 0.5, 0.95)
    d["length"] = jitter(d["length"], rate, 0.3, 2.5)
    d["branch_len"] = jitter(d["branch_len"], rate * 0.3, 0.6, 1.0)
    d["branch_rad"] = jitter(d["branch_rad"], rate * 0.3, 0.5, 1.0)
    # seg_taper was a DEAD GENE: it starts at 0 and this only jittered it when it
    # was already > 0, so evolution could never switch it on. A locus the optimiser
    # cannot reach is a locus that does not exist.
    if d["seg_taper"] > 0:
        d["seg_taper"] = jitter(d["seg_taper"], rate * 0.3, 0.55, 1.0)
    elif rng.random() < 0.12:
        d["seg_taper"] = rng.uniform(0.7, 1.0)      # switch the gene ON
    if rng.random() < 0.25:
        d["twist"] = jitter(d["twist"], rate, 20.0, 200.0)
    if rng.random() < 0.20:                       # posture: lie down / stand up
        d["pitch0"] = max(0.0, min(110.0, d["pitch0"] + rng.uniform(-12.0, 12.0)))
    if rng.random() < 0.30:
        d["depth"] = max(1, min(MAX_DEPTH, d["depth"] + rng.choice([-1, 1])))

    if rng.random() < 0.65 and d["rules"]:        # structural / topological
        k = rng.choice(sorted(d["rules"]))
        alts = d["rules"][k]
        if isinstance(alts, str):
            d["rules"][k] = _mutate_string(alts, rng)
        else:
            i = rng.randrange(len(alts))
            alts[i] = [_mutate_string(alts[i][0], rng), alts[i][1]]
            d["rules"][k] = alts

    return Genome(**d)


# --- geometry: skeleton -> mesh ----------------------------------------------
# "He'll have to find a way to translate that to geometry." Two ways. Both real.

def mesh_tubes(bones: list, sides: int = 8) -> tuple:
    """Generalised cylinders: sweep a ring along every bone. Exact, instant, pure
    python. This is how L-system plants have been rendered since Lindenmayer."""
    verts, faces = [], []
    for b in bones:
        d = _norm(_sub(b.p1, b.p0))
        a = (0.0, 0.0, 1.0) if abs(d[2]) < 0.9 else (1.0, 0.0, 0.0)
        u = _norm(_cross(d, a))
        v = _norm(_cross(d, u))
        base = len(verts)
        for i in range(sides):
            t = 2.0 * math.pi * i / sides
            off = _add(_mul(u, math.cos(t)), _mul(v, math.sin(t)))
            verts.append(_add(b.p0, _mul(off, b.r0)))
            verts.append(_add(b.p1, _mul(off, b.r1)))
        for i in range(sides):
            a0 = base + 2 * i
            a1 = base + 2 * ((i + 1) % sides)
            faces.append((a0, a1, a1 + 1))
            faces.append((a0, a1 + 1, a0 + 1))
    return verts, faces


def mesh_blob(bones: list, res: int = 72, blend: float = 0.55) -> tuple:
    """SDF + smooth-min + marching cubes. The organic path.

    Every bone is a capsule distance field; they are combined with a SMOOTH minimum
    rather than a hard one, which is precisely what turns a bundle of tubes into a
    body — the joints FUSE instead of intersecting. `blend` is one float in the
    genome that slides the creature from bony to fleshy.

    Note what falls out for free: because the mesh is GROWN from the skeleton, we
    know which bone produced every vertex. Auto-rigging — normally a hard problem —
    is not a problem we have.
    """
    import numpy as np
    from skimage import measure

    pts = [p for b in bones for p in (b.p0, b.p1)]
    rmax = max((max(b.r0, b.r1) for b in bones), default=0.1)
    lo = [min(p[i] for p in pts) - 3 * rmax for i in range(3)]
    hi = [max(p[i] for p in pts) + 3 * rmax for i in range(3)]

    gx = [np.linspace(lo[i], hi[i], res) for i in range(3)]
    X, Y, Z = np.meshgrid(gx[0], gx[1], gx[2], indexing="ij")
    P = np.stack([X, Y, Z], axis=-1)

    field = np.full(X.shape, 1e9, dtype=np.float32)
    for b in bones:
        a = np.array(b.p0, dtype=np.float32)
        c = np.array(b.p1, dtype=np.float32)
        ab = c - a
        denom = float(np.dot(ab, ab)) or 1e-9
        t = np.clip(((P - a) @ ab) / denom, 0.0, 1.0)          # project onto segment
        closest = a + t[..., None] * ab
        r = b.r0 + (b.r1 - b.r0) * t                            # taper
        d = np.linalg.norm(P - closest, axis=-1) - r            # capsule SDF
        # Polynomial smooth minimum (Quilez) — the fleshiness operator.
        # h MUST be (new - acc), not (acc - new): with the sign flipped, an
        # accumulator seeded at +1e9 clamps h to 1, returns itself, and never
        # takes a single bone — the field stays at 1e9 and marching cubes finds
        # no surface at all. Cost me a 10-second run of zero triangles.
        h = np.clip(0.5 + 0.5 * (d - field) / blend, 0.0, 1.0)
        field = d * (1.0 - h) + field * h - blend * h * (1.0 - h)

    if float(field.min()) > 0.0 or float(field.max()) < 0.0:
        return [], []                                           # no surface crossing
    v, f, _, _ = measure.marching_cubes(field, level=0.0)
    step = [(hi[i] - lo[i]) / (res - 1) for i in range(3)]
    verts = [(lo[0] + p[0] * step[0], lo[1] + p[1] * step[1], lo[2] + p[2] * step[2])
             for p in v]
    return verts, [tuple(int(i) for i in tri) for tri in f]


def write_obj(verts: list, faces: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# grown by core.terrarium — a genome, not a model\n")
        for v in verts:
            fh.write(f"v {v[0]:.5f} {v[1]:.5f} {v[2]:.5f}\n")
        for f in faces:
            fh.write(f"f {f[0]+1} {f[1]+1} {f[2]+1}\n")


# --- looking at it (the kill criterion is "a shape you'd look at twice") ------

def svg(bones: list, w: int = 300, h: int = 300, pad: int = 14,
        yaw: float = 0.5, bg: bool = True) -> str:
    """Orthographic projection, depth-sorted, tapered limbs. Pure python."""
    if not bones:
        return f'<svg width="{w}" height="{h}"></svg>'
    cy, sy = math.cos(yaw), math.sin(yaw)

    def proj(p):                       # rotate about Z, then look from the side
        x = p[0] * cy - p[1] * sy
        y = p[0] * sy + p[1] * cy
        return (x, p[2], y)            # (screen x, screen y=up, depth)

    P = [(proj(b.p0), proj(b.p1), b) for b in bones]
    xs = [q[i] for a, c, _ in P for q in (a, c) for i in (0,)]
    ys = [q[1] for a, c, _ in P for q in (a, c)]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    sc = min((w - 2 * pad) / max(x1 - x0, 1e-6), (h - 2 * pad) / max(y1 - y0, 1e-6))

    def px(q):
        return (pad + (q[0] - x0) * sc, h - pad - (q[1] - y0) * sc)

    P.sort(key=lambda t: (t[0][2] + t[1][2]) * 0.5)      # painter's algorithm
    maxd = max(b.depth for b in bones) or 1
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}">']
    if bg:
        out.append(f'<rect width="{w}" height="{h}" fill="#0d1117"/>')
    for a, c, b in P:
        (ax, ay), (cx_, cy_) = px(a), px(c)
        t = b.depth / maxd
        col = f"hsl({140 + int(80 * t)},{int(70 - 25 * t)}%,{int(35 + 40 * t)}%)"
        wdt = max(0.7, (b.r0 + b.r1) * 0.5 * sc * 2.0)
        out.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{cx_:.1f}" y2="{cy_:.1f}" '
                   f'stroke="{col}" stroke-width="{wdt:.2f}" stroke-linecap="round"/>')
    out.append("</svg>")
    return "".join(out)


def sheet(g: Genome, n: int, seed: int, cell: int = 190, cols: int = 6) -> str:
    """STAGE 1, free: the parent, then n-1 MUTANTS. One glance answers the only
    question that matters — do mutations give a FAMILY, or noise and clones?"""
    rng = random.Random(seed)
    rows = (n + cols - 1) // cols
    W, H = cols * cell, rows * cell
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#0d1117"/>']
    for i in range(n):
        gi = g if i == 0 else mutate(g, rng)
        body = svg(grow(gi, seed + i), cell, cell, bg=False)
        inner = body[body.index(">") + 1:body.rindex("</svg>")]
        x, y = (i % cols) * cell, (i // cols) * cell
        out.append(f'<g transform="translate({x},{y})">{inner}'
                   f'<rect width="{cell}" height="{cell}" fill="none" '
                   f'stroke="#1f2937"/>'
                   f'<text x="6" y="{cell-6}" font-family="monospace" font-size="9" '
                   f'fill="{"#7dd3a0" if i == 0 else "#4b5563"}">'
                   f'{"PARENT" if i == 0 else f"m{i}"}</text></g>')
    out.append("</svg>")
    return "".join(out)


# --- CLI ---------------------------------------------------------------------

def _main() -> int:
    ap = argparse.ArgumentParser(prog="python -m core.terrarium",
                                 description="Grow an organism from a genome.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("seed", help="write a starter genome")
    s.add_argument("--out", default="docs/terrarium/seed0.json")
    s.add_argument("--plan", choices=["plant", "quadruped"], default="plant",
                   help="plant = a RECURSION (A->...A). quadruped = a CASCADE.")

    gr = sub.add_parser("grow", help="genome -> skeleton -> mesh -> .obj + .svg")
    gr.add_argument("--genome", default="docs/terrarium/seed0.json")
    gr.add_argument("--seed", type=int, default=7)
    gr.add_argument("--mesh", choices=["tubes", "blob"], default="tubes")
    gr.add_argument("--res", type=int, default=72)
    gr.add_argument("--out", default="scratch/terrarium")

    sh = sub.add_parser("sheet", help="parent + mutants, one SVG (Stage 1)")
    sh.add_argument("--genome", default="docs/terrarium/seed0.json")
    sh.add_argument("--n", type=int, default=24)
    sh.add_argument("--seed", type=int, default=7)
    sh.add_argument("--out", default="scratch/terrarium/sheet.svg")

    a = ap.parse_args()

    if a.cmd == "seed":
        p = Path(a.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        g0 = Genome.quadruped() if a.plan == "quadruped" else Genome()
        p.write_text(g0.to_json(), encoding="utf-8")
        print(f"{a.plan} genome -> {p}  ({p.stat().st_size} bytes)")
        return 0

    g = Genome.from_json(Path(a.genome).read_text(encoding="utf-8"))

    if a.cmd == "sheet":
        p = Path(a.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(sheet(g, a.n, a.seed), encoding="utf-8")
        print(f"contact sheet ({a.n} individuals) -> {p}")
        return 0

    import time
    t0 = time.time()
    bones = grow(g, a.seed)
    t_grow = time.time() - t0

    t0 = time.time()
    verts, faces = (mesh_blob(bones, a.res) if a.mesh == "blob"
                    else mesh_tubes(bones))
    t_mesh = time.time() - t0

    out = Path(a.out)
    write_obj(verts, faces, out / f"organism_{a.seed}.obj")
    (out / f"organism_{a.seed}.svg").write_text(svg(bones, 600, 600),
                                                encoding="utf-8")

    print(f"  genome      {Path(a.genome).stat().st_size} bytes")
    print(f"  grow        {len(bones)} bones      {t_grow*1000:.1f} ms")
    print(f"  mesh[{a.mesh:<5}] {len(verts)} verts / {len(faces)} tris   "
          f"{t_mesh*1000:.1f} ms")
    print(f"  -> {out / f'organism_{a.seed}.obj'}")
    print(f"  -> {out / f'organism_{a.seed}.svg'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
