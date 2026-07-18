// Copyright Chimera. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SurfaceMaterialType.h"
#include "FFootstepEvent.h"
#include "ChimeraMovementComponent.generated.h"

class UPhysicalMaterial;
class USoundBase;
class ADecalActor;
class UMaterialInterface;
class UDecalComponent;
class UDustAccumulationParticleComponent; // Forward declare from ProceduralGenerated/Materials/

UCLASS(meta = (Blueprintable, Category = "Movement|Walking"))
class CHIMERA_API UChimeraMovementComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UChimeraMovementComponent();

protected:
    // Runtime-attach guarantee (H-34): BeginPlay ensures the owner carries a
    // USandSoundComponent even when no Blueprint ever wired one.
    virtual void BeginPlay() override;

public:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    // === Speed ===
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Walking")
    float WalkSpeed;

    // === Sprint (Sprint_Input/state, decomposition dc_b1af6b6e2f33) ===
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Sprint")
    float SprintMultiplier;

    UPROPERTY(BlueprintReadOnly, Category = "Movement|Sprint")
    bool bSprinting;

    // The verb flag must CHANGE simulated numbers (H-21): scales the owner
    // CharacterMovementComponent's MaxWalkSpeed by SprintMultiplier.
    UFUNCTION(BlueprintCallable, Category = "Movement|Sprint")
    void SetSprinting(bool bNewSprinting);

    // === Camera offset ===
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Camera")
    float CameraOffsetX;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Camera")
    float CameraOffsetY;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Camera")
    float CameraOffsetZ;

    // === Footsteps and Audio ===
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Audio")
    float FootstepInterval;

    // Auto-load default CC0 footstep assets from /Game/Audio/Footsteps when not explicitly set
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Audio")
    bool bAutoLoadDefaultFootsteps = true;

    // === Footstep Event (canonical body-fact, tb-0150) ===
    // Broadcast once per step (TickComponent's FootstepInterval hook) - the seed's
    // "OnFootstep lives on UChimeraMovementComponent directly" (CHIMERA_VISION.py:
    // 792-794). BlueprintAssignable so Blueprint listeners can bind alongside
    // USandSoundComponent's native C++ binding (BeginPlay, AddUniqueDynamic).
    UPROPERTY(BlueprintAssignable, Category = "Movement|Footstep")
    FOnFootstepEvent OnFootstep;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Dust")
    TObjectPtr<UDustAccumulationParticleComponent> DustAccumulationComponent;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Audio|FootstepSounds")
    TObjectPtr<USoundBase> SandFootstepSound;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Audio|FootstepSounds")
    TObjectPtr<USoundBase> MetalFootstepSound;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Audio|FootstepSounds")
    TObjectPtr<USoundBase> RockFootstepSound;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Audio|FootstepSounds")
    TObjectPtr<USoundBase> GroundFootstepSound;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Audio|FootstepSounds")
    TObjectPtr<USoundBase> WaterFootstepSound;

    // === Servo Sound Effects (Non-Diegetic Suit Actuators) ===
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Audio|ServoSounds")
    TObjectPtr<USoundBase> ServoSound;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Audio|ServoSounds")
    float ServoSoundMinVolume = 0.1f; // Quiet on walk

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Audio|ServoSounds")
    float ServoSoundMaxVolume = 0.6f; // Loud on sprint (non-diegetic, so kept subtle)

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Audio|ServoSounds")
    float ServoSoundSprintThreshold = 1.5f; // 1.5x walk speed triggers medium servo

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Audio|ServoSounds")
    bool bEnableServoSounds = true;

    // === Footprint Decals ===
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Decals")
    bool bEnableFootprints;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Decals")
    float FootprintSpawnInterval;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Decals")
    float FootprintSizeX;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Decals")
    float FootprintSizeY;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Decals")
    float FootprintSizeZ;

    // Level-assigned decal material for footprints (soft — assign in BP to make
    // prints visible; the size/enable/interval config is honored regardless).
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Decals")
    TSoftObjectPtr<UMaterialInterface> FootprintDecalMaterial;

    // Runtime throttle accumulator for footprint spawning (vs FootprintSpawnInterval).
    UPROPERTY(Transient)
    float FootprintSpawnTimer = 0.0f;

    // === Surface Detection ===
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|SurfaceDetection")
    float FootTraceDistance;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Movement|State")
    FVector CurrentVelocity;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Movement|State")
    ESurfaceMaterialType CurrentSurfaceMaterial;

    // === Weight Shift Animation ===
    // Current weight shift offset (in cm) applied to character mesh on state transitions
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Movement|WeightShift")
    FVector CurrentWeightShiftOffset;

    // Maximum overshoot magnitude (cm) on deceleration or direction change
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|WeightShift")
    float MaxWeightShiftMagnitude = 3.5f;

    // Overshoot coefficient (how much the weight shift exceeds target before settling)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|WeightShift")
    float WeightShiftOvershooting = 1.3f;

    // Damping factor for weight shift settling (higher = faster settling)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|WeightShift")
    float WeightShiftDamping = 8.0f;

    // Get the current weight shift offset (e.g., for animation blueprint to apply to mesh)
    UFUNCTION(BlueprintCallable, Category = "Movement|WeightShift")
    FVector GetWeightShiftOffset() const { return CurrentWeightShiftOffset; }

    void SetWalkSpeed(float NewSpeed);
    void GetCameraOffset(FVector& OutOffset) const;

    // Audio-visual sync telemetry (Sleepwalker playtest verification)
    UFUNCTION(BlueprintCallable, Category = "Movement|Audio|Telemetry")
    static int32 GetFootstepSyncEventCount();

    UFUNCTION(BlueprintCallable, Category = "Movement|Audio|Telemetry")
    static float GetAverageFootstepSyncLatencyMs();

    UFUNCTION(BlueprintCallable, Category = "Movement|Audio|Telemetry")
    static float GetMaxFootstepSyncLatencyMs();

    UFUNCTION(BlueprintCallable, Category = "Movement|Audio|Telemetry")
    static void ClearFootstepSyncTelemetry();

    // Last / max footstep audio volume (0..1), for audio-visual sync verification
    static float GetLastFootstepVolume();
    static float GetMaxFootstepVolume();

    // tb-0150: per-surface reaction traits (traction/makes_print/dust_kick), sourced
    // from docs/matter/matter_library.json's "pair_exceptions" (boot|sand, boot|basin,
    // boot|rock, boot|metal, boot|ice, boot|interior — see the .cpp implementation's
    // own doc comment for the full citation). Public + static so acceptance tests can
    // regression-proof the cited numbers directly.
    UFUNCTION(BlueprintCallable, Category = "Movement|SurfaceDetection")
    static void GetSurfaceFootstepTraits(ESurfaceMaterialType Surface, float& OutTraction, bool& OutMakesPrint, float& OutDustKick);

