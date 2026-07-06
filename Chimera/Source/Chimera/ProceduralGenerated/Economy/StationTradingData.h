#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "StationTradingData.generated.h"

UCLASS(Blueprintable, BlueprintType)
class CHIMERA_API UStationTradingData : public UDataAsset
{
	GENERATED_BODY()

public:
	UStationTradingData();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Station")
	FString StationName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Station|Location")
	FVector Location;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Station|Trading")
	float BuyPriceMultiplier; // Multiplier for buying prices from station (e.g., 0.9 for 10% discount)

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Station|Trading")
	float SellPriceMultiplier; // Multiplier for selling prices to station (e.g., 1.1 for 10% markup)

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Station|Inventory")
	TArray<FString> AvailableCommodities;

	UFUNCTION(BlueprintCallable, Category = "Station|Trading")
	float GetBuyPriceForCommodity(FString CommodityName, float BasePrice) const;

	UFUNCTION(BlueprintCallable, Category = "Station|Trading")
	float GetSellPriceForCommodity(FString CommodityName, float BasePrice) const;
};
