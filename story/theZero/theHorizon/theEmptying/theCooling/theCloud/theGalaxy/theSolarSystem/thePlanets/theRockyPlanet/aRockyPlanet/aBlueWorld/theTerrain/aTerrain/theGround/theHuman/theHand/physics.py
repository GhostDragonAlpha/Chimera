"""theHand -- the STRUCTURE. What a hand is, before anything is done with it.

THE EDGE FROM theHuman. The parent hands down a stature, a body mass and a gravity. From the
stature alone this chapter derives a hand: how big, how heavy, how many ways it can bend, how far
its fingertips reach, and -- the part that decides everything about how hands work -- how badly its
tendons are levered.

WHAT THIS CHAPTER IS NOT. It does not close on anything. Grip force, grasp type and the friction at
the contact belong to `theGrip`, which is a sibling and therefore unreachable from here in both
directions. What this publishes is the GEOMETRY and the TRANSMISSION -- the two things any closing
law would have to stand on.

THE FIVE DERIVATIONS, in the order they depend on each other:

  1. SIZE, from 4,082 measured men. `handlength / stature` is a MEASURED fraction, not a remembered
     one: median 0.10996, SD 0.0042, n=4,082 (ANSUR II, US Army 2012, public release 2017, in this
     repo). A hand is 11.0% of a person, and a 3.8% coefficient of variation is why that is a
     useful law rather than an average.

  2. THE LANDMARK TRAP, and it is worth more than any number here. ANSUR measures `palmlength` to
     the CREASE at the base of the finger. THE CREASE IS NOT THE KNUCKLE. Building a finger from
     the ANSUR split puts every joint 2.6 cm too far out and makes the fingers a quarter too short.
     This is the same defect that cost this project 3.6 cm of stature by pivoting the foot at the
     toe tip instead of the ball (docs/THE_FOLDING.md), and it is invisible to a units check because
     both quantities are honest metres. So: ANSUR supplies the OUTSIDE of the hand, and the
     vendored `myohand` model supplies where the JOINTS are inside it.

  3. THE DEGREES OF FREEDOM ARE COUNTED, not quoted. Walking the model's joint list gives 22 for the
     hand -- 2 wrist, 4 thumb, 16 across the four fingers -- and 27 bones, by counting bodies. The
     COUPLING between them is the one thing here that is cited rather than derived, and it is said
     so out loud.

  4. THE WORKSPACE is swept, not assumed: forward kinematics through the model's own measured joint
     ranges, 60,000 random postures per digit, and the reachable set is counted in voxels. It comes
     with an honest bracket rather than a false decimal, because the estimator has not converged.

  5. THE LEVER, which is the whole reason a hand is interesting. The flexor tendon runs a few
     millimetres from the joint it turns while the fingertip sticks out a hundred. Derived from the
     model's own tendon waypoints, a straight finger pressing 1 N at the tip needs about 12 N in its
     long flexor, and THE BINDING JOINT IS THE KNUCKLE -- which is exactly why a hand carries a set
     of small intrinsic muscles that cross only that joint. The disadvantage predicts the anatomy.

WHAT IT CONSUMES from theHuman: height_m, bare_mass_kg, g, skin_albedo_rgb, S_earth, duration_s.

WHAT IS NOT SOURCED, stated here rather than hidden:
  * the FINGER-COUPLING claim (2 postural synergies, >80% of variance) is Santello, Flanders &
    Soechting 1998, J Neurosci 18(23):10105-10115 -- QUOTED, not measured here, and the paper is not
    in this repo.
  * the literature MOMENT ARMS this chapter's derivation is checked against (An, Ueba, Chao, Cooney
    & Linscheid 1983, J Biomech 16:419-425) are likewise quoted from outside the repo. They are used
    as a RANGE to fall inside, never as an input.
  * the myohand model's BODY MASSES are round modelling numbers (every carpal exactly 20 g), so it
    is used for geometry only. Mass comes from de Leva 1996 and nowhere else.
  * the hand's own cross-section SHAPE (a flat slab with rounded borders) is a modelling choice made
    to turn a circumference into a thickness. It is tested against ANSUR's own waist triple, where
    it reads 7% high, and reported with that bias attached.
"""
from __future__ import annotations

import csv
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE TWO MEASURED SOURCES
# ════════════════════════════════════════════════════════════════════════════════════════════════
# Both live in the repo, and both are read here rather than remembered. A membrane may reach its
# PARENT and it may reach measured DATA; it may never reach a sibling.


def _repo(*parts) -> Path:
    """Walk up from this chapter until the named file appears. The story is a deep tree and a
    relative path counted in `..` is a fact about the tree's depth, which is the one thing about a
    story that is allowed to change."""
    here = Path(__file__).resolve()
    for q in here.parents:
        f = q.joinpath(*parts)
        if f.exists():
            return f
    raise FileNotFoundError("/".join(parts))


_ANSUR_CACHE = None


