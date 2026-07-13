# Interactions Subsystem — Verb Audit (Wave 1)

**Audit Date:** 2026-07-13  
**Auditor:** Haiku Interactions Specialist  
**Scope:** E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Interactions\  
**Related Scars:** H-21, H-22

---

## Executive Summary

Interactions subsystem has **3 fully functional verbs** (PickUp, Drop, Bend) with real behavior, proper component attachment, input binding, and verified world-state changes. **1 adjacent verb** (Shovel/Dig in Tools/) has behavior implemented but **no input binding**, rendering it unplayable.

---

## Per-Verb Status

### 1. PickUp (Verb_PickUp)

**Status:** ✅ FULLY FUNCTIONAL

**Component:** `UPickupInteractionComponent`  
**Behavior Method:** `bool TryInteract()`

**Trace:**
- Has behavior: YES — `TryInteract()` (line 142-170, PickupInteractionComponent.cpp)
  - Finds closest pickup within radius via overlap tracking + fallback world-query
  - Calls `PickupActor->PickUp()` (line 164)
  - Sets `bIsHoldingItem = true`, captures `HeldItemName` (line 161-160)
  - Fires `OnPickupCompleted()` event (line 167)
- Component attachment: YES
  - Created in `ADemoPlayerController` constructor (line 15, DemoPlayerController.cpp)
  - Registered via `RegisterComponent()` (line 18)
  - Owner is controller; no physical primitive, but fallback world-query handles this correctly (lines 123-137, PickupInteractionComponent.cpp)
- Input binding: YES
  - Bound to `DemoInteract` action in `ADemoPlayerController::SetupInputComponent()` (line 36, DemoPlayerController.cpp)
  - Calls `Interact()` → `TryInteract()` (lines 114-124)
- World state change: YES
  - `PickupActor::PickUp()` (line 61-77, PickupActor.cpp) hides and destroys actor
  - Item removed from world ✓

**No fixes required.**

---

### 2. Drop (Verb_Drop)

**Status:** ✅ FULLY FUNCTIONAL

**Component:** `UPickupInteractionComponent`  
**Behavior Method:** `bool TryDrop()`

**Trace:**
- Has behavior: YES — `TryDrop()` (line 172-213, PickupInteractionComponent.cpp)
  - Resolves owner pawn (controller or possessed pawn)
  - Spawns `ADropActor` forward of pawn + 20 units up (line 202)
  - Sets `ItemName` on dropped actor, clears held state (lines 205-209)
  - Returns true if spawn succeeded
- Component attachment: YES (same `PickupInteractionComponent` as PickUp)
- Input binding: YES
  - Bound to `DemoDrop` action in `ADemoPlayerController::SetupInputComponent()` (line 37)
  - Calls `DropItem()` → `TryDrop()` (lines 126-136)
- World state change: YES
  - `ADropActor` spawned and registered in world
  - Physics enabled at `ADropActor::BeginPlay()` (lines 21-34, DropActor.cpp)
  - Item added to world, physics simulating until stabilized ✓

**Note:** `ADropActor` inherits from `APickupActor`, so dropped items can be picked back up correctly.

**No fixes required.**

---

### 3. Bend/Crouch (Verb_Bend)

**Status:** ✅ FULLY FUNCTIONAL

**Behavior Method:** Built-in `ACharacter::Crouch()` / `ACharacter::UnCrouch()`

**Trace:**
- Has behavior: YES — UE5 native methods
  - `ACharacter::Crouch()` reduces capsule height, lowers view
  - `ACharacter::UnCrouch()` restores standing height
- Component setup: YES
  - `ADemoPlayerController::ConfigureCrouchCapsule()` (line 138-167, DemoPlayerController.cpp)
  - Called at possession time (line 46, `OnPossess`)
  - Sets `bCanCrouch = true` on movement component (line 154)
  - Sets crouched half-height to 40 units (line 158, from ~90 standing)
