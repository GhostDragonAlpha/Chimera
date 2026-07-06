#include "StationTradingData.h"

UStationTradingData::UStationTradingData()
{
	BuyPriceMultiplier = 0.9f; // Buy at 10% discount
	SellPriceMultiplier = 1.1f; // Sell at 10% markup
}

float UStationTradingData::GetBuyPriceForCommodity(FString CommodityName, float BasePrice) const
{
	return BasePrice * BuyPriceMultiplier;
}

float UStationTradingData::GetSellPriceForCommodity(FString CommodityName, float BasePrice) const
{
	return BasePrice * SellPriceMultiplier;
}
