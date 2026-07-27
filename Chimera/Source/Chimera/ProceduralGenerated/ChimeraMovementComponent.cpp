// Copyright Chimera. All rights reserved.

#include "ChimeraMovementComponent.h"
#include "Materials/DustAccumulationParticleComponent.h"
#include "Sound/SandSoundComponent.h"
#include "Save/SacrificeLogComponent.h"
#include "Save/StarMemorialComponent.h"
#include "Environment/WeatherComponent.h"
#include "Environment/WindSystemComponent.h"

#include "Components/SkeletalMeshComponent.h"
#include "Components/AudioComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "InputCoreTypes.h"
#include "Logging/LogMacros.h"
#include "Sound/SoundBase.h"
#include "UObject/UObjectGlobals.h" // LoadObject for default footstep assets
#include "PhysicalMaterials/PhysicalMaterial.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "Kismet/GameplayStatics.h"      // SpawnDecalAtLocation
#include "Components/DecalComponent.h"    // UDecalComponent::SetFadeOut
#include "Materials/MaterialInterface.h"  // UMaterialInterface (footprint decal)

#define LOG_MOVE() UE_LOG(LogTemp, Log, TEXT("[UChimeraMovementComponent] %s"), *GetFullName())

// Audio-visual sync telemetry structure
struct FAudioVisualSyncEvent
{
    double ParticleSpawnTime;
    double AudioTriggerTime;
    float SyncLatencyMs;
    ESurfaceMaterialType Surface;
    float MovementSpeed;
    float AudioVolume;
};

// Global telemetry array (for Sleepwalker playtest verification)
TArray<FAudioVisualSyncEvent> GFootstepSyncTelemetry;

// tb-0150: witness-marker surface stringifier. A dedicated helper (not UE's own
// LexToString/UEnum::GetValueAsString) so the [Footstep] log line reads a stable,
// short token (SAND/METAL/ROCK/...) regardless of UENUM display-name formatting.
static const TCHAR* LexSurfaceMaterialToString(ESurfaceMaterialType Surface)
{
    switch (Surface)
    {
        case ESurfaceMaterialType::Sand:   return TEXT("SAND");
        case ESurfaceMaterialType::Metal:  return TEXT("METAL");
        case ESurfaceMaterialType::Rock:   return TEXT("ROCK");
        case ESurfaceMaterialType::Ground: return TEXT("GROUND");
        case ESurfaceMaterialType::Water:  return TEXT("WATER");
        case ESurfaceMaterialType::Custom:
        default:                           return TEXT("CUSTOM");
    }
}

// ------------------------------------------------------------------
// Constructor — default values
// ------------------------------------------------------------------
UChimeraMovementComponent::UChimeraMovementComponent()
    : LastFrameVelocity(FVector::ZeroVector)
    , WeightShiftVelocity(FVector::ZeroVector)
    , TargetWeightShiftOffset(FVector::ZeroVector)
    , WeightShiftAnimationTime(0.0f)
{
    WalkSpeed        = 200.0f;   // ~2 m/s (UE uses cm)
    CameraOffsetX    = 170.0f;
    CameraOffsetY    = 0.0f;
    CameraOffsetZ    = 80.0f;
    FootstepInterval = 0.5f;
    SprintMultiplier = 2.0f;     // walk 200 -> sprint 400 cm/s (> the 300 telemetry bucket threshold)
    bSprinting       = false;

    // Weight shift animation defaults
    MaxWeightShiftMagnitude = 3.5f;     // 3.5 cm max offset (subtle)
    WeightShiftOvershooting = 1.3f;     // 30% overshoot
    WeightShiftDamping      = 8.0f;     // Medium-fast settling

    // Ensure component ticks every frame
    PrimaryComponentTick.TickInterval = 0.0f;
    PrimaryComponentTick.bCanEverTick = true;
}

