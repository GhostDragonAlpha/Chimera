// Copyright 2026 Chimera Project. All Rights Reserved.

#include "WeatherComponent.h"
#include "WindSystemComponent.h"
#include "FootprintComponent.h"
#include "GameFramework/Actor.h"
#include "Engine/World.h"

UWeatherComponent::UWeatherComponent()
{
    PrimaryComponentTick.bCanEverTick = true;

    // Wind bands (seed WIND dict).
    CalmWindSpeed = 2.0f;
    BreezeWindSpeed = 6.0f;
    GustWindSpeed = 12.0f;
    StormWindSpeed = 24.0f;

    // Cadence (seed WIND dict).
    GustPeriodMinSeconds = 8.0f;
    GustPeriodMaxSeconds = 30.0f;
    StormDurationMinMinutes = 18.0f;
    StormDurationMaxMinutes = 45.0f;
    StormPeriodMinDays = 5.0f;
    StormPeriodMaxDays = 9.0f;

    // Clock.
    DayLengthHours = 27.0f;          // seed DAY_LENGTH_HOURS
    HoursPerRealSecond = 0.1f;       // a full day every ~4.5 real minutes
    WeatherSeed = 1337;

    // State.
    WindSpeed = CalmWindSpeed;
    WindDirectionRadians = 0.0f;
    bStormActive = false;
    StormIntensity = 0.0f;
    DustAgeHours = 0.0f;
    DayNumber = 0;
    TimeOfDayHours = 8.0f;           // seed seeds time_h = 8
    bPlayerIndoors = false;

    // Telemetry.
    StormsPassed = 0;
    LastStormFootprintsErased = 0;
    TotalFootprintsErased = 0;

    // Internal.
    NextGustSeconds = GustPeriodMaxSeconds;
    StormEndsInHours = 0.0f;
    StormTotalHours = 0.0f;
    NextStormDay = StormPeriodMinDays;
    CachedWind = nullptr;
}

void UWeatherComponent::ResetWeather()
{
    Rng.Initialize(WeatherSeed);
    WindSpeed = CalmWindSpeed;
    WindDirectionRadians = Rng.FRandRange(0.0f, 2.0f * PI);
    NextGustSeconds = Rng.FRandRange(GustPeriodMinSeconds, GustPeriodMaxSeconds);
    NextStormDay = Rng.FRandRange(StormPeriodMinDays, StormPeriodMaxDays);
    DustAgeHours = 0.0f;
    DayNumber = 0;
    TimeOfDayHours = 8.0f;
    bStormActive = false;
    StormIntensity = 0.0f;
    StormEndsInHours = 0.0f;
}

void UWeatherComponent::BeginPlay()
{
    Super::BeginPlay();

    ResetWeather();

    if (AActor* Owner = GetOwner())
    {
        CachedWind = Owner->FindComponentByClass<UWindSystemComponent>();
    }

    UE_LOG(LogTemp, Log,
        TEXT("[WEATHER] initialized (seed=%d) — next storm on day %.2f, %s driving sibling wind"),
        WeatherSeed, NextStormDay, CachedWind ? TEXT("is") : TEXT("no"));
}

void UWeatherComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    AdvanceWeather(DeltaTime);
}

void UWeatherComponent::AdvanceWeather(float DeltaSeconds)
{
    if (DeltaSeconds > 0.0f)
    {
        TickWeather(DeltaSeconds);
    }
}