- Input binding: YES
  - `DemoCrouch` bound to StartCrouch (Pressed) / StopCrouch (Released) (lines 34-35, DemoPlayerController.cpp)
  - Maps to `C` key via DefaultInput.ini
- World state change: YES
  - Capsule height changes: 90 → 40 on crouch, 40 → 90 on uncrouch
  - Verified by beat test `verb_bend_location` (verb_interactions.beats.json line 24-35)
  - Test uses `pawn_property_toggles` to verify reversible state change ✓

**Beat Verification:** Passed `pawn_property_toggles` in verb_interactions.beats.json  
**Log Marker:** "[VERB_BEND]" logged at line 164 in DemoPlayerController.cpp

**No fixes required.**

---

## Adjacent Subsystem: Tools (Shovel) — **INCOMPLETE VERB**

**Status:** ⚠️ INCOMPLETE (behavior exists but unplayable)

**Component:** `ATool_Shovel` (not a component, an actor)  
**Behavior Method:** `bool Dig()`

**Trace:**
- Has behavior: YES — `Dig()` method (line 41-97, ATool_Shovel.cpp)
  - Raycasts from shovel location downward
  - On hit: emits dust particles, plays impact sound, creates decal, reduces durability
  - Returns true on successful dig, false on miss/zero-durability
  - World state change: Dust emitted, sound played, decal created, durability decremented ✓
- Input binding: **NO** ❌
  - No call to `TryDig()` or similar in DemoPlayerController
  - No input action bound to Dig (unlike Interact/Drop/Crouch)
  - Shovel beats (verb_interactions.beats.json lines 70-110) do NOT call `Dig()` — they only move and screenshot
- Consequence: Shovel is a hollow verb
  - Behavior method exists but is never called during gameplay
  - This matches H-21 scar: "A verb needs behavior, not metadata"
  - Currently: DigRadius/DigDepth/Durability properties exist, but Dig() is orphaned

**Root Cause:** Shovel is in Tools/, not fully integrated into interaction system. No input binding was added to DemoPlayerController.

**Requires Supervisor:** Add input binding for Shovel/Dig in DemoPlayerController::SetupInputComponent() and wire it to call Dig() on the currently-equipped tool (if any).

---

## Component Attachment Detail (H-22 Verification)

**Scar H-22:** "Read back live-PIE pawn components before staging an interaction verb — PickUp's component was never attached, bound, or given a level actor to grab."

**Finding:** Component is robust against the H-22 scenario.

**Design:**
- `PickupInteractionComponent` lives on the controller (not the pawn), as documented (DemoPlayerController.h line 26 comment: "Blueprint character carries no input/component graph the bridge can author into")
- Controller has no physical root, so overlap event binding fails silently (PickupInteractionComponent.cpp lines 26-31)
- **Fallback:** `GetClosestPickup()` uses world-query fallback (lines 123-137) that always works
- **Result:** Component IS "given a level actor to grab" via fallback; slower than overlap tracking but correct

**Verdict:** H-22 requirement satisfied by design. Not a bug, but overlap tracking is unused (acceptable trade-off for controller-side component ownership).

---

## Summary of Fixes

| Verb | Status | Fixes Required | Authority |
|---|---|---|---|
| PickUp | ✅ Functional | None | N/A |
| Drop | ✅ Functional | None | N/A |
| Bend | ✅ Functional | None | N/A |
| Shovel | ⚠️ Incomplete | Add input binding + Dig() call | Supervisor (touches DemoPlayerController) |

---

## Closing Notes

1. **Interactions/ subsystem is audit-complete:** All verbs in scope (PickUp, Drop, Bend) are fully functional with real behavior, proper binding, and world-state changes.

2. **Shovel remains unplayable:** H-21 scar is CONFIRMED but outside Interactions/ footprint. Supervisor must wire input binding.

3. **No bugs found in Interactions/* code:** Beat tests pass, fallback paths are robust.
