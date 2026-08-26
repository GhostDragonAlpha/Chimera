# THE_WOLFRAM_FRAME.md — THE OPERATOR'S ARCHITECTURE, AS GIVEN

> Recorded 2026-08-25. Every claim below is the operator's, stated in session and committed here
> as CANON. Where an older written rule contradicts something in this file, **this file wins**:
> a large part of the historical rule corpus was scaffolding built to constrain an earlier,
> less trustworthy generation of AI agents (rules against lying, drifting, self-decorating).
> Those rules did their job; they are not the product. Rule 0 (statement · prediction ·
> falsifier) and the dyad survive because they still earn their keep — adjusted as necessary.

This file exists because the architecture arrives from the operator ALL AT ONCE — the operator
is autistic and sees the whole board simultaneously; serializing it one piece per session loses
the shape. This is the shape, in one place. It is read-first context, not optional lore.

---

## 0 · THE LINEAGE: WOLFRAM

Stephen Wolfram's program — simple rules, computational irreducibility, equivalence, rulial
composition — is not an influence on this project. It is the load-bearing frame:

- **Simple local rules → complex behavior** is the whole construction method: `ca_core`'s
  cellular automata, the Cellular-Potts shaker (`core/matter_gpu.py`), grain fields, voxel
  muscles. Nothing complex is ever authored directly; it is *run*.
- **Emergent macro-numbers are the proof**: sandpile repose 40.03° inside the researched band,
  Kepler slope 1.50 at r²=1.000 measured from grown orbits — never coded, always SELECTED for.
- **Computational irreducibility, tamed, is the performance model**: verdict V62 (dirty-set
  grain sweep) proved a settled world costs ~nothing to hold — only *state change* spends
  compute. You cannot shortcut the unfolding; you can refuse to recompute what did not change.
- **Terms are translations, held in the GPU matrix, weighted 0→1 as needed** (operator,
  verbatim). One underlying computation; many observers; the weight picks the projection.
  Everything has to translate through the gravity algorithm — that is the project's
  equivalence principle.

## 1 · TIME IS THE FOURTH DIMENSION YOU EDIT

> "It's like making a video game by making a movie: you make a movie by editing the fourth
> dimension." — the operator

A game is not a box that simulates; it is a *film of a computation*. Time is the sequence of
rule applications, and smoothness is the quality of the translation between simulation states
along that axis. Rasterization is the limit of hardware technology; the GPU rasterizes the
projection while the CA computes the truth underneath. Physics and rendering are ONE system
read two ways — which is why every membrane's `derive()` and `emit()` sit in the same file
reading the same numbers.

## 2 · MEMBRANES ARE RAILROAD SWITCHES INTO THE FOURTH DIMENSION

> "Everything exists within membranes, and the membranes are the clips you insert into the
> fourth dimension. They are kind of like railroad switches that initialize complex behavior,
> like all cellular automata." — the operator

A membrane is NOT primarily a container or an audit unit. It is an INITIALIZER: a rule-set +
initial condition clipped into the timeline, after which the automaton runs. Choosing a
membrane is choosing which evolution you get — Wolfram's initial-condition selection. The
story tree (`ChimeraEngine/engine_state.json`) is therefore a graph of switch-points, each
term a place the timeline can be re-routed. The isolation tooling (`core/membrane.py`, sealed
worktrees) is the engineering shadow of the same concept: a boundary that makes causes
attributable.

## 3 · TISSUE = SEPARATE TRIANGLE SYSTEMS

There is no one body mesh. Each conceptual layer is its OWN triangle system:

- **skin** — the outer shell (what light hits),
- **muscle** — the actuator lattice,
- **bone** — the rigid frame.

They couple at interfaces, not by merging. The triangle was chosen deliberately: it is the
basis of essentially all rendering hardware. Rasterization is the hardware limit; triangles
are the coin the GPU actually trades in. Consequence for the engine: `load_mesh` is generic
on purpose — the near-term shape is N mesh slots (one per tissue system) with cross-system
constraints, not one welded body. The splat lane came first historically; geometry came when
CA physics needed a carrier to grab.

## 4 · DETERMINISM = ROM EXTREMITIES + CA-FILLED INTERIOR

