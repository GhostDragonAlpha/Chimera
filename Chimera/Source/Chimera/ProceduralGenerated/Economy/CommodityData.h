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
	float SupplyMultiplier; // 0.0 to 1.0, affects price based on supply

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|SupplyDemand")
	float DemandMultiplier; // 0.0 to 1.0, affects price based on demand

	UFUNCTION(BlueprintCallable, Category = "Commodity|Pricing")
	float CalculateCurrentPrice() const;
};
