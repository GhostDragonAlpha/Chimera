# Phantom Pain Verdict: Weather Erasure Registry

## Pain Statement

"The storm's world-wide footprint erasure (UFootprintComponent::EraseAllImpermanent) relies on a STATIC registry (LiveComponents) maintained in FootprintComponent BeginPlay/EndPlay. If a footprint component fails to register — attach order, or prints laid before BeginPlay runs — a storm's LastStormFootprintsErased could stay 0 even though sand prints are on the ground."

---

## Investigation Summary

Examined three components:
1. **FootprintComponent.cpp/.h** — Registration, footprint laying, and erasure logic
2. **WeatherComponent.cpp** — Storm lifecycle and erasure call
3. **UE5 lifecycle guarantees** — BeginPlay → TickComponent ordering

---

## Evidence & Analysis

### (A) Registration is Guaranteed Before Prints

**FootprintComponent.cpp line 55-59:**
```cpp
void UFootprintComponent::BeginPlay()
{
    Super::BeginPlay();
    LiveComponents.Add(this);  // enroll in the storm's world-wide erase sweep
}
```

**Fact:** BeginPlay() adds the component to the static LiveComponents registry.

**UE5 Guarantee:** In Unreal Engine 5, BeginPlay is ALWAYS called before the first TickComponent. This is a hard lifecycle contract. No component ticks before BeginPlay completes.

**Result:** Registration happens before ANY tick can run.

---

### (B) Prints Cannot Exist Before Registration

**FootprintComponent.cpp line 70-87 (TickComponent):**
```cpp
void UFootprintComponent::TickComponent(float DeltaTime, ...)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    
    if (!bInitialized)  // FIRST tick only
    {
        CachedMovement = Owner->FindComponentByClass<UCharacterMovementComponent>();
        LastSampleLocation = Owner->GetActorLocation();
        bInitialized = true;
        return;  // EXIT without laying any prints
    }
    
    // ... (prints are laid from line 131 onward, ONLY if bInitialized)
}
```

**Fact:** Footprints are spawned exclusively from TickComponent → LayFootprint (line 133, 210).

**Fact:** The first tick exits early (line 87) without laying prints. Only the SECOND tick can lay prints.

**Sequence:**
1. Component attached → BeginPlay runs → Added to LiveComponents
2. First tick → Initialize (bInitialized = true) → Return
3. Second tick → Can lay prints (now registered, safe)

**Result:** Prints cannot be laid before the component is registered.

---

### (C) Erasure Correctly Queries the World

**FootprintComponent.cpp line 235-250 (EraseAllImpermanent):**
```cpp
int32 UFootprintComponent::EraseAllImpermanent(const UWorld* World)
{
    int32 Total = 0;
    TArray<TWeakObjectPtr<UFootprintComponent>> Snapshot = LiveComponents;
    for (const TWeakObjectPtr<UFootprintComponent>& Comp : Snapshot)
    {
        UFootprintComponent* C = Comp.Get();
        if (C && C->GetWorld() == World)  // ← World filter
        {
            Total += C->EraseImpermanent();
        }
    }
    return Total;
}
```

**WeatherComponent.cpp line 188:**
```cpp
const int32 Erased = UFootprintComponent::EraseAllImpermanent(GetWorld());
LastStormFootprintsErased = Erased;
```

**Fact:** WeatherComponent passes GetWorld() to EraseAllImpermanent, which correctly filters components by world (line 244).

**Fact:** Each component's EraseImpermanent() (lines 214-233) iterates its LiveFootprints and destroys all impermanent prints.

**Result:** No cross-world contamination; erasure targets the correct component registry.

---

## Potential Failure Modes Investigated

1. **Could attach order delay BeginPlay?** — No. Component.BeginPlay is part of the actor's initialization, not deferred by attachment order.

2. **Could TickComponent run before BeginPlay?** — No. UE5 guarantees BeginPlay completes first.

3. **Could prints be spawned without going through LayFootprint?** — No. LayFootprint is the only print-spawning function (line 139).

4. **Could WeatherComponent use the wrong World?** — No. GetWorld() is the correct accessor; all components on the same actor share a world.

5. **Could LiveComponents be corrupted?** — No. RemoveAll in EndPlay (line 63) safely cleans weak pointers; Add in BeginPlay is atomic.

---

## Conclusion

The registration mechanism is **sound**. UE5's BeginPlay → TickComponent ordering, combined with the one-tick initialization delay in TickComponent, guarantees that:
- Components are registered BEFORE any ticks run
- Prints are laid ONLY AFTER registration
- Erasure queries the registry correctly, scoped to the correct world

**LastStormFootprintsErased will never be 0 due to a registration hole.** If it reads 0, the cause is that no impermanent prints existed to erase (all durable surfaces, or player never walked).

---

## DISPOSITION: weather-erasure-registry:refuted
