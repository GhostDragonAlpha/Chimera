# THE LANGUAGE — the syntax of the hierarchy

**In plain words —** The folder tree is not storage, it is a language. A path is a sentence, a
membrane is a noun, and the four functions are its only verbs. Most of this grammar we invented
without noticing; this writes it down so it can be checked.

Marked **[DESIGNED]** where I am *deciding* rather than describing what we already do — those are
the places to argue with.

---

## 1. A path is a sentence

```
theZero/theHorizon/theEmptying/theCooling/theCloud/theGalaxy/theSolarSystem/theStar/aYellowStar
```

Read `/` as **"and inside it"**. That path *is* the sentence:

> the point you may not divide by, and inside it the fence it draws, and inside that the emptying,
> and inside that the cooling, and inside that a cloud, and inside that a galaxy, and inside that a
> system, and inside that the law of stars, and inside that a yellow one.

A membrane's **serial** is its path; its **story** is that sentence; its **meaning** is where it sits.
Nothing else needs to encode position, because position *is* the encoding.

## 2. Articles — the three kinds of noun

| form | means | example |
|---|---|---|
| **`theX`** | **the LAW** — what an X is, and what any X must satisfy | `theStar` |
| **`theXs`** | **the SET** — all the X's in this membrane, and how they are distributed | `thePlanets` |
| **`aX` / `anX`** | **an INSTANCE** — one that actually formed here | `aYellowStar` |

The law says what is *possible*, the set says what is *present*, the instance is what *happened*.
**[DESIGNED]** The plural as a distinct third form — we were already using it (`thePlanets` holds
eleven worlds and the rule that spaces them), but it was never named.

## 3. Verbs — there are exactly four

```python
derive(parent, free) -> numbers        # inherit. the ONLY way facts enter a membrane
emit(numbers, t)     -> matter         # become visible, in local units, over its own time
layout(numbers)      -> {child: place} # contain. WHERE the children sit, in this frame
measure(numbers)     -> facts          # be checked. what a test must find true
```

Nothing else is a verb. A membrane that wants a fifth operation is a membrane that is doing
something that belongs to a different level.

## 4. Adjectives are computed, never asserted

An instance is named by its **kind**, and the kind comes from the established taxonomy *and is
derived*:

```
T_surface = 5772 K  →  Harvard class G  →  "Yellow"  →  the folder is aYellowStar
```

`measure()` checks the folder name still equals the class the physics produces. **An adjective is a
claim, so it is tested like one.** Never `aStarB`, never a letter, never a number: if two of a kind
exist in one place, they get *different descriptors*, because if nothing distinguishes them
physically then they are not two things.

## 5. Gerunds are processes

`theEmptying`, `theCooling` — the `-ing` form marks a membrane that is a **happening**, not a thing.
Objects have extent; processes have duration. **[DESIGNED]** Making this a rule rather than an
accident: if a membrane is best named with a verb, name it with a gerund, and expect its `emit` to
be mostly about *change* between `t=0` and `t=1`.

## 6. The suffix is the unit — this is the type system

Every number carries its unit in its name:

```
snow_line_au     M_star_solar     T_orbit_myr     r_system_kpc     gps_net_us_day
```

This is what makes a **seam** checkable. A child works in *its* unit and a parent in *theirs*, so a
number crossing between them must be converted — and an untyped number silently doesn't get
converted. (`thePlanets` is in snow-line units and `theSolarSystem` in disk-edge units; placed
without conversion the composed extent came out **11.2** instead of 1.0.)

**[DESIGNED]** Rule: a number that is not dimensionless **must** end in its unit. Dimensionless
ratios end in `_frac`, `_ratio`, or read as a plain count.

## 7. Scope — a membrane may read only its parent

Not a sibling, not a grandparent, not a child. This is the strictest rule in the language and it is
what makes the tree a program rather than a pile.

**The corollary is the useful part:** if two siblings need the same number, **the number belongs to
their parent.** The snow line is a fact about the *system's light*, so `theSolarSystem` derives it
and `thePlanets` inherits it — rather than both computing it and drifting apart.

And the cost of getting it wrong is not tidiness: `theDensityClock` parented inside one solar system
made time dilation **unreachable from `theShip`**. A misplaced membrane is a dependency that does
not resolve.

**The way this rule actually breaks is a LITERAL.** A membrane needs a sibling's number, cannot say
it, and types the value instead — usually under a comment claiming it was inherited. `thePlanets`
carried `"T_star_surface": 5772.0` this way, so moving the star's mass shifted the snow line and left
the sunlight the same colour forever. The language cannot stop you typing a number; only the test
can. **The test is a slider: move a free number at the top, and anything downstream that does not
move was typed, not derived.**

## 8. What cannot be said

The language has no way to express these, and that is deliberate:

- **A number with no derivation.** Every fact enters through `derive`, from the parent. If you are
  choosing a value, you have broken the chain and substituted taste for a law.
- **An appearance that disagrees with the physics.** `emit` reads the same `numbers` as `derive`, in
  the same file — there is no channel through which they could differ.
- **A body the derivation did not produce.** `emit` may only speak of what `derive` made. An
  exaggeration is a *scale* on something real; it is not a way to introduce an object. A "star
  marker" drawn beside a planet is **a moon**, and no moon was derived — the fact that the render
  needed one is not an argument, it is the bug. A light source is said by its **light**: the
  terminator, the lit limb, the shadow. If a thing is off-screen at true scale, it is off-screen;
  go up a level, where it is real and placed.
- **A skipped level.** `HIERARCHIES.md` holds the real paths; a missing step is a bug, not a shortcut.
- **A subtraction.** From zero only addition is legal. Chapters are revisited, never removed.
- **Self-judgement.** A membrane cannot certify its own render; that needs a second, blind eye.

## 9. Tense — a membrane is a movie

`emit(numbers, t)` runs `t = 0 → 1`: the membrane's own beginning to its own settled end. Three of
space, one of time, and the time is **local** — each membrane unfolds at its own rate.

**[DESIGNED, and currently unimplemented.** `t` is dimensionless, so `theCooling`'s 380,000 years and
`theGalaxy`'s 10 billion presently play in the same arbitrary unit. Each membrane should derive its
own **clock** — a characteristic duration — so `t=1` means a real elapsed time and the ratios between
scales become true. That is the next thing this language needs.**]**

---

## The whole grammar, on one line

> **A path is a sentence. `the` is a law, `theXs` a set, `a` an instance named by a derived
> adjective. There are four verbs. Numbers carry their units. A membrane reads only its parent, and
> what two siblings share belongs to the one above them.**