void UWeatherComponent::TickWeather(float DeltaSeconds)
{
    // Two timescales, exactly as the seed models them: gusts are short-term and
    // decrement in REAL seconds; the clock, dust, and storm duration are long-term
    // and advance in GAME hours (dt * HoursPerRealSecond).
    const float GameHours = DeltaSeconds * HoursPerRealSecond;

    // Advance the clock and roll the day.
    TimeOfDayHours += GameHours;
    while (TimeOfDayHours >= DayLengthHours)
    {
        TimeOfDayHours -= DayLengthHours;
        ++DayNumber;
    }
    const float FractionalDay = static_cast<float>(DayNumber) + TimeOfDayHours / DayLengthHours;

    if (bStormActive)
    {
        // Howling wind, re-jittered each tick (seed: storm * uniform(0.85,1.15)).
        WindSpeed = StormWindSpeed * Rng.FRandRange(0.85f, 1.15f);
        StormEndsInHours -= GameHours;

        // The scour: dust age falls fast mid-storm.
        DustAgeHours = FMath::Max(0.0f, DustAgeHours - 5.0f * GameHours);

        // Intensity ramps up over the first 15% and down over the last 15% so
        // materials/Niagara can fade the storm-wall in and out.
        const float Edge = FMath::Max(StormTotalHours * 0.15f, KINDA_SMALL_NUMBER);
        const float Elapsed = StormTotalHours - StormEndsInHours;
        StormIntensity = FMath::Clamp(FMath::Min3(Elapsed / Edge, StormEndsInHours / Edge, 1.0f), 0.0f, 1.0f);

        if (StormEndsInHours <= 0.0f)
        {
            EndStorm();
        }
    }
    else
    {
        StormIntensity = 0.0f;

        // Base band: calm at night, breeze by day — with brief gusts.
        float Base = IsNight() ? CalmWindSpeed : BreezeWindSpeed;
        NextGustSeconds -= DeltaSeconds;
        if (NextGustSeconds <= 0.0f)
        {
            NextGustSeconds = Rng.FRandRange(GustPeriodMinSeconds, GustPeriodMaxSeconds);
            Base = GustWindSpeed;
        }

        // Ease toward the target band; let direction wander.
        WindSpeed = FMath::Lerp(WindSpeed, Base, FMath::Clamp(0.4f * DeltaSeconds, 0.0f, 1.0f));
        WindDirectionRadians += Rng.FRandRange(-0.1f, 0.1f) * DeltaSeconds;

        // Between storms the land ages and dust settles.
        DustAgeHours += GameHours;

        if (FractionalDay >= NextStormDay)
        {
            BeginStorm();
        }
    }

    PushWindToSibling();
}

void UWeatherComponent::BeginStorm()
{
    bStormActive = true;
    StormTotalHours = Rng.FRandRange(StormDurationMinMinutes, StormDurationMaxMinutes) / 60.0f;
    StormEndsInHours = StormTotalHours;
    StormIntensity = 0.0f;
    NextStormDay += Rng.FRandRange(StormPeriodMinDays, StormPeriodMaxDays);

    UE_LOG(LogTemp, Log,
        TEXT("[DEMOBEAT][WEATHER] storm RISING on day %d (%.0f min) — next after day %.2f"),
        DayNumber, StormTotalHours * 60.0f, NextStormDay);

    OnStormStateChanged.Broadcast(EWeatherStormPhase::Rising, 0);
}

void UWeatherComponent::EndStorm()
{
    bStormActive = false;
    StormIntensity = 0.0f;

    // The memento mori: the storm scours every impermanent (sand) print in the
    // world. Durable surfaces (metal grating, dug pits) survive — this is why
    // footprints don't accumulate forever (Design Law 4).
    const int32 Erased = UFootprintComponent::EraseAllImpermanent(GetWorld());
    LastStormFootprintsErased = Erased;
    TotalFootprintsErased += Erased;
    ++StormsPassed;

    UE_LOG(LogTemp, Log,
        TEXT("[DEMOBEAT][WEATHER] storm PASSED on day %d — erased %d sand footprint(s) (%d total)"),
        DayNumber, Erased, TotalFootprintsErased);

    OnStormStateChanged.Broadcast(EWeatherStormPhase::Passed, Erased);
}

void UWeatherComponent::PushWindToSibling()
{
    // Resolve lazily — the wind component may attach after us (H-34 attach order).
    if (!CachedWind)
    {
        if (AActor* Owner = GetOwner())
        {
            CachedWind = Owner->FindComponentByClass<UWindSystemComponent>();
            if (!CachedWind && bStormActive)
            {
                UE_LOG(LogTemp, Warning,
                    TEXT("[WEATHER] Storm active but UWindSystemComponent not found on %s — wind not applied"),
                    *Owner->GetName());
            }
        }
    }
    if (CachedWind)
    {
        const FVector Dir(FMath::Cos(WindDirectionRadians), FMath::Sin(WindDirectionRadians), 0.0f);
        CachedWind->SetWindConfiguration(Dir, WindSpeed);
    }
}

FVector UWeatherComponent::GetWindVelocity() const
{
    return FVector(FMath::Cos(WindDirectionRadians), FMath::Sin(WindDirectionRadians), 0.0f) * WindSpeed;
}

bool UWeatherComponent::IsNight() const
{
    const float T = TimeOfDayHours / DayLengthHours;
    return T < 0.20f || T > 0.80f;
}

bool UWeatherComponent::ForceStorm()
{
    if (bStormActive)
    {
        return false;
    }
    BeginStorm();
    return true;
}
