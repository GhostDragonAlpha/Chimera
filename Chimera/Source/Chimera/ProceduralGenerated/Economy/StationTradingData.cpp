#include "StationTradingData.h"

UStationTradingData::UStationTradingData()
{
	BuyPriceMultiplier = 0.9f; // Buy at 10% discount
	SellPriceMultiplier = 1.1f; // Sell at 10% markup
	// Default tradable stock (previously a dead UPROPERTY — declared, never
	// populated; subsystem/Economy red atom). DSL station data overrides.
	AvailableCommodities = { TEXT("Ore"), TEXT("Water"), TEXT("Fuel") };
}

float UStationTradingData::GetBuyPriceForCommodity(FString CommodityName, float BasePrice) const
{
	// DSL absolute price wins; multiplier over base is the fallback
	if (const float* Price = BuyPrices.Find(FName(*CommodityName)))
	{
		return *Price;
	}
	return BasePrice * BuyPriceMultiplier;
}

float UStationTradingData::GetSellPriceForCommodity(FString CommodityName, float BasePrice) const
{
	if (const float* Price = SellPrices.Find(FName(*CommodityName)))
	{
		return *Price;
	}
	return BasePrice * SellPriceMultiplier;
}
