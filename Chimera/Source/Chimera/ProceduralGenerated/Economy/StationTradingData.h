#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "StationTradingData.generated.h"

UENUM(BlueprintType)
enum class EStationTier : uint8
{
	Outpost     UMETA(DisplayName="Outpost"),      // Remote, high risk, wide swings
	Settlement  UMETA(DisplayName="Settlement"),   // Developing, moderate swings
	Hub         UMETA(DisplayName="Hub"),           // High traffic, stable prices
	Capital     UMETA(DisplayName="Capital"),       // Core world, tight bounds
};

/**
 * Price bound configuration for a station tier.
 * Higher tiers = tighter bounds = less profit potential but safer trade.
 */
USTRUCT(BlueprintType)
struct FStationPriceBounds
{
	GENERATED_BODY()

	/** Minimum price multiplier (fraction of commodity base price). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float MinMultiplier;

	/** Maximum price multiplier (fraction of commodity base price). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float MaxMultiplier;

	/** Multiplier for buying from the player (player sells at this × market price). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float BuyMultiplier;

	/** Multiplier for selling to the player (player buys at this × market price). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float SellMultiplier;

	FStationPriceBounds()
		: MinMultiplier(0.20f), MaxMultiplier(5.0f),
		  BuyMultiplier(0.80f), SellMultiplier(1.30f)
	{}
};

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

	/** Security/development tier — determines price swing bounds and spread. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Station|Tier")
	EStationTier StationTier;

	/**
	 * Price bounds for this station. Overridden automatically on construction
	 * based on StationTier; can be hand-tuned per-station in the editor.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Station|Trading|Bounds")
	FStationPriceBounds Bounds;

	/**
	 * Convenience: commodity-level price bounds used by GetBuyPriceForCommodity
	 * to clamp extreme market prices. Set from Bounds on construction.
	 * Can also be set per-commodity for fine-grained control.
	 *
	 * Clamping logic: the station's market price is constrained to
	 * [commodity.BasePrice * Bounds.MinMultiplier,
	 *  commodity.BasePrice * Bounds.MaxMultiplier]
	 * before applying BuyMultiplier/SellMultiplier.
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Station|Trading|Bounds")
	float HardMinPrice;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Station|Trading|Bounds")
	float HardMaxPrice;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Station|Inventory")
	TArray<FString> AvailableCommodities;

	UFUNCTION(BlueprintCallable, Category = "Station|Trading")
	float GetBuyPriceForCommodity(FString CommodityName, float CommodityBasePrice, float MarketPrice) const;

	UFUNCTION(BlueprintCallable, Category = "Station|Trading")
	float GetSellPriceForCommodity(FString CommodityName, float CommodityBasePrice, float MarketPrice) const;

	/** Recalculate HardMinPrice/HardMaxPrice from Bounds and CommodityBasePrice. */
	UFUNCTION(BlueprintCallable, Category = "Station|Trading|Bounds")
	void UpdateHardBounds(float CommodityBasePrice);
};
