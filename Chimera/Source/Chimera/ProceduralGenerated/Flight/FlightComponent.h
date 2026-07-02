#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "FlightComponent.generated.h"
UCLASS(meta = (BlueprintType, Category = "Flight"))
class CHIMERA_API UFlightComponent : public UActorComponent
{
	GENERATED_BODY()
public:
	UFlightComponent(const FObjectInitializer& ObjectInitializer);
	void InitializeFromShip(float, float, float, float);
};
