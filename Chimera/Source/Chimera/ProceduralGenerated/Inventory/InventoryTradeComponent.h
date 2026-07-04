// Copyright 2026 Chimera Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "InventoryTradeComponent.generated.h"

USTRUCT(BlueprintType)
struct FTradeItem
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString ItemName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	int32 Quantity = 1;

	FTradeItem() {}
	FTradeItem(const FString& Name, int32 Qty) : ItemName(Name), Quantity(Qty) {}
};

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class CHIMERA_API UInventoryTradeComponent : public UActorComponent
{
	GENERATED_BODY()

public:	
	// Sets default values for this component's properties
	UInventoryTradeComponent();

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

public:	
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Get player's tradeable items */
	UFUNCTION(BlueprintCallable, Category="Inventory|Trade")
	TArray<FTradeItem> GetPlayerTradeItems() const;

	/** Get NPC's tradeable items */
	UFUNCTION(BlueprintCallable, Category="Inventory|Trade")
	TArray<FTradeItem> GetNPCTradeItems() const;

	/** Execute trade exchange between player and NPC */
	UFUNCTION(BlueprintCallable, Category="Inventory|Trade")
	bool ExecuteTradeExchange(const TArray<FTradeItem>& PlayerOffers, const TArray<FTradeItem>& NPCOffers);

private:
	/** Player's tradeable inventory items */
	UPROPERTY(VisibleAnywhere, Category="Inventory|Trade")
	TArray<FTradeItem> PlayerTradeItems;

	/** NPC's tradeable inventory items */
	UPROPERTY(VisibleAnywhere, Category="Inventory|Trade")
	TArray<FTradeItem> NPCTradeItems;
};