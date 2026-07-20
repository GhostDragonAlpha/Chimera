// Copyright 2026 Chimera Project. All Rights Reserved.

#pragma warning(disable: 5038)
#pragma warning(disable: 4996)
#include "InventoryTradeComponent.h"

// Sets default values
UInventoryTradeComponent::UInventoryTradeComponent()
	: Credits(0.0f)
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
	// Validation: ensure both parties have items to offer
	if (PlayerOffers.Num() == 0 || NPCOffers.Num() == 0)
	{
		UE_LOG(LogTemp, Warning, TEXT("ExecuteTradeExchange rejected: empty offers (Player=%d, NPC=%d)"),
		       PlayerOffers.Num(), NPCOffers.Num());
		return false;
	}

	// Step 1: Validate player has all offered items
	for (const FTradeItem& PlayerItem : PlayerOffers)
	{
		if (PlayerItem.ItemName.IsEmpty() || PlayerItem.Quantity <= 0)
		{
			UE_LOG(LogTemp, Warning, TEXT("ExecuteTradeExchange rejected: invalid player offer (%s, Qty=%d)"),
			       *PlayerItem.ItemName, PlayerItem.Quantity);
			return false;
		}

		int32 PlayerHas = 0;
		for (const FTradeItem& Held : PlayerTradeItems)
		{
			if (Held.ItemName == PlayerItem.ItemName)
			{
				PlayerHas = Held.Quantity;
				break;
			}
		}

		if (PlayerHas < PlayerItem.Quantity)
		{
			UE_LOG(LogTemp, Warning, TEXT("ExecuteTradeExchange rejected: player has only %d %s, offered %d"),
			       PlayerHas, *PlayerItem.ItemName, PlayerItem.Quantity);
			return false;
		}
	}

	// Step 2: Validate NPC has all offered items
	for (const FTradeItem& NPCItem : NPCOffers)
	{
		if (NPCItem.ItemName.IsEmpty() || NPCItem.Quantity <= 0)
		{
			UE_LOG(LogTemp, Warning, TEXT("ExecuteTradeExchange rejected: invalid NPC offer (%s, Qty=%d)"),
			       *NPCItem.ItemName, NPCItem.Quantity);
			return false;
		}

		int32 NPCHas = 0;
		for (const FTradeItem& Held : NPCTradeItems)
		{
			if (Held.ItemName == NPCItem.ItemName)
			{
				NPCHas = Held.Quantity;
				break;
			}
		}

		if (NPCHas < NPCItem.Quantity)
		{
			UE_LOG(LogTemp, Warning, TEXT("ExecuteTradeExchange rejected: NPC has only %d %s, offered %d"),
			       NPCHas, *NPCItem.ItemName, NPCItem.Quantity);
			return false;
		}
	}

	// Step 3: Remove offered items from inventories (player trades away)
	for (const FTradeItem& PlayerItem : PlayerOffers)
	{
		for (FTradeItem& Held : PlayerTradeItems)
		{
			if (Held.ItemName == PlayerItem.ItemName)
			{
				Held.Quantity -= PlayerItem.Quantity;
				if (Held.Quantity == 0)
				{
					PlayerTradeItems.RemoveAll([&](const FTradeItem& Item) { return Item.ItemName == PlayerItem.ItemName; });
				}
				break;
			}
		}
	}

	// Remove offered items from NPC inventory
	for (const FTradeItem& NPCItem : NPCOffers)
	{
		for (FTradeItem& Held : NPCTradeItems)
		{
			if (Held.ItemName == NPCItem.ItemName)
			{
				Held.Quantity -= NPCItem.Quantity;
				if (Held.Quantity == 0)
				{
					NPCTradeItems.RemoveAll([&](const FTradeItem& Item) { return Item.ItemName == NPCItem.ItemName; });
				}
				break;
			}
		}
	}

	// Step 4: Add received items to inventories (player receives NPC items, NPC receives player items)
	for (const FTradeItem& ReceivedFromNPC : NPCOffers)
	{
		bool bFound = false;
		for (FTradeItem& Held : PlayerTradeItems)
		{
			if (Held.ItemName == ReceivedFromNPC.ItemName)
			{
				Held.Quantity += ReceivedFromNPC.Quantity;
				bFound = true;
				break;
			}
		}
		if (!bFound)
		{
			PlayerTradeItems.Add(FTradeItem(ReceivedFromNPC.ItemName, ReceivedFromNPC.Quantity));
		}
	}

	// Add player-offered items to NPC inventory
	for (const FTradeItem& ReceivedByNPC : PlayerOffers)
	{
		bool bFound = false;
		for (FTradeItem& Held : NPCTradeItems)
		{
			if (Held.ItemName == ReceivedByNPC.ItemName)
			{
				Held.Quantity += ReceivedByNPC.Quantity;
				bFound = true;
				break;
			}
		}
		if (!bFound)
		{
			NPCTradeItems.Add(FTradeItem(ReceivedByNPC.ItemName, ReceivedByNPC.Quantity));
		}
	}

	// Log successful trade
	UE_LOG(LogTemp, Log, TEXT("ExecuteTradeExchange completed: Player traded %d item types for %d item types"),
	       PlayerOffers.Num(), NPCOffers.Num());
	for (const FTradeItem& Item : PlayerOffers)
	{
		UE_LOG(LogTemp, Log, TEXT("  Player offered: %s x%d"), *Item.ItemName, Item.Quantity);
	}
	for (const FTradeItem& Item : NPCOffers)
	{
		UE_LOG(LogTemp, Log, TEXT("  Player received: %s x%d"), *Item.ItemName, Item.Quantity);
	}

	return true;
}