protected:
    float FootstepTimer;
    float FootprintTimer;

    // tb-0150: alternates true/false every broadcast step (seed's ev.bLeftFoot,
    // CHIMERA_VISION.py:744) — cadence state, not an independent per-foot detector.
    bool bNextFootstepIsLeft = true;

private:
    // Audio component for 3D spatialized footstep sounds
    UPROPERTY(VisibleAnywhere, Category = "Movement|Audio")
    TObjectPtr<UAudioComponent> FootstepAudioComponent;

    // Audio component for servo/pneumatic sounds (suit actuators)
    UPROPERTY(VisibleAnywhere, Category = "Movement|Audio")
    TObjectPtr<UAudioComponent> ServoAudioComponent;

    // Cache for auto-loaded default footstep sounds
    TMap<ESurfaceMaterialType, TObjectPtr<USoundBase>> DefaultFootstepCache;

    // === Weight Shift Animation Internals ===
    // Track previous velocity to detect acceleration/deceleration
    FVector LastFrameVelocity;

    // Sprint: cached pre-sprint MaxWalkSpeed (<0 = not yet captured)
    float BaseMaxWalkSpeed = -1.0f;

    // Weight shift velocity (for damped oscillator)
    FVector WeightShiftVelocity;

    // Target weight shift offset (changes on state transitions)
    FVector TargetWeightShiftOffset;

    // Timer for weight shift animation (used for overshoot curve)
    float WeightShiftAnimationTime;

public:
    // Calculate and update weight shift based on velocity changes
    void UpdateWeightShift(float DeltaTime);

    // Detect surface material via line trace from character's feet position
    ESurfaceMaterialType DetectSurfaceMaterial(const FVector& TraceStart);

    // Play contextual footstep sound based on surface type with spatialization
    void PlayFootstepSound(ESurfaceMaterialType SurfaceMaterial, const FVector& Location, float SpeedMagnitude);

    // Resolve a default footstep sound asset (CC0 Fantozzi pack) for a surface type
    USoundBase* GetDefaultFootstepSound(ESurfaceMaterialType SurfaceMaterial);

    // Play servo/pneumatic sound for suit actuators (speed-based volume layering)
    void PlayServoSound(float SpeedMagnitude, const FVector& Location);

    // Spawn footprint decal at the given location and rotation
    void SpawnFootprintDecal(const FVector& Location, const FRotator& Rotation, ESurfaceMaterialType SurfaceMaterial);
};
