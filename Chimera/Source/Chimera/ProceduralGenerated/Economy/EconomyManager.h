#pragma once

#include "CoreMinimal.h"
#include "Engine/World.h"
#include "CommodityData.h"
#include "StationTradingData.h"
#include "EconomyManager.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnCommodityPriceChanged, FString, CommodityName, float, NewPrice);

UCLASS(Blueprintable, BlueprintType)
class CHIMERA_API UEconomyManager : public UActorComponent
{
	GENERATED_BODY()

public:
	UEconomyManager();

protected:
	virtual void BeginPlay() override;

public:
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Economy|Commodities")
	TArray<UCommodityData*> CommodityList;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Economy|Stations")
	TArray<UStationTradingData*> StationTradingList;

	/** Strength of the mean-reverting force that pulls prices toward equilibrium.
	 *  0.0 = pure random walk (unstable, professor grade F).
	 *  0.001 = gentle reversion (prices drift but don't run away).
	 *  0.01 = strong reversion (prices tightly hug equilibrium). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Economy|Stability")
	float MeanReversionStrength;

	UPROPERTY(BlueprintAssignable, Category = "Economy|Events")
	FOnCommodityPriceChanged OnCommodityPriceChanged;

	UFUNCTION(BlueprintCallable, Category = "Economy|Management")
	void UpdateCommodityPrices(float DeltaTime);

	UFUNCTION(BlueprintCallable, Category = "Economy|Management")
	float GetCommodityPrice(FString CommodityName) const;

	UFUNCTION(BlueprintCallable, Category = "Economy|Management")
	UCommodityData* GetCommodityByName(FString CommodityName) const;

	UFUNCTION(BlueprintCallable, Category = "Economy|SupplyDemand")
	void AdjustCommoditySupply(FString CommodityName, float SupplyChange);

	UFUNCTION(BlueprintCallable, Category = "Economy|SupplyDemand")
	void AdjustCommodityDemand(FString CommodityName, float DemandChange);

private:
	void CalculateStationTradePrices(UStationTradingData* StationData);
};