// ------------------------------------------------------------------
// BeginPlay — the H-34 runtime-attach guarantee. Four dream-loop nights
// (H-31..H-34) traced dead telemetry to one absence: nothing ever created
// the USandSoundComponent, so every query fell back to defaults. Attach it
// here, unconditionally-if-missing, so no Blueprint wiring can drop it.
// ------------------------------------------------------------------
void UChimeraMovementComponent::BeginPlay()
{
    Super::BeginPlay();

    AActor* Owner = GetOwner();
    if (!Owner)
    {
        return;
    }
    // Sprint_Input/volume_norm (tb-0017): capture the pawn's REAL base speed
    // up front — the BP overrides MaxWalkSpeed (600) far above this
    // component's WalkSpeed property (200), and every speed-derived number
    // must normalize against reality, not the stale default.
    if (const ACharacter* OwnerCharacter = Cast<ACharacter>(Owner))
    {
        if (const UCharacterMovementComponent* CharMove = OwnerCharacter->GetCharacterMovement())
        {
            if (BaseMaxWalkSpeed < 0.0f)
            {
                BaseMaxWalkSpeed = CharMove->MaxWalkSpeed;
            }
        }
    }
    if (!Owner->FindComponentByClass<USandSoundComponent>())
    {
        USandSoundComponent* SoundComp =
            NewObject<USandSoundComponent>(Owner, TEXT("SandSoundComponent"));
        if (SoundComp)
        {
            SoundComp->RegisterComponent();
            UE_LOG(LogTemp, Log,
                TEXT("ChimeraMovementComponent: runtime-attached USandSoundComponent to %s (H-34)"),
                *Owner->GetName());
        }
    }
    // tb-0150: bind the canonical body-event to its seed-specified listener
    // (CHIMERA_VISION.py:1672-1673's bus.OnFootstep.AddDynamic(self.OnFootstep)) —
    // re-fetch covers both the just-created and the already-attached branch above.
    // AddUniqueDynamic (not AddDynamic) guards a hypothetical repeated BeginPlay
    // against double-binding and double-firing the listener.
    if (USandSoundComponent* ExistingSoundComp = Owner->FindComponentByClass<USandSoundComponent>())
    {
        OnFootstep.AddUniqueDynamic(ExistingSoundComp, &USandSoundComponent::HandleFootstepEvent);
    }
    // The sacrifice log IS Design Law 2 — it records what the player protected
    // at cost, and the ending (dim star / empty mirror) reads it. Nothing
    // spawned it (H-34, same class as SandSound). Attach it to the player pawn
    // so the meaning system can actually accumulate.
    if (!Owner->FindComponentByClass<USacrificeLogComponent>())
    {
        USacrificeLogComponent* SacrificeLog =
            NewObject<USacrificeLogComponent>(Owner, TEXT("SacrificeLogComponent"));
        if (SacrificeLog)
        {
            SacrificeLog->RegisterComponent();
            UE_LOG(LogTemp, Log,
                TEXT("ChimeraMovementComponent: runtime-attached USacrificeLogComponent to %s (H-34)"),
                *Owner->GetName());
        }
    }
    // The star memorial is the other half of Design Law 2 — every finished
    // life becomes a star whose brightness IS its sacrifice, and bright
    // ancestors light the Yard's night. Persists across generations via its
    // SaveGame star array even though this pawn is recreated each life (H-34).
    if (!Owner->FindComponentByClass<UStarMemorialComponent>())
    {
        UStarMemorialComponent* Memorial =
            NewObject<UStarMemorialComponent>(Owner, TEXT("StarMemorialComponent"));
        if (Memorial)
        {
            Memorial->RegisterComponent();
            UE_LOG(LogTemp, Log,
                TEXT("ChimeraMovementComponent: runtime-attached UStarMemorialComponent to %s (H-34)"),
                *Owner->GetName());
        }
    }
    // The wind's physics applier — WeatherComponent decides the wind, this
    // component applies it. Attach it FIRST so Weather::PushWindToSibling finds
    // it instead of a null pointer (wave-1 recon: it was never attached, so wind
    // never applied to anything) (H-34).
    if (!Owner->FindComponentByClass<UWindSystemComponent>())
    {
        UWindSystemComponent* Wind =
            NewObject<UWindSystemComponent>(Owner, TEXT("WindSystemComponent"));
        if (Wind)
        {
            Wind->RegisterComponent();
            UE_LOG(LogTemp, Log,
                TEXT("ChimeraMovementComponent: runtime-attached UWindSystemComponent to %s (H-34)"),
                *Owner->GetName());
        }
    }

    // Weather is the meteorology authority (seed UWeatherSubsystem): it runs the
    // wind bands + the ~weekly storm that erases sand footprints, and drives the
    // sibling UWindSystemComponent. Attach it on the pawn so the storm's clock
    // and its world-wide footprint sweep are always live (H-34).
    if (!Owner->FindComponentByClass<UWeatherComponent>())
    {
        UWeatherComponent* Weather =
            NewObject<UWeatherComponent>(Owner, TEXT("WeatherComponent"));
        if (Weather)
        {
            Weather->RegisterComponent();
            UE_LOG(LogTemp, Log,
                TEXT("ChimeraMovementComponent: runtime-attached UWeatherComponent to %s (H-34)"),
                *Owner->GetName());
        }
    }
}

// ------------------------------------------------------------------
// SetSprinting — Sprint_Input/state (decomposition dc_b1af6b6e2f33).
// The verb flag must CHANGE simulated numbers (H-21): the pawn's real
// locomotion ceiling lives on its CharacterMovementComponent, so sprint
// scales MaxWalkSpeed there and restores the cached base on release.
// ------------------------------------------------------------------
void UChimeraMovementComponent::SetSprinting(bool bNewSprinting)
{
    if (bSprinting == bNewSprinting)
    {
        return;
    }
    bSprinting = bNewSprinting;

    if (ACharacter* OwnerCharacter = Cast<ACharacter>(GetOwner()))
    {
        if (UCharacterMovementComponent* CharMove = OwnerCharacter->GetCharacterMovement())
        {
            if (BaseMaxWalkSpeed < 0.0f)
            {
                BaseMaxWalkSpeed = CharMove->MaxWalkSpeed;
            }
            CharMove->MaxWalkSpeed = BaseMaxWalkSpeed * (bSprinting ? SprintMultiplier : 1.0f);
            UE_LOG(LogTemp, Log, TEXT("Sprint %s: MaxWalkSpeed=%.0f (base %.0f x %.2f)"),
                bSprinting ? TEXT("ON") : TEXT("OFF"),
                CharMove->MaxWalkSpeed, BaseMaxWalkSpeed,
                bSprinting ? SprintMultiplier : 1.0f);
        }
    }
}

