# Wave-4 NPC Trade Component — Acceptance Test Verdict

**Status:** PASSING (8/8 headless tests)  
**Date:** 2026-07-13  
**Agent:** Haiku Verification  
**Test File:** `Source/Chimera/ProceduralGenerated/Tests/NPCTradeAcceptanceTests.cpp`

## Test Summary

| Test | Scope | Result | Notes |
|---|---|---|---|
| Init | Defaults (TradeRange, bIsTradingActive, PlayerActor) | PASS | Component boots with correct seed state |
| StateToggle | bIsTradingActive toggle via EndTradeInteraction | PASS | Idempotent; safe repeated calls |
| StartTradeNoPlayer | Guard clause: fails without player | PASS | Correctly blocks trade when PlayerActor nullptr |
| DistanceNoPlayer | Sentinel return (-1.0f) when missing owner/player | PASS | Clear failure signal in headless |
| GetOwnerActor | Returns nullptr for bare NewObject | PASS | Expected in headless; owner set in PIE |
| RangeCheckNoWorld | IsPlayerWithinRange guard (no owner/player) | PASS | Prevents NaN/crash from missing actors |
| EndTradeIdempotent | Multiple EndTradeInteraction calls | PASS | State machine is robust |
| RangeProperty | TradeRange default and mutation | PASS | Property is readable and modifiable |

## What Each Test Asserts

### Init
- `TradeRange` defaults to 500.0f (as documented in header)
- `bIsTradingActive` defaults to false (not in active trade at boot)
- `PlayerActor` starts nullptr (not yet found)

### StateToggle
- `EndTradeInteraction()` unconditionally sets `bIsTradingActive = false`
- Calling it when already false is safe (idempotent, logs only when `bIsTradingActive` is true per code)

### StartTradeNoPlayer
- `StartTradeInteraction()` calls `IsPlayerWithinRange()` as first guard
- `IsPlayerWithinRange()` returns false when `PlayerActor == nullptr`
- Therefore, `StartTradeInteraction()` does NOT set `bIsTradingActive = true` without a player
- **This is the critical safety check preventing orphaned trades**

### DistanceNoPlayer
- `GetDistanceToPlayer()` returns -1.0f sentinel when `Owner == nullptr` or `PlayerActor == nullptr`
- Clear error signal (negative distance is impossible in physics, signals missing data)
- Allows calling code to detect and handle missing world state

### GetOwnerActor
- Returns `GetOwner()` (which is nullptr for a bare `NewObject<>()` without world)
- Expected behavior in headless; in PIE, owner is set by the engine when component attaches

### RangeCheckNoWorld
- `IsPlayerWithinRange()` has two guard clauses: `!Owner || !PlayerActor`
- Returns false immediately when either is missing
- Prevents NaN or segfault from calling `FVector::Dist()` on nullptr actors

### EndTradeIdempotent
- Calling `EndTradeInteraction()` multiple times does not corrupt state
- Safe for repeated calls (e.g., from multiple systems, retry logic, cleanup on destruction)

### RangeProperty
- `TradeRange` is publicly readable (verified via direct member access in tests)
- `TradeRange` is publicly modifiable (can be set in editor or via C++)
- Default 500.0f is enforced in constructor

## Headless Coverage (World-Independent)

**Tested in automation (no PIE required):**
- Component instantiation and seed state
- State machine logic (active/inactive flag)
- Guard clauses (nullptr checks preventing crashes)
- Sentinel returns (-1.0f for missing data)
- Property defaults and mutation
- Idempotency (safe repeated calls)

**Reason:** All of these are pure logic with no dependency on actor transforms, physics, or world ticks.

## PIE-Only Coverage (World-Dependent)

The following behaviors **require a running level, player controller, and physics transforms**. They are NOT tested here and must be verified via beat scripts or live playtesting:

1. **FindPlayerActor()**
   - Requires: `GetWorld()` and `GetFirstPlayerController()`
   - Dependency: UE world initialization, player controller ownership
   - Must test: Player pawn correctly cached after BeginPlay

2. **BeginPlay() side effects**
   - Requires: World tick, component attachment to an actor in a level
   - Dependency: Actor lifecycle, world initialization order
   - Must test: Component correctly calls FindPlayerActor at startup

3. **Actual IsPlayerWithinRange calculations**
   - Requires: Both NPC actor and player pawn with valid transforms in world
   - Dependency: Actor position updates, physics/movement simulation
   - Behavior: Should return true if distance ≤ TradeRange, false otherwise
   - Must test: Distance threshold respected (e.g., at 500 units returns true, at 501 returns false)

4. **TickComponent() refresh logic**
   - Requires: World tick loop, repeated calls every 0.5 seconds (TickInterval)
   - Dependency: Engine tick, PlayerActor persistence
   - Must test: PlayerActor is refreshed if lost, trade range is checked each tick

5. **StartTradeInteraction() with real player in range**
   - Requires: Player within TradeRange of NPC
   - Dependency: Verified IsPlayerWithinRange, world state
   - Must test: bIsTradingActive correctly set to true when called with valid player nearby
   - Pre-condition: Only callable after successful guard (IsPlayerWithinRange must be true)

6. **Logging accuracy**
   - Requires: All guards passed, actual actor names available
   - Must test: Correct NPC/player names appear in trade interaction logs

## Correctness Findings

### State Machine Design
- **Simple and correct:** The component uses a single boolean flag `bIsTradingActive` to track state
- **No compound state:** No interaction bugs between multiple overlapping properties
- **Safe transitions:** EndTradeInteraction is an idempotent "off" switch; StartTradeInteraction is guarded by range check
- **Grade:** A (clean, minimal, no defects detected)

### Guard Clauses
- **Owner nullptr check:** Prevents FVector::Dist() crash on null pointer
- **PlayerActor nullptr check:** Prevents distance calculation with missing reference
- **Guard evaluation order:** Both checked in IsPlayerWithinRange() before any calculation
- **Grade:** A (defensive, no bypass paths)

### API Surface
- **Public functions:** All BlueprrintCallable functions are safe to call repeatedly
- **No side effects:** Getters don't mutate state; setters clearly named
- **Sentinel returns:** -1.0f for error case is unambiguous
- **Grade:** A (clean contract, no surprises)

## Known Limitations (by Design)

1. **No inventory/commodity exchange in header**
   - The `.h` file declares only the range/state logic
   - Inventory system (if any) must be in a separate component or subsystem
   - This is not a defect; it's modular design

2. **PlayerActor caching (no weak references)**
   - Stores a raw pointer to the player pawn
   - If player dies and is replaced, FindPlayerActor must be called again (it is, in TickComponent)
   - No use-after-free detected; tick loop handles stale reference
   - Grade: Acceptable for this architecture

3. **No distance event or callback**
   - Component only checks range on tick (every 0.5s)
   - No immediate notification when player enters/exits range
   - If immediacy is required, this would need a physics overlap trigger
   - Current design is sufficient for turn-based or delayed interaction

## Summary: Ready for Observation

**All headless tests pass. The component's world-independent logic is sound:**
- Initialization is correct
- State machine is safe
- Guard clauses prevent crashes
- Idempotent design is robust
- Sentinel returns are unambiguous

**PIE observation required for:**
- FindPlayerActor integration with world/controller
- Distance threshold enforcement with real transforms
- Trade interaction flow with actual player input
- Logging accuracy with live actor names

**Recommended next gate:** Beat script testing in headless Sleepwalker with mock actors, or live PIE playtest with NPC in a level and player movement.

No bugs or design defects detected in wave-2 hardening.
