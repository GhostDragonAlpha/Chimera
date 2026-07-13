// Copyright 2026 Chimera Project. All Rights Reserved.
#include "SuitLifeSupportComponent.h"
#include "GameFramework/Actor.h"
#include "Engine/Engine.h"   // GEngine on-screen readout

USuitLifeSupportComponent::USuitLifeSupportComponent()
{
    PrimaryComponentTick.bCanEverTick = true;

    // P1 retune (design directive Section 3, 2026-07-13): the original seed GE_*
    // rates (Idle 0.6 / Walk 1.0 / Sprint 3.0 per game-minute) made a full 100-O2
    // tank last 33-167 minutes — nowhere near the "will I make it back?" 5-minute
    // beat the design calls for. Retuned so a walking player empties the tank in
    // ~6m40s (hits the low-O2 alarm at 25% around the 5:00 mark, giving a ~1m40s
    // scramble-back window) and sprinting empties it in 2.5 min. Garden/bank regen
    // raised to match: a near-empty tank refills from the habitat in a few minutes,
    // not the better part of an hour. Battery-at-night bumped too (was ~3 battery
    // lost per ~108s night — never a threat); still secondary to O2's clock.
    O2DrainIdlePerMin      = 6.0f;
    O2DrainWalkPerMin      = 15.0f;
    O2DrainSprintPerMin    = 40.0f;
    O2RegenGardenPerMin    = 30.0f;
    BatteryDrainNightPerMin = 20.0f;
    BatteryRegenBankPerMin  = 30.0f;
    DustClogStormPerMin    = 4.0f;
    DustClogScrubPerMin    = 1.0f;

    // Exertion classification from owner speed (uu/s).
    WalkSpeedThreshold   = 10.0f;
    // P1 fix (2026-07-13): 400 was calibrated for an assumed 200uu/s base walk
    // speed (WalkSpeed*2, per ChimeraMovementComponent's OWN "stale WalkSpeed*2=400"
    // comment) — but that component's BeginPlay confirms the BP's real MaxWalkSpeed
    // is 600uu/s (design directive's own measured ~626uu/s W-hold agrees), and real
    // sprint (LeftShift held, SprintMultiplier x2) reaches ~1200uu/s. At the old 400,
    // ordinary WASD movement ALREADY exceeded the threshold, so the suit always
    // classified plain walking as Sprint -- the Walk drain rate was unreachable
    // through real input, silently collapsing the intended two-tier threat curve.
    // 900 sits between the real walk (600) and real sprint (1200) speeds so both
    // bands are actually reachable by a player.
    SprintSpeedThreshold = 900.0f;
    LowO2Threshold       = 25.0f;

    // Attribute start values — seed USuitAttributeSet defaults.
    MaxO2       = 100.0f;
    O2          = 100.0f;
    Battery     = 100.0f;
    DustClog    = 0.0f;
    Integrity   = 100.0f;
    Temperature = 20.0f;

    CurrentExertion   = ESuitExertion::Idle;
    bLowO2            = false;
    bDead             = false;
    bIsNight          = false;
    bExposedToStorm   = false;
    bAtOxygenGarden   = false;
    bAtBatteryBank    = false;
    bInShelter        = false;
    bOverrideExertion = false;
    // P0 witness-workflow fix (2026-07-13): WID_O2HUD now renders the real
    // diegetic wrist gauge (see DemoPlayerController::EnsureO2HUD), so the
    // GEngine on-screen debug text would double up with it on screen. Default
    // OFF; flip true only for a quick headless/no-HUD debug session.
    bShowOnScreenReadout = false;

    SecondsSurvived = 0.0f;
    TimesDepleted   = 0;
}

void USuitLifeSupportComponent::BeginPlay()
{
    Super::BeginPlay();
    ResetLifeSupport();
}

void USuitLifeSupportComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    TickLifeSupport(DeltaTime);

    // MVP on-screen readout — renders with no Blueprint/WBP dependency, so the
    // survival loop is VISIBLE in PIE immediately (the UMG WID_O2HUD gauge is the
    // polished follow-up once wired through a PIE session). Keyed messages update
    // in place; duration 0 = refreshed every frame.
    if (bShowOnScreenReadout && GEngine)
    {
        const FColor O2Color = bDead ? FColor::Red : (bLowO2 ? FColor::Orange : FColor::Cyan);
        const TCHAR* O2Tag = bDead ? TEXT("  [SUIT FAILURE]") : (bLowO2 ? TEXT("  [LOW O2]") : TEXT(""));
        GEngine->AddOnScreenDebugMessage(9001, 0.0f, O2Color,
            FString::Printf(TEXT("O2   %5.1f%%%s"), GetO2Fraction() * 100.0f, O2Tag));
        GEngine->AddOnScreenDebugMessage(9002, 0.0f, FColor::Yellow,
            FString::Printf(TEXT("BAT  %5.1f%%"), GetBatteryFraction() * 100.0f));
        GEngine->AddOnScreenDebugMessage(9003, 0.0f, FColor::White,
            FString::Printf(TEXT("DUST %5.1f%%"), GetDustClogFraction() * 100.0f));
    }
}