// ------------------------------------------------------------------
// TickComponent — apply velocity to owner root / mesh
// ------------------------------------------------------------------
void UChimeraMovementComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!GetOwner() || !GetOwner()->GetRootComponent())
        return;

    // Sprint_Input/binding (dc_b1af6b6e2f33): the physical LeftShift key
    // drives the sprint state through the REAL input path — PlayerController
    // key state, which the bridge's simulate_input key_down also lands on —
    // never a test injection (H-14).
    if (UWorld* World = GetOwner()->GetWorld())
    {
        if (const APlayerController* PC = World->GetFirstPlayerController())
        {
            const bool bShiftDown = PC->IsInputKeyDown(EKeys::LeftShift);
            if (bShiftDown != bSprinting)
            {
                SetSprinting(bShiftDown);
            }
        }
    }

    // Drive from the owner's actual movement (CharacterMovementComponent),
    // not the unpopulated external CurrentVelocity source. This makes footstep
    // detection, dust emission, and audio fire on real walking without the
    // component re-applying movement (which would double-move the pawn).
    CurrentVelocity = GetOwner()->GetVelocity();

    // Update weight shift animation (based on velocity changes)
    UpdateWeightShift(DeltaTime);

    // NOTE: This component is an ADDITIVE footstep/dust/sound detector that rides
    // on the pawn alongside CharacterMovementComponent. It must NOT re-apply
    // movement (that would double-move the pawn); the owner's real velocity above
    // is used only for footstep detection, surface tracing, and volume scaling.

    // Footstep timer — increment and trigger when interval reached.
    FootstepTimer += DeltaTime;
    if (FootstepTimer >= FootstepInterval)
    {
        FootstepTimer -= FootstepInterval;
        LOG_MOVE();

        if (GetOwner() && CurrentVelocity.SizeSquared() > KINDA_SMALL_NUMBER)
        {
            FVector FootstepLocation = GetOwner()->GetActorLocation();
            FootstepLocation.Z -= 50.0f; // Offset to ground level

            // PHASE 1: Record particle spawn timestamp
            const double ParticleSpawnTime = FPlatformTime::Seconds();

            // Detect surface material FIRST (tb-0150: moved ahead of dust emission so
            // dust intensity can be surface-scaled below; DetectSurfaceMaterial is a
            // pure line-trace read with no ordering dependency on anything that used
            // to precede it — PlayFootstepSound/footprint/servo already ran AFTER
            // detection before this change, so they are unaffected).
            const ESurfaceMaterialType SurfaceMaterial = DetectSurfaceMaterial(FootstepLocation);

            // tb-0150: per-surface reaction traits, sourced from
            // docs/matter/matter_library.json's pair_exceptions (see
            // GetSurfaceFootstepTraits's own doc comment for the full citation).
            float SurfaceTraction = 1.0f;
            bool bSurfaceMakesPrint = true;
            float SurfaceDustKick = 1.0f;
            GetSurfaceFootstepTraits(SurfaceMaterial, SurfaceTraction, bSurfaceMakesPrint, SurfaceDustKick);

            // PHASE 2: Emit dust particles on footstep (audio-visual coupling point),
            // scaled by the surface's dust_kick (tb-0150: was a flat 50 regardless of
            // surface; rock now kicks up ~0.15x, matching the seed's dust_scale).
            if (DustAccumulationComponent)
            {
                const int32 DustParticleCount = FMath::Max(0, FMath::RoundToInt(50.0f * SurfaceDustKick));
                DustAccumulationComponent->EmitDustAtLocation(FootstepLocation, DustParticleCount);
            }

            // PHASE 3: Immediately trigger synchronized audio (AAA <100ms latency target)
            const double AudioTriggerTime = FPlatformTime::Seconds();
            const float SyncLatencyMs = static_cast<float>((AudioTriggerTime - ParticleSpawnTime) * 1000.0);

            // Play contextual footstep sound with speed-based volume scaling
            const float SpeedMagnitude = CurrentVelocity.Size();
            PlayFootstepSound(SurfaceMaterial, FootstepLocation, SpeedMagnitude);

                // Footprint prints — the memento-mori sand marks the weather system
                // later erases (Design Law 4). Gated by bEnableFootprints, throttled by
                // FootprintSpawnInterval, sized by FootprintSize* (previously dead config),
                // and (tb-0150) by the surface's own makes_print — rock/ice no longer
                // print, matching the seed's SURFACE_TABLE.
                FootprintSpawnTimer += FootstepInterval;
                if (bEnableFootprints && bSurfaceMakesPrint && FootprintSpawnTimer >= FootprintSpawnInterval)
                {
                    FootprintSpawnTimer = 0.0f;
                    SpawnFootprintDecal(FootstepLocation, GetOwner()->GetActorRotation(), SurfaceMaterial);
                }

            // PHASE 4: Play servo sound (suit actuator feedback) with speed-based layering
            if (bEnableServoSounds)
            {
                PlayServoSound(SpeedMagnitude, FootstepLocation);
            }

            // Record telemetry for Sleepwalker verification
            FAudioVisualSyncEvent SyncEvent;
            SyncEvent.ParticleSpawnTime = ParticleSpawnTime;
            SyncEvent.AudioTriggerTime = AudioTriggerTime;
            SyncEvent.SyncLatencyMs = SyncLatencyMs;
            SyncEvent.Surface = SurfaceMaterial;
            SyncEvent.MovementSpeed = SpeedMagnitude;

            // Volume normalizer (tb-0017): walk ~0.5, sprint ~1.0. Normalize
            // by the REAL top speed (captured base x sprint multiplier) so the
            // curve cannot saturate below sprint — the stale WalkSpeed*2=400
            // ceiling sat under the pawn's actual 600 base and clamped walk
            // AND sprint to identical 1.0 (simtest_1e4fe7b372af6644).
            const float MaxSpeed = (BaseMaxWalkSpeed > 0.0f)
                ? BaseMaxWalkSpeed * SprintMultiplier
                : WalkSpeed * 2.0f;
            SyncEvent.AudioVolume = FMath::Clamp(SpeedMagnitude / MaxSpeed, 0.0f, 1.0f);

            GFootstepSyncTelemetry.Add(SyncEvent);


            // Also record to SandSoundComponent telemetry (BeginPlay guarantees
            // attachment — H-34); speed feeds the volume-vs-speed buckets. This is
            // the PRE-EXISTING tb-0001 sync-latency contract (H-31/H-32 lineage) —
            // left UNCHANGED by tb-0150's canonical-event work below, which is
            // additive (SandSoundComponent gains a SECOND, distinct responsibility
            // via the OnFootstep delegate, not a duplicate of this telemetry call).
            if (USandSoundComponent* SoundComp = Cast<USandSoundComponent>(GetOwner()->GetComponentByClass(USandSoundComponent::StaticClass())))
            {
                SoundComp->RecordFootstepSyncEvent(SyncLatencyMs, SyncEvent.AudioVolume, SpeedMagnitude);
            }

            // UE_LOG for monitoring (CHIMERA_AGENT_SIM will capture)
            UE_LOG(LogTemp, Log, TEXT("Footstep Sync: Latency=%.2f ms, Surface=%d, Volume=%.2f, Speed=%.0f cm/s"),
                SyncLatencyMs, (int32)SurfaceMaterial, SyncEvent.AudioVolume, SpeedMagnitude);

            // ------------------------------------------------------------------
            // tb-0150: THE CANONICAL BODY-EVENT (seed FFootstepEvent,
            // CHIMERA_VISION.py:737-747 / 4376-4380). Broadcasts the SAME step this
            // block already detected — no second detector, no duplicate hook (this
            // task's "unify existing consumers, not duplicate them"). Bound
            // listeners today: USandSoundComponent::HandleFootstepEvent (bound in
            // BeginPlay, H-34 pattern). Footprints/dust above stay direct calls
            // since they are already unified by construction (same class, same
            // hook, no cross-component call needed) — the delegate's real unifying
            // value is for consumers OUTSIDE this class (SandSoundComponent today;
            // UI/camera/analytics tomorrow, with zero further edits here).
            // ------------------------------------------------------------------
            bNextFootstepIsLeft = !bNextFootstepIsLeft;

            FFootstepEvent Event;
            Event.SourceActor = GetOwner();
            Event.SurfaceMaterial = SurfaceMaterial;
            Event.Location = FootstepLocation;
            Event.Yaw = GetOwner()->GetActorRotation().Yaw;
            Event.bLeftFoot = bNextFootstepIsLeft;
            Event.SpeedMagnitude = SpeedMagnitude;
            Event.AudioVolume = SyncEvent.AudioVolume;
            Event.TriggerTime = AudioTriggerTime;
            Event.bLanding = false; // walking cadence, not a landing impact — see FFootstepEvent.h

            // THE witness marker (H-2/H-21 lineage: a beat asserts log_contains on
            // this exact line, never a property read-back).
            UE_LOG(LogTemp, Log, TEXT("[Footstep] surface=%s intensity=%.2f"),
                LexSurfaceMaterialToString(SurfaceMaterial), Event.AudioVolume);

            OnFootstep.Broadcast(Event);
        }
    }

    // Clamp CurrentVelocity to WalkSpeed so it never exceeds the configured limit.
    const float Magnitude = CurrentVelocity.Size();
    if (Magnitude > WalkSpeed && WalkSpeed > KINDA_SMALL_NUMBER)
    {
        CurrentVelocity *= WalkSpeed / Magnitude;
    }
}

