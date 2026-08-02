# Emergence Roadmap — The Decoding Schedule

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> The game is a sequence of boxes. Each TODO item is one box.
> The formula collapses it. No scales. No maximize/minimize. Walls only.
> The human is the terminal for pattern quality.
> The features are the shape of the membrane.
> Work in order. Never skip forward. Never conflate rungs.

## THE MEMBRANE PRINCIPLE — how detailed we get

A membrane separates inside from outside. The feature defines the shape of the
membrane — what it must enclose to be real.

The sandpile's first membrane enclosed "repose angle measurement." Within that
membrane, 40.03° was correct. But the feature "sand the player experiences" needs
a wider membrane — one that encloses grain size distribution, footstep response,
dust behavior on kick, appearance under direct light. The old membrane was the
wrong shape because the feature was named wrong.

**The membrane decision is the design decision.** Every feature item asks:
what does this feature need to BE? The answer defines the constraint set.
The constraint set is the membrane's wall. The trainer searches within it.
The human judges whether the membrane enclosed the right thing.

**The sub-feature rule is a membrane question.** Does this feature need a wider
membrane, or a separate one? If a rock and sand both need to be in the world,
but one is about collecting and the other is about walking feel — separate
membranes. They don't share a boundary.

**The audit backlog is a membrane failure.** A feature that was trained without
a membrane (old method, maximize/minimize, no walls) produced a result that
leaks outside where it's supposed to work. The fix is not to retrain the
artifact — it's to expand the membrane to include what was missing.

## THE COMPOSITIONAL LADDER — the method

Every system in the game follows this pattern. Train it at its own scale.
Pass averages to the next rung. Never skip a rung. Never conflate rungs.

A solar system is not built by placing planets. It is grown from an
accretion disk simulation — the big bang rung. That rung passes
(mass, semi-major axis, eccentricity) as averages to the planet rung.
The planet rung consumes those triples and computes oceans, atmospheres,
interior gradients. It passes (surface temperature, atmosphere pressure,
ocean coverage) to the ground rung. The ground rung forms the terrain
the player walks on.

Each rung is one trained constraint at one scale. The big bang does not
know about oceans. The planet does not know about footsteps. The sand
does not know about the player. They do not need to — each rung's
output is an average the next rung consumes as a settled fact.

**Rung conflation is the named failure mode.** Five rounds of big bang
training could not grow planets from pebbles WHILE settling a solar system.
The fix was splitting into two rungs — star pre-formed, embryos seeded,
and the regime unlocked on the untrained smoke. A system that tries to
train two scales at once trains neither.

**The roadmap below follows this pattern. Each item names its scale,
its inputs from the previous rung, and what it passes forward.**

## THE CORE INSIGHT — no scales

Every metric gets cheated. The sandpile found 40.03° but was wrong-scale voxels.
The periodicity 0.78 gait was a lottery ticket that happened to converge.
The maximize/minimize framework optimizes for the number you gave it,
not the pattern you wanted. The answer was correct. The question was wrong.

**The fix: walls only. No maximize, no minimize.**

A constraint set says what a thing MUST NOT be. Everything within the walls
is valid. The survivors are candidates. A human judges whether the pattern
emerged. The cheats ARE the product — they tell you where the walls are
missing or mis-specified. Fix the walls, retrain, read what the next cheat reveals.

**The definition level problem:**

Sand is not a voxel with sand properties. Sand is random particles arranged
by rules that produce a pattern. The constraint has to name the right level
— not too high (just repose angle) and not too low (every molecule). The
right level is where the pattern emerges under human observation.

## The Formula (copy for every item)

```
CONSTRAINT: <what must be true, stated as physics — at the right definition level>
EXISTING:   <what's already compiled/wired that serves this>
WALLS:      <must not violate X, Y, Z — the constraint set, never a scale>
WORK:       <train / wire / decode — never place>
JUDGE:      <who looks at the survivors and says whether the pattern emerged>
```

