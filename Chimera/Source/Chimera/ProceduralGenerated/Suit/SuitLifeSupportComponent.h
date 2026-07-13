// Copyright 2026 Chimera Project. All Rights Reserved.
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SuitLifeSupportComponent.generated.h"

/**
 * How hard the wearer is working — the exertion band that selects the O2 drain
 * rate. Derived from owner speed each tick (or overridden by a beat/test).
 */
UENUM(BlueprintType)
enum class ESuitExertion : uint8
{
    Idle    UMETA(DisplayName = "Idle"),    // standing still
    Walk    UMETA(DisplayName = "Walk"),    // moving at foot pace
    Sprint  UMETA(DisplayName = "Sprint"),  // running
};

/** Broadcast the instant O2 crosses the low threshold in either direction. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLowO2Changed, bool, bIsLow);

/** Broadcast once when O2 reaches zero — the suit's death edge. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnSuitO2Depleted);

/**
 * EVA suit life-support — the seed's USuitAttributeSet, realized as an actor
 * component (the project's live pattern; the same way UWeatherComponent realizes
 * UWeatherSubsystem). It owns the survival stats the whole game leans on:
 *
 *   - O2 (0..MaxO2): the core clock of an EVA game. Drains every second by the
 *     wearer's EXERTION band — the seed's GE_O2Drain rates: Idle -0.6, Walk -1.0,
 *     Sprint -3.0 per game-minute (per-second internally, /60, for smooth needle
 *     motion). At 0 the suit fails: OnSuitO2Depleted fires once. An oxygen garden
 *     regenerates it (+0.8/min).
 *   - Battery (0..100): drains at night (-1.8/min) — you run on stored sun. A
 *     battery bank recharges it (+2.0/min).
 *   - DustClog (0..100): rises only while exposed to a storm outdoors (+4.0/min,
 *     the weather's ShouldClogSuit gate), scrubbed indoors (-1.0/min). High clog
 *     is the storms' bite — the reason to get inside.
 *   - Integrity / Temperature: carried for the seed's completeness; behaviour is
 *     a follow-up seam (damage + thermal subsystems), so they hold steady for now.
 *
 * GAS-faithful mapping: each field is a seed FGameplayAttributeData; the per-tick
 * deltas below ARE the seed's periodic UGameplayEffects (GE_O2Drain_* etc.). A
 * real UAbilitySystemComponent + UGameplayEffect assets are the follow-up wiring,
 * not a blocker — this component is the working stand-in the wrist gauge reads.
 *
 * Self-contained + deterministic: exertion is read from owner velocity (no
 * ChimeraMovementComponent coupling), and AdvanceLifeSupport() lets a beat/test
 * fast-forward the suit on demand (H-14/H-21: real behaviour reachable by real
 * state, not injection). The environmental inputs (night / storm / shelter /
 * regen stations) are BlueprintReadWrite flags a weather/shelter system sets.
 */
