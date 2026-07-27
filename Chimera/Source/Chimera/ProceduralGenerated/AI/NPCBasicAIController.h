#pragma once

#include "CoreMinimal.h"
#include "AIController.h"
#include "Perception/AIPerceptionComponent.h"
#include "Perception/AISenseConfig_Sight.h"
#include "BehaviorTree/BehaviorTreeComponent.h"
#include "BehaviorTree/BlackboardComponent.h"
#include "NPCBasicAIController.generated.h"

/**
 * Basic AI Controller for NPC characters with idle, patrol, engage, flee states.
 */
UCLASS()
class CHIMERA_API ANPCBasicAIController : public AAIController
{
	GENERATED_BODY()

public:
	ANPCBasicAIController();

protected:
	virtual void BeginPlay() override;

private:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "AI Components", meta=(AllowPrivateAccess=true))
	UAIPerceptionComponent* PerceptionComp;

	UPROPERTY(EditDefaultsOnly, Category = "AI | Behavior")
	UBehaviorTree* DefaultBehaviorTree;

	UPROPERTY(EditDefaultsOnly, Category = "AI | Perception")
	UAISenseConfig_Sight* SightConfig;
	
	void InitializeComponents();

	UFUNCTION()
	void OnPerceptionUpdated(const TArray<AActor*>& UpdatedActors);
};
