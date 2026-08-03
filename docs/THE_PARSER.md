# THE PARSER — the Phase D grammar over button state

> Membrane stated 2026-08-04, before the build. The parser is Layer 4 of
> `docs/THE_COMPILER.md` — *intent → program* — and the design is
> `docs/CONTROLLER_MAP.md`: ~12 verbs, two binding surfaces, ONE input-agnostic
> formula layer. What exists is v1, honestly labelled in `tools/f3_stand.py`:
> `BUTTONS = {"stand": lambda ...}` — one button, hard-wired. Milestone M4
> replaces it with the grammar itself. The parser is built last of the layers
> *because* it is the only one that cannot be wrong in an interesting way — a
> mis-parse produces the wrong program and you see it immediately — so its
> falsifiers are structural, not numerical.

---

## RULE 0 — THE THEORY

**STATEMENT.** Button handling is a grammar of three DATA tables and one
composition rule, and nothing else:

1. **Binding** — physical input → verb. A table, written twice (keyboard+mouse
   PRIMARY, Xbox gamepad port), never code. (`CONTROLLER_MAP.md`'s own table.)
2. **State** — verb → held / value. The button is a fact; the formula asks for
   it; nothing physical reaches the formula layer.
3. **Formula layer** — verb → formula (a state machine over atoms). One layer,
   input-agnostic. A verb with no trained formula is REGISTERED ANYWAY and
   REFUSES BY NAME — the same discipline `derive_ligaments` keeps: a refusal
   with a reason, never a silent zero.
4. **Composition** — formulas declare EXCLUSIVE or OVERLAY. v2 registers only
   exclusive formulas (stand is the only trained one); two exclusive verbs held
   at once resolve by registration order AND the conflict is named in the trace.
   A rule stated is a rule falsifiable; a silent priority is neither.

**PREDICTION.** `tools/parser_tests.py` passes: the stand port routed through
the parser produces a **bit-identical** control signal to v1's lambda over a
sweep of (z, pitch); both binding tables map onto the identical verb set with
zero formula-layer code; every unimplemented verb refuses by name; and
`tools/f3_stand.py` running THROUGH the parser (its local `BUTTONS` dict
deleted) reports the unchanged F3 verdict — PASS.

**FALSIFIERS.** Named before the build:
1. If the parser's stand control differs from v1's by ANY amount on any sample
   of the sweep, the grammar alters semantics it was only meant to carry — the
   theory loses.
2. If either binding table requires formula-layer code (an import, an if, a
   special case) to function, the "one layer, two bindings" claim loses.
3. If any registered-but-unimplemented verb can drive the muscles silently —
   zero command, crash, or a default — the grammar's honesty claim loses.

---

## THE DESIGN (nothing in it is new — the map already designed it)

Verbs, from the map's binding table: `MOVE · SPRINT · LOOK · JUMP · CROUCH ·
GRAB · ACTION · AIM · USE · LHAND · RHAND · STANCE`. The formula registry maps
verb → formula; v2 ships `stand` (the trained port, `stand_theta.npy`, the
inverted-pendulum formula `a0 + kh·(tgt−z) + kp·pitch`) and names every other
verb's refusal with its milestone (MOVE's formula is M3's STEP+PLANT+BALANCE;
GRAB's is M8's REACH+GRIP+BRACE). The registry is where programs arrive as the
atoms are trained — the parser does not change when they do, which is the
entire point of putting it last.

## THE VERDICT (2026-08-04): **PASS — the grammar carries, refuses, and names.**

Built: `tools/parser.py` (the three tables + one rule), `tools/parser_tests.py`
(eight checks), `tools/f3_stand.py` rewired through it (its local `BUTTONS`
dict and `stand_formula` deleted — the button's content lives in the layer now,
`parser.stand_formula_fn`, not in the harness). Measured:

- **Falsifier 1 — bit-identity: HOLDS.** Parser stand == v1 stand, max |diff|
  0.000e+00 over 135 (z, pitch) samples. The grammar altered nothing.
- **Falsifier 2 — bindings are data: HOLDS.** Keyboard and gamepad tables cover
  the identical 12-verb set with zero formula-layer code; an unbound physical
  input is a no-op, and the gamepad table drives verbs identically (X → GRAB).
- **Falsifier 3 — named refusal: HOLDS.** All 12 map verbs held at once refuse
  BY NAME with their milestone in the reason; the one trained formula drives;
  a verb the map does not name (FLY) is refused by the grammar itself.
- **The composition rule, exercised:** two exclusive formulas held →
  registration order wins, and the loser is named in the trace
  `conflicts [('STAND', 'MOVE')]`.
- **The slice's letter, through the grammar:** `tools/f3_stand.py` rerun —
  pelvis MIN 102.3%, CoM 0.80×, slump 1.16 s, **F3 PASS, unchanged**. The
  residual port-contract debt (7 joints, worst `subtalar_angle_r` 1.16) is the
  leg-ligament work list, not this membrane's.

What the grammar buys, concretely: M3's walking program arrives as
`reg["MOVE"] = Formula("MOVE", step_plant_balance, EXCLUSIVE)` — one line in
the registry, no parser change — and M8's grab the same. The parser is done
being built; from here it is only filled.
