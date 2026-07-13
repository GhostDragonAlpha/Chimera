// Copyright 2026 Chimera Project. All Rights Reserved.
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Math/RandomStream.h"
#include "WeatherComponent.generated.h"

class UWindSystemComponent;

/**
 * Which edge of a storm the OnStormStateChanged broadcast is reporting.
 */
UENUM(BlueprintType)
enum class EWeatherStormPhase : uint8
{
    Rising  UMETA(DisplayName = "Rising"),   // a storm just began
    Passed  UMETA(DisplayName = "Passed"),   // a storm just ended (footprints erased)
};

/** Broadcast on every storm edge. FootprintsErased is 0 on Rising, the swept count on Passed. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnStormStateChanged, EWeatherStormPhase, Phase, int32, FootprintsErased);

/**
 * Weather authority — the seed's UWeatherSubsystem, realized as an actor
 * component (the project's live pattern; H-34 runtime-attach). It owns the
 * meteorology the world runs on:
 *
 *   - a wind BAND schedule (calm at night, breeze by day, brief gusts every
 *     8-30 s) that it drives into the sibling UWindSystemComponent — this
 *     component decides the wind; that one applies its physics. One authority
 *     each, no fighting over state.
 *   - the ~weekly STORM (every 5-9 game-days, lasting 18-45 game-minutes) that
 *     raises wind to a howl, fills the DustAge with a storm-wall, and on passing
 *     ERASES every impermanent (sand) footprint in the world. This is the
 *     memento mori of Design Law 4: storms are why footprints don't accumulate
 *     forever — metal grating and dug pits survive, sand does not.
 *   - DustAgeHours: rises while calm, decays 5x faster mid-storm — the "how
 *     long since the land was scoured" term dust-accumulation materials read.
 *
 * WindSpeed / StormIntensity / DustAgeHours are exposed as BlueprintReadOnly
 * scalars: the project has no Material Parameter Collection runtime bridge yet,
 * so these ARE the MPC stand-in that materials/telemetry read (a real MPC push
 * is a follow-up seam, not a blocker).
 *
 * Deterministic: seeded FRandomStream, so a given WeatherSeed replays the same
 * storm calendar — hard-fact verifiable, and ForceStorm() lets a beat script
 * drive a storm on demand instead of waiting 5-9 game-days (H-14/H-21: real
 * behaviour reachable by real input, not injection).
 */
UCLASS(ClassGroup = (Chimera), meta = (BlueprintSpawnableComponent, Category = "Environment|Weather"))
class CHIMERA_API UWeatherComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UWeatherComponent();

    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    // === Wind band tuning (uu/s) — seed WIND dict ===
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather|Wind")
    float CalmWindSpeed;    // 2

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather|Wind")
    float BreezeWindSpeed;  // 6

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather|Wind")
    float GustWindSpeed;    // 12

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather|Wind")
    float StormWindSpeed;   // 24

    // === Cadence ===
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather|Cadence")
    float GustPeriodMinSeconds;    // 8

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather|Cadence")
    float GustPeriodMaxSeconds;    // 30

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather|Cadence")
    float StormDurationMinMinutes; // 18

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather|Cadence")
    float StormDurationMaxMinutes; // 45

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather|Cadence")
    float StormPeriodMinDays;      // 5

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather|Cadence")
    float StormPeriodMaxDays;      // 9

    // === Clock ===
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather|Clock")
    float DayLengthHours;          // 27 (seed DAY_LENGTH_HOURS)

    /** Game-hours advanced per real second. The world has no shared sun subsystem
     *  yet, so weather runs its own clock; a celestial system can later drive it. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather|Clock")
    float HoursPerRealSecond;      // 0.1 -> a 27h day every ~4.5 real minutes

    /** RNG seed — same seed replays the same storm calendar (deterministic verify). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather|Clock")
    int32 WeatherSeed;

    // === Live state (MPC stand-in; materials & telemetry read these) ===
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather|State")
    float WindSpeed;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather|State")
    float WindDirectionRadians;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather|State")
    bool bStormActive;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather|State")
    float StormIntensity;          // 0..1 ramp (storm-wall fade)

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather|State")
    float DustAgeHours;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather|State")
    int32 DayNumber;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather|State")
    float TimeOfDayHours;

    /** Set by shelter/suit systems; gates the storm's dust-clog (indoors = safe). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather|State")
    bool bPlayerIndoors;

    // === Telemetry (hard-fact verification counters) ===
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather|Telemetry")
    int32 StormsPassed;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather|Telemetry")
    int32 LastStormFootprintsErased;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather|Telemetry")
    int32 TotalFootprintsErased;

    /** Fires on every storm edge (rising / passed). */
    UPROPERTY(BlueprintAssignable, Category = "Weather")
    FOnStormStateChanged OnStormStateChanged;

    // === Queries ===

    /** Wind velocity vector (direction * current speed). */
    UFUNCTION(BlueprintCallable, Category = "Weather|Query")
    FVector GetWindVelocity() const;

    UFUNCTION(BlueprintCallable, Category = "Weather|Query")
    bool IsStormActive() const { return bStormActive; }

    /** Night = day-fraction < 0.20 or > 0.80 (seed ASun::IsNight). */
    UFUNCTION(BlueprintCallable, Category = "Weather|Query")
    bool IsNight() const;

    /** The suit clogs with dust only during a storm and only while outdoors. */
    UFUNCTION(BlueprintCallable, Category = "Weather|Query")
    bool ShouldClogSuit() const { return bStormActive && !bPlayerIndoors; }

    /** Beat/debug hook: begin a storm now. Returns false if one is already active. */
    UFUNCTION(BlueprintCallable, Category = "Weather|Debug")
    bool ForceStorm();

    /**
     * Seed the RNG from WeatherSeed and reset the clock + storm calendar to their
     * start-of-life values. Called by BeginPlay; also the deterministic entry an
     * acceptance test uses (same seed -> same storm calendar) without needing the
     * component registered into a world.
     */
    UFUNCTION(BlueprintCallable, Category = "Weather|Debug")
    void ResetWeather();

    /** Advance the simulation by DeltaSeconds (real seconds) — the same path Tick
     *  uses. Lets a beat/test fast-forward the clock and storm cycle on demand. */
    UFUNCTION(BlueprintCallable, Category = "Weather|Debug")
    void AdvanceWeather(float DeltaSeconds);

protected:
    virtual void TickWeather(float DeltaSeconds);
    void BeginStorm();
    void EndStorm();
    void PushWindToSibling();

private:
    FRandomStream Rng;
    float NextGustSeconds;      // real-seconds until the next gust
    float StormEndsInHours;     // game-hours remaining in the active storm
    float StormTotalHours;      // this storm's full duration (for the intensity ramp)
    float NextStormDay;         // fractional day the next storm begins

    UPROPERTY(Transient)
    UWindSystemComponent* CachedWind;
};
