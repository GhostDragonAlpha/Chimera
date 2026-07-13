# Phantom Pain Verdict: Weather-Wind Authority Conflict

## Pain Statement (Quoted)

> "UWeatherComponent drives the sibling UWindSystemComponent via SetWindConfiguration every tick, but UWindSystemComponent's own tick also drives its CurrentWindSpeed from BaseWindSpeed/its cycle. The two authorities may FIGHT — so the dust material could read the wrong/oscillating wind depending on tick order."

---

## Verdict

**REFUTED**

There is no authority conflict. Both components cooperate successfully in a well-defined sequence with no fighting or oscillation in CurrentWindSpeed values.

---

## Evidence

### Evidence 1: SetWindConfiguration Authority Chain (WeatherComponent.cpp → WindSystemComponent.cpp)

**File:** `Source/Chimera/ProceduralGenerated/Environment/WeatherComponent.cpp:213`
```cpp
CachedWind->SetWindConfiguration(Dir, WindSpeed);
```

**File:** `Source/Chimera/ProceduralGenerated/Environment/WindSystemComponent.cpp:118-127`
```cpp
void UWindSystemComponent::SetWindConfiguration(FVector Direction, float Speed, float Variance, float CycleTime)
{
    BaseWindDirection = Direction.GetSafeNormal();
    BaseWindSpeed = Speed;                          // Line 121: Weather's value becomes BaseWindSpeed
    WindVariance = FMath::Clamp(Variance, 0.0f, 1.0f);
    WindCycleTime = CycleTime;

    CurrentWindDirection = BaseWindDirection;
    CurrentWindSpeed = BaseWindSpeed;               // Line 126: CurrentWindSpeed set to Speed (Weather's value)
    CurrentWindVelocity = CurrentWindDirection * CurrentWindSpeed;
}
```

**Fact:** SetWindConfiguration sets both `BaseWindSpeed` and `CurrentWindSpeed` to Weather's provided `WindSpeed`. Weather is the authority; Wind accepts the configuration.

### Evidence 2: UpdateWindState Reads Back (No Overwrite, No Fight)

**File:** `Source/Chimera/ProceduralGenerated/Environment/WindSystemComponent.cpp:70-82`
```cpp
void UWindSystemComponent::UpdateWindState(float DeltaTime)
{
    // Apply time-varying variation if cycle time is set
    if (WindCycleTime > 0.0f)
    {
        UpdateVariation(DeltaTime);
    }

    // Calculate current wind velocity
    CurrentWindSpeed = BaseWindSpeed;               // Line 79: Reads BaseWindSpeed (which Weather just set)
    CurrentWindDirection = BaseWindDirection.GetSafeNormal();
    CurrentWindVelocity = CurrentWindDirection * CurrentWindSpeed;
}
```

**Fact:** Line 79 sets `CurrentWindSpeed = BaseWindSpeed`, which is the value that Weather just configured via SetWindConfiguration (line 121). This is a read-back of the configured value, not an independent override. Both authorities end up with the same value: Weather's `WindSpeed`.

### Evidence 3: Final Resolution (Consistent, Not Oscillating)

The sequence per frame is:
1. **Weather.TickComponent** → **PushWindToSibling** → **SetWindConfiguration(Dir, Weather.WindSpeed)**
   - Sets: `BaseWindSpeed = Weather.WindSpeed`, `CurrentWindSpeed = Weather.WindSpeed`
2. **Wind.TickComponent** → **UpdateWindState**
   - Sets: `CurrentWindSpeed = BaseWindSpeed = Weather.WindSpeed` (same value re-read)

**Dust material reads:** `CurrentWindSpeed = Weather.WindSpeed` (consistent, not oscillating)

---

## Separate Issue (Not a Conflict)

**File:** `Source/Chimera/ProceduralGenerated/Environment/WindSystemComponent.cpp:75, 93, 79`

UpdateVariation *computes* a variation but line 79 *overwrites* it:
```cpp
// Line 75: Calls UpdateVariation (if WindCycleTime > 0)
// Line 93 (inside UpdateVariation): CurrentWindSpeed = BaseWindSpeed * (1 + variation)
// Line 79: CurrentWindSpeed = BaseWindSpeed   <-- CLOBBERS the variation
```

This means Wind's own sinusoidal variation (if intended) is suppressed. However, this is an internal Wind bug, not a conflict with Weather's authority. Weather's value is consistent and never oscillates due to this Wind component issue.

---

## Disposition

**DISPOSITION: weather-wind-authority:refuted**

No authority fight exists. The dust material will read CurrentWindSpeed consistently as Weather's configured value. The separate issue (Wind's variation being clobbered by UpdateWindState) does not create oscillation or conflict with Weather's control.