UCLASS(ClassGroup = (Chimera), meta = (BlueprintSpawnableComponent, Category = "Suit|LifeSupport"))
class CHIMERA_API USuitLifeSupportComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    USuitLifeSupportComponent();

    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    // === Drain / regen rates (per game-MINUTE; applied /60 per second) — seed GE_* ===
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Rates")
    float O2DrainIdlePerMin;     // 0.6

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Rates")
    float O2DrainWalkPerMin;     // 1.0

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Rates")
    float O2DrainSprintPerMin;   // 3.0

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Rates")
    float O2RegenGardenPerMin;   // 0.8

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Rates")
    float BatteryDrainNightPerMin;  // 1.8

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Rates")
    float BatteryRegenBankPerMin;   // 2.0

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Rates")
    float DustClogStormPerMin;   // 4.0

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Rates")
    float DustClogScrubPerMin;   // 1.0

    // === Exertion thresholds (uu/s owner speed) ===
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Exertion")
    float WalkSpeedThreshold;    // > this = at least Walk (10)

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Exertion")
    float SprintSpeedThreshold;  // > this = Sprint (400)

    /** O2 at or below this (percent of MaxO2) raises the low-O2 alarm — seed 25. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Exertion")
    float LowO2Threshold;        // 25

    // === Live attributes (the wrist gauge / HUD read these) — seed USuitAttributeSet ===
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Suit|State")
    float O2;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|State")
    float MaxO2;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Suit|State")
    float Battery;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Suit|State")
    float DustClog;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Suit|State")
    float Integrity;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Suit|State")
    float Temperature;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Suit|State")
    ESuitExertion CurrentExertion;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Suit|State")
    bool bLowO2;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Suit|State")
    bool bDead;

    // === Environmental inputs (a weather/shelter system sets these) ===
    /** Night drains the battery (you run on stored sun). Set by weather/celestial. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Environment")
    bool bIsNight;

    /** Outdoors in a storm — the only thing that clogs the suit. Set by weather's ShouldClogSuit(). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Environment")
    bool bExposedToStorm;

    /** Standing in/near an oxygen garden — O2 regenerates. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Environment")
    bool bAtOxygenGarden;

    /** Docked at a battery bank — Battery recharges. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Environment")
    bool bAtBatteryBank;

    /** Inside a shelter — dust scrubs off. Also implies not storm-exposed. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Environment")
    bool bInShelter;

    /** If true, CurrentExertion is driven by SetExertion() instead of owner speed (beats/tests). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Environment")
    bool bOverrideExertion;

    /** Draw a minimal on-screen O2/battery/dust readout each tick via GEngine debug
     *  text — an MVP gauge with no Blueprint dependency until WID_O2HUD is wired. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Suit|Debug")
    bool bShowOnScreenReadout;

    // === Telemetry (hard-fact verification) ===
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Suit|Telemetry")
    float SecondsSurvived;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Suit|Telemetry")
    int32 TimesDepleted;

    // === Delegates ===
    UPROPERTY(BlueprintAssignable, Category = "Suit")
    FOnLowO2Changed OnLowO2Changed;

    UPROPERTY(BlueprintAssignable, Category = "Suit")
    FOnSuitO2Depleted OnSuitO2Depleted;

    // === Queries (the diegetic wrist gauge reads these) ===

    /** O2 as 0..1 of MaxO2 — the wrist needle position. */
    UFUNCTION(BlueprintCallable, Category = "Suit|Query")
    float GetO2Fraction() const;

    UFUNCTION(BlueprintCallable, Category = "Suit|Query")
    float GetBatteryFraction() const;

    UFUNCTION(BlueprintCallable, Category = "Suit|Query")
    float GetDustClogFraction() const;

    UFUNCTION(BlueprintCallable, Category = "Suit|Query")
    bool IsLowO2() const { return bLowO2; }

    UFUNCTION(BlueprintCallable, Category = "Suit|Query")
    bool IsDead() const { return bDead; }

    UFUNCTION(BlueprintCallable, Category = "Suit|Query")
    ESuitExertion GetExertion() const { return CurrentExertion; }

    // === Beat / debug hooks ===

    /** Force the exertion band (requires bOverrideExertion). Lets a beat drive drain without moving. */
    UFUNCTION(BlueprintCallable, Category = "Suit|Debug")
    void SetExertion(ESuitExertion NewExertion);

    /** Advance the suit by DeltaSeconds — the same path Tick uses. Fast-forwards for beats/tests. */
    UFUNCTION(BlueprintCallable, Category = "Suit|Debug")
    void AdvanceLifeSupport(float DeltaSeconds);

    /** Restore all attributes to full and clear death/low flags. Called by BeginPlay; also a refill station. */
    UFUNCTION(BlueprintCallable, Category = "Suit|Debug")
    void ResetLifeSupport();

    /** Directly set O2 (debug/refill). Clamped; updates low/death flags. */
    UFUNCTION(BlueprintCallable, Category = "Suit|Debug")
    void SetO2(float NewO2);

protected:
    virtual void TickLifeSupport(float DeltaSeconds);

    /** Classify exertion from owner speed unless overridden. */
    ESuitExertion ResolveExertion() const;

    /** O2 drain (per game-minute) for a given exertion band. */
    float O2DrainForExertion(ESuitExertion Exertion) const;

    /** Apply low-O2 / death edges after O2 changes, firing delegates once per edge. */
    void UpdateO2Edges();
};
