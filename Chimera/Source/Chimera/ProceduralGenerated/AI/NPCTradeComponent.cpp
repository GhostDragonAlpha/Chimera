// Copyright 2026 Chimera Project. All Rights Reserved.

#include "NPCTradeComponent.h"

UNPCTradeComponent::UNPCTradeComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickInterval = 0.5f;  // Check player range twice per second
}

void UNPCTradeComponent::BeginPlay()
{
	Super::BeginPlay();

	// Find the player actor in the world
	FindPlayerActor();

	if (PlayerActor)
	{
		UE_LOG(LogTemp, Log, TEXT("[NPCTrade] Player found for trade component on %s"), *GetOwner()->GetName());
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("[NPCTrade] Player not found at component initialization for %s"), *GetOwner()->GetName());
	}
}

void UNPCTradeComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// Periodically refresh player reference in case actor changed
	if (!PlayerActor)
	{
		FindPlayerActor();
	}

	// Update trade state based on proximity
	if (PlayerActor && IsPlayerWithinRange())
	{
		if (!bIsTradingActive)
		{
			// Witness marker: sleepwalker log_contains expects key on this exact string.
			UE_LOG(LogTemp, Log, TEXT("[NPCTrade] Player within trade range of %s (distance: %.1f)"),
				*GetOwner()->GetName(), GetDistanceToPlayer());
		}
	}
}

void UNPCTradeComponent::FindPlayerActor()
{
	APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (PC)
	{
		PlayerActor = PC->GetPawn();
	}
	else
	{
		PlayerActor = nullptr;
	}
}

void UNPCTradeComponent::StartTradeInteraction()
{
	if (!bIsTradingActive && IsPlayerWithinRange())
	{
		bIsTradingActive = true;
		// Witness marker: sleepwalker log_contains expects key on this exact string.
		UE_LOG(LogTemp, Log, TEXT("[NPCTrade] Trade interaction started on %s with player: %s"),
		       *GetOwner()->GetName(), *GetNameSafe(PlayerActor));
	}
	else if (!IsPlayerWithinRange())
	{
		UE_LOG(LogTemp, Warning, TEXT("[NPCTrade] Cannot start trade: player out of range (distance: %.1f)"), GetDistanceToPlayer());
	}
}

void UNPCTradeComponent::EndTradeInteraction()
{
	if (bIsTradingActive)
	{
		bIsTradingActive = false;
		UE_LOG(LogTemp, Log, TEXT("[NPCTrade] Trade interaction ended on %s"), *GetOwner()->GetName());
	}
}

bool UNPCTradeComponent::IsPlayerWithinRange() const
{
	AActor* Owner = GetOwner();
	if (!Owner || !PlayerActor) return false;

	float Distance = FVector::Dist(Owner->GetActorLocation(), PlayerActor->GetActorLocation());
	return Distance <= TradeRange;
}

float UNPCTradeComponent::GetDistanceToPlayer() const
{
	AActor* Owner = GetOwner();
	if (!Owner || !PlayerActor) return -1.0f;

	return FVector::Dist(Owner->GetActorLocation(), PlayerActor->GetActorLocation());
}

AActor* UNPCTradeComponent::GetOwnerActor() const
{
	return GetOwner();
}