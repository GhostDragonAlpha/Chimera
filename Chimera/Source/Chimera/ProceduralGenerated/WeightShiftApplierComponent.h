// Copyright Chimera. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "WeightShiftApplierComponent.generated.h"

class UChimeraMovementComponent;
class USkeletalMeshComponent;

/**
 * Weight Shift Applier Component
 * Applies the calculated weight shift offset from ChimeraMovementComponent
 * to the character's skeletal mesh root bone position.
 *
 * This creates the visual effect of the character leaning back on deceleration
 * and settling forward, giving natural inertial animation.
 */
UCLASS(ClassGroup=(Movement), meta=(BlueprintSpawnableComponent))
class CHIMERA_API UWeightShiftApplierComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UWeightShiftApplierComponent();

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	// Strength multiplier for weight shift application (1.0 = full, <1.0 = reduced)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WeightShift|Apply")
	float WeightShiftStrength = 1.0f;

	// Skeletal mesh component to apply offset to (auto-found if not set)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WeightShift|Apply")
	TObjectPtr<USkeletalMeshComponent> TargetMesh;

	// Store original mesh relative location for reset
	UPROPERTY(VisibleAnywhere, Category = "WeightShift|State")
	FVector OriginalMeshLocation;

	// Current applied offset
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WeightShift|State")
	FVector AppliedOffset;

	// Enable/disable weight shift application
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WeightShift|Apply")
	bool bEnableWeightShift = true;

private:
	// Reference to the movement component
	UPROPERTY()
	TObjectPtr<UChimeraMovementComponent> MovementComponent;

	// Find the ChimeraMovementComponent on the owner
	void FindMovementComponent();

	// Apply weight shift offset to mesh
	void ApplyWeightShiftToMesh();
};
