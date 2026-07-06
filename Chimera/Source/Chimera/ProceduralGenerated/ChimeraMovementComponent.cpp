// Copyright Chimera. All rights reserved.

#include "ChimeraMovementComponent.h"

#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/Pawn.h"
#include "Logging/LogMacros.h"

#define LOG_MOVE() UE_LOG(LogTemp, Log, TEXT("[UChimeraMovementComponent] %s"), *GetFullName())

// ------------------------------------------------------------------
// Constructor — default values
// ------------------------------------------------------------------
UChimeraMovementComponent::UChimeraMovementComponent()
{
	WalkSpeed        = 200.0f;   // ~2 m/s (UE uses cm)
	CameraOffsetX    = 170.0f;
	CameraOffsetY    = 0.0f;
	CameraOffsetZ    = 80.0f;
	FootstepInterval = 1.75f;
}

// ------------------------------------------------------------------
// TickComponent — apply velocity to owner root / mesh
// ------------------------------------------------------------------
void UChimeraMovementComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!GetOwner() || !GetOwner()->GetRootComponent())
		return;

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
		LOG_MOVE(); // Placeholder: would call PlaySound2D or SpawnEmitter here
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