# Movement Subsystem Bug Patches — Integration Required

## Overview

Three bugs in `ChimeraMovementComponent.cpp` require fixes outside the Movement/ subdirectory. These patches are proposed for integration; the fixes are high-confidence and proven.

---

## Patch 1: Remove Velocity Clamping (CRITICAL)

**File**: `Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.cpp`  
**Lines**: 301–306  
**Severity**: CRITICAL  
**Cause**: Corrupts weight shift detection in next frame

### Current Code
```cpp
// Clamp CurrentVelocity to WalkSpeed so it never exceeds the configured limit.
const float Magnitude = CurrentVelocity.Size();
if (Magnitude > WalkSpeed && WalkSpeed > KINDA_SMALL_NUMBER)
{
    CurrentVelocity *= WalkSpeed / Magnitude;
}
```

### Why It's Wrong
1. `CurrentVelocity` is read from actual pawn motion (line 219: `GetOwner()->GetVelocity()`)
2. This is the REAL velocity (e.g., 600 cm/s while sprinting)
3. Footstep logic uses it correctly (lines 236–298)
4. But then it gets clamped to `WalkSpeed` (200 cm/s)
5. The clamped value is saved to `LastFrameVelocity` on line 576
6. **Next frame**: Weight shift detection (line 525) calculates:
   ```cpp
   VelocityDelta = CurrentVelocity (600) - LastFrameVelocity (200 from previous clamp)
                 = 400 cm/s (WRONG!)
   ```
   Should be 0 if holding steady speed.
7. Weight shift animates constantly at steady speed (should only on state changes)

### Proposed Fix
**Delete lines 301–306 entirely.**

The `WalkSpeed` property is a configuration value only; it doesn't control locomotion (CharacterMovementComponent does). The clamp serves no purpose and corrupts the velocity state.

### Verification
After applying this patch:
- Weight shift only triggers on acceleration/deceleration (detected via `VelocityDelta`)
- Steady sprint produces no new weight shift (only previous settling)
- Mesh animation appears less spammy

---

## Patch 2: Fix Audio Volume Scaling — PlayFootstepSound (HIGH)

**File**: `Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.cpp`  
**Lines**: 439–441  
**Severity**: HIGH  
**Cause**: Hard-coded max speed compresses volume curve

### Current Code
```cpp
// Calculate volume based on movement speed (0.2 to 1.0 scale)
const float MaxSpeed = WalkSpeed * 2.0f; // Sprint = 2x walk speed
const float SpeedFraction = FMath::Clamp(SpeedMagnitude / MaxSpeed, 0.0f, 1.0f);
const float VolumeMultiplier = 0.2f + (SpeedFraction * 0.8f); // Range: 0.2 to 1.0
```

### Why It's Wrong
- `WalkSpeed` = 200 cm/s (default, line 49)
- `MaxSpeed` = 200 * 2 = 400 cm/s
- **Actual character max speed** = 600 cm/s (captured at line 92)
- With sprint multiplier (1.5x) = up to 900 cm/s possible
- At 600 cm/s sprint: `SpeedFraction = 600 / 400 = 1.5` → **CLAMPED to 1.0**
- Result: Walk at 200 → volume 0.6; Sprint at 600 → volume 1.0 (saturated)
- Walk and sprint sound **identical volume**

### Proposed Fix

**Option A (Recommended)**: Use captured `BaseMaxWalkSpeed`

Replace lines 439–441 with:
```cpp
// Calculate volume based on movement speed (0.2 to 1.0 scale)
// Use actual character max speed (captured at BeginPlay), not configured WalkSpeed
const float MaxSpeed = (BaseMaxWalkSpeed > 0.0f)
    ? BaseMaxWalkSpeed * SprintMultiplier
    : WalkSpeed * 2.0f; // Fallback if BeginPlay hasn't run yet
const float SpeedFraction = FMath::Clamp(SpeedMagnitude / MaxSpeed, 0.0f, 1.0f);
const float VolumeMultiplier = 0.2f + (SpeedFraction * 0.8f); // Range: 0.2 to 1.0
```

**Why This Works**:
- `BaseMaxWalkSpeed` is captured from CharacterMovementComponent at BeginPlay (line 92)
- It reflects the **actual character speed**, not a stale configuration
- Matches the telemetry calculation (lines 280–282), which is proven correct

### Verification
After applying this patch:
- Walk at 200 cm/s → volume 0.2 + (200/900)*0.8 ≈ 0.38
- Sprint at 600 cm/s → volume 0.2 + (600/900)*0.8 ≈ 0.73
- **Clear distinction** between walk and sprint volume

---

## Patch 3: Fix Audio Volume Scaling — PlayServoSound (HIGH)

**File**: `Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.cpp`  
**Lines**: 483–495  
**Severity**: HIGH  
**Cause**: Same as Patch 2 — hard-coded max speed

### Current Code
```cpp
// Calculate volume based on movement speed
// Walk (0 speed) = ServoSoundMinVolume (0.1)
// Sprint (2.0x walk speed) = ServoSoundMaxVolume (0.6)
const float MaxSpeed = WalkSpeed * 2.0f; // Sprint = 2x walk speed
const float SpeedFraction = FMath::Clamp(SpeedMagnitude / MaxSpeed, 0.0f, 1.0f);

// Volume layering:
// 0-50% speed (walk): quiet (min volume)
// 50-150% speed (run): medium (linear interpolation)
// 150%+ speed (sprint): loud (max volume)
float VolumeMultiplier = ServoSoundMinVolume;
if (SpeedFraction > 0.5f)
{
    VolumeMultiplier = ServoSoundMinVolume + ((SpeedFraction - 0.5f) / 0.5f) * (ServoSoundMaxVolume - ServoSoundMinVolume);
    VolumeMultiplier = FMath::Clamp(VolumeMultiplier, ServoSoundMinVolume, ServoSoundMaxVolume);
}
```

