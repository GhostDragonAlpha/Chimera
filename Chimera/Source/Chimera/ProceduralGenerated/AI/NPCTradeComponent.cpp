// Copyright 2026 Chimera Project. All Rights Reserved.

#include "NPCTradeComponent.h"

// Sets default values
UNPCTradeComponent::UNPCTradeComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = true;

	// ...
}


// Called when the game starts
void UNPCTradeComponent::BeginPlay()
{
	Super::BeginPlay();

	// ...
	
}


// Called every frame
void UNPCTradeComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// ...
}

/** Trigger trade interaction with player */
void UNPCTradeComponent::StartTradeInteraction()
{
	if (!bIsTradingActive && IsPlayerWithinRange())
	{
		bIsTradingActive = true;
		
		// In a full implementation, this would open the trade UI
		UE_LOG(LogTemp, Log, TEXT("NPC Trade Interaction Started with player: %s"), 
		       PlayerActor ? *PlayerActor->GetName() : TEXT("Unknown"));
	}
}

/** Check if player is within trade range */
bool UNPCTradeComponent::IsPlayerWithinRange() const
{
	AActor* Owner = GetOwner();
	if (!Owner) return false;

	// In a full implementation, this would check for the player actor and calculate distance
	// For now, we'll assume the player is within range if we have a reference to them
	return PlayerActor != nullptr;
}

/** Get the NPC actor this component is attached to */
AActor* UNPCTradeComponent::GetOwnerActor() const
{
	return GetOwner();
}