// ------------------------------------------------------------------
// SetWalkSpeed — public setter
// ------------------------------------------------------------------
void UChimeraMovementComponent::SetWalkSpeed(float NewSpeed)
{
    WalkSpeed = FMath::Max(NewSpeed, 0.0f);
}

// ------------------------------------------------------------------
// GetCameraOffset — returns the camera offset vector
// ------------------------------------------------------------------
void UChimeraMovementComponent::GetCameraOffset(FVector& OutOffset) const
{
    OutOffset = FVector(CameraOffsetX, CameraOffsetY, CameraOffsetZ);
}

// ------------------------------------------------------------------
// DetectSurfaceMaterial — raycast from feet to detect surface type
// ------------------------------------------------------------------
ESurfaceMaterialType UChimeraMovementComponent::DetectSurfaceMaterial(const FVector& TraceStart)
{
    if (!GetOwner() || !GetOwner()->GetWorld())
    {
        return ESurfaceMaterialType::Ground;
    }

    // Raycast downward from footstep location
    FVector TraceEnd = TraceStart - FVector(0.0f, 0.0f, FootTraceDistance);
    FHitResult OutHit;
    FCollisionQueryParams QueryParams;
    QueryParams.AddIgnoredActor(GetOwner());

    bool bHit = GetOwner()->GetWorld()->LineTraceSingleByChannel(
        OutHit,
        TraceStart,
        TraceEnd,
        ECC_WorldStatic,
        QueryParams
    );

    if (bHit && OutHit.PhysMaterial.IsValid())
    {
        // Map physical material to surface type
        UPhysicalMaterial* PhysMat = OutHit.PhysMaterial.Get();
        if (PhysMat)
        {
            FString MatName = PhysMat->GetName();
            if (MatName.Contains(TEXT("Sand"), ESearchCase::IgnoreCase))
            {
                CurrentSurfaceMaterial = ESurfaceMaterialType::Sand;
                return ESurfaceMaterialType::Sand;
            }
            else if (MatName.Contains(TEXT("Metal"), ESearchCase::IgnoreCase))
            {
                CurrentSurfaceMaterial = ESurfaceMaterialType::Metal;
                return ESurfaceMaterialType::Metal;
            }
            else if (MatName.Contains(TEXT("Rock"), ESearchCase::IgnoreCase))
            {
                CurrentSurfaceMaterial = ESurfaceMaterialType::Rock;
                return ESurfaceMaterialType::Rock;
            }
            else if (MatName.Contains(TEXT("Water"), ESearchCase::IgnoreCase))
            {
                CurrentSurfaceMaterial = ESurfaceMaterialType::Water;
                return ESurfaceMaterialType::Water;
            }
        }
    }

    CurrentSurfaceMaterial = ESurfaceMaterialType::Ground;
    return ESurfaceMaterialType::Ground;
}

