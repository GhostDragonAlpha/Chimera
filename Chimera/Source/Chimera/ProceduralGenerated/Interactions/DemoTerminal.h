// Copyright 2026 Chimera Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Actor.h"
#include "../Economy/EconomyManager.h"
#include "../Economy/EconomyInitializer.h"
#include "../Inventory/InventoryTradeComponent.h"
#include "../Factions/FactionComponent.h"
#include "../Save/SaveGameComponent.h"
#include "../Missions/MissionComponent.h"
#include "DemoTerminal.generated.h"

UCLASS()
class CHIMERA_API ADemoTerminal : public AActor
{
	GENERATED_BODY()

public:
	ADemoTerminal();

protected:
	virtual void BeginPlay() override;

public:
	virtual void Tick(float DeltaTime) override;

	UPROPERTY(VisibleAnywhere, Category="Demo|Visual")
	UStaticMeshComponent* TerminalMesh;

	UPROPERTY(BlueprintReadOnly, Category="Demo|Systems")
	UEconomyManager* EconomySystem;

	UPROPERTY(BlueprintReadOnly, Category="Demo|Systems")
	UInventoryTradeComponent* TradeSystem;

	UPROPERTY(BlueprintReadOnly, Category="Demo|Systems")
	UFactionComponent* FactionSystem;

	UPROPERTY(BlueprintReadOnly, Category="Demo|Systems")
	USaveGameComponent* SaveSystem;

	UPROPERTY(BlueprintReadOnly, Category="Demo|Systems")
	UMissionComponent* MissionSystem;

public:
	// Exec wrappers for agent verification via `ke <ActorName> <Func>`
	UFUNCTION(Exec)
	void DemoStatus();

	UFUNCTION(Exec)
	void DemoBuy(int32 Quantity);

	UFUNCTION(Exec)
	void DemoSell(int32 Quantity);

	UFUNCTION(Exec)
	void DemoSave();

	UFUNCTION(Exec)
	void DemoLoad();

	UFUNCTION(Exec)
	void DemoMission();

private:
	float GetCommodityPrice(FName CommodityName) const;

	UFUNCTION()
	void OnPriceChanged(FString CommodityName, float NewPrice);
};
