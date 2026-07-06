#include "EconomyManager.h"

// Equilibrium levels: supply and demand naturally pull toward these values.
// A commodity at equilibrium has price = BasePrice × (1001/1001)^1 = BasePrice.
static constexpr float EQUILIBRIUM_SUPPLY = 1000.0f;
static constexpr float EQUILIBRIUM_DEMAND = 1000.0f;

UEconomyManager::UEconomyManager()
{
	PrimaryComponentTick.bCanEverTick = true;
	MeanReversionStrength = 0.002f;
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

		// --- Mean-reverting supply/demand fluctuation ---
		//
		// Pure random walks let prices drift arbitrarily (professor grade F).
		// Instead we combine:
		//   1. Small random noise (market noise)
		//   2. Mean reversion toward equilibrium (restoring force)
		//
		// Net effect: prices jitter realistically but stay near equilibrium.
		// At 60fps: ±0.05% noise × 60 ≈ ±3%/s maximum drift,
		// reversion pulls back ~0.2% of deviation per tick (~12%/s at max deviation).

		// 1. Random walk component (greatly reduced from ±0.5% → ±0.05%)
		float SupplyFluctuation = FMath::RandRange(-0.05f, 0.05f) * DeltaTime;
		float DemandFluctuation = FMath::RandRange(-0.05f, 0.05f) * DeltaTime;

		// 2. Mean reversion: pull supply/demand toward equilibrium
		float SupplyDeviation = Commodity->CurrentSupply - EQUILIBRIUM_SUPPLY;
		float DemandDeviation = Commodity->CurrentDemand - EQUILIBRIUM_DEMAND;

		float Reversion = MeanReversionStrength * DeltaTime * 60.0f;
		float ReversionPullSupply = SupplyDeviation * Reversion;
		float ReversionPullDemand = DemandDeviation * Reversion;

		// Apply: noise pushes away, reversion pulls back
		Commodity->CurrentSupply += SupplyFluctuation * Commodity->CurrentSupply * 0.01f
									- ReversionPullSupply;
		Commodity->CurrentDemand += DemandFluctuation * Commodity->CurrentDemand * 0.01f
									- ReversionPullDemand;

		// Clamp so supply/demand never go negative
		Commodity->CurrentSupply = FMath::Max(Commodity->CurrentSupply, 10.0f);
		Commodity->CurrentDemand = FMath::Max(Commodity->CurrentDemand, 10.0f);

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
		Commodity->CurrentSupply = FMath::Max(Commodity->CurrentSupply, 10.0f);
	}
}

void UEconomyManager::AdjustCommodityDemand(FString CommodityName, float DemandChange)
{
	UCommodityData* Commodity = GetCommodityByName(CommodityName);
	if (Commodity)
	{
		Commodity->CurrentDemand += DemandChange;
		Commodity->CurrentDemand = FMath::Max(Commodity->CurrentDemand, 10.0f);
	}
}

void UEconomyManager::CalculateStationTradePrices(UStationTradingData* StationData)
{
	if (!StationData) return;

	// Sanitize station multipliers — a bad data asset must never produce zero/negative prices
	StationData->Bounds.BuyMultiplier = FMath::Clamp(StationData->Bounds.BuyMultiplier, 0.1f, 10.0f);
	StationData->Bounds.SellMultiplier = FMath::Clamp(StationData->Bounds.SellMultiplier, 0.1f, 10.0f);

	// Update hard price bounds based on the most expensive commodity this station deals in,
	// so the station's price ceiling covers all its inventory.
	float MaxBasePrice = 100.0f; // default fallback
	for (const FString& CommodityName : StationData->AvailableCommodities)
	{
		UCommodityData* Commodity = GetCommodityByName(CommodityName);
		if (Commodity && Commodity->BasePrice > MaxBasePrice)
		{
			MaxBasePrice = Commodity->BasePrice;
		}
	}
	StationData->UpdateHardBounds(MaxBasePrice);
}