// ------------------------------------------------------------------
// PlayFootstepSound — trigger spatialized footstep audio with volume scaling
// ------------------------------------------------------------------
void UChimeraMovementComponent::PlayFootstepSound(ESurfaceMaterialType SurfaceMaterial, const FVector& Location, float SpeedMagnitude)
{
    if (!GetOwner() || !GetOwner()->GetWorld())
    {
        return;
    }

    // Select sound based on surface type
    USoundBase* SelectedSound = nullptr;
    switch (SurfaceMaterial)
    {
        case ESurfaceMaterialType::Sand:
            SelectedSound = SandFootstepSound;
            break;
        case ESurfaceMaterialType::Metal:
            SelectedSound = MetalFootstepSound;
            break;
        case ESurfaceMaterialType::Rock:
            SelectedSound = RockFootstepSound;
            break;
        case ESurfaceMaterialType::Water:
            SelectedSound = WaterFootstepSound;
            break;
        case ESurfaceMaterialType::Ground:
        case ESurfaceMaterialType::Custom:
        default:
            SelectedSound = GroundFootstepSound;
            break;
    }

    if (!SelectedSound && bAutoLoadDefaultFootsteps)
    {
        SelectedSound = GetDefaultFootstepSound(SurfaceMaterial);
    }

    if (!SelectedSound)
    {
        return; // No sound asset configured for this surface
    }

    // Create or reuse audio component
    if (!FootstepAudioComponent)
    {
        FootstepAudioComponent = NewObject<UAudioComponent>(GetOwner(), TEXT("FootstepAudioComponent"));
        if (FootstepAudioComponent)
        {
            FootstepAudioComponent->RegisterComponent();
        }
    }

    if (FootstepAudioComponent)
    {
        // Calculate volume based on movement speed (0.2 to 1.0 scale). Real sprint
        // ceiling: the BP overrides MaxWalkSpeed (600) far above WalkSpeed (200), so
        // the stale WalkSpeed*2=400 saturated walk & sprint into one volume (matches
        // the telemetry path's fix above; found independently by 2 audit agents).
        const float MaxSpeed = (BaseMaxWalkSpeed > 0.0f) ? BaseMaxWalkSpeed * SprintMultiplier : WalkSpeed * 2.0f;
        const float SpeedFraction = FMath::Clamp(SpeedMagnitude / MaxSpeed, 0.0f, 1.0f);
        const float VolumeMultiplier = 0.2f + (SpeedFraction * 0.8f); // Range: 0.2 to 1.0

        // Set audio properties and play
        FootstepAudioComponent->SetSound(SelectedSound);
        FootstepAudioComponent->SetVolumeMultiplier(VolumeMultiplier);
        FootstepAudioComponent->SetWorldLocation(Location);
        FootstepAudioComponent->Play(0.0f);

        UE_LOG(LogTemp, Verbose, TEXT("PlayFootstepSound: Surface=%d, Volume=%.2f, Speed=%.0f cm/s"),
            (int32)SurfaceMaterial, VolumeMultiplier, SpeedMagnitude);
    }
}

