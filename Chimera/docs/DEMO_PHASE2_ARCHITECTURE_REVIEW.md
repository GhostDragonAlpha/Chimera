> **DEPRECATED** — This document describes the old approach.
> Read `AGENT_ONBOARDING.md`, `DECISION_METHOD.md`, and `EMERGENT_WORKFLOW.md` instead.
> The thought chain is at `docs/THOUGHT_CHAIN.md`.

# Demo Phase 2 Architecture Review

**Date**: 2026-07-07  
**Reviewer Role**: System Architect (ARCHITECTURE REVIEW)  
**Review Directive**: Validate that Demo Phase 2 recipe is executable and parity-checked with current codebase state.

**Status**: **BLOCKED** — Two actionable issues identified; fixes required before execution.

---

## 1. Recipe Overview

From `DEMO_ARCHITECTURE.md §5 PHASE 2`, items 1–5:

| Item | Deliverable | Owner | Status |
|---|---|---|---|
| 1 | DemoTerminal.h/cpp (manual lane, Interactions/) | hand-edit | ✓ DONE |
| 2 | GameMode template (astronaut FClassFinder, delete double-spawn, AStationActor spawns, guarded DemoTerminal) | generator | ⚠ PARTIAL |
| 3 | MissionComponent payout branch (AddCredits on completion) | generator | ✓ DONE |
| 4 | core/witness.py (beat-timeline recorder) | hand-edit | ✓ DONE |
| 5 | Regenerate + UBT build → exit code 0 | pipeline | ? NOT TESTED |

---

## 2. Code Parity Checklist

### ITEM 1: DemoTerminal.h/cpp

**Location**: `Source/Chimera/ProceduralGenerated/Interactions/DemoTerminal.h|cpp`

**Expected Contents** (from recipe §5 Phase 2 item 1):
- ADemoTerminal : AActor with StaticMesh root
- Subobjects: UEconomyManager, UInventoryTradeComponent, UFactionComponent, USaveGameComponent, UMissionComponent
- BeginPlay: initialize all systems, set credits to 10000, EnableInput(PC)
- UFUNCTION(Exec) wrappers: DemoStatus, DemoBuy(int32), DemoSell(int32), DemoSave, DemoLoad, DemoMission
- All state changes emit [DEMOBEAT] log lines
- Tick draws debug when pawn <800uu

**Actual File Contents**:
- ✓ ADemoTerminal : AActor with TerminalMesh (UStaticMeshComponent)
- ✓ All 5 subobjects present (EconomySystem, TradeSystem, FactionSystem, SaveSystem, MissionSystem)
- ✓ BeginPlay initializes systems (lines 22–58):
  - EconomySystem initialized (logged)
  - TradeSystem credits = 10000.0f (line 36, logged at line 37)
  - FactionSystem->InitializeFromDSL() (line 42)
  - MissionSystem->InitializeMissionBoardFromDSL() (line 48)
  - PC->EnableInput(PC) (line 55)
- ✓ All 6 Exec functions present: DemoStatus, DemoBuy, DemoSell, DemoSave, DemoLoad, DemoMission
- ✓ [DEMOBEAT] logging in all methods
- ✓ Tick draws debug lines when pawn <800uu (lines 60–78)

**Status**: ✓ **PARITY ACHIEVED**

---

### ITEM 2: GameMode Template Surgery

**Location**: `core/game_code_generator.py` (template) → `Source/Chimera/ProceduralGenerated/GameMode/DeepSpaceTraderGameMode.h|cpp` (generated)

#### 2a. FClassFinder Astronaut DefaultPawnClass with Ship Fallback

**Expected**: `FClassFinder` on `/Game/Characters/Astronaut/BP_Astronaut_Character` → `DefaultPawnClass` with ship fallback

**Actual**: Uses LoadClass (functionally equivalent), astronaut first, ship fallback, ADefaultPawn final fallback (lines 24–34)

**Status**: ✓ **PARITY ACHIEVED**

---

#### 2b. Delete Double-Spawn Block (cpp:72–86)

**Expected**: Remove old double-ship spawn + re-possess block