> "We find the maximum extremities of a concept (like bending a knee), which results in an
> angle range. Within that range, we determine how many steps happen through the interaction
> of CA." — the operator

Determinism is not bit-reproducibility bookkeeping. It is a CONSTRUCTION PROCEDURE:

1. find the maxima of a concept — full extension, full flexion — that is the range;
2. the interior of the range is filled by cellular-automaton interaction, not interpolation;
3. smooth, natural motion (clothed or skinned) comes from harnessing the model with a bone
   rig: each triangle is assigned to a bone, and bones tell triangles what to do;
4. the whole thing is a combined physics-rendering system — the same numbers drive both.

In Wolfram's language: locate the attractors of a rule, then sample its evolution. In this
repo's language: declare the ROM, train the continuum.

## 5 · THE IN-BETWEEN MUST BE TRAINED

> "Between fully extended and fully bent there is everything in between. That in-between needs
> to be trained — both the physics AND the physical structure between the states." — the operator

Endpoints are DECLARED; the continuum is EARNED. Both tracks train together:

- **structure** — how the tissue systems deform across the range (geometry is a function of
  the state variable, not a fixed mesh);
- **physics** — forces, limits, damping as functions of position within the range.

This is why the live failure list is the real work queue: `JOINT_LIMIT` overshooting its stop
by ~3.6° means the RANGE BOUNDARY leaks; `SWING`'s period error means cadence cannot yet be
derived; `LAND`'s energy injection means the fall is not honest; `UPRIGHT`/`RHYTHM_DRIVE`/
`END_STOP` fail downstream of those. The lane name for all of it: **train the in-between.**

## 6 · GRAVITY IS EARTH

No sensor will ever be strapped to this world, so the world gets the one gravity we actually
have: **g = 9.80665 m/s², standard Earth**, by operator decree (2026-08-25). The derived-world
chain that once produced g = 7.076 is retired history — kept in dated stories, never in
constants. Single source of truth: `story/theHuman/numbers.json`, read dynamically by
`tools/world.py::gravity()`. Nothing hardcodes either number.

## 7 · OPEN SOURCE IS DOCTRINE, NOT PREFERENCE

> The product spine: "Anything that's not closed source."

AGPL v3 is the license and the boundary. Closed engines are structurally disqualified — the
UE5 pipeline was excised from the tree on 2026-08-25 for this reason, not merely tidied. The
spine is the C++/Vulkan engine + native relay + ca_core + the Python trainer stack.

## 8 · THE HUMAN IS THE VISUAL CHECKPOINT

Between major features stands a human being looking at the thing. No gate, witness, or
verdict substitutes for the operator's eyes at a feature boundary; the machinery exists to
make what the operator sees *honest*, never to replace the seeing.

## 9 · HOW TO WORK HERE (THE OPERABLE SUMMARY)

1. Read this file whole — it IS the board.
2. Rule 0 before any build: statement · prediction · falsifier.
3. Constants come from ledgers, decrees, or derivations — never from taste.
4. The operator decides what runs and judges what appears; agents prove and build.
5. When this file conflicts with older prose, this file wins; flag the conflict where found.

## 10 · PUBLISHEDOLOGY — THE MEMBERSHIP REQUIREMENT FOR DECLARATIONS

> "All declared items must fit within publishedology. An ology is anything that you can use
> the word 'ology' behind." — the operator

**Publishedology** (n.) — the union of every published body of organized knowledge: any
discipline whose name admits "-ology" (biomechanics, tribology, geology, kinesiology…) plus
the published codifications that behave like one (ACI design codes, Cordage Institute
standards, the Lunar Sourcebook).

**The law**: every DECLARED item — a constant, a range, a limit, a term's claim — is legal
only if it docks into a named ology. A declaration must say WHICH body of knowledge it comes
from and, where possible, where in that literature it sits. A number declared from nothing
is not conservative, not safe, not provisional — it is MINTED, and minting is the defect
this project exists to kill.

This is provenance as membership, not decoration. The repo's strongest ports were already
obeying it (splice retention cited to Cordage Institute, ρ_b capped by ACI, regolith angles
to Carrier/Lunar Sourcebook); this rule promotes that habit to LAW. Practical form:
`declare(value, ology="kinesiology", source="<published anchor>")` — and a declaration whose
ology field is empty does not pass S2 PROVENANCE.

