#include "CommodityData.h"

UCommodityData::UCommodityData()
{
	BasePrice = 100.0f;
	CurrentSupply = 1000.0f;
	CurrentDemand = 1000.0f;
	SupplyMultiplier = 0.5f;
	DemandMultiplier = 0.5f;
}

float UCommodityData::CalculateCurrentPrice() const
{
	// Price follows the demand/supply ratio: ratio > 1 (scarcity) raises price,
	// ratio < 1 (glut) lowers it. SupplyMultiplier + DemandMultiplier act as the
	// market's elasticity: at the defaults (0.5 + 0.5 = 1.0) price scales linearly
	// with D/S; higher values make prices more sensitive to imbalance.
	float epsilon = 1.0f; // Prevent division by zero
	float ratio = (CurrentDemand + epsilon) / (CurrentSupply + epsilon);
	float elasticity = FMath::Clamp(SupplyMultiplier + DemandMultiplier, 0.1f, 2.0f);
	float priceMultiplier = FMath::Pow(ratio, elasticity);

	// Clamp so a trade route can swing at most 4x either way
	priceMultiplier = FMath::Clamp(priceMultiplier, 0.25f, 4.0f);

	return BasePrice * priceMultiplier;
}
