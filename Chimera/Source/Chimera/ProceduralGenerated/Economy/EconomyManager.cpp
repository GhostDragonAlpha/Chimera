#include "EconomyManager.h"

UEconomyManager::UEconomyManager()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UEconomyManager::BeginPlay()
{
	Super::BeginPlay();

	for (UStationTradingData* StationData : StationTradingList)
	{
		CalculateStationTradePrices(StationData);
	}
}

void UEconomyManager::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	UpdateCommodityPrices(DeltaTime);
}

void UEconomyManager::UpdateCommodityPrices(float DeltaTime)
{
	for (UCommodityData* Commodity : CommodityList)
	{
		if (!Commodity) continue;

		float OldPrice = Commodity->CalculateCurrentPrice();

		// Simulate natural supply/demand fluctuations over time
		// Small random variations to simulate market dynamics
		float SupplyFluctuation = FMath::RandRange(-0.5f, 0.5f) * DeltaTime;
		float DemandFluctuation = FMath::RandRange(-0.5f, 0.5f) * DeltaTime;

		Commodity->CurrentSupply += SupplyFluctuation * Commodity->CurrentSupply * 0.01f;
		Commodity->CurrentDemand += DemandFluctuation * Commodity->CurrentDemand * 0.01f;

		float NewPrice = Commodity->CalculateCurrentPrice();

		if (FMath::Abs(NewPrice - OldPrice) > 0.1f)
		{
			OnCommodityPriceChanged.Broadcast(Commodity->CommodityName, NewPrice);
		}
	}
}

float UEconomyManager::GetCommodityPrice(FString CommodityName) const
{
	UCommodityData* Commodity = GetCommodityByName(CommodityName);
	if (Commodity)
	{
		return Commodity->CalculateCurrentPrice();
	}
	return 0.0f;
}

UCommodityData* UEconomyManager::GetCommodityByName(FString CommodityName) const
{
	for (UCommodityData* Commodity : CommodityList)
	{
		if (Commodity && Commodity->CommodityName == CommodityName)
		{
			return Commodity;
		}
	}
	return nullptr;
}

void UEconomyManager::AdjustCommoditySupply(FString CommodityName, float SupplyChange)
{
	UCommodityData* Commodity = GetCommodityByName(CommodityName);
	if (Commodity)
	{
		Commodity->CurrentSupply += SupplyChange;
		Commodity->CurrentSupply = FMath::Max(Commodity->CurrentSupply, 0.0f);
	}
}

void UEconomyManager::AdjustCommodityDemand(FString CommodityName, float DemandChange)
{
	UCommodityData* Commodity = GetCommodityByName(CommodityName);
	if (Commodity)
	{
		Commodity->CurrentDemand += DemandChange;
		Commodity->CurrentDemand = FMath::Max(Commodity->CurrentDemand, 0.0f);
	}
}

void UEconomyManager::CalculateStationTradePrices(UStationTradingData* StationData)
{
	if (!StationData) return;

	// Station prices are computed on demand via GetBuy/SellPriceForCommodity, which
	// multiply these directly — sanitize once at startup so a bad data asset can
	// never produce zero or negative trade prices.
	StationData->BuyPriceMultiplier = FMath::Clamp(StationData->BuyPriceMultiplier, 0.1f, 10.0f);
	StationData->SellPriceMultiplier = FMath::Clamp(StationData->SellPriceMultiplier, 0.1f, 10.0f);
}