def ansur_hand(sex: str = "male") -> dict:
    """THE POPULATION. ANSUR II, the US Army's 2012 anthropometric survey, public release 2017:
    4,082 men, 93 direct measurements each, in millimetres. Public domain, in this repo.

    THIS RETURNS FRACTIONS OF STATURE, WITH THEIR SPREAD, and the spread is the point. A fraction
    with no SD is a number pretending the population is one person; the SD is what makes a
    long-fingered body a legal body instead of an error.

    RATIOS ARE TAKEN PER SUBJECT and then the median is read, rather than dividing one median by
    another. The two agree here to four decimals -- which is a fact worth knowing, not one worth
    assuming, because they part company the moment a measure is skewed."""
    global _ANSUR_CACHE
    if _ANSUR_CACHE is not None and _ANSUR_CACHE["sex"] == sex:
        return _ANSUR_CACHE
    f = _repo("research_references", "human",
              f"ANSUR_II_{'MALE' if sex == 'male' else 'FEMALE'}_Public.csv")
    want = ("stature", "handlength", "handbreadth", "handcircumference", "palmlength",
            "wristcircumference", "waistbreadth", "waistdepth", "waistcircumference")
    cols = {k: [] for k in want}
    with f.open(encoding="latin-1", newline="") as fh:
        for row in csv.DictReader(fh):
            for k in want:
                cols[k].append(float(row[k]))
    n = len(cols["stature"])

    def band(values):
        v = sorted(values)
        mean = sum(v) / len(v)
        sd = math.sqrt(sum((x - mean) ** 2 for x in v) / len(v))
        return {"median": v[len(v) // 2], "mean": mean, "sd": sd,
                "p5": v[int(0.05 * len(v))], "p95": v[int(0.95 * len(v))]}

    def over_stature(key):
        return band([a / b for a, b in zip(cols[key], cols["stature"])])

    out = {
        "sex": sex, "n": n, "source": ANSUR_CITE,
        "stature_mm": band(cols["stature"]),
        # every hand measure as a fraction of the body it grew on
        "hand_length": over_stature("handlength"),
        "hand_breadth": over_stature("handbreadth"),
        "hand_circumference": over_stature("handcircumference"),
        "palm_length": over_stature("palmlength"),
        "wrist_circumference": over_stature("wristcircumference"),
        # and the palm/finger split of the hand itself, per subject
        "palm_over_hand": band([a / b for a, b in zip(cols["palmlength"], cols["handlength"])]),
        "breadth_over_length": band([a / b for a, b in zip(cols["handbreadth"], cols["handlength"])]),
        # THE CONTROL for the cross-section model below: the one place ANSUR measures a breadth, a
        # depth AND a circumference at the same landmark level, so the shape model can be tested
        # rather than believed.
        "waist_mm": {k: band(cols[f"waist{k}"]) for k in ("breadth", "depth", "circumference")},
    }
    _ANSUR_CACHE = out
    return out


ANSUR_CITE = ("ANSUR II, US Army Anthropometric Survey 2012 (public release 2017), "
              "4,082 male subjects x 93 measures, public domain; "
              "research_references/human/ANSUR_II_MALE_Public.csv")
MYOHAND_CITE = ("MyoSuite myo_sim MyoHand_v0.1.7, vendored at vendor/myo_sim (Apache 2.0); "
                "Caggiano et al. 2022. Used for GEOMETRY ONLY -- its body masses are round "
                "modelling numbers, not measurements.")

_MYO_CACHE = None


def myohand() -> dict:
    """THE SKELETON. Every body's offset from its parent, every joint's axis and measured range,
    every tendon waypoint, and the soft-tissue radius of each segment.

    WHY A MODEL AND NOT A TABLE. A table of phalanx lengths is a list; this is a TREE, and the tree
    is what turns lengths into a workspace. XML nesting IS the kinematic chain -- the same reason
    this studio's MJCF work reads a body tree rather than a link list.

    THE CHAIN INSIDE THE HAND IS PURE TRANSLATION -- no body from the wrist outward carries a
    rotation -- so an offset really is a bone length and a site position really is where that point
    sits. Asserted here and CHECKED: `rotations_in_hand` in the return is the count that must be 0."""
    global _MYO_CACHE
    if _MYO_CACHE is not None:
        return _MYO_CACHE
    f = _repo("vendor", "myo_sim", "hand", "assets", "myohand_body.xml")
    bodies = {}

    def walk(node, parent):
        for b in node.findall("body"):
            nm = b.get("name")
            bodies[nm] = {
                "rotated": bool(b.get("euler") or b.get("quat")),
                "parent": parent,
                "pos": np.array([float(v) for v in (b.get("pos") or "0 0 0").split()]),
                "joints": [(j.get("name"),
                            np.array([float(v) for v in j.get("axis").split()]),
                            *[float(v) for v in (j.get("range") or "0 0").split()])
                           for j in b.findall("joint")],
                "sites": {s.get("name"):
                          np.array([float(v) for v in (s.get("pos") or "0 0 0").split()])
                          for s in b.findall("site")},
                # the soft-tissue capsule: size[0] is the radius of the flesh around the bone
                "radius": next((float(g.get("size").split()[0]) for g in b.findall("geom")
                                if g.get("class") == "skin" and g.get("type") is None), None),
            }
            walk(b, nm)

    walk(ET.parse(f).getroot(), None)
    # the hand's own bones, named by the anatomy they are
    CARPALS = ("lunate", "scaphoid", "pisiform", "triquetrum", "capitate",
               "trapezium", "trapezoid", "hamate")
    META = ("firstmc", "secondmc", "thirdmc", "fourthmc", "fifthmc")
    PHAL = ("proximal_thumb", "distal_thumb",
            "proxph2", "midph2", "distph2", "proxph3", "midph3", "distph3",
            "proxph4", "midph4", "distph4", "proxph5", "midph5", "distph5")
    # world positions, relative to the wrist (lunate), by summing the translation chain
    world = {}

    def place(nm, off):
        world[nm] = off + bodies[nm]["pos"]
        for k, v in bodies.items():
            if v["parent"] == nm:
                place(k, world[nm])

    place("full_body", np.zeros(3))
    # REBASE ONTO THE WRIST, and take a COPY of the origin first. Subtracting `world["lunate"]`
    # inside the loop zeroes the origin partway through and leaves every key after it in the old
    # frame -- which is a silent 10x scale error in every length downstream, and it happened here.
    origin = world["lunate"].copy()
    for k in world:
        world[k] = world[k] - origin
    # ROTATIONS BELONG TO THE ARM, NOT THE HAND. The model carries a whole shoulder above the wrist,
    # and two of its bodies are rotated; counting those against the hand would be reading another
    # membrane's geometry as this one's. So count only from the wrist DOWN, which is also the claim
    # this function makes: inside the hand an offset really is a bone length.
    def below(nm):
        yield nm
        for k, v in bodies.items():
            if v["parent"] == nm:
                yield from below(k)

    rot = sum(1 for nm in below("lunate") if bodies[nm]["rotated"])
    _MYO_CACHE = {"bodies": bodies, "world": world, "rotations_in_hand": rot,
                  "carpals": CARPALS, "metacarpals": META, "phalanges": PHAL,
                  "source": MYOHAND_CITE}
    return _MYO_CACHE


# ── DIGITS, and where their fingertips are. The model marks each tip with a site; nothing here has
#    to decide what counts as a fingertip.
DIGITS = {
    "thumb":  {"chain": ("firstmc", "proximal_thumb", "distal_thumb"), "tip": "THtip"},
    "index":  {"chain": ("secondmc", "proxph2", "midph2", "distph2"), "tip": "IFtip"},
    "middle": {"chain": ("thirdmc", "proxph3", "midph3", "distph3"), "tip": "MFtip"},
    "ring":   {"chain": ("fourthmc", "proxph4", "midph4", "distph4"), "tip": "RFtip"},
    "little": {"chain": ("fifthmc", "proxph5", "midph5", "distph5"), "tip": "LFtip"},
}
# THE FAN IS CENTRED ON THE MIDDLE FINGER, because that is the definition: abduction of the fingers
# is measured from the axis of the third ray. Anatomy, not composition.
FAN = {"index": 1.0, "middle": 0.0, "ring": -0.7, "little": -1.0, "thumb": 0.0}

FREE = {
    # WHICH HAND, out of 4,082. The law fixes hand length as a fraction of stature; which fraction
    # inside the measured population a particular body drew is not a law, it is that body.
    "hand_size": {"lo": 0.0, "hi": 1.0, "default": 0.5,
                  "label": "hand size in its population", "unit": "0 = 5th percentile, 1 = 95th",
                  "local": "a hand's share of its owner is measured to +-4%, and varies"},
}

# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE LAWS
# ════════════════════════════════════════════════════════════════════════════════════════════════


def slab_thickness(breadth, circumference):
    """A THICKNESS OUT OF A CIRCUMFERENCE AND A BREADTH -- the only way to get the third dimension
    of a hand out of ANSUR, which never measures it.

    THE SHAPE IS A CHOICE AND IT IS DECLARED. A cross-section at the knuckles is a flat slab with
    rounded borders -- a stadium -- whose perimeter is `2(w - d) + pi*d`. The two neighbours bracket
    it: a rectangle (`2(w + d)`) gives 18.0 mm and an ellipse gives 43.1 mm for the same hand, so
    the shape carries a factor of 2.4 and cannot be waved through.

    AND IT IS TESTED, on the one place ANSUR measures all three of breadth, depth and circumference
    at one landmark: the waist. There the stadium predicts 251 mm against a measured 234 -- 7% high.
    That bias travels with this number and is published beside it."""
    w, c = float(breadth), float(circumference)
    return (c - 2.0 * w) / (math.pi - 2.0)


def frustum(height, r1, r2):
    """Volume of a truncated cone: a finger segment, tapering the way a finger tapers."""
    return math.pi * float(height) / 3.0 * (r1 * r1 + r1 * r2 + r2 * r2)


def frustum_com(height, r1, r2):
    """How far along it its own centre of mass sits. A cone is nose-light, so this is never h/2 and
    using h/2 would put a finger's mass too far out and slow its pendulum."""
    h = float(height)
    return h * (r1 * r1 + 2.0 * r1 * r2 + 3.0 * r2 * r2) / (4.0 * (r1 * r1 + r1 * r2 + r2 * r2))


def moment_arm(axis, origin, p_prox, p_dist):
    """THE LEVER A TENDON TURNS A JOINT WITH: the perpendicular distance from the joint's axis to
    the straight line the tendon takes across it.

    r = axis . ( (p1 - O) x u ),  u the tendon's unit direction

    THIS IS THE WHOLE HAND PROBLEM IN ONE LINE. The distance is millimetres and the fingertip is a
    hundred millimetres away, so the tendon is at a disadvantage of roughly ten to one, everywhere,
    by construction -- a joint cannot be far from the bone that contains it."""
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    u = np.asarray(p_dist, float) - np.asarray(p_prox, float)
    u = u / np.linalg.norm(u)
    return float(np.dot(a, np.cross(np.asarray(p_prox, float) - np.asarray(origin, float), u)))


def _rot(axis, q):
    """(N,3,3) rotations of N angles about one axis -- Rodrigues, so the whole population of
    postures turns in one call and the workspace is a sweep rather than a loop.

        R = I + sin(q) K + (1 - cos q) K^2

    AND THE IDENTITY IS NOT SCALED BY cos(q). Rodrigues has two equivalent spellings -- that one,
    and `cos(q) I + sin(q) K + (1 - cos q) a a^T` -- and this first carried a splice of the two,
    `cos(q) I + sin(q) K + (1 - cos q) K^2`, which is neither. Since K^2 = a a^T - I, the splice
    leaves `(2cos q - 1) I` where the identity should be, so it is exactly right at q = 0 and
    silently wrong everywhere else. Every posture in the sweep was bent.

    IT WAS CAUGHT BY THE PICTURE. emit() draws the same chain from the published linkage with the
    correct spelling, and the two tips that derive() said met at 1.6 mm were drawn 20 mm apart. One
    membrane, two independent evaluations of one geometry, and their disagreement is the only reason
    this was found -- a sweep that is quietly 20 mm out looks like a perfectly good workspace."""
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    q = np.atleast_1d(np.asarray(q, float))
    c = np.cos(q)[:, None, None]
    s = np.sin(q)[:, None, None]
    K = np.array([[0.0, -a[2], a[1]], [a[2], 0.0, -a[0]], [-a[1], a[0], 0.0]])
    return np.eye(3)[None] + s * K[None] + (1.0 - c) * (K @ K)[None]


def _uniq(*lists):
    """The union of some joint-name lists, IN ORDER, with no duplicates.

    NOT `set(a + b)`. A set of strings iterates in hash order, and Python randomises string hashes
    per process -- so drawing random postures over `set(...)` handed the generator its joints in a
    different order every run and the same seed produced a different hand. Measured: the opposition
    gap moved between 1.37 and 2.33 mm across three processes while being byte-identical within any
    one of them, which is the worst possible signature because a single session looks reproducible.
    Determinism is one of this studio's three rules for a grown thing; a set broke it silently."""
    out = []
    for xs in lists:
        for x in xs:
            if x not in out:
                out.append(x)
    return out


def _chain_to(bodies, name, base="lunate"):
    ch = []
    n = name
    while n is not None:
        ch.append(n)
        n = bodies[n]["parent"]
    ch = ch[::-1]
    return ch[ch.index(base) + 1:]


def fk(model, body, local, Q, n):
    """Where a point on a bone ends up, for n postures at once, in the wrist's frame.

    Positions are OUTPUTS. This is the studio's control law made literal: nothing here is told where
    a fingertip should be, it is told what every joint did and the fingertip is wherever that puts
    it."""
    bodies = model["bodies"]
    R = np.broadcast_to(np.eye(3), (n, 3, 3)).copy()
    p = np.zeros((n, 3))
    for nm in _chain_to(bodies, body):
        b = bodies[nm]
        p = p + np.einsum("nij,j->ni", R, b["pos"])
        for (jn, ax, lo, hi) in b["joints"]:
            q = Q[jn] if jn in Q else np.zeros(n)
            R = R @ _rot(ax, q)
    return p + np.einsum("nij,j->ni", R, np.asarray(local, float))


def voxel_volume(points, cell):
    """The volume of a reachable SET, counted rather than fitted: bin the sampled postures and add
    up the boxes that got hit.

    IT IS BIASED LOW AND SAYS SO. Finer boxes need more postures, so this climbs with sample count
    and falls with box size; the number is only meaningful WITH ITS GRAIN, which is published beside
    it. The convex hull is carried too, as the upper bracket -- the truth is between them and this
    chapter does not pretend to a decimal it has not earned."""
    k = np.floor(np.asarray(points, float) / float(cell)).astype(np.int64)
    return len(np.unique(k, axis=0)) * float(cell) ** 3


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE EDGE
# ════════════════════════════════════════════════════════════════════════════════════════════════
def derive(parent, free):
    if parent is None or "height_m" not in parent:
        raise ValueError("theHand requires theHuman as its parent")
    free = free or {}
    size = float(free.get("hand_size", FREE["hand_size"]["default"]))

    h = float(parent["height_m"])
    m_body = float(parent.get("bare_mass_kg", parent["mass_kg"]))
    g = float(parent["g"])

    AN = ansur_hand("male")
    MY = myohand()
    W = MY["world"]
    B = MY["bodies"]

    # ── 1. HOW BIG. Stature times a measured fraction; `size` walks the fraction across the
    #    population's own 5th-to-95th band rather than across a range somebody liked.
    f_lo, f_med, f_hi = (AN["hand_length"]["p5"], AN["hand_length"]["median"],
                         AN["hand_length"]["p95"])
    frac = f_lo + (f_hi - f_lo) * size
    L = frac * h                                    # hand length, wrist crease to fingertip
    # breadth and circumference ride the same draw, so a big hand is big in every direction
    ride = frac / f_med
    Bw = AN["hand_breadth"]["median"] * h * ride
    Cc = AN["hand_circumference"]["median"] * h * ride
    D = slab_thickness(Bw, Cc)                      # the third dimension ANSUR never measured
    palm_crease = AN["palm_over_hand"]["median"] * L

    # the shape model's own bias, measured on the one triple ANSUR takes at one level
    wb, wd, wc = (AN["waist_mm"]["breadth"]["median"], AN["waist_mm"]["depth"]["median"],
                  AN["waist_mm"]["circumference"]["median"])
    slab_bias = slab_thickness(wb, wc) / wd

    # ── 2. WHERE THE JOINTS ARE. The model's proportions, scaled onto this hand: LENGTHS by hand
    #    length, WIDTHS by hand breadth. Two scales because the model is a slimmer hand than the
    #    median -- 0.396 breadth-over-length against ANSUR's 0.457 -- and stretching it by one
    #    factor would have made either the fingers fat or the moment arms thin.
    tipb, tipl = DIGITS["middle"]["chain"][-1], DIGITS["middle"]["tip"]
    L_model = float(np.linalg.norm(W[tipb] + B[tipb]["sites"][tipl]))
    B_model = 2.0 * sum(B[b]["radius"] for b in ("proxph2", "proxph3", "proxph4", "proxph5"))
    s_len = L / L_model
    s_wid = Bw / B_model

    def digit_segments(name):
        """(length, radius) of each phalanx from the MCP joint out to the tip, in THIS hand."""
        ch = DIGITS[name]["chain"]
        out = []
        for a, b in zip(ch[1:], ch[2:]):
            out.append((float(np.linalg.norm(W[b] - W[a])) * s_len, B[a]["radius"] * s_wid))
        last = ch[-1]
        tip = W[last] + B[last]["sites"][DIGITS[name]["tip"]]
        out.append((float(np.linalg.norm(tip - W[last])) * s_len, B[last]["radius"] * s_wid))
        return out

    segs = {d: digit_segments(d) for d in DIGITS}
    finger_len = {d: sum(a for a, _ in segs[d]) for d in segs}
    wrist_to_mcp = float(np.linalg.norm(W["proxph3"])) * s_len
    knuckle_span = float(np.linalg.norm(W["proxph2"] - W["proxph5"])) * s_len

    # ── THE LINKAGE ITSELF, PUBLISHED. Root, bones, joint axes, tip -- everything a forward
    #    kinematic chain needs, in this hand's metres, so `emit()` can draw the SAME skeleton this
    #    function measured instead of a hand-rolled approximation of it.
    #
    #    THE FIRST VERSION DID NOT DO THIS and the drawing lied. emit() carried its own planar chain
    #    -- one flexion angle per segment, rotating in a plane -- and fed it the opposition pose this
    #    chapter had SEARCHED FOR on the model's real oblique axes. The tips did not meet: the gap
    #    OPENED from 87 mm to 110 mm as the hand closed, while the published number said 0.9 mm. Same
    #    file, same numbers, and still a picture contradicting its own derivation, because the two
    #    were doing different geometry. Publishing the linkage is what makes that impossible.
    #
    #    It is legal to lay the whole chain out in one frame because no body inside the hand carries
    #    a rotation -- checked, and published as `model_rotations_in_hand_count`.
    linkage = {}
    for d, spec in DIGITS.items():
        ch = spec["chain"]
        first = next(b for b in ch if B[b]["joints"])       # the first body that actually moves
        i0 = ch.index(first)
        bones, axes, names = [], [], []
        for a, b in zip(ch[i0:], ch[i0 + 1:]):
            names.append([j[0] for j in B[a]["joints"]])
            axes.append([list(np.asarray(j[1]) / np.linalg.norm(j[1])) for j in B[a]["joints"]])
            bones.append(list(B[b]["pos"] * s_len))
        last = ch[-1]
        names.append([j[0] for j in B[last]["joints"]])
        axes.append([list(np.asarray(j[1]) / np.linalg.norm(j[1])) for j in B[last]["joints"]])
        linkage[d] = {
            "root_m": list(W[first] * s_len),
            "bones_m": bones,
            "tip_m": list(B[last]["sites"][spec["tip"]] * s_len),
            "joints": names,
            "axes": axes,
            "radii_m": [r for _, r in segs[d]],
        }

    # THE LANDMARK GAP, and it is the most useful number in this chapter. ANSUR's palm ends at the
    # CREASE; the model's palm ends at the JOINT. Both are honest metres of the same hand.
    crease_offset = palm_crease - wrist_to_mcp

    # ── 3. HOW MANY WAYS IT BENDS. Counted from the model, never quoted.
    hand_bodies = set(MY["carpals"]) | set(MY["metacarpals"]) | set(MY["phalanges"])
    joints = [(jn, lo, hi) for nm, b in B.items() if nm in hand_bodies
              for (jn, ax, lo, hi) in b["joints"]]
    wrist_j = [j for j in joints if j[0] in ("flexion", "deviation")]
    thumb_j = [j for j in joints if j[0] in ("cmc_abduction", "cmc_flexion", "mp_flexion",
                                             "ip_flexion")]
    finger_j = [j for j in joints if j[0] not in [x[0] for x in wrist_j + thumb_j]]
    rom_total = sum(hi - lo for _, lo, hi in joints)

    # ── 4. WHAT IT CAN REACH. Forward kinematics through the model's own measured ranges.
    rng = np.random.default_rng(1729)
    N = 60000
    JR = {jn: (lo, hi) for jn, lo, hi in joints}
    DJ = {d: [jn for nm in _chain_to(B, DIGITS[d]["chain"][-1]) for (jn, _a, _l, _h) in B[nm]["joints"]]
          for d in DIGITS}
    Q = {jn: rng.uniform(*JR[jn], N) for jn in JR}
    tips = {}
    for d in DIGITS:
        b = DIGITS[d]["chain"][-1]
        tips[d] = fk(MY, b, B[b]["sites"][DIGITS[d]["tip"]], Q, N) * s_len
    allp = np.concatenate([tips[d] for d in DIGITS], 0)
    grain = L / 32.0
    ws_box = voxel_volume(allp, grain)
    try:
        from scipy.spatial import ConvexHull
        ws_hull = float(ConvexHull(allp).volume)
    except Exception:
        ws_hull = float("nan")
    reach = float(np.linalg.norm(allp, axis=1).max())

    # THE APERTURE, and OPPOSITION -- the structural claim that separates a hand from a hook. The
    # thumb and each finger are sampled TOGETHER, so the span is what the two digits can actually do
    # at the same time rather than two independent best cases.
    gaps = {}
    for f in ("index", "middle", "ring", "little"):
        Qp = {jn: rng.uniform(*JR[jn], N) for jn in _uniq(DJ["thumb"], DJ[f])}
        th = fk(MY, "distal_thumb", B["distal_thumb"]["sites"]["THtip"], Qp, N) * s_len
        fb = DIGITS[f]["chain"][-1]
        ft = fk(MY, fb, B[fb]["sites"][DIGITS[f]["tip"]], Qp, N) * s_len
        dd = np.linalg.norm(th - ft, axis=1)
        gaps[f] = (float(dd.min()), float(dd.max()))
        if f == "index":
            i_best = int(np.argmin(dd))
            oppose_q = {jn: float(Qp[jn][i_best]) for jn in DJ["thumb"]}
            index_q = {jn: float(Qp[jn][i_best]) for jn in DJ["index"]}

    # THE SPAN OF A FLAT SPREAD HAND, which is what a person's "hand span" actually means and what
    # `aperture_max_m` above is NOT. The maximum over the whole joint box is an UPPER BOUND and
    # nothing more: the model's limits are independent boxes, so the search is free to combine a
    # fully hyperextended thumb with a fully deviated index in a posture no wrist permits. This
    # instead holds every flexion joint at neutral -- the hand flat on a table -- and lets only the
    # thumb's saddle joint and the fingers' spread move, which is a real posture family.
    Qs = {jn: np.zeros(N) for jn in _uniq(DJ["thumb"], DJ["index"])}
    for jn in ("cmc_abduction", "cmc_flexion", "mcp2_abduction"):
        Qs[jn] = rng.uniform(*JR[jn], N)
    th = fk(MY, "distal_thumb", B["distal_thumb"]["sites"]["THtip"], Qs, N) * s_len
    ft = fk(MY, "distph2", B["distph2"]["sites"]["IFtip"], Qs, N) * s_len
    spread = float(np.linalg.norm(th - ft, axis=1).max())
    # AND HOW FAR THE THUMB ITSELF REACHES, published because it is the suspect when the span above
    # comes out too wide: this model's thumb tip sits 0.73 of a hand length from the wrist, and a
    # thumb that long makes every span involving it long.
    thumb_reach = float(np.linalg.norm(th, axis=1).max())

    # THE LARGEST THING FOUR FINGERS CAN GO ROUND. A digit wrapping half a cylinder lays its own
    # length along a half-circumference: L_finger = pi*R. Pure geometry, and it is the number a
    # closing law would need -- what it then DOES with it is not this chapter's business.
    enclose_d = 2.0 * finger_len["middle"] / math.pi

    # ── 5. THE LEVER. Moment arms read off the model's own flexor waypoints, scaled by WIDTH.
    arms = {}
    for d, n in (("index", 2), ("middle", 3), ("ring", 4), ("little", 5)):
        pre = {2: "mcp2", 3: "mcp3", 4: "mcp4", 5: "mcp5"}[n]
        try:
            arms[d] = {
                "mcp": abs(moment_arm(dict((j[0], j[1]) for j in B[f"proxph{n}"]["joints"])[f"{pre}_flexion"],
                                      W[f"proxph{n}"], _site(MY, f"FDP{n}-P5"), _site(MY, f"FDP{n}-P6"))) * s_wid,
                "pip": abs(moment_arm(dict((j[0], j[1]) for j in B[f"midph{n}"]["joints"])[f"pm{n}_flexion"],
                                      W[f"midph{n}"], _site(MY, f"FDP{n}-P7"), _site(MY, f"FDP{n}-P8"))) * s_wid,
                "dip": abs(moment_arm(dict((j[0], j[1]) for j in B[f"distph{n}"]["joints"])[f"md{n}_flexion"],
                                      W[f"distph{n}"], _site(MY, f"FDP{n}-P9"), _site(MY, f"FDP{n}-P10"))) * s_wid,
            }
        except KeyError:
            continue
    a3 = arms["middle"]
    # THE INDEPENDENT BOUND, from ANSUR alone: four fingers share the hand's breadth, so one finger
    # is a quarter of it, and a tendon inside that finger cannot be further from the bone than half
    # its width. 11.0 mm -- and the model's tendon sits inside it, which is the check that the two
    # sources describe the same hand.
    arm_bound = Bw / 8.0

    # the fingertip's own levers about each joint: how far out the load is
    l_dist = segs["middle"][-1][0]
    l_mid = segs["middle"][-2][0] + l_dist
    l_prox = finger_len["middle"]
    ratio = {"dip": l_dist / a3["dip"], "pip": l_mid / a3["pip"], "mcp": l_prox / a3["mcp"]}
    binding = max(ratio, key=ratio.get)

    # ── 6. WHERE THE MASS IS. de Leva for HOW MUCH, this chapter's own geometry for WHERE.
    from measured import segment
    dl = segment("hand", "male")
    # AND THE DRAW HAS TO REACH THE MASS TOO. de Leva's fraction describes the population's median
    # hand; a hand drawn at the 95th percentile is 6% longer in every direction, so it holds 1.06^3
    # of the tissue. Without this the slider moved the size and left the mass alone, and the model
    # answered by inventing 19% more density -- which is the studio's own test for a typed number:
    # move a free number at the top and anything that fails to move downstream was never derived.
    m_hand = dl["mass_frac"] * m_body * ride ** 3
    # the hand as a palm slab plus five tapering digits, all at one density
    area = (Bw - D) * D + math.pi * (D / 2.0) ** 2          # the stadium's own area
    V_palm = area * wrist_to_mcp
    parts = [(V_palm, wrist_to_mcp / 2.0, (wrist_to_mcp ** 2 + D * D) / 12.0)]
    for d in DIGITS:
        x = wrist_to_mcp
        ss = segs[d]
        for i, (hgt, r1) in enumerate(ss):
            r2 = ss[i + 1][1] if i + 1 < len(ss) else r1 * 0.75
            v = frustum(hgt, r1, r2)
            cz = frustum_com(hgt, r1, r2)
            k2 = hgt * hgt / 12.0 + 0.25 * ((r1 + r2) / 2.0) ** 2
            parts.append((v, x + cz, k2))
            x += hgt
    V = sum(p[0] for p in parts)
    rho = m_hand / V
    com = sum(p[0] * p[1] for p in parts) / V
    I_wrist = rho * sum(v * (k2 + x * x) for v, x, k2 in parts)
    I_com = rho * sum(v * (k2 + (x - com) ** 2) for v, x, k2 in parts)
    k_com = math.sqrt(I_com / m_hand)

    # ── 7. ITS OWN CLOCK. A finger is a compound pendulum hinged at its knuckle, and it is the SAME
    #    law that set this body's cadence one membrane up -- T = 2*pi*sqrt(I/(m*g*d)). So the hand's
    #    rhythm is gravity's, and it changes on another world exactly the way a stride does.
    mf = 0.0
    nf = 0.0
    If = 0.0
    x = 0.0
    ss = segs["middle"]
    for i, (hgt, r1) in enumerate(ss):
        r2 = ss[i + 1][1] if i + 1 < len(ss) else r1 * 0.75
        v = frustum(hgt, r1, r2)
        mm = rho * v
        cz = frustum_com(hgt, r1, r2)
        k2 = hgt * hgt / 12.0 + 0.25 * ((r1 + r2) / 2.0) ** 2
        mf += mm
        nf += mm * (x + cz)
        If += mm * (k2 + (x + cz) ** 2)
        x += hgt
    d_com = nf / mf
    T_finger = 2.0 * math.pi * math.sqrt(If / (mf * g * d_com))

    out = {
        # ITS REAL SIZE: a hand is a hand.
        "extent_m": L,
        # ITS OWN DURATION: one free swing of a finger about its knuckle, there and back. Derived,
        # gravity-coupled, and the same pendulum the leg uses -- so the hand's clock and the walk's
        # clock come from one law at two scales.
        "duration_s": T_finger,

        # ── the outside of the hand (ANSUR II, n = 4,082)
        "hand_length_m": L,
        "hand_breadth_m": Bw,
        "hand_circumference_m": Cc,
        "hand_thickness_m": D,
        "palm_length_to_crease_m": palm_crease,
        "hand_over_stature_ratio": frac,
        "hand_over_stature_median_ratio": AN["hand_length"]["median"],
        "hand_over_stature_sd_ratio": AN["hand_length"]["sd"],
        "hand_over_stature_p5_ratio": f_lo,
        "hand_over_stature_p95_ratio": f_hi,
        "hand_over_stature_cv_pct": 100.0 * AN["hand_length"]["sd"] / AN["hand_length"]["mean"],
        "breadth_over_stature_ratio": AN["hand_breadth"]["median"],
        "circumference_over_stature_ratio": AN["hand_circumference"]["median"],
        "palm_over_hand_ratio": AN["palm_over_hand"]["median"],
        "breadth_over_length_ratio": AN["breadth_over_length"]["median"],
        "ansur_subject_count": AN["n"],
        "anthropometry_source": ANSUR_CITE,
        "slab_bias_ratio": slab_bias,
        "thickness_rectangle_m": (Cc - 2.0 * Bw) / 2.0,
        "hand_size_draw_frac": size,

        # ── the inside: where the joints actually are
        "wrist_to_mcp_m": wrist_to_mcp,
        "knuckle_span_m": knuckle_span,
        "linkage_m": linkage,
        "crease_to_mcp_offset_m": crease_offset,
        "crease_offset_over_hand_ratio": crease_offset / L,
        "finger_length_at_crease_m": L - palm_crease,
        "finger_length_at_joint_m": finger_len["middle"],
        "finger_understated_by_crease_pct": 100.0 * (finger_len["middle"] - (L - palm_crease))
                                            / finger_len["middle"],
        "model_scale_length_ratio": s_len,
        "model_scale_width_ratio": s_wid,
        "model_breadth_over_length_ratio": B_model / L_model,
        "skeleton_source": MYOHAND_CITE,
        "model_rotations_in_hand_count": MY["rotations_in_hand"],

        # phalanx lengths, out from the knuckle, for every digit
        "phalanx_lengths_m": {d: [round(a, 6) for a, _ in segs[d]] for d in DIGITS},
        "phalanx_radii_m": {d: [round(r, 6) for _, r in segs[d]] for d in DIGITS},
        "digit_length_m": {d: finger_len[d] for d in DIGITS},
        "phalanx_taper_ratio": [segs["middle"][1][0] / segs["middle"][0][0],
                                segs["middle"][2][0] / segs["middle"][1][0]],

        # ── how many ways it bends
        "bone_count": len(MY["carpals"]) + len(MY["metacarpals"]) + len(MY["phalanges"]),
        "carpal_count": len(MY["carpals"]),
        "metacarpal_count": len(MY["metacarpals"]),
        "phalanx_count": len(MY["phalanges"]),
        "dof_count": len(joints),
        "dof_wrist_count": len(wrist_j),
        "dof_thumb_count": len(thumb_j),
        "dof_finger_count": len(finger_j),
        "rom_total_rad": rom_total,
        "rom_mean_rad": rom_total / len(joints),
        # CITED, NOT DERIVED, and the only such claim in this chapter.
        "synergy_dims_cited_count": 2,
        "synergy_variance_cited_frac": 0.80,
        "coupling_source": ("Santello, Flanders & Soechting 1998, J Neurosci 18(23):10105-10115 -- "
                            "two postural synergies span >80% of static hand-posture variance. "
                            "QUOTED: the paper is not in this repo and nothing here measured it."),

        # ── what it can reach
        "fingertip_reach_m": reach,
        "reach_over_hand_ratio": reach / L,
        "workspace_m3": ws_box,
        "workspace_hull_m3": ws_hull,
        "workspace_grain_m": grain,
        "workspace_over_hand_cubed_ratio": ws_box / L ** 3,
        "workspace_bracket_ratio": ws_hull / ws_box if ws_box > 0 else float("nan"),
        "workspace_samples_count": N,
        "aperture_max_m": gaps["index"][1],
        "aperture_min_m": gaps["index"][0],
        "aperture_spread_m": spread,
        "aperture_over_hand_ratio": spread / L,
        "thumb_reach_m": thumb_reach,
        "thumb_reach_over_hand_ratio": thumb_reach / L,
        "opposition_gap_m": {f: gaps[f][0] for f in gaps},
        "enclosable_cylinder_m": enclose_d,

        # ── the lever
        "moment_arm_mcp_m": a3["mcp"],
        "moment_arm_pip_m": a3["pip"],
        "moment_arm_dip_m": a3["dip"],
        "moment_arm_index_m": [arms["index"]["mcp"], arms["index"]["pip"], arms["index"]["dip"]],
        # THE MODEL'S OWN, UNSTRETCHED. The scaled numbers above are this hand's; these are the
        # hand the model was built from, and the gap between them is entirely `model_scale_width`.
        # Both are published because a reader checking against a cadaver paper should be able to see
        # which one they are looking at.
        "moment_arm_model_mcp_m": a3["mcp"] / s_wid,
        "moment_arm_model_pip_m": a3["pip"] / s_wid,
        "moment_arm_model_dip_m": a3["dip"] / s_wid,
        "moment_arm_skin_bound_m": arm_bound,
        "moment_arm_inside_bound_ratio": a3["mcp"] / arm_bound,
        "tip_lever_mcp_m": l_prox,
        "tip_lever_pip_m": l_mid,
        "tip_lever_dip_m": l_dist,
        "tendon_per_tip_mcp_ratio": ratio["mcp"],
        "tendon_per_tip_pip_ratio": ratio["pip"],
        "tendon_per_tip_dip_ratio": ratio["dip"],
        "binding_joint": binding,
        "tendon_per_tip_ratio": ratio[binding],

        # ── where the mass is
        "hand_mass_kg": m_hand,
        "both_hands_mass_kg": 2.0 * m_hand,
        "hand_mass_frac": dl["mass_frac"],
        "hand_mass_scale_ratio": ride ** 3,
        "hand_volume_m3": V,
        "hand_density_kg_m3": rho,
        # SOURCED, NOT DERIVED: whole-body density by hydrostatic weighing is ~1050 kg/m3 for a lean
        # adult (Siri 1961; Brozek et al. 1963 -- the two-compartment body-composition standards).
        # It is here only so that the volume this chapter's geometry misses is a NUMBER instead of
        # an apology.
        "tissue_density_kg_m3": 1050.0,
        "hand_volume_expected_m3": m_hand / 1050.0,
        "volume_shortfall_pct": 100.0 * (1.0 - V / (m_hand / 1050.0)),
        "hand_com_from_wrist_m": com,
        "hand_com_over_length_ratio": com / L,
        "hand_inertia_wrist_kgm2": I_wrist,
        "hand_inertia_com_kgm2": I_com,
        "hand_gyration_m": k_com,
        "hand_gyration_over_length_ratio": k_com / L,
        "rod_bound_ratio": 1.0 / math.sqrt(12.0),
        "de_leva_gyration_ratio": dl["gyration"][0],
        "de_leva_com_ratio": dl["com_frac"],
        "mass_source": dl["source"],
        "finger_mass_kg": mf,
        "finger_com_from_mcp_m": d_com,
        "finger_inertia_mcp_kgm2": If,
        "finger_swing_period_s": T_finger,
        # per MINUTE, not per second: `_hz` is a unit no table in this story reads, and an unreadable
        # unit is exactly what the folding audit exists to refuse. Same number, bindable.
        "finger_swing_rate_per_min": 60.0 / T_finger,

        # ── carried on, so a child never has to reach past this membrane
        "height_m": h,
        "g": g,
        "S_earth": float(parent.get("S_earth", 1.0)),
        "skin_albedo_rgb": list(parent.get("skin_albedo_rgb", [0.33, 0.20, 0.12])),
        "thumb_opposition_rad": oppose_q,
        "index_at_opposition_rad": index_q,
    }
    return out


def _site(model, name):
    """A tendon waypoint in the wrist's frame. Raises on a name that is not there, rather than
    returning the origin -- a silent zero here would put a tendon through the middle of the joint
    and report an infinite mechanical advantage."""
    for nm, b in model["bodies"].items():
        if name in b["sites"]:
            return model["world"][nm] + b["sites"][name]
    raise KeyError(f"{name!r} is not a site in the hand model")


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE MATTER -- a hand opening and closing through the range this chapter derived
# ════════════════════════════════════════════════════════════════════════════════════════════════
def emit(nums, t=1.0):
    """ONE FULL OPEN-CLOSE CYCLE, at the pendulum period this chapter derived.

    LOCAL UNITS: 1.0 is the hand's length, wrist to fingertip. +Y is distal, +X across the palm,
    +Z out of the palm.

    WHAT IS BEING DRAWN, and every part of it is a published number:
      * the palm, a slab of the derived breadth and the derived thickness;
      * five digits, each a chain of the derived phalanx lengths and radii;
      * every joint driven from its OWN measured range -- there is no animation curve, the closure
        fraction is a scalar and the range does the rest;
      * the four fingers fanning about the third ray, because that is where abduction is measured
        from;
      * the thumb travelling to the OPPOSITION POSE this chapter searched for -- the posture that
        brings its tip to the index tip -- so the movie's subject is the one structural fact that
        makes this a hand and not a paw;
      * two bright marks on the tips that are closing, and the gap between them, which IS the
        aperture number;
      * a pale trail behind each fingertip: the workspace, drawn by the thing that sweeps it.

    IT IS A MOVIE, NOT A PHOTOGRAPH. The closure is `0.5 - 0.5*cos(2*pi*t)`, so t = 0 is a flat open
    hand, t = 0.5 is a closed one, and t = 1 is open again -- one period of the finger pendulum,
    which is what `duration_s` says this scene lasts."""
    from matter import blank, lit, SOLID, GLOW, AR, AB

    L = float(nums["hand_length_m"])
    D = float(nums["hand_thickness_m"]) / L
    palm = float(nums["wrist_to_mcp_m"]) / L
    LK = nums["linkage_m"]

    c = 0.5 - 0.5 * math.cos(2.0 * math.pi * float(t))        # closure: 0 open, 1 closed

    P, kind, rr = [], [], []

    def tube(a, b, r, k, n=26):
        """A segment of finger, as a short cloud of grains between two joints."""
        a = np.asarray(a, float)
        b = np.asarray(b, float)
        u = np.linspace(0.0, 1.0, n)[:, None]
        line = a[None] + (b - a)[None] * u
        ang = np.linspace(0.0, 2.0 * math.pi, 7)[:-1]
        ax = (b - a) / max(np.linalg.norm(b - a), 1e-9)
        p1 = np.cross(ax, [0.0, 0.0, 1.0])
        p1 = p1 / max(np.linalg.norm(p1), 1e-9)
        p2 = np.cross(ax, p1)
        ring = (np.cos(ang)[:, None] * p1[None] + np.sin(ang)[:, None] * p2[None]) * r
        pts = (line[:, None, :] + ring[None, :, :]).reshape(-1, 3)
        P.append(pts)
        kind.append(np.full(len(pts), k))
        rr.append(np.full(len(pts), r * 0.55))

    # WHERE EACH DIGIT IS TRAVELLING TO, and only two of them are special. The thumb and the index
    # go to the OPPOSITION POSE `derive()` searched for -- the two sets of joint angles that bring
    # their tips together -- so the movie ends on the fact this chapter is about. The other three
    # close through their own measured range, spreading about the third ray on the way open, because
    # that is where abduction is measured from.
    pose_end = dict(nums["thumb_opposition_rad"])
    pose_end.update(nums["index_at_opposition_rad"])
    for d in ("middle", "ring", "little"):
        for js in LK[d]["joints"]:
            for jn in js:
                pose_end.setdefault(jn, math.radians(90.0) if jn.endswith("_flexion") else 0.0)
    pose_open = {}
    for d in ("index", "middle", "ring", "little"):
        for js in LK[d]["joints"]:
            for jn in js:
                if jn.endswith("_abduction"):
                    pose_open[jn] = FAN[d] * math.radians(15.0)   # the model's own abduction range

    def rot(axis, q):
        a = np.asarray(axis, float)
        c_, s_ = math.cos(q), math.sin(q)
        K = np.array([[0.0, -a[2], a[1]], [a[2], 0.0, -a[0]], [-a[1], a[0], 0.0]])
        return np.eye(3) + s_ * K + (1.0 - c_) * (K @ K)

    # THE MODEL'S FINGERS POINT ALONG -Y. Turning the whole hand half a turn about X puts them along
    # +Y for the viewer. It is a ROTATION and not a sign flip on Y alone -- negating one axis is a
    # reflection, and a reflected right hand is a left hand, which is a body this chapter did not
    # derive.
    FLIP = np.diag([1.0, -1.0, -1.0])

    def chainpts(d, cl):
        """THE PUBLISHED LINKAGE, at closure `cl`: start at the root, turn each joint by its own
        share of the pose, walk down the bone. This is the same forward kinematics `derive()` used
        to sweep the workspace and to find the opposition pose, reading the same axes -- so the
        picture cannot disagree with the numbers, because there is only one chain."""
        lk = LK[d]
        R = np.eye(3)
        p = np.asarray(lk["root_m"], float) / L
        pts = [FLIP @ p]
        for lvl, (names, axes) in enumerate(zip(lk["joints"], lk["axes"])):
            for jn, ax in zip(names, axes):
                q = pose_open.get(jn, 0.0) * (1.0 - cl) + pose_end.get(jn, 0.0) * cl
                R = R @ rot(ax, q)
            step = (np.asarray(lk["bones_m"][lvl], float) / L if lvl < len(lk["bones_m"])
                    else np.asarray(lk["tip_m"], float) / L)
            p = p + R @ step
            pts.append(FLIP @ p)
        return pts

    tip_now, trail = {}, {}
    for d in ("index", "middle", "ring", "little", "thumb"):
        radii = [r / L for r in LK[d]["radii_m"]]
        pts = chainpts(d, c)
        for i in range(len(pts) - 1):
            tube(pts[i], pts[i + 1], radii[min(i, len(radii) - 1)], 0)
        tip_now[d] = pts[-1]
        trail[d] = np.array([chainpts(d, u)[-1] for u in np.linspace(0.0, c, 22)])

    # ── THE PALM: a stadium slab of the derived thickness, spanning the knuckles it actually
    #    carries. Its width is read off where the linkage puts the finger roots, NOT from ANSUR's
    #    breadth, because a palm drawn wider than the fingers rooted in it is a palm this derivation
    #    did not produce. The skeleton is narrower than the ANSUR median hand and both numbers are
    #    published -- `knuckle_span_m` and `hand_breadth_m` -- so the disagreement is readable rather
    #    than quietly split down the middle.
    roots = np.array([np.asarray(LK[d]["root_m"], float) / L for d in ("index", "little")])
    Bw = abs(roots[0][0] - roots[1][0]) + 2.0 * (LK["index"]["radii_m"][0] / L)
    nu, nv = 30, 16
    u = np.linspace(-0.02, palm, nu)
    th = np.linspace(0.0, 2.0 * math.pi, nv, endpoint=False)
    flat = max(Bw - D, 0.0) / 2.0
    mid = 0.5 * (roots[0][0] + roots[1][0])
    px = mid + np.where(np.cos(th) >= 0, flat, -flat) + (D / 2.0) * np.cos(th)
    pz = (D / 2.0) * np.sin(th)
    palm_pts = np.stack([np.repeat(px, nu), np.tile(u, nv), np.repeat(pz, nu)], 1)
    P.append(palm_pts)
    kind.append(np.zeros(len(palm_pts)))
    rr.append(np.full(len(palm_pts), D * 0.16))

    # ── THE TRAILS: where each fingertip has already been. The workspace, self-drawn.
    for d, tr in trail.items():
        if len(tr) > 1:
            P.append(tr)
            kind.append(np.full(len(tr), 3))
            rr.append(np.full(len(tr), 0.006))

    # ── THE APERTURE: the two tips that are closing, and the span between them.
    a, b = tip_now["thumb"], tip_now["index"]
    span = np.linalg.norm(b - a)
    bar = a[None] + (b - a)[None] * np.linspace(0.0, 1.0, 24)[:, None]
    P.append(bar)
    kind.append(np.full(len(bar), 2))
    rr.append(np.full(len(bar), 0.008))
    P.append(np.stack([a, b], 0))
    kind.append(np.full(2, 4))
    rr.append(np.full(2, 0.019))

    Pts = np.concatenate(P, 0)
    kind = np.concatenate(kind)
    rr = np.concatenate(rr)

    n = len(Pts)
    buf = blank(n)
    buf[:, 0:3] = Pts
    nrm = np.zeros((n, 3), np.float32)
    nrm[:, 2] = 1.0
    buf[:, 21:24] = nrm

    skin = np.asarray(nums.get("skin_albedo_rgb", [0.33, 0.20, 0.12]), np.float32)
    alb = np.zeros((n, 3), np.float32)
    alb[kind == 0] = skin                                        # flesh: the parent's own measured skin
    alb[kind == 2] = np.array([0.95, 0.80, 0.30], np.float32)     # the aperture it is closing
    alb[kind == 3] = np.array([0.42, 0.52, 0.72], np.float32)     # where a fingertip has been
    alb[kind == 4] = np.array([1.00, 0.55, 0.18], np.float32)     # the two tips that meet
    S = float(nums.get("S_earth", 1.0))
    buf[:, 16:19] = lit(alb, S * 0.85 + 0.15, e_ref=S, tone=0.45)
    buf[:, AR:AB + 1] = alb
    buf[:, 19] = np.where(kind == 3, 0.42, 0.97)                 # the trail is faint
    buf[:, 20] = rr
    buf[:, 11] = np.where(kind >= 2, GLOW, SOLID)
    return buf


def measure(nums):
    """Facts a reader can check without trusting a word of the prose above.

    THREE OF THESE ARE CHECKS THIS CHAPTER WAS NOT FITTED TO, and one of them FAILS."""
    ma = nums["moment_arm_mcp_m"] * 1000.0
    return {
        # ── THE CHECK NOTHING WAS FITTED TO #1: a moment arm derived from a model's tendon path,
        #    against cadaver measurements taken 40 years earlier. An et al. 1983 put the index
        #    flexor at roughly 8-10 mm at the knuckle, 6-8 at the middle joint, 4-5 at the tip.
        "moment_arm_mcp_mm": ma,
        "moment_arm_in_literature_band": 6.0 <= ma <= 11.0,
        # ── #2: and it must fit INSIDE the finger. ANSUR says four fingers share 88 mm of breadth,
        #    so a tendon cannot be more than 11 mm from the bone. Two unrelated sources, one hand.
        "moment_arm_inside_skin": nums["moment_arm_inside_bound_ratio"] < 1.0,
        "moment_arm_inside_bound_ratio": nums["moment_arm_inside_bound_ratio"],
        # ── #3: a hand's radius of gyration cannot exceed a rod's. This is the check that REFUSES
        #    de Leva's tabulated 0.628 -- 0.628 of hand length is 12.1 cm for a hand 19.3 cm long,
        #    and no body of that length can have it. His table is normalised to a different length
        #    than ANSUR's hand, so this chapter does not use it. A number that cannot be bound is
        #    left unbound.
        "gyration_under_rod_bound": nums["hand_gyration_over_length_ratio"] < nums["rod_bound_ratio"],
        "hand_gyration_over_length_ratio": nums["hand_gyration_over_length_ratio"],
        "de_leva_gyration_would_exceed_rod": nums["de_leva_gyration_ratio"] > nums["rod_bound_ratio"],
        # ── THE ONE THAT FAILS, kept because deleting it would delete the finding: a slab and five
        #    cones has no thenar and no hypothenar -- the two muscle bellies that are most of what
        #    makes a palm a palm, and one of which is the very muscle that opposes the thumb. So the
        #    volume is 29% short and the density needed to carry de Leva's mass comes out at 1457,
        #    which is denser than bone-free tissue can be. The SHAPE is wrong, not the mass.
        "hand_density_kg_m3": nums["hand_density_kg_m3"],
        "density_within_tissue_range": 950.0 <= nums["hand_density_kg_m3"] <= 1200.0,
        "volume_shortfall_pct": nums["volume_shortfall_pct"],
        # ── the structure itself
        "bones_are_27": nums["bone_count"] == 27,
        "dof_count": nums["dof_count"],
        "dof_split_sums": (nums["dof_wrist_count"] + nums["dof_thumb_count"]
                           + nums["dof_finger_count"]) == nums["dof_count"],
        "model_is_pure_translation": nums["model_rotations_in_hand_count"] == 0,
        # ── opposition: the thumb reaches every fingertip. That is what makes it a hand.
        "opposes_all_four": all(v < 0.006 for v in nums["opposition_gap_m"].values()),
        "opposition_gap_max_mm": 1000.0 * max(nums["opposition_gap_m"].values()),
        # ── the landmark trap, as a number
        "crease_offset_mm": 1000.0 * nums["crease_to_mcp_offset_m"],
        "finger_understated_by_crease_pct": nums["finger_understated_by_crease_pct"],
        # ── the lever, and which joint is the hard one
        "binding_joint": nums["binding_joint"],
        "tendon_per_tip_ratio": nums["tendon_per_tip_ratio"],
        "binding_joint_is_mcp": nums["binding_joint"] == "mcp",
        # ── the workspace, honestly bracketed rather than stated
        "workspace_cm3": 1e6 * nums["workspace_m3"],
        "workspace_bracket_ratio": nums["workspace_bracket_ratio"],
        "workspace_is_bracketed_not_converged": True,
        # ── THE SECOND THING THAT DOES NOT PASS. A spread hand's thumb-to-index span reads 0.95 of
        #    hand length; on a real hand it is nearer 0.7. The suspect is published beside it -- this
        #    model's thumb reaches 0.73 of a hand length from the wrist, which is a long thumb, and
        #    every span involving it inherits that. Named, not smoothed.
        "aperture_over_hand_ratio": nums["aperture_over_hand_ratio"],
        "spread_span_plausible": nums["aperture_over_hand_ratio"] < 0.80,
        "thumb_reach_over_hand_ratio": nums["thumb_reach_over_hand_ratio"],
        # ── and its own rhythm needs no gearing
        "period_in_human_band": 0.04 <= nums["duration_s"] <= 10.0,
    }
