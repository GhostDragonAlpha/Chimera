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

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnCommodityPurchased, FName, Commodity, int32, Quantity, float, TotalCost);

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

	// --- Commodity trading (credits + cargo) ---

	UPROPERTY(BlueprintAssignable, Category="Inventory|Trade")
	FOnCommodityPurchased OnCommodityPurchased;

	UFUNCTION(BlueprintCallable, Category="Inventory|Trade")
	float GetCredits() const;

	UFUNCTION(BlueprintCallable, Category="Inventory|Trade")
	void SetCredits(float NewCredits);

	UFUNCTION(BlueprintCallable, Category="Inventory|Trade")
	void AddCredits(float Amount);

	UFUNCTION(BlueprintCallable, Category="Inventory|Trade")
	int32 GetCargoQuantity(FName Commodity) const;

	/** Full cargo snapshot for save/load. */
	UFUNCTION(BlueprintCallable, Category="Inventory|Trade")
	TMap<FName, int32> GetCargo() const;

	/** Replace the cargo hold wholesale (load-game restore). */
	UFUNCTION(BlueprintCallable, Category="Inventory|Trade")
	void SetCargo(const TMap<FName, int32>& NewCargo);

	/**
	 * Buy Quantity units of Commodity at UnitPrice each.
	 * Deducts credits and adds to cargo atomically.
	 * Fails (returns false, no state change) if Quantity <= 0, UnitPrice < 0,
	 * or credits are insufficient.
	 */
	UFUNCTION(BlueprintCallable, Category="Inventory|Trade")
	bool BuyCommodity(FName Commodity, int32 Quantity, float UnitPrice);

	/**
	 * Sell Quantity units of Commodity at UnitPrice each.
	 * Removes cargo and adds credits atomically.
	 * Fails if cargo holds fewer than Quantity units.
	 */
	UFUNCTION(BlueprintCallable, Category="Inventory|Trade")
	bool SellCommodity(FName Commodity, int32 Quantity, float UnitPrice);

private:
	/** Player's tradeable inventory items */
	UPROPERTY(VisibleAnywhere, Category="Inventory|Trade")
	TArray<FTradeItem> PlayerTradeItems;

	/** NPC's tradeable inventory items */
	UPROPERTY(VisibleAnywhere, Category="Inventory|Trade")
	TArray<FTradeItem> NPCTradeItems;

	/** Player wallet, in credits. */
	UPROPERTY(VisibleAnywhere, Category="Inventory|Trade")
	float Credits;

	/** Commodity cargo hold: commodity name -> units. */
	UPROPERTY(VisibleAnywhere, Category="Inventory|Trade")
	TMap<FName, int32> Cargo;
};