**Actual**: No double-spawn present; only PCG, DemoTerminal self-spawn, and station spawns

**Status**: ✓ **PARITY ACHIEVED**

---

#### 2c. AStationActor Spawns

**Expected**: `station spawns → AStationActor::StaticClass()`

**Actual**: Uses `AActor::StaticClass()` (lines 101, 117, 133)

**Generator Source**: `core/game_code_generator.py` line 923–924 comment says "StationActor.h not yet generated" but it IS generated at `Source/Chimera/ProceduralGenerated/Stations/StationActor.h`

**Issues**:
- Uses `AActor::StaticClass()` instead of `AStationActor::StaticClass()`
- Comment claiming "not yet generated" is FALSE
- No include of StationActor.h in generated GameMode.cpp

**Status**: ⚠ **BLOCKING ISSUE #1**

---

#### 2d. Guarded DemoTerminal Self-Spawn

**Expected**: Guarded spawn at (500, -500, 20) if none exists

**Actual**: Present at lines 82–92, exactly as spec

**Status**: ✓ **PARITY ACHIEVED**

---

### ITEM 3: MissionComponent Payout Branch

**Location**: `Source/Chimera/ProceduralGenerated/Missions/MissionComponent.cpp`

**Expected**: 
```cpp
if (auto* Inv = GetOwner()->FindComponentByClass<UInventoryTradeComponent>()) 
  Inv->AddCredits(M.RewardCredits);
```

**Actual** (lines 1487–1490):
```cpp
if (UInventoryTradeComponent* Inv = GetOwner()->FindComponentByClass<UInventoryTradeComponent>())
{
    Inv->AddCredits(Mission.RewardCredits);
}
```

**Status**: ✓ **PARITY ACHIEVED**

#### 3a. Payout Test Emission

**Expected**: Recipe says "Emit test."

**Actual**: No explicit test named `FMissionCompletePayoutCredits` exists. Related tests (FMissionObjectiveProgressionAndCompletion, FFactionStandingChangesFromGameplay) exercise mission completion transitively but not payout in isolation.

**Status**: ⚠ **BLOCKING ISSUE #2**

---

### ITEM 4: core/witness.py

**Location**: `core/witness.py`

**Expected**: 
- Reuse MCPStdioClient from core/telemetry_probe.py
- Tail Saved/Logs/Chimera.log for [DEMOBEAT]
- Poll inspect runtime_report every 10s
- Emit beat-timeline JSON
- CLI: `python -m core.witness --session A --out beats_A.json`

**Actual**: All features present; MCPStdioClient reused; CLI supports required args

**Status**: ✓ **PARITY ACHIEVED**

---

### ITEM 5: Regenerate + UBT Build

**Expected**: Execute full pipeline → exit code 0

**Actual**: Build artifacts exist; not tested in this review

**Status**: ? **PENDING EXECUTION**

---

## 3. Architectural Issues & Recommendations

### BLOCKING ISSUE #1: Station Spawning Uses AActor Instead of AStationActor

**Severity**: BLOCKER (recipe non-compliance; breaks type contract)

**Problem**:
1. Generator template uses `AActor::StaticClass()` instead of `AStationActor::StaticClass()`
2. Comment claims "StationActor.h not yet generated" — FALSE
3. Stations spawn as generic AActor with no specialized behavior

**Impact**: Demo runs "demo-correct" but architecturally unsound; Phase 3 may break on docking expectations

**Fix**: Update `core/game_code_generator.py` line 923–924:
```python
# OLD:
# Spawn station actor as generic AActor (StationActor.h not yet generated)
spawn_station_code += f"\t\tAActor* SpawnedStation{idx} = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), ...);\n"

# NEW:
# Spawn station actor with full specialization (AStationActor available)
spawn_station_code += f"\t\tAStationActor* SpawnedStation{idx} = GetWorld()->SpawnActor<AStationActor>(AStationActor::StaticClass(), ...);\n"
```

Also add include at line 769:
```python
source_content += f'#include "../Stations/StationActor.h"\n'
```

**Estimated Time**: 5 minutes

---

