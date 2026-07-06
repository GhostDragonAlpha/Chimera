#include "StationTradingData.h"

UStationTradingData::UStationTradingData()
{
	BuyPriceMultiplier = 0.9f; // Buy at 10% discount
	SellPriceMultiplier = 1.1f; // Sell at 10% markup
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