// ------------------------------------------------------------------
// PlayServoSound — play servo/pneumatic sounds (suit actuator feedback)
// Speed-based volume layering: quiet on walk, medium on run, loud on sprint
// ------------------------------------------------------------------
void UChimeraMovementComponent::PlayServoSound(float SpeedMagnitude, const FVector& Location)
{
    if (!GetOwner() || !GetOwner()->GetWorld() || !ServoSound)
    {
        return;
    }

    // Create or reuse servo audio component
    if (!ServoAudioComponent)
    {
        ServoAudioComponent = NewObject<UAudioComponent>(GetOwner(), TEXT("ServoAudioComponent"));
        if (ServoAudioComponent)
        {
            ServoAudioComponent->RegisterComponent();
        }
    }

    if (!ServoAudioComponent)
    {
        return;
    }

    // Calculate volume based on movement speed
    // Walk (0 speed) = ServoSoundMinVolume (0.1)
    // Sprint (2.0x walk speed) = ServoSoundMaxVolume (0.6)
    // Real sprint ceiling (BP MaxWalkSpeed 600), not the stale WalkSpeed*2=400.
    const float MaxSpeed = (BaseMaxWalkSpeed > 0.0f) ? BaseMaxWalkSpeed * SprintMultiplier : WalkSpeed * 2.0f;
    const float SpeedFraction = FMath::Clamp(SpeedMagnitude / MaxSpeed, 0.0f, 1.0f);

    // Volume layering:
    // 0-50% speed (walk): quiet (min volume)
    // 50-150% speed (run): medium (linear interpolation)
    // 150%+ speed (sprint): loud (max volume)
    float VolumeMultiplier = ServoSoundMinVolume;
    if (SpeedFraction > 0.5f)
    {
        // Linear interpolation from min to max for speeds above 50%
        VolumeMultiplier = ServoSoundMinVolume + ((SpeedFraction - 0.5f) / 0.5f) * (ServoSoundMaxVolume - ServoSoundMinVolume);
        VolumeMultiplier = FMath::Clamp(VolumeMultiplier, ServoSoundMinVolume, ServoSoundMaxVolume);
    }

    // Set audio properties and play
    ServoAudioComponent->SetSound(ServoSound);
    ServoAudioComponent->SetVolumeMultiplier(VolumeMultiplier);
    ServoAudioComponent->SetWorldLocation(Location);
    ServoAudioComponent->Play(0.0f);

    UE_LOG(LogTemp, Verbose, TEXT("PlayServoSound: Volume=%.3f (min=%.1f, max=%.1f), Speed=%.0f cm/s, Pitch=%.2f"),
        VolumeMultiplier, ServoSoundMinVolume, ServoSoundMaxVolume, SpeedMagnitude, 1.0f + (SpeedFraction * 0.3f));
}

// ------------------------------------------------------------------
// SpawnFootprintDecal — spawn footprint decal at location
// ------------------------------------------------------------------
void UChimeraMovementComponent::SpawnFootprintDecal(const FVector& Location, const FRotator& Rotation, ESurfaceMaterialType SurfaceMaterial)
{
    // Honor the configured footprint switch — no print when disabled.
    if (!bEnableFootprints)
    {
        return;
    }
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }
    // The print is sized by the configured footprint dimensions (half-extents).
    const FVector DecalSize(FootprintSizeX * 0.5f, FootprintSizeY * 0.5f, FootprintSizeZ * 0.5f);
    // A level-assigned decal material (soft; may be unset early). A missing material
    // still honors the config + logs; assigning one in BP makes the prints visible.
    UMaterialInterface* DecalMat = FootprintDecalMaterial.LoadSynchronous();
    if (DecalMat)
    {
        if (UDecalComponent* Decal = UGameplayStatics::SpawnDecalAtLocation(
                World, DecalMat, DecalSize, Location, Rotation, 0.0f))
        {
            Decal->SetFadeOut(30.0f, 5.0f);  // the print fades — memory made temporary
        }
    }
    UE_LOG(LogTemp, Verbose, TEXT("Footprint: loc=%.0f,%.0f,%.0f size=%.0fx%.0f surf=%d en=%d"),
        Location.X, Location.Y, Location.Z, FootprintSizeX, FootprintSizeY,
        (int32)SurfaceMaterial, bEnableFootprints ? 1 : 0);
}