The JUDGE is always a human. Not an LM giving a percentile (H-14's
sibling: a model's opinion is a claim, not a terminal). Not a composite
score. A human says "yes, that's sand" or "no, it's still voxels." The
system's job is to produce candidates narrow enough that the human's
yes/no costs seconds, not hours.

## The audit backlog

Every feature previously built with the old method (authoring forms,
maximize/minimize objectives, placed objects) carries a defect: the
constraint was incomplete, the frame was wrong, the scale was cheatable.

The backlog is not a task list. It triggers when a feature fails a
human judgment. The sandpile was judged "still voxels" — retrain it
with walls-only constraints at the right definition level. The gait
was judged "trust the periodicity number" — retrain it with walls that
name the real failure mode (the lottery ticket).

The backlog grows as the human judges. It shrinks as features retrain.
Never proactively retrain — wait for the judgment.

## Execution Rhythm — The Farming Method

Every item runs through 4 seasons. Each season is a batch process with explicit inputs,
procedure, and outputs. Any agent can run any batch. Nothing lives in memory.

```
SPRING (design)   → Saturate with questions → Spec
SUMMER (build)    → Train / wire / compile   → Artifact
FALL (verify)     → Beat / observe / collapse → Evidence
WINTER (reflect)  → Audit / distill / compact → Lesson
```

Full season recipes: `docs/FARMING_SEASONS.md`

## The Sub-Feature Decision Rule

**When does a feature need sub-features?** This is how detail enters at the right level.

A feature needs sub-features when ANY of these is true:

1. **The CONSTRAINT contains "AND" between independent systems.**
   Example: "O2 refills AND habitat is visible from 50m AND walking inside feels like crossing a threshold"
   — that's three independent physics. Three independent constraints cannot be collapsed as one box.

2. **The VERIFY beat would need multiple independent assertions.**
   Example: "check O2 refills, check mesh is visible, check threshold feel"
   — each assertion tests a different system. A compound beat fails for ambiguous reasons.

3. **A season fails at the feature level.**
   Example: SUMMER training produces a degenerate winner because the search space is too large.
   → Decompose. Train each axis separately. Compose at decode time.

4. **The WORK section says "AND" instead of "/".**
   Example: "Create a Blueprint AND train a domain AND write a beat"
   — each is a different agent lane. Split them.

**When does a sub-feature stop splitting?**

When the formula fits on one page and the work fits in one agent tunnel.

The decomposition is NOT pre-planned. It emerges when the item hits a season boundary
and can't pass. The decomposer (`core/decomposer.py`) breaks it into parts; each part
rides the normal conveyor (claim → work → reps → beats → collapse).

---

## Item 1: Survival pressure is real (body rung)

The core clock of the game. **Scale: the player's body.** Inputs: none (this is rung 0 —
the first thing the player feels). Outputs to next rung: average survival time,
average resource consumption rate, average distance-from-shelter-at-death.

```
CONSTRAINT: O2, battery, and dust must drain at rates that force a player to return to shelter
            within 5 minutes. The shelter refills all three.
EXISTING:   USuitLifeSupportComponent — ticks, drains by exertion, fires OnSuitO2Depleted.
            WID_O2HUD — CreateWidget'd on possession.
            UShelterHabitatComponent — sets refill flags on overlap.
WALLS:      Must not take longer than 6 minutes of walking to drain a full tank.
            Must not kill a sprinting player in under 1 minute (panic is not pressure).
            Shelter refill must feel faster than the drain (recovery is earned, not slow).
WORK:       Place a shelter trigger in the level (need Blueprint child to work around
            MCP CLASS_NOT_FOUND). Verify O2 drain and refill via sleepwalker beat.
JUDGE:      A human plays 5 minutes. Does returning to shelter feel like relief, not inevitability?
            If the answer is "I just watched numbers go down" → the walls are wrong.
```

## Item 2: Resources exist to discover (biome rung)

The reason to leave the habitat. **Scale: the biome.** Inputs from Item 1: how far the player
can travel before needing to return. Outputs to Item 5: which resources exist and where,
the average effort to find each.