ESuitExertion USuitLifeSupportComponent::ResolveExertion() const
{
    if (bOverrideExertion)
    {
        return CurrentExertion;
    }
    const AActor* Owner = GetOwner();
    const float Speed = Owner ? Owner->GetVelocity().Size() : 0.0f;
    if (Speed > SprintSpeedThreshold)
    {
        return ESuitExertion::Sprint;
    }
    if (Speed > WalkSpeedThreshold)
    {
        return ESuitExertion::Walk;
    }
    return ESuitExertion::Idle;
}

float USuitLifeSupportComponent::O2DrainForExertion(ESuitExertion Exertion) const
{
    switch (Exertion)
    {
    case ESuitExertion::Sprint: return O2DrainSprintPerMin;
    case ESuitExertion::Walk:   return O2DrainWalkPerMin;
    case ESuitExertion::Idle:
    default:                    return O2DrainIdlePerMin;
    }
}

void USuitLifeSupportComponent::TickLifeSupport(float DeltaSeconds)
{
    if (bDead || DeltaSeconds <= 0.0f)
    {
        return;
    }

    // Per-minute rates become per-second deltas over DeltaSeconds.
    const float PerSecond = DeltaSeconds / 60.0f;

    CurrentExertion = ResolveExertion();

    // --- O2: drain by exertion, regen in an oxygen garden ---
    float O2Delta = -O2DrainForExertion(CurrentExertion);
    if (bAtOxygenGarden)
    {
        O2Delta += O2RegenGardenPerMin;
    }
    O2 = FMath::Clamp(O2 + O2Delta * PerSecond, 0.0f, MaxO2);

    // --- Battery: drain at night, regen at a battery bank ---
    float BatteryDelta = 0.0f;
    if (bIsNight)
    {
        BatteryDelta -= BatteryDrainNightPerMin;
    }
    if (bAtBatteryBank)
    {
        BatteryDelta += BatteryRegenBankPerMin;
    }
    Battery = FMath::Clamp(Battery + BatteryDelta * PerSecond, 0.0f, 100.0f);

    // --- DustClog: rises only in a storm outdoors, scrubs off in shelter ---
    float ClogDelta = 0.0f;
    if (bExposedToStorm && !bInShelter)
    {
        ClogDelta += DustClogStormPerMin;
    }
    else if (bInShelter)
    {
        ClogDelta -= DustClogScrubPerMin;
    }
    DustClog = FMath::Clamp(DustClog + ClogDelta * PerSecond, 0.0f, 100.0f);

    SecondsSurvived += DeltaSeconds;

    UpdateO2Edges();
}

void USuitLifeSupportComponent::UpdateO2Edges()
{
    // Low-O2 alarm edge.
    const bool bNowLow = (O2 <= LowO2Threshold);
    if (bNowLow != bLowO2)
    {
        bLowO2 = bNowLow;
        OnLowO2Changed.Broadcast(bLowO2);
    }

    // Death edge — fires exactly once when O2 first reaches zero.
    if (!bDead && O2 <= 0.0f)
    {
        bDead = true;
        ++TimesDepleted;
        OnSuitO2Depleted.Broadcast();
    }
}

float USuitLifeSupportComponent::GetO2Fraction() const
{
    return (MaxO2 > 0.0f) ? FMath::Clamp(O2 / MaxO2, 0.0f, 1.0f) : 0.0f;
}

float USuitLifeSupportComponent::GetBatteryFraction() const
{
    return FMath::Clamp(Battery / 100.0f, 0.0f, 1.0f);
}

float USuitLifeSupportComponent::GetDustClogFraction() const
{
    return FMath::Clamp(DustClog / 100.0f, 0.0f, 1.0f);
}

void USuitLifeSupportComponent::SetExertion(ESuitExertion NewExertion)
{
    CurrentExertion = NewExertion;
}

void USuitLifeSupportComponent::AdvanceLifeSupport(float DeltaSeconds)
{
    TickLifeSupport(DeltaSeconds);
}

void USuitLifeSupportComponent::ResetLifeSupport()
{
    O2          = MaxO2;
    Battery     = 100.0f;
    DustClog    = 0.0f;
    Integrity   = 100.0f;
    Temperature = 20.0f;
    CurrentExertion = ESuitExertion::Idle;
    SecondsSurvived = 0.0f;

    const bool bWasLow = bLowO2;
    bLowO2 = false;
    bDead  = false;
    if (bWasLow)
    {
        OnLowO2Changed.Broadcast(false);
    }
}

void USuitLifeSupportComponent::SetO2(float NewO2)
{
    O2 = FMath::Clamp(NewO2, 0.0f, MaxO2);
    UpdateO2Edges();
}
