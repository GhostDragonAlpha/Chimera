// Copyright Chimera. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EnsureWeightShiftOnPossess.generated.h"

class UWeightShiftApplierComponent;
class UChimeraMovementComponent;

/**
 * Weight Shift Applier Guarantor
 *
 * Runtime attachment guarantor for UWeightShiftApplierComponent (H-34 pattern).
 * The Weight Shift Applier is defined but never instantiated in DemoPlayerController,
 * leaving weight shift animations invisible in-game. This component ensures it exists
 * at possess time, fixing the missing mesh animation.
 *
 * Attach this to the pawn's controller, or call EnsureWeightShiftApplier(InPawn)
 * from DemoPlayerController::OnPossess().
 */
UCLASS(ClassGroup=(Movement), meta=(BlueprintSpawnableComponent))
class CHIMERA_API UEnsureWeightShiftOnPossess : public UActorComponent
{
	GENERATED_BODY()

public:
	UEnsureWeightShiftOnPossess();

	virtual void BeginPlay() override;

	/**
	 * Ensure the pawn has a WeightShiftApplierComponent (creates one if missing).
	 * This mirrors the pattern of DemoPlayerController::EnsureChimeraMovement().
	 *
	 * Call from OnPossess(InPawn):
	 *   EnsureWeightShiftApplier(InPawn);
	 */
	UFUNCTION(BlueprintCallable, Category = "Movement|WeightShift")
	static void EnsureWeightShiftApplier(APawn* InPawn);

private:
	// The owner pawn (set at BeginPlay)
	UPROPERTY()
	TObjectPtr<APawn> OwnerPawn;
};
