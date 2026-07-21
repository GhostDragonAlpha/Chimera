# Emergence Roadmap — The Decoding Schedule

> The game is a sequence of boxes. Each TODO item is one box.
> The formula collapses it in 6 observations.
> Work in order. Never skip forward.

## The Formula (copy for every item)

```
CONSTRAINT: <what must be true, stated as physics>
MEASURE:    <one number that proves the constraint holds>
EXISTING:   <what's already compiled/wired that serves this>
WORK:       <train / wire / decode — never place>
VERIFY:     <the beat that tests the rule, not the thing>
```

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

## Item 1: Survival pressure is real

The core clock of the game. Without this, nothing else matters — there's no reason to leave the habitat, no cost to helping a stranger, no tension in the beacon.

```
CONSTRAINT: A player must feel pressure to return to shelter within 5 minutes of leaving.
MEASURE:    A walking player at full O2 reaches low-O2 alarm (~25%) in ~5 minutes.
            A sprinting player burns out in ~2.5 minutes.
EXISTING:   USuitLifeSupportComponent — ticks, drains by exertion, fires OnSuitO2Depleted.
            WID_O2HUD — CreateWidget'd on possession, shows O2/BAT/DUST.
            UShelterHabitatComponent — sets bInShelter/bAtOxygenGarden/bAtBatteryBank on overlap.
WORK:       This is already compiled and wired. The work is:
            1. Place a shelter actor in the level (need BP_Habitat Blueprint to work around MCP CLASS_NOT_FOUND)
            2. Place the player start near it
            3. Run a beat: walk 30s out → O2 drains → return → O2 refills
VERIFY:     Beat: player starts at habitat → walks 30s → O2 < 70% → walks back → O2 rises above 95%.
            If O2 doesn't drain → the rates are wrong. If O2 doesn't refill → the shelter trigger isn't wired.
```

## Item 2: Resources exist to discover

The reason to leave the habitat. Scattered across biomes, visually distinct, collectible.

```
CONSTRAINT: Different biomes contain different collectible resources. Players must leave
            the habitat to find them. 8 inventory slots force choice.
MEASURE:    6 resource types exist. At least 3 biomes have distinct offerings.
            A player can fill their inventory in 2 minutes of exploring.
EXISTING:   APickupActor — compiled, has mesh, PickUp(), ItemName, OnPickedUp() event.
            UPickupInteractionComponent — compiled, on BP_Astronaut_Character, E to pickup.
            66 BP_Verb_PickUp actors already in the level.
WORK:       This is partially done — the 66 pickups exist but may all be verb tests.
            Verify what the 66 pickups contain. If they're all test items, retheme them
            as resources (basalt, iron ore, quartz, water ice, copper, circuit scrap).
            Add resource-type Blueprints: BP_Resource_Basalt, BP_Resource_IronOre, etc.
            These are child Blueprints of APickupActor with different meshes colors.
VERIFY:     Beat: player walks to a resource → E → item is "held" → Q → item drops.
            Read component property: HeldItemName matches the resource type.
```

## Item 3: The habitat is real

Not a cube. A place. Geometry that communicates shelter, safety, the line between alive and dead.

```
CONSTRAINT: The habitat must be visibly distinct from the terrain — a structure, not a rock.
            Walking inside must feel like crossing a threshold.
            O2 refills only when the player is inside the threshold.
MEASURE:    Habitat has a mesh, collision, and trigger zone. Player entering the trigger
            sets SuitLifeSupportComponent refill flags. Player leaving clears them.
EXISTING:   UShelterHabitatComponent — compiled, creates sphere trigger, sets refill flags.
            ShelterHabitatComponent.cpp lines 59-113 (OnShelterBeginOverlap) wire the refill.
WORK:       Create a Blueprint child (BP_Habitat) with:
            - A static mesh (geodesic dome, airlock arch, habitat module — need mesh)
            - UShelterHabitatComponent attached
            Position near player start. Save level.
            If no habitat mesh exists → train the form from a constraint (Item 4 below)
            or use the best available mesh as placeholder.
VERIFY:     Beat: start at habitat → O2 = 100, Bat = 100 → walk 10 units out → O2 draining →
            walk back inside → O2 rising. Read SuitLifeSupportComponent properties to confirm.
```

