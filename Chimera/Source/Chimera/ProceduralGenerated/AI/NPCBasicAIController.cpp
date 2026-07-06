#include "NPCBasicAIController.h"
#include "BehaviorTree/BehaviorTree.h"

ANPCBasicAIController::ANPCBasicAIController()
{
	PrimaryActorTick.bCanEverTick = false;

	PerceptionComp = CreateDefaultSubobject<UAIPerceptionComponent>(TEXT("PerceptionComp"));

	SightConfig = CreateDefaultSubobject<UAISenseConfig_Sight>(TEXT("SightConfig"));
	if (SightConfig)
	{
		SightConfig->SightRadius = 1000.0f;
		SightConfig->LoseSightRadius = 1200.0f;
		SightConfig->PeripheralVisionAngleDegrees = 90.0f;
		SightConfig->DetectionByAffiliation.bDetectEnemies = true;
		SightConfig->DetectionByAffiliation.bDetectNeutrals = false;
		SightConfig->DetectionByAffiliation.bDetectFriendlies = false;
	}

	if (PerceptionComp && SightConfig)
	{
		PerceptionComp->ConfigureSense(*SightConfig);
		PerceptionComp->SetDominantSense(SightConfig->GetSenseImplementation());
		PerceptionComp->OnPerceptionUpdated.AddDynamic(this, &ANPCBasicAIController::OnPerceptionUpdated);
	}
}

void ANPCBasicAIController::BeginPlay()
{
	Super::BeginPlay();

	InitializeComponents();
}

void ANPCBasicAIController::InitializeComponents()
{
	if (DefaultBehaviorTree)
	{
		RunBehaviorTree(DefaultBehaviorTree);
	}

	if (PerceptionComp)
	{
		PerceptionComp->Activate();
	}
}

void ANPCBasicAIController::OnPerceptionUpdated(const TArray<AActor*>& UpdatedActors)
{
	for (AActor* Actor : UpdatedActors)
	{
		// Handle perception updates for engage/flee states based on Blackboard values and Behavior Tree decisions
	}
}