### BLOCKING ISSUE #2: Mission Payout Test Missing

**Severity**: BLOCKER (recipe requires test; gate H-13 requires all criteria have direct evidence)

**Problem**: No explicit test for mission payout credits (AddCredits on completion)

**Fix**: Add test to generator template emission in `core/game_code_generator.py` (~line 2300):

```cpp
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMissionCompletePayoutCredits,
    "ChimeraTests.Acceptance.MissionCompletePayoutCredits",
    EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FMissionCompletePayoutCredits::RunTest(const FString& Parameters)
{
    UWorld* World = nullptr;
    if (GEngine) {
        for (const FWorldContext& Context : GEngine->GetWorldContexts()) {
            if (Context.World()) { World = Context.World(); break; }
        }
    }
    if (!TestNotNull(TEXT("World available"), World)) return false;
    
    AActor* Actor = World->SpawnActor<AActor>();
    if (!TestNotNull(TEXT("Actor spawned"), Actor)) return false;
    
    UInventoryTradeComponent* Inv = NewObject<UInventoryTradeComponent>(Actor);
    Inv->RegisterComponent();
    Inv->SetCredits(1000.0f);
    
    UMissionComponent* Missions = NewObject<UMissionComponent>(Actor);
    Missions->RegisterComponent();
    
    FMissionData M;
    M.MissionID = FName(TEXT("PAYOUT1"));
    M.RewardCredits = 5000.0f;
    FMissionObjective Dock;
    Dock.Type = TEXT("Dock");
    M.Objectives.Add(Dock);
    Missions->AvailableMissions.Add(M);
    
    Missions->AcceptMission(FName(TEXT("PAYOUT1")));
    float CreditsBeforeCompletion = Inv->GetCredits();
    Missions->UpdateObjective(TEXT("Dock"), TEXT(""));
    float CreditsAfterCompletion = Inv->GetCredits();
    
    TestEqual(TEXT("Credits increased by exact payout amount"), 
        CreditsAfterCompletion, 
        CreditsBeforeCompletion + 5000.0f);
    TestTrue(TEXT("Mission completed"), 
        Missions->CompletedMissions.Contains(FName(TEXT("PAYOUT1"))));
    
    Actor->Destroy();
    return true;
}
```

**Estimated Time**: 10 minutes

---

## 4. Recipe Parity Summary Table

| Phase 2 Item | Requirement | Status | Gap |
|---|---|---|---|
| 1a | DemoTerminal class + subobjects | ✓ DONE | None |
| 1b | BeginPlay initialization | ✓ DONE | None |
| 1c | Exec wrappers | ✓ DONE | None |
| 1d | [DEMOBEAT] logging | ✓ DONE | None |
| 2a | Astronaut DefaultPawnClass | ✓ DONE | None |
| 2b | Delete double-spawn | ✓ DONE | None |
| 2c | AStationActor spawns | ⚠ BROKEN | Uses AActor, not AStationActor |
| 2d | Guarded DemoTerminal self-spawn | ✓ DONE | None |
| 3a | Mission payout logic | ✓ DONE | None |
| 3b | Mission payout test | ✗ MISSING | Test not emitted |
| 4 | core/witness.py | ✓ DONE | None |
| 5 | Regenerate + UBT → exit 0 | ? PENDING | Build not tested |

---

## 5. Execution Readiness Assessment

**Overall Status**: **BLOCKED**

**Go/No-Go Decision**: **NO-GO** until both issues fixed.

**Required Actions**:
1. Fix Issue #1: Update generator to use AStationActor::StaticClass()
2. Fix Issue #2: Add mission payout test to generator template
3. Regenerate DeepSpaceTraderGameMode.cpp and FeatureAcceptanceTests.cpp
4. Run UBT build → verify exit code 0
5. Record build via postflight

**Estimated Fix Time**: 15–20 minutes

**Next Steps**: Escalate to Code mode for fixes, re-validate, proceed to Phase 2 execution

---

**Document Status**: REVIEW COMPLETE  
**Written**: 2026-07-07  
**Recommendation**: Fix issues, re-validate, proceed to Phase 2 execution
