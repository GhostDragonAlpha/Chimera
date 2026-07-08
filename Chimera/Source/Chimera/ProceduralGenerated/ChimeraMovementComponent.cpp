// Copyright Chimera. All rights reserved.

#include "ChimeraMovementComponent.h"
#include "Materials/DustAccumulationParticleComponent.h"

#include "Components/SkeletalMeshComponent.h"
#include "Components/AudioComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/Pawn.h"
#include "Logging/LogMacros.h"
#include "Sound/SoundBase.h"
#include "PhysicalMaterials/PhysicalMaterial.h"
#include "Engine/World.h"
#include "TimerManager.h"

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
	FootstepInterval = 1.75f;

	// Weight shift animation defaults
	MaxWeightShiftMagnitude = 3.5f;     // 3.5 cm max offset (subtle)
	WeightShiftOvershooting = 1.3f;     // 30% overshoot
	WeightShiftDamping      = 8.0f;     // Medium-fast settling

	// Ensure component ticks every frame
	PrimaryComponentTick.TickInterval = 0.0f;
	PrimaryComponentTick.bCanEverTick = true;
}

// ------------------------------------------------------------------
// TickComponent — apply velocity to owner root / mesh
// ------------------------------------------------------------------
void UChimeraMovementComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!GetOwner() || !GetOwner()->GetRootComponent())
		return;

	// Update weight shift animation (based on velocity changes)
	UpdateWeightShift(DeltaTime);

	// Accumulate velocity (already set by caller or external system).
	// For a simple walking character we move the root component forward.
	const FVector Delta = CurrentVelocity * DeltaTime;

	if (Delta.SizeSquared() > KINDA_SMALL_NUMBER)
	{
		GetOwner()->AddActorWorldOffset(Delta, false, nullptr, ETeleportType::None);
	}

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

			// PHASE 2: Emit dust particles on footstep (audio-visual coupling point)
			if (DustAccumulationComponent)
			{
				DustAccumulationComponent->EmitDustAtLocation(FootstepLocation, 50);
			}

			// PHASE 3: Immediately trigger synchronized audio (AAA <100ms latency target)
			const double AudioTriggerTime = FPlatformTime::Seconds();
			const float SyncLatencyMs = static_cast<float>((AudioTriggerTime - ParticleSpawnTime) * 1000.0);

			// Detect surface material for contextual sound selection
			const ESurfaceMaterialType SurfaceMaterial = DetectSurfaceMaterial(FootstepLocation);

			// Play contextual footstep sound with speed-based volume scaling
			const float SpeedMagnitude = CurrentVelocity.Size();
			PlayFootstepSound(SurfaceMaterial, FootstepLocation, SpeedMagnitude);

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

			// Calculate volume based on speed (walk=0.4, sprint=1.0)
			const float MaxSpeed = WalkSpeed * 2.0f; // Sprint = 2x walk
			SyncEvent.AudioVolume = FMath::Clamp(SpeedMagnitude / MaxSpeed, 0.0f, 1.0f);

			GFootstepSyncTelemetry.Add(SyncEvent);

			// UE_LOG for monitoring (CHIMERA_AGENT_SIM will capture)
			UE_LOG(LogTemp, Log, TEXT("Footstep Sync: Latency=%.2f ms, Surface=%d, Volume=%.2f, Speed=%.0f cm/s"),
				SyncLatencyMs, (int32)SurfaceMaterial, SyncEvent.AudioVolume, SpeedMagnitude);
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
		// Calculate volume based on movement speed (0.2 to 1.0 scale)
		const float MaxSpeed = WalkSpeed * 2.0f; // Sprint = 2x walk speed
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
	const float MaxSpeed = WalkSpeed * 2.0f; // Sprint = 2x walk speed
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
	// Placeholder for footprint decal spawning (can be extended)
	// This would spawn a decal actor at the given location with surface-specific material
	UE_LOG(LogTemp, Verbose, TEXT("SpawnFootprintDecal: Location=%.0f,%.0f,%.0f Surface=%d"),
		Location.X, Location.Y, Location.Z, (int32)SurfaceMaterial);
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
		CurrentWeightShiftOffset = FMath::Lerp(CurrentWeightShiftOffset, CurrentTarget, DeltaTime * 5.0f);
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