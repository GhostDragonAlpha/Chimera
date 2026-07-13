// Copyright Chimera. All rights reserved.

#include "EnsureWeightShiftOnPossess.h"
#include "../WeightShiftApplierComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/Character.h"
#include "GameFramework/Controller.h"
#include "Logging/LogMacros.h"

UEnsureWeightShiftOnPossess::UEnsureWeightShiftOnPossess()
	: OwnerPawn(nullptr)
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UEnsureWeightShiftOnPossess::BeginPlay()
{
	Super::BeginPlay();

	// This component lives on the controller, so we need to find the possessed pawn
	if (AController* OwnerController = Cast<AController>(GetOwner()))
	{
		if (APawn* PossessedPawn = OwnerController->GetPawn())
		{
			OwnerPawn = PossessedPawn;
			EnsureWeightShiftApplier(PossessedPawn);
		}
	}
}

void UEnsureWeightShiftOnPossess::EnsureWeightShiftApplier(APawn* InPawn)
{
	if (!InPawn || InPawn->FindComponentByClass<UWeightShiftApplierComponent>())
	{
		return;
	}

	// H-34: Runtime attachment guarantee. The WeightShiftApplierComponent is defined
	// but never instantiated, leaving weight shift calculations invisible (not applied
	// to mesh). Create and register it unconditionally-if-missing.
	UWeightShiftApplierComponent* WeightShiftApplier =
		NewObject<UWeightShiftApplierComponent>(InPawn, TEXT("WeightShiftApplierComponent"));
	if (WeightShiftApplier)
	{
		WeightShiftApplier->RegisterComponent();
		UE_LOG(LogTemp, Display,
			TEXT("EnsureWeightShiftOnPossess: UWeightShiftApplierComponent runtime-attached to %s (H-34)"),
			*InPawn->GetName());
	}
}
