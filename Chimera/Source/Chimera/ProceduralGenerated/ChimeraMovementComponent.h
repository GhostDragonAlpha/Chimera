// Copyright Chimera. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ChimeraMovementComponent.generated.h"

class UPhysicalMaterial;
class USoundBase;
class ADecalActor;
class UDustAccumulationParticleComponent; // Forward declare from ProceduralGenerated/Materials/

UENUM(BlueprintType)
enum class ESurfaceMaterialType : uint8
{
	Sand UMETA(DisplayName = "Sand"),
	Metal UMETA(DisplayName = "Metal"),
	Rock UMETA(DisplayName = "Rock"),
	Ground UMETA(DisplayName = "Ground/Dirt"),
	Water UMETA(DisplayName = "Water"),
	Custom UMETA(DisplayName = "Custom/Unknown")
};

UCLASS(meta = (Blueprintable, Category = "Movement|Walking"))
class CHIMERA_API UChimeraMovementComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UChimeraMovementComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	// === Speed ===
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Walking")
	float WalkSpeed;

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

protected:
	float FootstepTimer;
	float FootprintTimer;

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
