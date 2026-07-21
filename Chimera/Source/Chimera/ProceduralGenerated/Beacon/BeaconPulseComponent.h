// BeaconPulseComponent — header
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "BeaconPulseComponent.generated.h"

class UPointLightComponent;

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class CHIMERA_API UBeaconPulseComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UBeaconPulseComponent();

    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    // Set the help count (0-3+). Pulse rate and color respond.
    UFUNCTION(BlueprintCallable, Category="Beacon")
    void SetHelpCount(int32 Count);

private:
    UPROPERTY()
    UPointLightComponent* LightComp;

    float PulseRate0Helps;
    float PulseRate3Helps;
    FLinearColor CurrentColor0;
    FLinearColor CurrentColor3;
    float BaseIntensity;
    int32 HelpCount;
    float ElapsedTime;
};
