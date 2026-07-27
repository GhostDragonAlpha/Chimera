#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "CommodityData.generated.h"

UCLASS(Blueprintable, BlueprintType)
class CHIMERA_API UCommodityData : public UDataAsset
{
	GENERATED_BODY()

public:
	UCommodityData();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity")
	FString CommodityName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity")
	FString Description;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|Pricing")
	float BasePrice;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|SupplyDemand")
	float CurrentSupply;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|SupplyDemand")
	float CurrentDemand;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|SupplyDemand")
	float SupplyMultiplier; // elasticity weight, 0.0 to 1.0

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|SupplyDemand")
	float DemandMultiplier; // elasticity weight, 0.0 to 1.0

	UFUNCTION(BlueprintCallable, Category = "Commodity|Pricing")
	float CalculateCurrentPrice() const;
};