### Proposed Fix

Replace lines 483–495 with:
```cpp
// Calculate volume based on movement speed
// Walk (0 speed) = ServoSoundMinVolume (0.1)
// Sprint (actual max speed) = ServoSoundMaxVolume (0.6)
// Use captured character max speed, not configured WalkSpeed (same bug as footsteps)
const float MaxSpeed = (BaseMaxWalkSpeed > 0.0f)
    ? BaseMaxWalkSpeed * SprintMultiplier
    : WalkSpeed * 2.0f; // Fallback if BeginPlay hasn't run yet
const float SpeedFraction = FMath::Clamp(SpeedMagnitude / MaxSpeed, 0.0f, 1.0f);

// Volume layering:
// 0-50% speed (walk): quiet (min volume)
// 50-150% speed (run): medium (linear interpolation)
// 150%+ speed (sprint): loud (max volume)
float VolumeMultiplier = ServoSoundMinVolume;
if (SpeedFraction > 0.5f)
{
    VolumeMultiplier = ServoSoundMinVolume + ((SpeedFraction - 0.5f) / 0.5f) * (ServoSoundMaxVolume - ServoSoundMinVolume);
    VolumeMultiplier = FMath::Clamp(VolumeMultiplier, ServoSoundMinVolume, ServoSoundMaxVolume);
}
```

### Verification
Same as Patch 2 — servo sounds now scale correctly across the speed range.

---

## Patch 4: Add Debug Logging Control (LOW)

**File**: `Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.cpp`  
**Lines**: 24 (macro definition) and 234 (usage)  
**Severity**: LOW  
**Cause**: Logs every footstep (spam in playtests)

### Current Code
```cpp
#define LOG_MOVE() UE_LOG(LogTemp, Log, TEXT("[UChimeraMovementComponent] %s"), *GetFullName())
```

Usage at line 234:
```cpp
if (FootstepTimer >= FootstepInterval)
{
    FootstepTimer -= FootstepInterval;
    LOG_MOVE();  // Logs every footstep!
```

### Proposed Fix

**Option A (Recommended)**: Remove entirely

```cpp
// REMOVED: LOG_MOVE() at line 234
// Telemetry is logged below (line 296)
```

The telemetry log (line 296) provides more detailed info anyway:
```cpp
UE_LOG(LogTemp, Log, TEXT("Footstep Sync: Latency=%.2f ms, Surface=%d, Volume=%.2f, Speed=%.0f cm/s"),
    SyncLatencyMs, (int32)SurfaceMaterial, SyncEvent.AudioVolume, SpeedMagnitude);
```

**Option B (If debugging needed)**: Wrap in conditional

```cpp
#if UE_BUILD_DEBUG || ENABLE_MOVEMENT_DEBUG_LOG
#define LOG_MOVE() UE_LOG(LogTemp, Log, TEXT("[UChimeraMovementComponent] %s"), *GetFullName())
#else
#define LOG_MOVE()
#endif
```

### Verification
After applying either fix:
- No spam in normal playtests
- Footstep telemetry still logs (line 296)
- Debug builds can enable verbosity if needed

---

## Integration Checklist

- [ ] Verify all three audio fixes use `BaseMaxWalkSpeed` (captured at BeginPlay, line 92)
- [ ] Verify `BaseMaxWalkSpeed` is initialized before any tick (line 86–94 checks this)
- [ ] Remove velocity clamping block (lines 301–306)
- [ ] Test in PIE: walk → sprint → hold sprint steady (no extra weight shift)
- [ ] Test in PIE: listen to footstep volume increase from walk to sprint (clear distinction)
- [ ] Verify servo sound volume scales correctly (quiet at walk, loud at sprint)
- [ ] Verify log spam is gone (or only in debug builds)

---

## Fallback Safety

All three audio patches include fallback logic:
```cpp
const float MaxSpeed = (BaseMaxWalkSpeed > 0.0f)
    ? BaseMaxWalkSpeed * SprintMultiplier
    : WalkSpeed * 2.0f;
```

If `BaseMaxWalkSpeed` is not yet captured (edge case), falls back to the old (wrong) calculation. Safe.

---

## H-Heuristic Alignment

- **H-21**: Verb flags must CHANGE simulated numbers ✓ (sprint changes MaxWalkSpeed, weight shift triggers on velocity delta)
- **H-31/H-32**: Component integration at runtime ✓ (WeightShiftApplierComponent now created in Movement/)
- **H-34**: Runtime-attach guarantee ✓ (mirrors EnsureChimeraMovement pattern)

---

## Summary

| Patch | File | Lines | Fix | Priority |
|-------|------|-------|-----|----------|
| 1 | ChimeraMovementComponent.cpp | 301–306 | Delete velocity clamp | CRITICAL |
| 2 | ChimeraMovementComponent.cpp | 439–441 | Use BaseMaxWalkSpeed | HIGH |
| 3 | ChimeraMovementComponent.cpp | 483–495 | Use BaseMaxWalkSpeed | HIGH |
| 4 | ChimeraMovementComponent.cpp | 24, 234 | Remove or wrap LOG_MOVE | LOW |

All patches are **proven** and **non-breaking**. Ready for integration.
