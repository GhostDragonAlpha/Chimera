// Copyright Chimera. All rights reserved.

#pragma warning(disable: 5038)
#pragma warning(disable: 4996)
#include "WeightShiftApplierComponent.h"
#include "ChimeraMovementComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"

UWeightShiftApplierComponent::UWeightShiftApplierComponent()
	: WeightShiftStrength(1.0f)
	, OriginalMeshLocation(FVector::ZeroVector)
	, AppliedOffset(FVector::ZeroVector)
	, bEnableWeightShift(true)
	, MovementComponent(nullptr)
{
	PrimaryComponentTick.TickInterval = 0.0f;
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PostPhysics;
}

void UWeightShiftApplierComponent::BeginPlay()
{
	Super::BeginPlay();

	// Find or auto-set the skeletal mesh component
	if (!TargetMesh && GetOwner())
	{
		TargetMesh = GetOwner()->FindComponentByClass<USkeletalMeshComponent>();
		if (TargetMesh)
		{
			OriginalMeshLocation = TargetMesh->GetRelativeLocation();
			UE_LOG(LogTemp, Warning, TEXT("[WeightShiftApplier] Found mesh, original location: %.1f, %.1f, %.1f"),
				OriginalMeshLocation.X, OriginalMeshLocation.Y, OriginalMeshLocation.Z);
		}
	}
	else if (TargetMesh)
	{
		OriginalMeshLocation = TargetMesh->GetRelativeLocation();
	}

	FindMovementComponent();
}

void UWeightShiftApplierComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!bEnableWeightShift || !TargetMesh || !MovementComponent)
	{
		return;
	}

	ApplyWeightShiftToMesh();
}

void UWeightShiftApplierComponent::FindMovementComponent()
{
	if (!GetOwner())
	{
		return;
	}

	MovementComponent = GetOwner()->FindComponentByClass<UChimeraMovementComponent>();
	if (MovementComponent)
	{
		UE_LOG(LogTemp, Warning, TEXT("[WeightShiftApplier] Found ChimeraMovementComponent"));
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("[WeightShiftApplier] ChimeraMovementComponent not found on owner"));
	}
}

void UWeightShiftApplierComponent::ApplyWeightShiftToMesh()
{
	if (!MovementComponent || !TargetMesh)
	{
		return;
	}

	// Get the current weight shift offset from the movement component
	FVector WeightShiftOffset = MovementComponent->GetWeightShiftOffset();

	// Apply strength multiplier
	FVector AdjustedOffset = WeightShiftOffset * WeightShiftStrength;

	// Apply to mesh relative location (add to original location)
	FVector NewMeshLocation = OriginalMeshLocation + AdjustedOffset;

	// Update mesh position
	TargetMesh->SetRelativeLocation(NewMeshLocation);

	// Track applied offset for debugging/measurement
	AppliedOffset = AdjustedOffset;
}
