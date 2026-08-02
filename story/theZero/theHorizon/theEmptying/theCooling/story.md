# theCooling

<!-- CHIMERA-LAW -->
> *Derive before you train — [THE LAW](../../../../../docs/THE_LAW.md). Every number below is derived from the parent's or measured; none is chosen.*
<!-- CHIMERA-LAW -->

> **chapter 06** of the story  ·  **t = 1.19917e+13 s** since theZero  ·  lasts **1.19917e+13 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** As the universe spreads out it cools, and every time it gets cold enough, one more kind of thing is allowed to stay in one piece instead of being smashed apart.

*Chapter 4.*

The sea the fence left behind is expanding, and expansion cools it: `T ∝ 1/a`, so the clock and the
temperature are the same fact read two ways.

Everything that happens next happens **once**: when `kT` falls below a binding energy, whatever that
energy holds together stops being torn apart and **survives**. Structure is not built here — it is
*permitted*. But it is late every time, because there are ~10⁹ photons for every particle, so even
the thin hot tail of the distribution keeps breaking things.

*How late* is the thing that must be derived rather than guessed. Counting photons alone
(`kT ≈ E_bind/ln(1/η)`) says 21× — and lands atoms at 7438 K, which is wrong. The missing half is
**phase space**: a freed electron has an enormous number of places to go, so freedom is favoured far
below the bond. Saha balances the two:

```
x²/(1−x) = (1/n_b)·(2π mₑkT/h²)^{3/2}·exp(−E/kT)
```

Solved for half-neutral, that gives **3760 K** — the literature's 3700 K to 1.6% — and the lateness
comes out **42×**, derived, where the photon count alone said 21.

Nuclei are permitted first, around 10⁹ K, and the sea settles at three-quarters hydrogen,
one-quarter helium, and stays that way. Then at 3760 K — not 13.6 eV but a forty-second of it —
electrons are permitted to stay with nuclei, and the instant matter is neutral there is nothing left
for photons to scatter from, so **the universe goes transparent all at once.** The light released at
that moment is still arriving.

What is handed on is neutral matter no longer held apart by radiation, one part in 100,000 denser
here than there — and gravity, which has no threshold and never switches off, finally has something
it is allowed to pull on.

## Where this chapter is still typed, and what that costs downstream

`python tools/slider.py` moves the one free number at the top of the world — the mass added to
the seed — and watches what follows. It reaches four chapters and stops **here**:

    theHorizon    4/8  numbers moved
    theEmptying   5/5  moved
    theCooling    1/11 moved
    theCloud      0/15 moved   <-- and every chapter below it, all the way to the human

**One of those is correct and one is not, and they must not be confused.**

`T_end` is right to sit still. Atoms form at 3760 K because that is where hydrogen's 13.6 eV bond
finally beats the photon bath — it is solved from Saha here, and it does not care what mass fell
into the seed. A universe that started hotter still recombines at 3760 K; it simply takes longer
to get there.

`extent_m` and `duration_s` are **typed**:

    "duration_s": 3.8e5 * 3.1557e7          # 380,000 years, written in by hand
    "extent_m":   c * 3.8e5 * 3.1557e7      # and the horizon that follows from it

That number is not a constant of nature. The time to recombination follows from the expansion
history — how fast the universe dilutes, set by the matter and radiation densities, integrated
down to the temperature atoms need. It is a Friedmann calculation, and it is skipped.

**The cost is not local.** Every chapter inherits its scale from its parent, so a typed duration
here is the anchor the entire lower tree hangs from. That is why moving the seed's mass changes
nothing about the galaxy, the star, the world or the person standing on it: they are not
downstream of the seed at all. They are downstream of *this literal*.

Recorded rather than fixed, because deriving it is a real derivation and not a patch — and
because a typed number that is *named* is a debt, while a typed number that is hidden is a lie.