// ------------------------------------------------------------------
// UpdateWeightShift — damped oscillator for weight shift on state transitions
// ------------------------------------------------------------------
void UChimeraMovementComponent::UpdateWeightShift(float DeltaTime)
{
    // Detect state change (acceleration or deceleration)
    const FVector VelocityDelta = CurrentVelocity - LastFrameVelocity;
    const float AccelerationMagnitude = VelocityDelta.Size();

    // If there's significant acceleration/deceleration, trigger weight shift
    if (AccelerationMagnitude > 50.0f) // 50 cm/s² threshold
    {
        // Calculate direction opposite to acceleration (back-lean on deceleration, forward on acceleration)
        // For character feel, we want back-lean on deceleration (feels more natural)
        const FVector AccelerationDirection = VelocityDelta.GetSafeNormal();

        // Target offset is in the direction OPPOSITE to acceleration (for inertial feel)
        TargetWeightShiftOffset = -AccelerationDirection * MaxWeightShiftMagnitude;

        // Reset animation timer to start the overshoot curve
        WeightShiftAnimationTime = 0.0f;

        UE_LOG(LogTemp, Verbose, TEXT("Weight shift triggered: AccelMag=%.0f"), AccelerationMagnitude);
    }

    // Apply damped oscillator (spring-like motion with overshoot, then settle)
    // This creates a smooth, believable sway that doesn't feel stiff
    if (WeightShiftAnimationTime < 1.5f) // Animation duration: 1.5 seconds
    {
        WeightShiftAnimationTime += DeltaTime;

        // Overshoot curve: starts fast, peaks with overshoot, settles with damping
        // Using a simplified damped harmonic motion formula
        const float T = FMath::Min(WeightShiftAnimationTime / 0.5f, 1.0f); // Normalize to [0,1] over first 0.5s
        const float PI_VAL = 3.14159265359f;
        const float OvershotCurve = (WeightShiftOvershooting - 1.0f) * FMath::Exp(-WeightShiftDamping * T) * FMath::Sin(PI_VAL * T);
        const float SettleCurve = 1.0f - FMath::Exp(-WeightShiftDamping * WeightShiftAnimationTime);

        const FVector CurrentTarget = TargetWeightShiftOffset * (SettleCurve + OvershotCurve / WeightShiftOvershooting);

        // Smooth interpolation towards current target
        CurrentWeightShiftOffset = FMath::Lerp(CurrentWeightShiftOffset, CurrentTarget, DeltaTime * 15.0f);
    }
    else
    {
        // Animation complete, settle to zero offset
        CurrentWeightShiftOffset = FMath::Lerp(CurrentWeightShiftOffset, FVector::ZeroVector, DeltaTime * 3.0f);
    }

    // Clamp to max magnitude to keep it believable
    const float CurrentMagnitude = CurrentWeightShiftOffset.Size();
    if (CurrentMagnitude > MaxWeightShiftMagnitude)
    {
        CurrentWeightShiftOffset = CurrentWeightShiftOffset.GetSafeNormal() * MaxWeightShiftMagnitude;
    }

    // Update last frame velocity for next frame's acceleration calculation
    LastFrameVelocity = CurrentVelocity;
}

// ------------------------------------------------------------------
// Telemetry Accessors (static, for Sleepwalker playtest verification)
// ------------------------------------------------------------------
int32 UChimeraMovementComponent::GetFootstepSyncEventCount()
{
    return GFootstepSyncTelemetry.Num();
}

float UChimeraMovementComponent::GetAverageFootstepSyncLatencyMs()
{
    if (GFootstepSyncTelemetry.Num() == 0)
    {
        return 0.0f;
    }

    float TotalLatency = 0.0f;
    for (const FAudioVisualSyncEvent& Event : GFootstepSyncTelemetry)
    {
        TotalLatency += Event.SyncLatencyMs;
    }

    return TotalLatency / GFootstepSyncTelemetry.Num();
}

float UChimeraMovementComponent::GetMaxFootstepSyncLatencyMs()
{
    float MaxLatency = 0.0f;
    for (const FAudioVisualSyncEvent& Event : GFootstepSyncTelemetry)
    {
        if (Event.SyncLatencyMs > MaxLatency)
        {
            MaxLatency = Event.SyncLatencyMs;
        }
    }
    return MaxLatency;
}

void UChimeraMovementComponent::ClearFootstepSyncTelemetry()
{
    GFootstepSyncTelemetry.Empty();
    UE_LOG(LogTemp, Log, TEXT("Footstep sync telemetry cleared"));
}

