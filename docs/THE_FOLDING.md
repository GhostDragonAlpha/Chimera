# THE FOLDING — a serial that says what it can connect to

> The operator, 2026-07-31: *"What if we could label the solutions the way we do the serial numbers
> for the materials — the serial could be a way that helps it identify what it can connect to, as a
> kind of metaphor using protein folding."*

This is that, built. It is the second read after `Chimera/docs/THE_GROWTH.md`, and it is what makes
that document's **ruling 4** — *"each membrane is an intersection of ALL applicable physics; a
membrane ignoring a governing row is incomplete by construction"* — into something a machine can
check rather than a sentence a human has to remember.

---

## The metaphor is load-bearing

In a protein, the **sequence** determines the **fold**, the fold presents a **binding site**, and two
molecules bind when their surfaces are complementary. Proteins sharing a fold — a *domain family* —
are interchangeable in the same socket. And a protein can **misfold**: right sequence, wrong shape,
so it binds the wrong thing and the cell is poisoned by something that looked correct.

**Every serious defect found in this project on 2026-07-31 was a misfold** — the right quantity
docking at the wrong interface, silently:

| membrane | what bound where | cost |
|---|---|---|
| `theBiomes` | **294.19 Kelvin** into a table whose axis is **Celsius** | the whole planet, poles included, rendered as hot desert |
| `theHuman` | the foot at the **toe tip** where the law wants the **ball** | 3.6 cm of stature; read as a gait bug for weeks |
| `theAtmosphere` | scale height **0.05** of a radius where its own derivation says **0.00215** | 23× |
| `aTerraceMine` | `slag_fraction = 1.15` | a fraction above one, from a `* 0.0` that annihilated its own derivation |

Three different *kinds* of wrongness, so three checks — and each is earned by one of them.

---

## The three checks

**THE FOLD — the dimensional signature.** Says what may **substitute**. Two laws consuming a
temperature and producing a pressure share a fold; either can sit in that socket. Derived by hash,
never assigned: *a serial you can choose is a serial that can lie.*

**THE BOND — the exact unit, offset included.** Says what may **connect**. `K` and `degC` share a
fold and must never bond. A units table without offsets cannot represent theBiomes' bug, so it
cannot catch it.

**THE REGIME — the range the law holds over.** Catches what neither of the above can: a value of the
right dimension *and* the right unit that is simply not in this world. It is the only thing that
sees theAtmosphere's 23×.

### A fourth distinction the sweep forced

**A temperature difference is not a temperature.** `dT_equator_pole = 45` is a *span*: 45 K of
difference is also 45 °C of difference, because a span has no zero point to disagree about. It can
bond to neither absolute unit. Bond a span into an absolute socket and the planet is 45 K; bond an
absolute into a span socket and the gradient is 279. Same dimension, invisible to a dimension check.
The unit `dK` exists and refuses both.

---

## What a membrane must now do

**1. Every published number declares its unit.** Either in the key name — `extent_m`, `duration_s`,
`foot_pressure_kPa` — or in `story/data/units.json`. The suffix wins where present; a name carrying
its own unit cannot drift out of step with a table somewhere else.

**Currently 811 of 942 (86%).** The rest are invisible to every check below.

**2. Anything genuinely unreadable stays undeclared.** A guessed unit is *worse* than a missing one,
because it makes a bad bond look legal. `S` in `theEmptying` and `A` in `theHorizon` are left alone
on purpose, and reported.

**3. A law that wants binding declares a signature** in `story/folding.py` — what it consumes, what
it produces, the range it holds over, and the **name fragment** each symbol expects.

That last part is specificity, and it is not optional. The first run of this system claimed
"segment moments of inertia" binds to `aSaltOcean`, because every membrane publishes *something* in
metres and *something* in kilograms. **A site that binds everything is a site not doing its job.**
Unit is the *shape* of a binding site; the name is the *chemistry*, and both must match.

---

## Running it

```bash
python story/folding.py            # coverage, folds, what binds where
python story/folding.py audit      # misfolds — needs no signatures at all
python story/folding.py membrane theHuman
python tools/parse_physics_catalog.py --check
```

`audit` is the cheap one and the one to run habitually. It uses only the unit convention the
membranes already follow and asks a question needing nothing else: **does this value violate what
its own unit forbids?** Not *unlikely* — forbidden. A Kelvin below absolute zero. A negative mass. A
fraction outside 0–1. That check, at 57% coverage, found `slag_fraction = 1.15` in a membrane
committed the same day under `PROVEN`.

---

## What it deliberately does not do

**It does not infer signatures from equation text.** Proteins fold spontaneously from sequence; a
law's signature is *declared*. Parsing intent out of prose is a guessing machine, and this whole
catalog exists so that nothing in it is a guess.

**It does not score binding by similarity.** Protein binding is approximate and continuous; law
docking is exact — units match or they do not. A fuzzy matcher would reintroduce the silent-default
failure that made this project's own witnesses report three phantom defects in one afternoon.

---

## Where it stands

| | |
|---|---:|
| physics rows indexed (`story/data/physics_catalog.json`) | **158** across 23 branches |
| signatures declared | 10 (6.3%) |
| **rows nothing can dock to yet** | **148** |
| numbers declaring a unit | 811 / 942 (86%) |
| impossible values | 0 |
| inconsistent unit pairs | 0 |

**The 148 unbound rows are the work.** Each needs a declared signature, and each one that gets one
turns a line of a bibliography into something a membrane can be checked against.

---

## The dead-term signature — watch for this specifically

Three defects of one species appeared in a single day, two of them written by a language model and
one of them by the agent auditing the other:

```python
slag = 1.0 - metal_yield / max(fe_grade, 1e-9) * 0.0 + 0.15    # -> the constant 1.15
T_cmb = T_CMB_EARTH * (0.55 + 0.45 * heat / heat0 * (heat0 / heat) ** 0.0)   # -> ** 0.0 is 1
```

You write the real formula, something goes wrong mid-edit, a zero factor survives, and what remains
is **a plausible constant sitting under a real-looking derivation**. Plausibility is exactly why it
survives review — a wrong number under a formula that looks alive is invisible to reading.

A unit check does not care how plausible it looks.

---

*Built 2026-07-31. `story/folding.py`, `story/data/units.json`, `story/data/physics_catalog.json`,
`tools/parse_physics_catalog.py`.*
