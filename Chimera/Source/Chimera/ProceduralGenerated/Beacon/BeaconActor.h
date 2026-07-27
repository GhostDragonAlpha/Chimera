// BeaconActor — an actor with PointLight + BeaconPulseComponent
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BeaconActor.generated.h"

class UPointLightComponent;
class UBeaconPulseComponent;

UCLASS()
class CHIMERA_API ABeaconActor : public AActor
{
    GENERATED_BODY()

public:
    ABeaconActor();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Beacon")
    UPointLightComponent* BeaconLight;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Beacon")
    UBeaconPulseComponent* PulseComponent;
};
