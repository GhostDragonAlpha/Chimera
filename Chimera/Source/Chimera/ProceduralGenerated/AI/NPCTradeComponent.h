// Copyright 2026 Chimera Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "NPCTradeComponent.generated.h"

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class CHIMERA_API UNPCTradeComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UNPCTradeComponent();

protected:
	virtual void BeginPlay() override;

public:
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Trigger trade interaction with player */
	UFUNCTION(BlueprintCallable, Category="NPC|Trade")
	void StartTradeInteraction();

	/** End trade interaction */
	UFUNCTION(BlueprintCallable, Category="NPC|Trade")
	void EndTradeInteraction();

	/** Check if player is within trade range */
	UFUNCTION(BlueprintCallable, Category="NPC|Trade")
	bool IsPlayerWithinRange() const;

	/** Get the NPC actor this component is attached to */
	UFUNCTION(BlueprintCallable, Category="NPC|Trade")
	AActor* GetOwnerActor() const;

	/** Get distance to player */
	UFUNCTION(BlueprintCallable, Category="NPC|Trade")
	float GetDistanceToPlayer() const;

private:
	/** Range within which player can initiate trade (default 500 units) */
	UPROPERTY(EditAnywhere, Category="NPC|Trade")
	float TradeRange = 500.0f;

	/** Flag indicating if trade interaction is currently active */
	UPROPERTY(VisibleAnywhere, Category="NPC|Trade")
	bool bIsTradingActive = false;

	/** Reference to the player actor for trade interactions */
	UPROPERTY(VisibleAnywhere, Category="NPC|Trade")
	AActor* PlayerActor = nullptr;

	/** Helper to find and cache the player actor */
	void FindPlayerActor();
};