// BeaconActor — an actor with PointLight + BeaconPulseComponent
#include "BeaconActor.h"
#include "Components/PointLightComponent.h"
#include "BeaconPulseComponent.h"

ABeaconActor::ABeaconActor()
{
    PrimaryActorTick.bCanEverTick = false;
    BeaconLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("BeaconLight"));
    BeaconLight->SetIntensity(50000.0f);
    BeaconLight->SetLightColor(FLinearColor(1.0f, 0.08f, 0.03f));
    BeaconLight->SetAttenuationRadius(8000.0f);
    BeaconLight->SetCastShadows(true);
    RootComponent = BeaconLight;
    PulseComponent = CreateDefaultSubobject<UBeaconPulseComponent>(TEXT("PulseComponent"));
}
