# One file per branch, so declarations never collide

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

`folding.py` loads every `*.json` here and merges it with the seed set in `story/folding.py`.
Split by BRANCH — `classical_mechanics.json`, `optics.json`, `biophysics.json` — so several
writers can work at once. A shared dict is a merge conflict waiting to happen, and a conflict
inside a physics declaration is how a signature ends up on the wrong row, which is a misfold
committed by the tooling rather than by the physics.

## The shape

```json
{
  "_source": "who declared these and against which catalog",
  "E2.11": {
    "consumes": {"rho": "kg/m3", "g": "m/s2"},
    "produces": {"q": "Pa"},
    "keys":     {"rho": "density", "g": "g"},
    "regime":   {"q": [1e4, 1e7]},
    "note":     "what the law is, and what the regime bounds mean"
  }
}
```

- **`consumes` / `produces`** — symbol to unit. Units must exist in `folding.UNITS`.
- **`keys`** — SPECIFICITY, and it is not optional. The name fragment each symbol expects in a
  membrane's published keys. Unit alone is the *shape* of a binding site; the name is the
  *chemistry*. Without it, "segment moments of inertia" binds to an ocean, because every membrane
  publishes something in metres and something in kilograms. A site that binds everything is a site
  not doing its job.
- **`regime`** — the range the law is true over, in the produced/consumed unit. This is the only
  check that catches a value of the right dimension and the right unit that is simply not in this
  world — `theAtmosphere` drew its scale height 23x too thick and nothing else could see it.

## The rules

1. **Look the row id up. Do not remember it.** Read `story/data/physics_catalog.json`. Five of the
   first nine seeded signatures were attached to the wrong rows because they were typed from
   memory — E2.09 is "Turbulence", not Terzaghi. A serial assigned from memory instead of looked up
   is precisely the misfold this system exists to catch.
2. **Declare, never infer.** If a row's variables are not clear from its equation and source, leave
   it out. An unbound row is honest; a guessed signature makes a bad bond look legal.
3. **Check it binds to something real** with `python story/folding.py` — a signature that docks
   nowhere may be right and early, but a signature that docks *everywhere* is underspecified.
