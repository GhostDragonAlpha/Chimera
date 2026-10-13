# B9 — Material–geometry–solver qualification envelope (scoping work item)

Date: 2026-10-12. Status: **scoped, not implemented.** This is the
qualification work item that turns the B8 gallery's measured failure modes
into declared, enforceable limits. It connects to both contracts: the plan
(amendment text in §4, to be applied when the plan file is next clean) and
the construction release candidate
(`docs/releases/chimera-construction-v0.1.0-rc.1.md` §6.2).

## 1. Why a material name is not enough

Every B8 failure was "honest material, honest geometry, honest solver — and
an outcome no player could read":

| Measured failure | What the material name hid |
|---|---|
| Slender wall (20 mm base × 110 mm) topples under 2 N at COM | Thickness/aspect ratio: the F×55 mm friction couple needs ~11 N normal shift across a 20 mm base; on a 10 mm-sink foundation that is ~18° tilt > the ~10° tipping angle |
| 4× stiffer ground + 0.3 kg block → 81 m/s explosion in 5 ms | Stiffness × mass × timestep: the catch's explicit-stability margins (ω·h, c·h/m) left their safe range for that pair |
| Thin sliding block → 91 m/s explosion | Contact arrangement: friction torque pitches a thin body nose-down with no pressure redistribution to answer |
| Granite rests at 17.9 mm past the 15 mm declared stop | Rest vs arrest: a static sink beyond a dynamic stop is honest, but nothing said so |
| Sustained 3 N on 0.26 kg wall → 48 m/s runaway | Relative velocity over time: Coulomb friction gives no terminal velocity |

The envelope is therefore a **tuple**, not a label: material (density,
friction, rung stiffness/damping), geometry (smallest thickness, aspect
ratio, base half-width vs foundation sink), mass ratios in the contact,
relative-velocity and load bands, solver state (substep, declared stop,
catch parameters) and contact arrangement (resting vs sliding vs
impinging). A part is *qualified* only as the whole tuple.

## 2. Definition

A **material–geometry–solver qualification envelope** is, for each admitted
contact law, a declared band over that tuple inside which the law is
qualified — no explosion, no phantom contact, statics not corrupted, rest
state reproducible — plus a declared, visible behavior outside the band.
Divergence inside the band is a defect; divergence outside it is a refusal
or a reported out-of-envelope event, never a NaN-freeze or a silent
explosion.

## 3. Acceptance criteria for the B9 gate

1. **Named refusals before mutation.** Admitting a part whose tuple falls
   outside the band refuses with a message naming the violated limit
   (e.g. `"base half-width 10 mm below 18 mm minimum for aspect 5.5 at
   lateral load"`); nothing is appended to the live world.
2. **Unchanged state after rejection.** State hash byte-identical across
   every refusal (the existing transaction guarantee, now exercised against
   envelope refusals specifically).
3. **Boundary cases.** Just-inside admits and behaves; just-outside refuses;
   the boundary tolerance is itself declared.
4. **Known-failure reproductions.** Each B8 failure mode becomes a test:
   statically outside → refused at admission; dynamically entered (load or
   velocity evolves past the band after admission) → the visible runtime
   response of criterion 5.
5. **Visible runtime response to envelope exit.** Evolving velocity or load
   can leave the envelope *after* admission, which transaction checks alone
   cannot address. The state must expose an out-of-envelope report (named
   limit, part, measured value) and the scene must degrade declaredly —
   the current backstop engagement counter and `diverged` flag are the
   seed; B9 extends them to per-limit events.
6. **Release coupling.** A known failure inside the advertised release
   envelope blocks that release (defect). A case outside it requires an
   explicit limit and its enforcement (refusal or event) before the case may
   ship unqualified.

## 4. Proposed plan amendments (apply when the plan file is clean)

The plan file is dirty with another agent's uncommitted edits in the shared
checkout; these are delivered as text, not applied.

**§11.1 (admission/refusal semantics), append:**

> Admission validates the part's full qualification tuple — material,
> geometry (smallest thickness, aspect ratio, base footprint against
> foundation sink), mass ratios, and the declared load/velocity band —
> against the contact law's qualified envelope, and refuses before any
> mutation with a message naming the violated limit. A refused admission
> leaves the accepted state byte-identical. A material name alone never
> establishes qualification.

**§11.3 (contact-law limits), append:**

> Each declared contact approximation states its qualified band over that
> tuple and its behavior outside it. Because load and velocity evolve, the
> runtime must report envelope exit visibly (named limit, part, measured
> value) rather than only refusing at transaction time; divergence inside a
> declared band is a defect, outside it is a reported condition. Known
> failures inside an advertised band block release; cases outside need
> explicit limits and enforcement.

## 5. Enforcement sketch (for the implementation gate, not this scope)

- Admission document gains an optional `envelope_expectation` block (max
  relative speed, max sustained load, contact role: rest/slide/impinge);
  the engine derives geometry terms (thickness, aspect, base half-width)
  from the admitted volume and checks the tuple against per-law bands.
- Bands live beside the law constants (the B8 block in `b2_scene.cpp` is
  the seed: `B8_STOP_M`, `B8_BS_VGATE`, ω·h and c·h/m margins) and are
  published in `/tick_b2_state` so the UI can warn before the player commits.
- Runtime watchdog per substep: approach speed vs catch gate, penetration
  vs stop, sticking-damper margin, aspect-vs-sink ratio for standing
  contacts → first breach raises a named out-of-envelope event in state
  (cumulative counter + latest event), never mutates physics silently.
- Non-goals for B9: fracture modeling, general continuous collision,
  player-facing UI (each keeps its own gate).
