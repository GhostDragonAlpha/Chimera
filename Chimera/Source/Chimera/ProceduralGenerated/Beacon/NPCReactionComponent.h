// NPCReactionComponent — NPCs turn toward the player when approached.
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "NPCReactionComponent.generated.h"

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class CHIMERA_API UNPCReactionComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UNPCReactionComponent();

    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    UPROPERTY(EditAnywhere, Category="NPC Reaction")
    float DetectionRadius;

    UPROPERTY(EditAnywhere, Category="NPC Reaction")
    float RotationSpeed;
};