## Item 4: The habitat's form emerges (trainable)

Not authored. The shape of the habitat should be something the system discovers — the answer to "what geometry keeps a person alive on this world?"

```
CONSTRAINT: Habitat form is a trained genome, not a hand-placed mesh.
MEASURE:    Trainer produces habitats that: provide shelter, signal safety, enclose a refill zone.
EXISTING:   core/trainables/ framework — seed/mutate/measure pattern.
            UShelterHabitatComponent — defines what a shelter IS functionally.
WORK:       Write domain `core/trainables/habitat_form.py`:
            - seed: parametric geometry (height, radius, wall curvature, entrance width, material)
            - mutate: perturb parameters
            - measure: provides enclosed volume, entrance visibility from distance, structural plausibility
            Write `docs/objectives/habitat_form.json`:
            - maximize: enclosed_volume, entrance_visibility
            - minimize: surface_area (material cost)
            - walls: must have an entrance, must enclose >0 volume
            Train. Decode. The decoder writes MCP spawn commands for the winner.
VERIFY:     Decoded genome → MCP spawns the form → exists in level → beat verifies refill still works.
```

## Item 5: NPCs want what you have

Strangers have visible, specific needs. You can help them by giving resources from your inventory.

```
CONSTRAINT: At least 3 NPCs must have a visible resource need (displayed above them or through gesture).
            Giving the right resource satisfies the need and unlocks a blueprint.
            Giving nothing or the wrong resource does nothing.
MEASURE:    3 NPCs with distinct needs. Each accepts 1 specific resource type.
            Each grants 1 unique blueprint when helped.
EXISTING:   41 BP_NPC_Basic actors in the level. Gesture system exists (Tab).
            SacrificeLogComponent has Record() and trained SACRIFICE_WEIGHTS.
WORK:       This is the heart — the trainable social economy.
            Domain: `core/trainables/npc_needs.py`
            - seed: which NPCs want which resources, what they offer in return
            - mutate: swap needs, rotate rewards
            - measure: how many NPCs get helped, average time-to-help, reciprocity rate
            Wire the C++: NPC needs display → player gives via gesture → blueprint unlocks.
            The gameplay loop between Item 2 (resources) and Item 5 (give) is the game.
VERIFY:     Beat: player has resource → approaches NPC → NPC displays need →
            player gestures to give → resource consumed → blueprint available at fabricator.
```

## Item 6: The fabricator trades resources for progress

The habitat has a terminal. Deposit resources → unlock blueprints. Advanced blueprints only come from helping NPCs.

```
CONSTRAINT: Players can convert collected resources into survival items (O2 cans, battery packs)
            and tools (shovel, scanner). NPC-unlocked blueprints give advanced stuff (beacon parts).
MEASURE:    6 basic blueprints (3 survival + 3 tools). At least 3 NPC-unlocked blueprints.
            Each costs resources the player must go out to find.
EXISTING:   InventoryTradeComponent — compiled, credits/cargo/trade API.
WORK:       This is a terminal UI + DataTables.
            Blueprint list is a DataTable. Player deposits resources → checks against table → spawns item.
            NPC-unlocked blueprints require a flag set by SacrificeLogComponent.
VERIFY:     Beat: player has resources → uses fabricator → consumes resources → produces item.
```

## Item 7: The beacon ends the loop

The tower on the highest peak. Needs 3 components — each unlocked by helping a specific NPC. Signal strength = how many NPCs you helped.

```
CONSTRAINT: The only way to finish the game is to help people who cannot pay you.
            A costless playthrough produces a dim signal. A generous one produces a strong signal.
MEASURE:    Beacon signal strength = f(NPCs helped). 0 NPCs helped → dim. 3 NPCs helped → full.
EXISTING:   StarMemorialComponent — compiled, AddLife/TotalBrightness.
            SacrificeLogComponent — compiled, FeedStarMemorial/GetSacrificeCount.
WORK:       Tower actor + beacon signal visual. Wire count of helped NPCs to signal intensity.
            No new training needed — the trained SACRIFICE_WEIGHTS already define the curve.
VERIFY:     Beat: help 0 NPCs → tower is dim. Help 3 NPCs → tower is bright.
            The human plays it and feels whether a dim signal is a satisfying "bad ending."
```

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