float UChimeraMovementComponent::GetLastFootstepVolume()
{
    if (GFootstepSyncTelemetry.Num() == 0)
    {
        return 0.0f;
    }
    return GFootstepSyncTelemetry.Last().AudioVolume;
}

float UChimeraMovementComponent::GetMaxFootstepVolume()
{
    float MaxVol = 0.0f;
    for (const FAudioVisualSyncEvent& Event : GFootstepSyncTelemetry)
    {
        MaxVol = FMath::Max(MaxVol, Event.AudioVolume);
    }
    return MaxVol;
}

// ------------------------------------------------------------------
// GetSurfaceFootstepTraits — traction/print/dust reaction per surface.
//
// SOURCE OF TRUTH: docs/matter/matter_library.json, top-level "pair_exceptions"
// (its own _doc: "Explicit couples that override family rules. boot|X rows ARE
// the seed's SURFACE_TABLE read as what it always was: the player-contact
// interaction row"). That table is itself a literal transcription of
// CHIMERA_VISION.py's SURFACE_TABLE dict (~line 3559: traction, makes_print,
// dust_scale, footstep_synth_hz per ESurfaceType). ESurfaceMaterialType
// (Sand/Metal/Rock/Ground/Water/Custom, this codebase's own taxonomy) is a
// DIFFERENT enum from the seed's ESurfaceType (Sand/Rock/Metal/Basin/Ice/
// Interior) — there is no literal "boot|ground" key in the matter library.
// Ground/Dirt is DetectSurfaceMaterial's generic fallback for any unrecognized
// physical material (open, walkable, regolith-like exterior terrain — the
// L_RegolithYard level's dominant surface), so it is mapped to boot|sand's
// numbers, the closest analog, documented here rather than invented silently.
// Water has no seed/matter-library entry at all (the seed never modeled it);
// until one exists, Water keeps this component's pre-tb-0150 UNSCALED behavior
// (full traction, prints, full dust) rather than guessing a number nothing
// measured. Traction is plumbed through for completeness/seed-fidelity and
// acceptance-test coverage; it is NOT YET consumed by movement physics
// (no slip-on-low-traction mechanic exists in this component) — a real,
// named, scoped-out follow-up, not silently dropped data.
// ------------------------------------------------------------------
void UChimeraMovementComponent::GetSurfaceFootstepTraits(ESurfaceMaterialType Surface, float& OutTraction, bool& OutMakesPrint, float& OutDustKick)
{
    switch (Surface)
    {
        case ESurfaceMaterialType::Sand:
            // matter_library.json pair_exceptions["boot|sand"]
            OutTraction = 0.75f; OutMakesPrint = true;  OutDustKick = 1.00f; break;
        case ESurfaceMaterialType::Metal:
            // matter_library.json pair_exceptions["boot|metal"]
            OutTraction = 0.90f; OutMakesPrint = true;  OutDustKick = 0.05f; break;
        case ESurfaceMaterialType::Rock:
            // matter_library.json pair_exceptions["boot|rock"] — the seed's only
            // surface with makes_print == false.
            OutTraction = 1.00f; OutMakesPrint = false; OutDustKick = 0.15f; break;
        case ESurfaceMaterialType::Ground:
            // No literal "boot|ground" key exists — mapped to boot|sand (see this
            // function's header comment).
            OutTraction = 0.75f; OutMakesPrint = true;  OutDustKick = 1.00f; break;
        case ESurfaceMaterialType::Water:
        case ESurfaceMaterialType::Custom:
        default:
            // No matter-library entry for either — unscaled (pre-tb-0150 default).
            OutTraction = 1.00f; OutMakesPrint = true;  OutDustKick = 1.00f; break;
    }
}

// ------------------------------------------------------------------
// GetDefaultFootstepSound - auto-resolve CC0 footstep asset by surface type
// ------------------------------------------------------------------
USoundBase* UChimeraMovementComponent::GetDefaultFootstepSound(ESurfaceMaterialType SurfaceMaterial)
{
    if (TObjectPtr<USoundBase>* Cached = DefaultFootstepCache.Find(SurfaceMaterial))
    {
        return Cached->Get();
    }

    FString AssetPath;
    switch (SurfaceMaterial)
    {
        case ESurfaceMaterialType::Sand:
            AssetPath = TEXT("/Game/Audio/Footsteps/Fantozzi-SandL1");
            break;
        case ESurfaceMaterialType::Rock:
        case ESurfaceMaterialType::Metal:
        case ESurfaceMaterialType::Water:
            AssetPath = TEXT("/Game/Audio/Footsteps/Fantozzi-StoneL1");
            break;
        case ESurfaceMaterialType::Ground:
        case ESurfaceMaterialType::Custom:
        default:
            AssetPath = TEXT("/Game/Audio/Footsteps/Fantozzi-SandL1");
            break;
    }

    USoundBase* Loaded = LoadObject<USoundBase>(nullptr, *AssetPath);
    DefaultFootstepCache.Add(SurfaceMaterial, Loaded);
    return Loaded;
}
