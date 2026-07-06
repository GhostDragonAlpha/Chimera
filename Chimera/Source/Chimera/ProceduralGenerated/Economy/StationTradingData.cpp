#include "StationTradingData.h"

static FStationPriceBounds PriceBoundsForTier(EStationTier Tier)
{
	FStationPriceBounds B;
	switch (Tier)
	{
	case EStationTier::Outpost:
		// Remote station: wild price swings, poor spread — high risk, high reward
		B.MinMultiplier = 0.20f;
		B.MaxMultiplier = 5.0f;
		B.BuyMultiplier  = 0.75f;  // Station buys low from player
		B.SellMultiplier = 1.35f; // Station sells high to player
		break;
	case EStationTier::Settlement:
		// Developing: moderate swings, improving spread
		B.MinMultiplier = 0.25f;
		B.MaxMultiplier = 4.0f;
		B.BuyMultiplier  = 0.85f;
		B.SellMultiplier = 1.20f;
		break;
	case EStationTier::Hub:
		// High-traffic: stable prices, tight spread — safe but lower margin
		B.MinMultiplier = 0.33f;
		B.MaxMultiplier = 3.0f;
		B.BuyMultiplier  = 0.90f;
		B.SellMultiplier = 1.10f;
		break;
	case EStationTier::Capital:
		// Core world: very stable, near-perfect market — minimal arbitrage
		B.MinMultiplier = 0.50f;
		B.MaxMultiplier = 2.0f;
		B.BuyMultiplier  = 0.95f;
		B.SellMultiplier = 1.05f;
		break;
	}
	return B;
}

UStationTradingData::UStationTradingData()
{
	StationTier = EStationTier::Outpost;
	Bounds = PriceBoundsForTier(StationTier);
	UpdateHardBounds(100.0f); // Default commodity base price
}

float UStationTradingData::GetBuyPriceForCommodity(FString CommodityName, float CommodityBasePrice, float MarketPrice) const
{
	// Station buys FROM the player — applies buy multiplier to bounded market price
	float BoundedMarket = FMath::Clamp(MarketPrice,
		CommodityBasePrice * Bounds.MinMultiplier,
		CommodityBasePrice * Bounds.MaxMultiplier);
	return BoundedMarket * Bounds.BuyMultiplier;
}

float UStationTradingData::GetSellPriceForCommodity(FString CommodityName, float CommodityBasePrice, float MarketPrice) const
{
	// Station sells TO the player — applies sell multiplier to bounded market price
	float BoundedMarket = FMath::Clamp(MarketPrice,
		CommodityBasePrice * Bounds.MinMultiplier,
		CommodityBasePrice * Bounds.MaxMultiplier);
	return BoundedMarket * Bounds.SellMultiplier;
}

void UStationTradingData::UpdateHardBounds(float CommodityBasePrice)
{
	HardMinPrice = CommodityBasePrice * Bounds.MinMultiplier;
	HardMaxPrice = CommodityBasePrice * Bounds.MaxMultiplier;
}
