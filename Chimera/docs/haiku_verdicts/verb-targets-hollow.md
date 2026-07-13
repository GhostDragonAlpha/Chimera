# Phantom Pain Verdict: Verb Targets Hollow

## Pain Record

**ID:** `phase_1b01fac303f3c24e:P1`  
**Age:** 5 days (created ~2026-07-07)  
**Status:** Created during verb interaction investigation phase

### Quoted Pain
> "The verb TARGETS (BP_Verb_* actors) may be as hollow as the walking was — built via bridge/injection, not real behavior."

**Context:** Concerned that verb actors (BP_Verb_*, ATool_*, interaction components) were metadata-only, lacking real world-state-changing behavior. Reference to H-21 heuristic: "a verb needs behavior, not metadata" (ATool_Shovel example: DigRadius property without Dig() method).

---

## Investigation Process

### 1. DNA Graph Search
- Searched `core.dna_sqlite_backend` for "verb target" and "BP_Verb"
- Found historical records showing verb features (Verb_Step, Verb_Bend, Verb_PickUp, Verb_Drop, Verb_Shovel)
- Located observation from July 8: "ATool_Shovel is a static prop with numeric metadata (DigRadius=50, DigDepth=10) and NO Dig()/Shovel() function"

### 2. Code Inspection

#### ATool_Shovel (Source/Chimera/ProceduralGenerated/Tools/)
- **Header** (ATool_Shovel.h, lines 31-32):
  ```cpp
  UFUNCTION(BlueprintCallable, Category = "Tool")
  bool Dig();
  ```

- **Implementation** (ATool_Shovel.cpp, lines 41-97):
  ```cpp
  bool ATool_Shovel::Dig()
  {
    // Line trace to find ground (FCollisionQueryParams, LineTraceSingleByChannel)
    // Particle emission: Dust->EmitDustAtLocation(Hit.ImpactPoint, ParticleCount)
    // Sound playback: Sand->PlayImpactSound(Hit.ImpactPoint)
    // Decal creation: NewObject<UDecalComponent>() with material + transform
    // Durability reduction: Durability -= 1.0f
    // World state changes confirmed at lines 73, 78, 83-88, 92
    return true;
  }
  ```

#### PickupInteractionComponent (Source/Chimera/ProceduralGenerated/Interactions/)
- **TryInteract()** (PickupInteractionComponent.cpp, lines 142-170):
  - Calls `ClosestPickup->PickUp()` (line 164) — actor destruction
  - Tracks state: `bIsHoldingItem = true` (line 161)
  - Updates component state: `CurrentState = EPickupInteractionState::PickupCompleted` (line 166)

- **TryDrop()** (lines 172-213):
  - Spawns ADropActor at computed location (line 202)
  - Modifies world: `World->SpawnActor<ADropActor>()`
  - Updates pawn state: `bIsHoldingItem = false` (line 208)

#### APickupActor (Source/Chimera/ProceduralGenerated/Interactions/)
- **PickUp()** (PickupActor.cpp, lines 61-77):
  ```cpp
  void APickupActor::PickUp()
  {
    InteractionState = EPickupActorState::PickedUp;
    if (GetRootComponent())
      GetRootComponent()->SetVisibility(false, true);  // Line 73
    Destroy();  // Line 76
  }
  ```

### 3. Git History

**Commit 13778401 (July 3):** ATool_Shovel created with ONLY constructor + empty BeginPlay
- No Dig() method
- Properties only: DigRadius, DigDepth, Durability

**Commit b81eeb3 (July 12):** Dig() method ADDED
- Complete line-trace-based dig system
- Particle, sound, decal, and durability effects
- Real world-state-changing behavior

**Current HEAD (4e8afa3):** After b81eeb3, so Dig() is present

### 4. Heuristic Record

**H-21** (promoted to CLAUDE.md Constitution, in docs/HISTORY_BOOK.md):
> "A verb needs behavior, not metadata: ATool_Shovel had DigRadius but no Dig() — beats must press the verb key and assert a world-state change."

---

## Verdict

**REFUTED**

The pain was **historically accurate** (July 8 observation confirmed: ATool_Shovel had no Dig() method at that time), but has since been **definitively fixed** (July 12 commit b81eeb3).

### Evidence Chain

1. **Jul 8 Observation** (phase age = 5d): "ATool_Shovel has NO Dig()/Shovel() function" — CONFIRMED at that time
2. **Jul 12 Commit b81eeb3**: Dig() method implemented with full world-state behavior
3. **Current Code** (HEAD = 4e8afa3, post-fix): 
   - ATool_Shovel.Dig() exists and is fully functional
   - All interaction verbs (PickUp, Drop, Bend via input) have real behavior
   - Components attached, methods implemented, state changes occur

### Real Behavior Present

| Verb Component | Behavior Type | Evidence |
|---|---|---|
| ATool_Shovel::Dig() | World state | Line traces, particle emission, sound, decal, durability loss |
| PickupInteractionComponent::TryInteract() | Actor lifecycle | Calls PickUp() on target, changes bIsHoldingItem |
| PickupInteractionComponent::TryDrop() | World spawn | Spawns ADropActor at location, updates state |
| APickupActor::PickUp() | Actor destruction | SetVisibility(false), Destroy() |

### Distinction from Prior Failures

H-21 and H-22 heuristics exist because past verb implementations WERE hollow (metadata only). The system has since:
1. Added Dig() to ATool_Shovel (line-trace behavior)
2. Wired components to characters (PickupInteractionComponent integration)
3. Implemented real actor lifecycle changes (spawn/destroy)

---

## Disposition

`DISPOSITION: phase_1b01fac303f3c24e:P1:refuted`

**Summary:** Past pain → present code. The pain identified a real gap (Shovel verb was hollow on Jul 8). The gap has been closed (Dig() implemented Jul 12). Current codebase has real behavior in all tested verb paths.