```
CONSTRAINT: Different biomes must contain different collectible resources. The player must
            leave the habitat and make choices about what to carry home.
EXISTING:   APickupActor — compiled, has mesh, PickUp(), ItemName, OnPickedUp() event.
            UPickupInteractionComponent — compiled, on BP_Astronaut_Character, E to pickup.
            66 BP_Verb_PickUp actors already in the level (need verification).
WALLS:      Must have at least as many resource types as inventory slots (8), so every slot
            is a choice. No single biome may contain every resource (must explore multiple).
            Resources must be physically visible at walk distance (no pixel-hunting).
WORK:       Verify what the 66 pickups contain. If test items → retheme or retrain.
            The distribution (what appears where) is a trainable domain, not authored placement.
JUDGE:      A human walks to a biome they haven't visited. Do they find something new?
            Do they have to leave something behind because inventory is full?
```

## Item 3: The habitat is real (shelter rung)

Not a cube. A threshold between alive and dead. The form is trained, not placed.
**Scale: the structure.** Inputs from Items 1+2: player survival range, resource
collection radius. Outputs to Items 4+6: which forms are buildable, what materials
they need, what volume they enclose.

```
CONSTRAINT: The habitat must communicate shelter and safety through its form.
            Walking inside must feel like crossing a threshold. O2 refills only inside.
EXISTING:   UShelterHabitatComponent — compiled, creates sphere trigger, sets refill flags.
WALLS:      Must be visibly distinct from natural terrain at 50m. Must have an entrance
            the player can identify from any approach angle. Must enclose a volume the
            player can stand inside. Refill zone must be inside the threshold.
WORK:       Train the form (Item 4 domain). Not placed — discovered.
JUDGE:      A human walks toward it from 50m. Do they know it's shelter? Do they feel
            the threshold when they cross it? If the answer is "it's a box" → retrain.
```

## Item 4: The habitat's form emerges (form rung)

The shape of the habitat is a genome, not a mesh. **Scale: the form's parameters.**
Inputs from Item 3: the functional definition of what a shelter must do. Outputs
to Item 6: the decoded geometry blueprint (which vertices, which materials).

```
CONSTRAINT: Habitat form must emerge from a trained genome — the answer to
            "what geometry keeps a person alive on this world?"
EXISTING:   core/trainables/ framework — seed/mutate/measure pattern.
            UShelterHabitatComponent — defines what a shelter IS functionally.
WALLS:      Must provide enclosed volume. Must have at least one entrance.
            Must be buildable from available materials (no impossible geometry).
            No scale measures "safety" — only human judgment validates the form.
WORK:       Write domain with parametric geometry. Constraint satisfaction only
            (no maximize/minimize). All valid genomes are candidates.
            Human judges the candidates. Survivors get decoded to MCP spawn.
JUDGE:      A human looks at the candidates. "Yes, that's a habitat" or "no, that's
            a shape with a hole in it." The walls narrow the field; the human picks.
```

## Item 5: NPCs want what you have (social rung)

The social economy. **Scale: the encounter.** Inputs from Item 2: which resources
are available to give. Inputs from Item 1: how much survival pressure the NPC
feels (their O2 drains too). Outputs to Items 6+7: which blueprints are unlocked,
how many NPCs were helped.

```
CONSTRAINT: At least 3 NPCs must have visible, simulation-driven needs. Giving the
            right resource satisfies the need and unlocks a blueprint. Giving nothing
            does nothing. There is no other way to get the blueprint.
EXISTING:   41 BP_NPC_Basic in the level. Gesture system exists (Tab).
            SacrificeLogComponent with trained SACRIFICE_WEIGHTS.
WALLS:      Needs must be readable without UI (NPC animation/state communicates them).
            Blueprints unlocked by helping must not be obtainable any other way.
            A costless playthrough (help no one) must still be completable —
            but the beacon signal is at minimum.
WORK:       Train NPC need state machine (walls-only constraint satisfaction).
            Wire: NPC state → visual indicator → player gesture → resource consumed →
            blueprint unlocked. No authored dialogue.
JUDGE:      A human encounters an NPC. Do they understand the need without text?
            Do they remember helping after they've moved on?
```

## Item 6: The fabricator trades resources for progress (economy rung)

**Scale: the terminal exchange.** Inputs from Items 2+5: available resources and
unlocked blueprints. Outputs to Item 7: which beacon components are buildable.

