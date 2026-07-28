"""binding.py -- S4 BINDING: the generator must CONSUME the variables the term traced.

THE HOLE THIS CLOSES (found 2026-07-28, by the operator's eye, not by the machine):
`theTerrain` traced 39 variables, saturated the discovery curve (Chao2 complete), and classified
every one as PHYSICS -- and then its appearance was rendered from `_fbm()` RANDOM NOISE plus a
colour ramp. Of 39 variables, ~5 were physically present. The relief was 40x Earth's
(0.13 of radius; Earth is 0.0031) and the elevation histogram was unimodal where a terrestrial
planet's is BIMODAL (two crust types, isostasy). Every gate passed. Only the human caught it.

The chain was: trace variables -> [ NOTHING ] -> appearance -> converge. The missing link is that
**the traced variables ARE the generator**. A term's appearance is a PROJECTION of the code that
makes the thing; if the code never reads the variables, the picture is decoration and the whole
saturation/classify effort did no work.

WHAT THIS GATE PROVES, AND WHAT IT DOES NOT -- stated plainly so the gate cannot become the
rubber stamp it exists to remove:
  * PROVES: the generator's CODE references the traced variable (identifier-level, AST-parsed).
  * DOES NOT PROVE: that it computes it CORRECTLY. Naming a noise field `elevation_field` passes.
    Catching a mislabeled implementation is the job of the two-messenger convergence, not this.
  * COMMENTS AND DOCSTRINGS ARE NOT COUNTED, deliberately. If prose counted, the gate would be
    passable by writing a comment -- which is precisely the failure mode it exists to prevent.
So this gate catches ABSENCE (the 5/39 case). It is strictly stronger than nothing and strictly
weaker than proof.

Run:  python ChimeraEngine/binding.py theTerrain
"""
from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# The floor is a HUMAN dial, not a physics constant. There is no measured baseline for "how much
# of a term's traced physics a faithful generator consumes", so this is taste until one exists --
# and taste terminates at the operator. Set low enough not to block honest work, high enough that
# a decorative render (theTerrain's noise globe: 5/39 = 0.13) cannot pass.
FLOOR = 0.60

# tokens that carry no discriminating meaning -- dropped before matching
_STOP = {"the", "a", "an", "of", "from", "to", "at", "on", "in", "by", "per", "is", "and", "or",
         "for", "with", "its", "it", "this", "that", "above", "below", "no"}
_MIN_PREFIX = 5          # how many leading chars must agree for two tokens to count as the same word
# Generic PROGRAMMING words carry no domain evidence -- a container called `spec` is not proof that
# the code computes a `spectrum`. (Caught on this gate's own first run: `spec` prefix-matched
# `spectrum` and falsely marked `spherical_harmonic_spectrum` CONSUMED in a generator built from
# random noise. A gate that flatters is the thing this gate exists to remove, so the bias is set
# toward STRICTNESS: a false negative only makes the gate harder to pass; a false positive is a
# rubber stamp.)
_GENERIC = {"spec", "buf", "arr", "val", "vals", "idx", "tmp", "out", "res", "data", "args",
            "kwargs", "self", "np", "rng", "obj", "item", "items", "parts", "cfg", "opts",
            "kind", "name", "term", "copy", "len", "range", "float", "int", "str", "min", "max"}


def _tokens(name: str) -> list:
    """Split a variable name into discriminating word tokens."""
    return [t for t in name.replace("-", "_").lower().split("_") if t and t not in _STOP]


def code_identifiers(fn) -> set:
    """Every identifier the function's CODE mentions -- names, args, attributes, keywords, and the
    string keys of subscripts (`spec["relief"]` is a real parameter read). Docstrings and comments
    are excluded by construction: comments never reach the AST, and bare string expressions
    (docstrings) are skipped, so prose cannot satisfy this gate."""
    import textwrap
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    out: set = set()
    doc_nodes = {n.value for n in ast.walk(tree) if isinstance(n, ast.Expr)
                 and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)}
    for node in ast.walk(tree):
        if node in doc_nodes:
            continue
        if isinstance(node, ast.Name):
            out.add(node.id)
        elif isinstance(node, ast.Attribute):
            out.add(node.attr)
        elif isinstance(node, ast.arg):
            out.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg:
            out.add(node.arg)
        elif isinstance(node, ast.FunctionDef):
            out.add(node.name)
        elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
                and isinstance(node.slice.value, str):
            out.add(node.slice.value)                     # spec["relief"] -- a genuine parameter read
    words: set = set()
    for ident in out:
        words.update(_tokens(ident))
    return words - _GENERIC


def _matches(token: str, words: set) -> bool:
    """Does a variable's word appear among the code's words? Exact, or a >= _MIN_PREFIX shared
    prefix (so `elev` in code satisfies `elevation` in the trace)."""
    if token in words:
        return True
    return any(w[:_MIN_PREFIX] == token[:_MIN_PREFIX]
               for w in words if len(w) >= _MIN_PREFIX and len(token) >= _MIN_PREFIX)


def generator_for(term: str):
    """The callable that BUILDS this term's appearance, or (None, reason)."""
    import splat_appearance as SA
    if term in getattr(SA, "COMPOSITIONS", {}):
        return None, ("composed"
                      if term not in SA.SCENES else "composed")
    spec = SA.SCENES.get(term)
    if not spec:
        return None, "no scene"
    builders = {"planet": SA._planet_buffers, "terrain": SA._terrain_buffers,
                "row": SA._row_buffers, "system": SA._system_buffers}
    fn = builders.get(spec.get("kind"))
    return (fn, "ok") if fn else (None, f"no builder for kind {spec.get('kind')!r}")


def check(term: str, variables: list, floor: float = FLOOR) -> dict:
    """Do the term's traced variables actually appear in the code that generates its appearance?"""
    fn, why = generator_for(term)
    if fn is None:
        if why == "composed":
            return {"applies": False, "pass": True, "term": term,
                    "detail": "composed from PROVEN children -- its matter is theirs, already bound"}
        return {"applies": True, "pass": False, "term": term, "coverage": 0.0,
                "detail": f"no generator to bind to ({why}) -- the appearance is not produced by any code"}
    if not variables:
        return {"applies": True, "pass": False, "term": term, "coverage": 0.0,
                "detail": "no variables traced -- nothing to bind"}
    words = code_identifiers(fn)
    covered, missing = [], []
    for v in variables:
        toks = _tokens(v)
        hits = [t for t in toks if _matches(t, words)]
        # a variable counts as CONSUMED when a MAJORITY of its discriminating words appear in code
        (covered if toks and len(hits) * 2 >= len(toks) else missing).append(v)
    cov = len(covered) / len(variables)
    ok = cov >= floor
    return {"applies": True, "pass": ok, "term": term, "coverage": round(cov, 3),
            "floor": floor, "generator": fn.__name__,
            "covered": covered, "missing": missing,
            "detail": (f"the generator `{fn.__name__}` consumes {len(covered)}/{len(variables)} "
                       f"traced variables ({cov:.0%}) -- {'>=' if ok else '<'} floor {floor:.0%}"
                       + ("" if ok else f". NOT CONSUMED: {', '.join(missing[:8])}"
                                        + (f" (+{len(missing)-8} more)" if len(missing) > 8 else "")))}


if __name__ == "__main__":
    import json
    term = sys.argv[1] if len(sys.argv) > 1 else "theTerrain"
    sys.path.insert(0, str(_HERE))
    from engine_state import Engine                            # the traced variables live here
    r = check(term, list(Engine()._vars(term)))
    print(json.dumps(r, indent=2))
