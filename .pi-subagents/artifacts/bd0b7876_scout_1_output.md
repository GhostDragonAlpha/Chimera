# Code Context

## Files Retrieved

1. **`Chimera/Source/Chimera/ProceduralGenerated/Demo/DemoPlayerController.cpp`** (lines 1-50) — Constructor sets up PickupInteraction, GestureWheelWidget, habitat placeholder mesh, mouse cursor. Key integration target for GameMode's PlayerControllerClass override.

2. **`Chimera/Source/Chimera/ProceduralGenerated/GameMode/DeepSpaceTraderGameMode.cpp`** (136 lines, full file) — GameMode constructor + BeginPlay. Central initialization orchestrator: PCG volumes, demo terminal, 3 stations, demo player controller binding.

3. **`Chimera/Source/Chimera/ProceduralGenerated/Save/DeepSpaceTraderSaveGame.cpp`** (2 lines) — 73-byte stub: only `#include "DeepSpaceTraderSaveGame.h"`. The actual class shape lives in the **header** (see below).

4. **`Chimera/docs/STEAM_PAGE.md`** (full file) — Steam marketing page describing "Deep Space Trader: Educational Frontier" demo.

## Key Code

### DemoPlayerController constructor (lines 25-49) — integration point
```cpp
PickupInteraction = CreateDefaultSubobject<UPickupInteractionComponent>(TEXT("PickupInteraction"));
GestureWheelWidget = CreateDefaultSubobject<UGestureWheel>(TEXT("GestureWheelWidget"));
HabitatHullMesh = ConstructorHelpers::FObjectFinder mesh reference;
bShowMouseCursor = true;
```

### GameMode constructor (lines 23-44) — PC class binding
```cpp
DefaultPawnClass = BP_Astronaut_Character or AShip_Trader_Vessel_Alpha (fallback);
PlayerControllerClass = ADemoPlayerController::StaticClass();
UniverseGen = CreateDefaultSubobject<UUniverseGenerationComponent>(TEXT("UniverseGen"));
```

### GameMode BeginPlay (lines 46-131) — initialization order
1. Bind `PlayerShip` via `GetFirstPlayerController()->GetPawn()`
2. Spawn `PCGVolumeManager` via `SpawnActor<APCGVolumeManager>`
3. Spawn PCG clutter volume (`Environment_Clutter_Graph`, 50000x50000x10000 at +100 Z)
4. Spawn PCG planet surface volume (`Planet_Surface_Generation`, 50000x50000x10000 at 100000 X offset)
5. DemoTerminal self-spawn (guarded: only if none exists)
6. Spawn 3 station actors: `Orbital_Hub_7` (0,0,0), `Ares_Market_Central` (50000,0,0), `Shadow_Reef` (-30000,20000,0)

### DeepSpaceTraderSaveGame.h (full class, 38 lines)
```cpp
UCLASS()
class CHIMERA_API UDeepSpaceTraderSaveGame : public USaveGame
{
    // Wallet + cargo: PlayerCredits, PlayerCargo (TMap<FName, int32>)
    // Ship state: CurrentShipClass, CurrentFuel, CurrentHullHealth, CurrentShield, SubsystemHealth
    // Placement: PlayerLocation, PlayerRotation, CurrentStation
    // Missions: ActiveMissions (FMissionData[]), AvailableMissions, CompletedMissions, FailedMissions
    // Factions: FactionStandings, FactionRelationships
    // Economy: StationSupplies, SaveTimestamp
};
```

### Steam Page — marketing assertions
- "No loading screens. No fictional lore. Actual geology, meteorology, and astronomy."
- "Educational content written with scientific reviewers."
- "Procedural Alien World: Each playthrough generates unique terrain"
- Prototype demo: canyon with 16 educational markers
- Target price: $9.99 Early Access

## Architecture

| System | File | Role |
|--------|------|------|
| **Player Controller** | `DemoPlayerController.cpp` | Handles mouse-look, pickup, gesture wheel (radial menu), demo habitat spawning |
| **Game Mode** | `DeepSpaceTraderGameMode.cpp` | Boot sequence: player pawn → PCG volumes → kiosk → station actors |
| **Save System** | `DeepSpaceTraderSaveGame.cpp` (stub) + `.h` (full class) | Serializes wallet, cargo, ship, missions, factions, economy. Implementation is **header-only** — cpp is a generated stub with no serialization logic. |
| **Marketing** | `STEAM_PAGE.md` | Describes the educational demo for Steam storefront |

**Data Flow:**
- GameMode constructor sets PlayerControllerClass → DemoPlayerController, which handles input (mouse, pickup, gesture wheel) and spawns demo habitat/pickup actors at possess time.
- GameMode BeginPlay spawns PCG volumes (procedural terrain), then a DemoTerminal (kiosk), then three named stations at hardcoded positions.
- SaveGame class lives as data-only header; the cpp is a code-gen stub with no `Serialize()` or `SaveGameToMemory` override — that logic must live in `SaveGameComponent` (Sav/SaveGameComponent.cpp).

## Gaps & Risks

| Severity | Issue | File |
|----------|-------|------|
| **high** | `DeepSpaceTraderSaveGame.cpp` is a 73-byte stub with only the include line. The SaveGame class data is all in the header, but **no serialization logic** (Serialize/Load/Store) exists in the cpp. Actual save/load likely lives in SaveGameComponent or is simply missing. | `DeepSpaceTraderSaveGame.cpp` |
| **medium** | Station spawn positions are hardcoded world-space coordinates. PCG volume placement at (0,0,100) and (100000,0,0) may need to be reconciled with station locations for coherent world layout. Orbital_Hub_7 at (0,0,0) sits inside or adjacent to the clutter volume. | `DeepSpaceTraderGameMode.cpp` lines 72-131 |
| **low** | Two PCG graph asset loads use `StaticLoadObject` with a failed-path warning but no graceful degradation — if the asset doesn't exist, PCG generation silently skips with a log warning. Consider whether that's acceptable for release. | `DeepSpaceTraderGameMode.cpp` lines 78-98 |
| **info** | DemoTerminal spawn is guarded against duplicates via `GetActorOfClass`, but the three station spawns are not — they will fire every BeginPlay, including on travel/restart. | `DeepSpaceTraderGameMode.cpp` lines 100-131 |
| **info** | Steam page claims "no loading screens" and "real science" but `docs/steam_capsule.png` and demo screenshots (`docs/demo_images/slide_01.png` etc.) are referenced but may not exist yet. | `STEAM_PAGE.md` |

## Start Here
Open `DeepSpaceTraderGameMode.cpp` — it is the initialization orchestrator. Every other system (player controller, PCG, stations, terminals) is called from its BeginPlay. Understanding its spawn order reveals where world coherence gaps exist.

---