```
CONSTRAINT: Players must convert collected resources into survival items and tools.
            NPC-unlocked blueprints must give advanced capabilities unobtainable otherwise.
EXISTING:   InventoryTradeComponent — compiled, credits/cargo/trade API.
WALLS:      Must have more blueprints than any player can unlock in one trip (forces
            return visits). Basic blueprints cost only time (go out, find resources,
            come back). Advanced blueprints require NPC help — no resource bypass.
WORK:       Terminal UI + Blueprint DataTable. The unlock graph is a constraint
            satisfaction problem: which blueprints are reachable from which resource
            combinations, and which require NPC flags.
JUDGE:      A human has a full inventory. At the fabricator, do they have to choose
            what to build? Do they unlock something new on their second trip?
```

## Item 7: The beacon ends the loop (narrative rung)

**Scale: the whole playthrough — the widest rung.** Inputs from all previous items:
survival pressure, resources collected, NPCs helped, blueprints built. Passes
nothing forward — this is the terminal rung. It is one question, not a score.

```
CONSTRAINT: The only way to reach a strong signal is to help people who cannot pay you.
            A costless playthrough produces minimum signal. Signal strength is
            not a score — it is a map of your choices.
EXISTING:   StarMemorialComponent — compiled, AddLife/TotalBrightness.
            SacrificeLogComponent — compiled, FeedStarMemorial/GetSacrificeCount.
WALLS:      Signal must be visibly different at 0 helps vs 3+ helps. The player must
            not be told what the signal means (no UI text — Law 3). The tower must
            be reachable without any NPC help (dim signal is the bad ending, not a
            locked ending).
WORK:       Tower actor + beacon visual. Wire signal intensity to sacrifice count.
JUDGE:      A human plays to the ending. A costless playthrough — does the dim signal
            feel earned? A generous playthrough — does the strong signal feel like
            a connection, not a reward bar filling up?
```

## The full ladder — 10 rungs

The roadmap items (1-7) start at the body. They rest on three rungs that are already
trained, compiled, and real. The player stands on the output of those rungs right now.

```
cosmic rung  ─── planetary rung ─── ground rung ─── body rung ─── biome rung ─── shelter rung
(big bang)      (climate)          (40° sand)      (O2 drains)    (resources)    (threshold)
     │               │                  │               │              │              │
     │ tb-0193       │ tb-0194          │ tb-0192+0198  │ Item 1       │ Item 2       │ Items 3+4
     │ trained+      │ trained+         │ trained+      │              │              │
     │ compiled      │ compiled         │ compiled      │              │              │
     ▼               ▼                  ▼               ▼              ▼              ▼

                         form rung ─── social rung ─── economy rung ─── narrative rung
                         (geometry)     (NPC needs)     (fabricator)     (beacon)
                            │               │               │               │
                            │ Item 4        │ Item 5        │ Item 6        │ Item 7
                            ▼               ▼               ▼               ▼
```

**The foundation is already real.** The cosmic, planetary, and ground rungs were
trained across tb-0192 through tb-0198. They compile. They run. The materialization
subsystem (tb-0198) forms terrain under the player's boots in PIE. The 40° sand is
grown, not placed. The planet's climate determined the sand's composition.

**What the roadmap actually builds is the chain from body to meaning.**
The ground exists. The player can stand on it. The roadmap makes that standing matter.

## The beacon as quality target

Star Citizen has no ending. It is a persistent universe where you grind forever.
This game has an ending. A costless life produces a dim signal. A generous life
produces a strong one. The ending is not a cutscene — it is the player looking
at the sky and recognizing their choices.

This beats Star Citizen because Star Citizen has nothing at the end of the grind.
We have a question.

---

## The sequence as a quantum chain

Each item's box must collapse before the next item's box is meaningful:

```
Item 1 (survival)     → player cares about leaving the habitat
  └── Item 2 (resources) → player has a reason to leave
       └── Item 3 (habitat) → player has a place to return to
            └── Item 4 (emergent form) → the habitat looks right
                 └── Item 5 (NPC needs) → there are people worth helping
                      └── Item 6 (fabricator) → helping unlocks stuff
                           └── Item 7 (beacon) → the whole thing closes
```

Item 1's box is mostly already collapsed (the code exists). Item 2's box is partially collapsed (pickup system exists, resources need retheming). The rest are unopened.

Each item follows the formula. Always. The old way — placing a cube — collapses a box that isn't on this chain. It costs time and resolves nothing that helps the next item.
