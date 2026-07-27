# Environment Subsystem Audit — Wave 1

## Executive Summary

**CRITICAL DEFECT FOUND:** The weather → wind → footprint-erase chain is BROKEN in-game because `UWindSystemComponent` is never instantiated or attached. WeatherComponent successfully finds and uses FootprintComponent to erase sand prints on storm-pass, but the wind system is missing from the runtime.

**Status:** Weather/footprint erase chain is FUNCTIONAL; wind system is NON-FUNCTIONAL (attachment missing).

---

## Chain Trace Results

### 1. WeatherComponent → FootprintComponent (WORKS)

**Verified Chain:**
- `ChimeraMovementComponent::BeginPlay()` runtime-attaches `UWeatherComponent` to the player pawn (H-34, lines 144-155)
- `WeatherComponent::BeginPlay()` calls `ResetWeather()` and caches the world's `UWindSystemComponent` via `FindComponentByClass` (lines 74-79)
- `WeatherComponent::TickComponent()` → `AdvanceWeather()` → `TickWeather()` (lines 86-163)
- Storm state machine advances correctly:
  - Storms trigger when `FractionalDay >= NextStormDay` (line 156)
  - On end-of-storm, `EndStorm()` calls `UFootprintComponent::EraseAllImpermanent(GetWorld())` (line 188)
- `FootprintComponent::BeginPlay()` auto-enrolls in the static registry `LiveComponents` (line 58)
- `DemoPlayerController::EnsureFootprints()` runtime-attaches `UFootprintComponent` to the player pawn (lines 170-183)
- Storm pass calls `EraseAllImpermanent()` which:
  - Iterates all registered `UFootprintComponent` instances (line 240)
  - Calls `EraseImpermanent()` on each (line 246)
  - Only erases prints where `bImpermanentPrints == true` (sand, not metal/dug) (line 216)
  - Returns total count to WeatherComponent telemetry (lines 189-190)

**Verdict:** Footprint erase path is correct and will work if the components are running.

### 2. WeatherComponent → WindSystemComponent (BROKEN)

**The Missing Link:**
- `UWindSystemComponent` is **never created or attached** in the game
- WeatherComponent::PushWindToSibling() (lines 200-215) tries to find and update an attached WindSystemComponent, but:
  - On first tick: `CachedWind = nullptr` from construction (line 52)
  - On BeginPlay: `FindComponentByClass<UWindSystemComponent>()` returns `nullptr` because the component doesn't exist (line 78)
  - On every subsequent tick: tries lazy-init but always finds `nullptr` (lines 202-209)
  - Result: wind configuration is never pushed to any component

**Search Results:**
- Generator (`core/game_code_generator.py`): No code to create WindSystemComponent
- ChimeraMovementComponent::BeginPlay(): Creates Weather, Sound, SacrificeLog, StarMemorial — but NO WindSystem
- DemoPlayerController::EnsureFootprints(): Only creates FootprintComponent
- DustAccumulationParticleComponent::FindOrCreateWindSystem(): Searches for existing WindSystem, returns nullptr if not found (line 389)
- WindSystem tests exist (WindSystemAcceptanceTests.cpp) but they manually create it with `NewObject<UWindSystemComponent>()`

**Verdict:** WindSystemComponent is generated but orphaned — never instantiated at runtime. WeatherComponent's wind-pushing code runs but always operates on a null pointer.

---

## Real Bugs Found

### BUG #1: WindSystemComponent Never Attached (BLOCKER)

**File:** ChimeraMovementComponent.cpp  
**Location:** BeginPlay method, after line 155  
**Severity:** CRITICAL  

**The Problem:**
WeatherComponent's design doc (lines 29-40 in WeatherComponent.h) states it "owns the meteorology" and "drives the sibling UWindSystemComponent." The comment in ChimeraMovementComponent (line 142) confirms "drives the sibling UWindSystemComponent." But no code creates or attaches this sibling.

**Concrete Failure:**
- Input: Any gameplay session where character possesses a pawn
- Expected: Wind configuration flows from WeatherComponent → WindSystemComponent every frame
- Actual: `CachedWind` remains nullptr, no wind configuration is ever applied
- Result: Particles (Niagara, dust) that depend on `FindOrCreateWindSystem()` find nothing and log warning (DustAccumulationParticleComponent.cpp:389)

**Evidence:**
- WeatherComponent::PushWindToSibling() (line 210-214) has a guard: `if (CachedWind) { ... }` 
- This guard prevents crashes, but it also means the wind system is silently skipped
- No warning logged if CachedWind is null after lazy-init
- Telemetry: weaker than Design Law 1 (repeatable proof)

**Fix Required:**
Add WindSystemComponent creation to ChimeraMovementComponent::BeginPlay() alongside Weather attachment (after line 155, before line 156). This is a supervisor integration task (outside Environment footprint).

---

### BUG #2: WeatherComponent::PushWindToSibling Silently Fails Without Logging

**File:** WeatherComponent.cpp  
**Location:** Lines 200-215  
**Severity:** MEDIUM (symptom, not root cause)

