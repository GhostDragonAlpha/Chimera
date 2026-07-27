# Wave 1 Audit: Missions Subsystem

**Trace Status**: Mission loop is functionally BROKEN in shipping code. Player has zero path to assign, track, and complete missions in-game.

## Critical Bugs Found & Fixed

### BUG #1 (FIXED): MissionComponent Not Initialized on Player Ship
**Severity**: CRITICAL — blocks entire mission loop

**Root Cause**:  
AShip_Trader_Vessel_Alpha::BeginPlay() creates but never initializes MissionComponent.

**Proof**:
- File: `Source/Chimera/ProceduralGenerated/Ships/AShip_Trader_Vessel_Alpha.cpp` lines 32–62
- Constructor (line 27): `MissionComponent = CreateDefaultSubobject<UMissionComponent>(TEXT("MissionComponent"));`
- BeginPlay (lines 32–62): Initializes FlightComponent, ShieldComponent, DamageComponent, SystemDamageComponent
- MissionComponent: **never called with InitializeMissionBoardFromDSL()**
- Result: AvailableMissions array stays empty → player has zero missions to accept

**Before**:
```cpp
void AShip_Trader_Vessel_Alpha::BeginPlay()
{
	Super::BeginPlay();
	// ... initialize FlightComponent, ShieldComponent, DamageComponent ...
	// MissionComponent is missing!
}
```

**After** (APPLIED):
```cpp
void AShip_Trader_Vessel_Alpha::BeginPlay()
{
	Super::BeginPlay();
	// ... existing initializations ...
	
	// Initialize mission board from DSL
	if (MissionComponent)
	{
		MissionComponent->InitializeMissionBoardFromDSL();
	}
}
```

**Test Proof**:
- DemoTerminal (line 47 of DemoTerminal.cpp) correctly calls `MissionSystem->InitializeMissionBoardFromDSL()` 
- DemoTerminal missions work (demo test in ADemoTerminal::DemoMission passes objectives)
- Player ship missions were uninitialized (no data), proving the bug

---

## Structural Issues (Require Supervisor Integration)

### ISSUE #2: No Gameplay-to-Mission Objective Bridge
**Severity**: HIGH — mission objectives won't progress even after initialization

**Root Cause**: No code path connects actual gameplay events to MissionComponent::UpdateObjective().

**Proof**:
- `UpdateObjective()` calls: grep found only test files + DemoTerminal's demo function
  - `ChimeraDSLTests.cpp`: manual test call
  - `FeatureAcceptanceTests.cpp`: manual test calls
  - `DemoTerminal.cpp::DemoMission()`: demo-only test harness
- No gameplay integration points found:
  - `DockingComponent.cpp`: No MissionComponent reference, no UpdateObjective call
  - `InventoryTradeComponent.cpp`: No MissionComponent reference, no UpdateObjective call
  - `FlightComponent.cpp`: No MissionComponent reference
- Result: Player can accept a mission (after fix #1), but completing it requires manual UpdateObjective call

**What Needs to Happen** (supervisor scope):
1. DockingComponent → on successful dock, call player's `MissionComponent->UpdateObjective(TEXT("Dock"), StationName)`
2. InventoryTradeComponent → on cargo delivered to station, call `UpdateObjective(TEXT("Deliver"), CommodityName)`
3. Wire CompleteMission event (line 33 of MissionComponent.h) to UI/player rewards
4. Verify FactionComponent reward logic (line 139 of MissionComponent.cpp) fires on completion

---

### ISSUE #3: Mission System Exists in Two Disconnected Places
**Severity**: MEDIUM — architectural fragmentation

**Where MissionComponent Lives**:
1. **Player Ship** (AShip_Trader_Vessel_Alpha): Created, now initialized ✓
2. **DemoTerminal** (ADemoTerminal): Created, initialized, has demo test harness ✓
3. **VoiceEntity** (AVoiceEntity): Reference exists but MissionSystem explicitly set to nullptr (BeginPlay line 9)

**Impact**: VoiceEntity can't interact with missions (Phase 2+ issue, lower priority).

---

## Verification Matrix

| Gate | Status | Evidence |
|---|---|---|
| **Can mission be assigned?** | ✗→✓ | MissionComponent now initialized; AvailableMissions populated on BeginPlay |
| **Can mission objectives be tracked?** | ✗ | UpdateObjective() not wired to gameplay events (supervisor scope) |
| **Can completion be detected?** | ⚠ | UpdateObjective() logic works (tested), but not called from gameplay |
| **Can rewards be claimed?** | ⚠ | RewardCredits/FactionStanding logic in UpdateObjective (line 142–148), but mission completion unreachable |
| **Is MissionComponent ticked?** | ✗ | MissionComponent is UActorComponent; no Tick() method. Updates happen only on UpdateObjective() calls. |

---

## What's Ready (Low Risk)

1. ✓ Mission data structure (FMissionData, FMissionObjective) — correct
2. ✓ InitializeMissionBoardFromDSL() — generates 3 sample missions correctly
3. ✓ AcceptMission() logic — moves mission from Available to Active ✓
4. ✓ UpdateObjective() state machine — tracks objective completion ✓
5. ✓ CompleteMission event — dispatches on all objectives done ✓
6. ✓ SaveGameComponent integration — saves/loads mission state ✓
7. ✓ Faction reward notification (line 139) — calls FactionComponent::NotifyMissionCompleted() ✓
8. ✓ Credit payout (line 147) — calls InventoryTradeComponent::AddCredits() ✓

---

## What's Missing (Supervisor Scope)

1. **Gameplay hooks**: DockingComponent, InventoryTradeComponent must call UpdateObjective
2. **Event binding**: CompleteMission event must wire to UI/HUD
3. **VoiceEntity integration**: Deferred (Phase 2+)
4. **Mission failure logic**: FailMission event exists but never triggered

---

## Files Changed

- `Source/Chimera/ProceduralGenerated/Ships/AShip_Trader_Vessel_Alpha.cpp` — Added MissionComponent initialization in BeginPlay

## Recommendation

**Ship with Fix #1 applied** (MissionComponent initialization). Mission board now populates on game start. Supervisor must wire gameplay events to UpdateObjective() before missions can be functionally completed in-game.
