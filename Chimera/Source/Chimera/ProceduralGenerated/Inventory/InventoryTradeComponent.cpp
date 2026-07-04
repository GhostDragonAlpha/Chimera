// Copyright 2026 Chimera Project. All Rights Reserved.

#include "InventoryTradeComponent.h"

// Sets default values
UInventoryTradeComponent::UInventoryTradeComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = true;

	// Initialize with some default trade items for demonstration
	PlayerTradeItems.Add(FTradeItem(TEXT("Lunar Sample"), 5));
	PlayerTradeItems.Add(FTradeItem(TEXT("Ration Pack"), 10));
	
	NPCTradeItems.Add(FTradeItem(TEXT("Advanced Battery"), 3));
	NPCTradeItems.Add(FTradeItem(TEXT("Oxygen Filter"), 2));
}


// Called when the game starts
void UInventoryTradeComponent::BeginPlay()
{
	Super::BeginPlay();

	// ...
}


// Called every frame
void UInventoryTradeComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// ...
}

/** Get player's tradeable items */
TArray<FTradeItem> UInventoryTradeComponent::GetPlayerTradeItems() const
{
	return PlayerTradeItems;
}

/** Get NPC's tradeable items */
TArray<FTradeItem> UInventoryTradeComponent::GetNPCTradeItems() const
{
	return NPCTradeItems;
}

/** Execute trade exchange between player and NPC */
bool UInventoryTradeComponent::ExecuteTradeExchange(const TArray<FTradeItem>& PlayerOffers, const TArray<FTradeItem>& NPCOffers)
{
	// In a full implementation, this would:
	// 1. Validate that the player has the items they're offering
	// 2. Validate that the NPC has the items it's offering
	// 3. Remove offered items from respective inventories
	// 4. Add received items to respective inventories
	
	UE_LOG(LogTemp, Log, TEXT("Executing trade exchange: Player offers %d items, NPC offers %d items"), 
	       PlayerOffers.Num(), NPCOffers.Num());

	// For demonstration, we'll simulate a successful trade
	if (PlayerOffers.Num() > 0 && NPCOffers.Num() > 0)
	{
		UE_LOG(LogTemp, Log, TEXT("Trade exchange completed successfully"));
		
		// In a real implementation, we would update the actual inventories here
		// For now, we'll just log the trade details
		for (const FTradeItem& Item : PlayerOffers)
		{
			UE_LOG(LogTemp, Log, TEXT("Player offered: %s (Qty: %d)"), *Item.ItemName, Item.Quantity);
		}
		
		for (const FTradeItem& Item : NPCOffers)
		{
			UE_LOG(LogTemp, Log, TEXT("NPC offered: %s (Qty: %d)"), *Item.ItemName, Item.Quantity);
		}
		
		return true;
	}

	UE_LOG(LogTemp, Warning, TEXT("Trade exchange failed: No items to trade"));
	return false;
}