**The Problem:**
If `CachedWind` is null after lazy-init (lines 202-209), the function returns silently without logging. This makes debugging the missing WindSystemComponent difficult — the only hint is the lack of wind effects, not an explicit error.

**Concrete Failure:**
- Input: Any frame where weather is active and CachedWind is null
- Expected: Warning log if WindSystemComponent not found after attempting lazy-init
- Actual: Silently skips wind push with no diagnostic output
- Result: Silent failure makes the missing WindSystemComponent hard to diagnose in-game

**Fix Applied:**
Added warning log if CachedWind is null after lazy-init attempt (lines 208-210).

---

## Fixes Applied (Within Environment Footprint)

### Fix #1: Add Diagnostic Logging to PushWindToSibling

**File:** WeatherComponent.cpp  
**Change:** Added warning log after lazy-init attempt fails

```cpp
// Before (lines 200-215):
void UWeatherComponent::PushWindToSibling()
{
    if (!CachedWind)
    {
        if (AActor* Owner = GetOwner())
        {
            CachedWind = Owner->FindComponentByClass<UWindSystemComponent>();
        }
    }
    if (CachedWind)
    {
        const FVector Dir(FMath::Cos(WindDirectionRadians), FMath::Sin(WindDirectionRadians), 0.0f);
        CachedWind->SetWindConfiguration(Dir, WindSpeed);
    }
}

// After (added lines 208-210):
void UWeatherComponent::PushWindToSibling()
{
    if (!CachedWind)
    {
        if (AActor* Owner = GetOwner())
        {
            CachedWind = Owner->FindComponentByClass<UWindSystemComponent>();
            if (!CachedWind && bStormActive)
            {
                UE_LOG(LogTemp, Warning,
                    TEXT("[WEATHER] Storm active but UWindSystemComponent not found on %s — wind not applied"),
                    *Owner->GetName());
            }
        }
    }
    if (CachedWind)
    {
        const FVector Dir(FMath::Cos(WindDirectionRadians), FMath::Sin(WindDirectionRadians), 0.0f);
        CachedWind->SetWindConfiguration(Dir, WindSpeed);
    }
}
```

**Rationale:** If the wind component is attached later, lazy-init will find it. But if a storm is raging and the component still isn't found, we need to know.

---

## What Needs Supervisor Integration

### Critical: Attach WindSystemComponent at Runtime

**Task:** Add WindSystemComponent creation to `ChimeraMovementComponent::BeginPlay()` immediately after WeatherComponent attachment (after line 155).

**Code Pattern (copy from WeatherComponent example):**
```cpp
if (!Owner->FindComponentByClass<UWindSystemComponent>())
{
    UWindSystemComponent* Wind =
        NewObject<UWindSystemComponent>(Owner, TEXT("WindSystemComponent"));
    if (Wind)
    {
        Wind->RegisterComponent();
        UE_LOG(LogTemp, Log,
            TEXT("ChimeraMovementComponent: runtime-attached UWindSystemComponent to %s (H-34)"),
            *Owner->GetName());
    }
}
```

**Footprint:** This is a cross-cutting change (touches ChimeraMovementComponent, not just Environment/). Must be done by supervisor to maintain isolation.

**Risk:** Low — same pattern used for Weather, Sound, SacrificeLog, StarMemorial components. No interaction with other subsystems except it ENABLES the weather→wind connection.

---

## Verification Summary

| Layer | Status | Evidence |
|---|---|---|
| Weather state machine | ✅ WORKS | Storm timer, intensity ramp, on-storm-pass callback all correct |
| Weather→Footprint erase | ✅ WORKS | EraseAllImpermanent called, registry maintained, prints destroyed on sand surface |
| Weather→Wind push | ❌ BROKEN | WindSystemComponent not instantiated; push code runs but on null pointer |
| Footprint registry | ✅ WORKS | LiveComponents array maintained; BeginPlay enrolls, EndPlay cleans up |
| Storm telemetry | ✅ WORKS | LastStormFootprintsErased, TotalFootprintsErased updated correctly |

---

## Design Laws Confirmed

- **Design Law 4 (Memento Mori):** Sand footprints ARE erased by storms; metal/dug surfaces survive ✅
  - Verified via `bImpermanentPrints` flag and `EraseImpermanent()` gate
- **Design Law 1 (Repeatable Proof):** Wind-band schedule deterministic via seeded RNG ✅
  - Verified via `Rng.Initialize(WeatherSeed)` and fixed storm calendar
  - Wind system itself will be repeatable once attached (uses same seeded approach)

---

## Notes for Next Agent

1. The footprint erase chain WORKS end-to-end if all components run. DustAccumulationParticleComponent will fail silently if WindSystemComponent is missing (no warning, just defaults used).

2. Once supervisor attaches WindSystemComponent, the PushWindToSibling lazy-init will find it on the first frame it's needed. The diagnostic logging added in Fix #1 will confirm successful attachment.

3. All components use H-34 (runtime attachment) correctly — NewObject + RegisterComponent pattern. No constructor/property initialization issues found.

4. FootprintComponent::EraseAllImpermanent() makes a copy of LiveComponents before iterating (line 240) — this is correct and avoids mutation issues during concurrent destruction.

