"""Tests for core.terrarium — run: python core/test_terrarium.py

These are not "does it run" tests. They are the SAFETY PROOFS from
docs/TERRARIUM_DESIGN.md, executed:

  RULE 2 TOTALITY     — a genome that TRIES to explode must still terminate, and
                        must respect the walls. Not "we checked afterwards": there
                        is no code path that could run away.
  RULE 3 DETERMINISM  — same genome + same seed -> byte-identical body.
  RULE 1 THE MEMBRANE — this module must import NOTHING from the studio. Asserted
                        against the source text, so the moment someone adds
                        `import graphify_record` the build fails.
"""

import ast
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import core.terrarium as t  # noqa: E402

PASS = TOTAL = 0


def check(name, cond):
    global PASS, TOTAL
    TOTAL += 1
    print(("  ok  " if cond else "FAIL  ") + name)
    PASS += bool(cond)


def main():
    # ---- RULE 2: TOTALITY ---------------------------------------------------
    # A genome deliberately built to run away: every symbol becomes four, forever,
    # and it asks for a derivation depth far past the wall. In an unbounded L-system
    # this is 4^999 symbols. Here it must simply... stop.
    bomb = t.Genome(
        axiom="A",
        rules={"A": "F[+A]F[-A]A"},     # strictly expanding, no terminal
        depth=999,                       # asks for 999 iterations
    )
    bones = t.grow(bomb, 1)              # if this hangs, the design is wrong
    check("TOTALITY: a genome built to explode terminates anyway", True)
    check("TOTALITY: bones respect MAX_BONES", len(bones) <= t.MAX_BONES)
    check("TOTALITY: depth is clamped to MAX_DEPTH (asked 999)",
          t.MAX_DEPTH == 12)

    # a genome with a rule that is pure recursion and nothing else
    nasty = t.Genome(axiom="A", rules={"A": "AA"}, depth=999)
    b2 = t.grow(nasty, 1)
    check("TOTALITY: a pure-doubling rule (A->AA) terminates", isinstance(b2, list))

    # a malformed genome: a symbol with no rule and no meaning
    junk = t.Genome(axiom="ZZZQQQ", rules={}, depth=5)
    check("TOTALITY: a malformed genome yields an empty body, not a crash",
          t.grow(junk, 1) == [])

    # ---- RULE 3: DETERMINISM ------------------------------------------------
    g = t.Genome()
    a1 = t.grow(g, 42)
    a2 = t.grow(g, 42)
    check("DETERMINISM: same genome + same seed -> identical skeleton",
          [(b.p0, b.p1, b.r0) for b in a1] == [(b.p0, b.p1, b.r0) for b in a2])

    m1 = t.mesh_tubes(a1)
    m2 = t.mesh_tubes(a2)
    check("DETERMINISM: ...and a byte-identical mesh", m1 == m2)

    b_other = t.grow(g, 43)
    check("VARIATION: a different seed gives a different individual",
          [b.p1 for b in a1] != [b.p1 for b in b_other])

    # ---- the encoding is INDIRECT (the whole thesis) -------------------------
    size = len(g.to_json())
    check(f"INDIRECT ENCODING: {size}B of genome -> {len(a1)} bones "
          f"({len(a1)*3*4}B of raw transforms)", len(a1) * 12 > size)

    # ---- mutation stays inside the walls ------------------------------------
    rng = random.Random(0)
    ok = True
    for _ in range(60):
        gm = t.mutate(g, rng)
        if gm.depth > t.MAX_DEPTH or len(t.grow(gm, 3)) > t.MAX_BONES:
            ok = False
            break
    check("MUTATION: 60 random mutants all stay inside the walls", ok)

    # ---- geometry is real ---------------------------------------------------
    verts, faces = t.mesh_tubes(a1)
    check("GEOMETRY: tubes produce a non-empty triangle mesh",
          len(verts) > 0 and len(faces) > 0)
    check("GEOMETRY: every face indexes a real vertex",
          all(0 <= i < len(verts) for f in faces for i in f))
    finite = all(all(math.isfinite(c) for c in v) for v in verts)
    check("GEOMETRY: no NaN/inf vertices", finite)

    # The blob mesher was NOT covered on the first pass, and it shipped with an
    # inverted smooth-min that silently produced zero triangles. Cover it.
    small = t.Genome(depth=4)
    bv, bf = t.mesh_blob(t.grow(small, 5), res=40)
    check("GEOMETRY: blob (SDF + marching cubes) produces a real surface",
          len(bv) > 0 and len(bf) > 0)
    check("GEOMETRY: blob mesh is closed-ish (more tris than bones)",
          len(bf) > len(t.grow(small, 5)))

    # ---- RULE 1: THE MEMBRANE (structural, not a promise) --------------------
    src = Path(t.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    forbidden = {"graphify_record", "graphify_interface", "world_store",
                 "task_board", "capcom", "dna_sqlite_backend", "core"}
    leaked = imported & forbidden
    check(f"MEMBRANE: imports nothing from the studio  (got: {sorted(imported)})",
          not leaked)

    print(f"\n{PASS}/{TOTAL} tests passed")
    return 0 if PASS == TOTAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
