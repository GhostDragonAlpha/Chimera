# theHumanClock

<!-- CHIMERA-LAW -->
> *Derive before you train — [THE LAW](../../../../../docs/THE_LAW.md). Every number below is derived from the parent's or measured; none is chosen.*
<!-- CHIMERA-LAW -->

> **chapter 05** of the story  ·  **t = 3 s** since theZero  ·  lasts **3 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** A person can only produce and notice events inside a narrow band of speeds —
roughly a twenty-fifth of a second to about ten seconds. Everything the player controls has to be
geared into that band, or they cannot feel it: too fast and a tap overshoots, too slow and the
button feels dead.

*The clock at the other end of the ladder.* Every other clock here is set by density. **This one is
set by a body** — and because the player only ever acts through it, it decides which of the other
clocks the game can actually put in their hands.

## The band, measured

| what | how long | why it bounds the design |
|---|---|---|
| **frame** | 16.7 ms | one tick at 60 Hz — the finest grain that can be shown |
| **fusion** | ~40 ms | below this, separate events are perceived as one |
| **tap** | 80–150 ms | the shortest press a person can *deliberately* make |
| **reaction** | ~250 ms | the delay between seeing and pressing |
| **hold** | 0.2–3 s | comfortable, controllable, repeatable |
| **sustained** | up to ~10 s | past this it stops being an action and becomes a setting |

So the controllable band spans about **0.04 s to 10 s** — barely **2.5 orders of magnitude**, against
the 60 the rest of the ladder covers.

## A button is a duration; a stick is a magnitude

That is the whole input vocabulary, and together they are an **impulse**:

```
Δv  =  (stick deflection) × a_max × (how long you held it)
```

A tap and a lean are the same act with two dials. Which is why so few controls can express so much:
the button supplies *how long*, the stick supplies *how hard*, and the membrane being acted on
supplies everything else.

## The gearing law

**A system is controllable only if its response time lands inside the band.** Anything outside must
be *geared* into it — exactly as a gearbox trades torque for speed:

```
a_max chosen so that a 1-second burn changes the state by a noticeable fraction
```

Too much thrust and a 100 ms tap overshoots the target; too little and a 10-second hold does nothing
visible, and the control feels broken even though the physics is perfect. **The physics being right
is not sufficient — it has to be reachable.**

*Contained in `theClock`. What it hands on: the band every control must be geared into, and the
impulse formula that turns a press into a change.*