float UInventoryTradeComponent::GetCredits() const
{
	return Credits;
}

void UInventoryTradeComponent::SetCredits(float NewCredits)
{
	Credits = FMath::Max(NewCredits, 0.0f);
}

void UInventoryTradeComponent::AddCredits(float Amount)
{
	Credits = FMath::Max(Credits + Amount, 0.0f);
}

int32 UInventoryTradeComponent::GetCargoQuantity(FName Commodity) const
{
	const int32* Found = Cargo.Find(Commodity);
	return Found ? *Found : 0;
}

TMap<FName, int32> UInventoryTradeComponent::GetCargo() const
{
	return Cargo;
}

void UInventoryTradeComponent::SetCargo(const TMap<FName, int32>& NewCargo)
{
	Cargo = NewCargo;
}

bool UInventoryTradeComponent::BuyCommodity(FName Commodity, int32 Quantity, float UnitPrice)
{
	if (Commodity == NAME_None || Quantity <= 0 || UnitPrice < 0.0f)
	{
		UE_LOG(LogTemp, Warning, TEXT("BuyCommodity rejected: invalid arguments (%s x%d @ %.2f)"),
			*Commodity.ToString(), Quantity, UnitPrice);
		return false;
	}

	const float TotalCost = UnitPrice * static_cast<float>(Quantity);
	if (Credits < TotalCost)
	{
		UE_LOG(LogTemp, Warning, TEXT("BuyCommodity rejected: %.2f credits < %.2f cost"), Credits, TotalCost);
		return false;
	}

	Credits -= TotalCost;
	Cargo.FindOrAdd(Commodity) += Quantity;

	UE_LOG(LogTemp, Log, TEXT("Bought %d x %s for %.2f credits (remaining: %.2f, cargo: %d)"),
		Quantity, *Commodity.ToString(), TotalCost, Credits, Cargo[Commodity]);

	OnCommodityPurchased.Broadcast(Commodity, Quantity, TotalCost);
	return true;
}

bool UInventoryTradeComponent::SellCommodity(FName Commodity, int32 Quantity, float UnitPrice)
{
	if (Commodity == NAME_None || Quantity <= 0 || UnitPrice < 0.0f)
	{
		return false;
	}

	int32* Held = Cargo.Find(Commodity);
	if (!Held || *Held < Quantity)
	{
		UE_LOG(LogTemp, Warning, TEXT("SellCommodity rejected: cargo holds %d x %s, tried to sell %d"),
			Held ? *Held : 0, *Commodity.ToString(), Quantity);
		return false;
	}

	*Held -= Quantity;
	if (*Held == 0)
	{
		Cargo.Remove(Commodity);
	}
	Credits += UnitPrice * static_cast<float>(Quantity);

	UE_LOG(LogTemp, Log, TEXT("Sold %d x %s for %.2f credits (balance: %.2f)"),
		Quantity, *Commodity.ToString(), UnitPrice * Quantity, Credits);
	return true;
}