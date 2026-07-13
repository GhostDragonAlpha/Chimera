// Copyright 2026 Chimera Project. All Rights Reserved.
// Economy Acceptance Tests — supply/demand pricing, commodity initialization, market dynamics.
// Proves the seed's UEconomyManager behaviour: BuildEconomy populates commodities,
// GetCommodityPrice returns supply/demand-derived values, and UpdateCommodityPrices
// shifts prices as supply/demand change. Headless (NewObject, no PIE).

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "../Economy/EconomyManager.h"
#include "../Economy/EconomyInitializer.h"
#include "../Economy/CommodityData.h"

#if WITH_DEV_AUTOMATION_TESTS

// ==================================================================
// BuildEconomy populates CommodityList and StationTradingList.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEconomy_BuildEconomy_PopulatesCommodities,
	"ChimeraTests.Acceptance.Economy.BuildEconomy_PopulatesCommodities",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FEconomy_BuildEconomy_PopulatesCommodities::RunTest(const FString& Parameters)
{
	UEconomyManager* Manager = NewObject<UEconomyManager>();
	TestNotNull(TEXT("Manager instantiated"), Manager);
	TestEqual(TEXT("CommodityList starts empty"), Manager->CommodityList.Num(), 0);
	TestEqual(TEXT("StationTradingList starts empty"), Manager->StationTradingList.Num(), 0);

	// BuildEconomy populates from DSL economy_systems block
	UEconomyInitializer::BuildEconomy(Manager);

	TestEqual(TEXT("4 commodities created"), Manager->CommodityList.Num(), 4);
	TestEqual(TEXT("3 stations created"), Manager->StationTradingList.Num(), 3);

	// Verify commodity names exist
	UCommodityData* Titanium = Manager->GetCommodityByName(TEXT("Titanium"));
	UCommodityData* IronOre = Manager->GetCommodityByName(TEXT("Iron_Ore"));
	UCommodityData* SyntheticFood = Manager->GetCommodityByName(TEXT("Synthetic_Food"));
	UCommodityData* QuantumCores = Manager->GetCommodityByName(TEXT("Quantum_Cores"));

	TestNotNull(TEXT("Titanium commodity exists"), Titanium);
	TestNotNull(TEXT("Iron_Ore commodity exists"), IronOre);
	TestNotNull(TEXT("Synthetic_Food commodity exists"), SyntheticFood);
	TestNotNull(TEXT("Quantum_Cores commodity exists"), QuantumCores);

	// Verify base prices are set per DSL spec
	if (Titanium)
	{
		TestEqual(TEXT("Titanium BasePrice = 62.5"), Titanium->BasePrice, 62.5f);
	}
	if (IronOre)
	{
		TestEqual(TEXT("Iron_Ore BasePrice = 30.0"), IronOre->BasePrice, 30.0f);
	}
	if (SyntheticFood)
	{
		TestEqual(TEXT("Synthetic_Food BasePrice = 15.0"), SyntheticFood->BasePrice, 15.0f);
	}
	if (QuantumCores)
	{
		TestEqual(TEXT("Quantum_Cores BasePrice = 5000.0"), QuantumCores->BasePrice, 5000.0f);
	}

	return true;
}

// ==================================================================
// GetCommodityPrice returns non-zero, supply/demand-derived price.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEconomy_GetCommodityPrice_ReturnsPositive,
	"ChimeraTests.Acceptance.Economy.GetCommodityPrice_ReturnsPositive",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FEconomy_GetCommodityPrice_ReturnsPositive::RunTest(const FString& Parameters)
{
	UEconomyManager* Manager = NewObject<UEconomyManager>();
	UEconomyInitializer::BuildEconomy(Manager);

	// GetCommodityPrice delegates to CalculateCurrentPrice on the commodity
	float TitaniumPrice = Manager->GetCommodityPrice(TEXT("Titanium"));
	float IronPrice = Manager->GetCommodityPrice(TEXT("Iron_Ore"));
	float FoodPrice = Manager->GetCommodityPrice(TEXT("Synthetic_Food"));
	float QuantumPrice = Manager->GetCommodityPrice(TEXT("Quantum_Cores"));

	TestTrue(TEXT("Titanium price > 0"), TitaniumPrice > 0.0f);
	TestTrue(TEXT("Iron price > 0"), IronPrice > 0.0f);
	TestTrue(TEXT("Food price > 0"), FoodPrice > 0.0f);
	TestTrue(TEXT("Quantum price > 0"), QuantumPrice > 0.0f);

	// At default supply/demand (1000/1000 = ratio 1.0), price multiplier
	// should be 1.0, so prices should equal base prices
	TestEqual(TEXT("Titanium at equilibrium ≈ 62.5"), TitaniumPrice, 62.5f, 0.1f);
	TestEqual(TEXT("Iron at equilibrium ≈ 30.0"), IronPrice, 30.0f, 0.1f);
	TestEqual(TEXT("Food at equilibrium ≈ 15.0"), FoodPrice, 15.0f, 0.1f);
	TestEqual(TEXT("Quantum at equilibrium ≈ 5000.0"), QuantumPrice, 5000.0f, 1.0f);

	return true;
}

// ==================================================================
// Price responds to supply changes — low supply raises price.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEconomy_Price_RespondsToSupplyChange,
	"ChimeraTests.Acceptance.Economy.Price_RespondsToSupplyChange",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FEconomy_Price_RespondsToSupplyChange::RunTest(const FString& Parameters)
{
	UEconomyManager* Manager = NewObject<UEconomyManager>();
	UEconomyInitializer::BuildEconomy(Manager);

	UCommodityData* Titanium = Manager->GetCommodityByName(TEXT("Titanium"));
	TestNotNull(TEXT("Titanium exists"), Titanium);

	float InitialPrice = Manager->GetCommodityPrice(TEXT("Titanium"));
	TestTrue(TEXT("Initial price > 0"), InitialPrice > 0.0f);

	// Reduce supply: demand/supply ratio rises -> price should rise
	Manager->AdjustCommoditySupply(TEXT("Titanium"), -500.0f);
	float PriceAfterSupplyReduction = Manager->GetCommodityPrice(TEXT("Titanium"));
	TestTrue(TEXT("Price rises when supply drops"), PriceAfterSupplyReduction > InitialPrice);

	// Increase supply beyond equilibrium: demand/supply ratio falls -> price should fall
	Manager->AdjustCommoditySupply(TEXT("Titanium"), 1000.0f);
	float PriceAfterSupplyIncrease = Manager->GetCommodityPrice(TEXT("Titanium"));
	TestTrue(TEXT("Price falls when supply rises"), PriceAfterSupplyIncrease < PriceAfterSupplyReduction);

	return true;
}

// ==================================================================
// Price responds to demand changes — high demand raises price.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEconomy_Price_RespondsToDemandChange,
	"ChimeraTests.Acceptance.Economy.Price_RespondsToDemandChange",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FEconomy_Price_RespondsToDemandChange::RunTest(const FString& Parameters)
{
	UEconomyManager* Manager = NewObject<UEconomyManager>();
	UEconomyInitializer::BuildEconomy(Manager);

	UCommodityData* IronOre = Manager->GetCommodityByName(TEXT("Iron_Ore"));
	TestNotNull(TEXT("Iron_Ore exists"), IronOre);

	float InitialPrice = Manager->GetCommodityPrice(TEXT("Iron_Ore"));
	TestTrue(TEXT("Initial price > 0"), InitialPrice > 0.0f);

	// Increase demand: demand/supply ratio rises -> price should rise
	Manager->AdjustCommodityDemand(TEXT("Iron_Ore"), 500.0f);
	float PriceAfterDemandIncrease = Manager->GetCommodityPrice(TEXT("Iron_Ore"));
	TestTrue(TEXT("Price rises when demand increases"), PriceAfterDemandIncrease > InitialPrice);

	// Decrease demand: demand/supply ratio falls -> price should fall
	Manager->AdjustCommodityDemand(TEXT("Iron_Ore"), -1000.0f);
	float PriceAfterDemandDecrease = Manager->GetCommodityPrice(TEXT("Iron_Ore"));
	TestTrue(TEXT("Price falls when demand decreases"), PriceAfterDemandDecrease < PriceAfterDemandIncrease);

	return true;
}

// ==================================================================
// UpdateCommodityPrices shifts supply/demand and triggers price events.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEconomy_UpdateCommodityPrices_ShiftsMarket,
	"ChimeraTests.Acceptance.Economy.UpdateCommodityPrices_ShiftsMarket",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FEconomy_UpdateCommodityPrices_ShiftsMarket::RunTest(const FString& Parameters)
{
	UEconomyManager* Manager = NewObject<UEconomyManager>();
	UEconomyInitializer::BuildEconomy(Manager);

	UCommodityData* Food = Manager->GetCommodityByName(TEXT("Synthetic_Food"));
	TestNotNull(TEXT("Synthetic_Food exists"), Food);

	float InitialSupply = Food->CurrentSupply;
	float InitialDemand = Food->CurrentDemand;

	// UpdateCommodityPrices applies small random fluctuations to supply/demand
	// over DeltaTime. After one call, supply/demand should have changed (small but measurable).
	Manager->UpdateCommodityPrices(1.0f);

	// Fluctuations are: ±0.5 * DeltaTime * value * 0.01
	// So for supply/demand = 1000, max change per second = 1000 * 0.5 * 1.0 * 0.01 = 5.0
	// We can't guarantee direction, but we CAN measure that the commodity WAS touched
	// (i.e., the algorithm ran). Verify supply/demand bounds are respected (>= 0).
	TestTrue(TEXT("Supply remains non-negative"), Food->CurrentSupply >= 0.0f);
	TestTrue(TEXT("Demand remains non-negative"), Food->CurrentDemand >= 0.0f);

	// Run update again with a longer delta to trigger a more obvious fluctuation.
	// With DeltaTime=5.0, fluctuation range is ±2.5 * value * 0.01 = ±25 for 1000 base.
	float SupplyBefore = Food->CurrentSupply;
	float DemandBefore = Food->CurrentDemand;
	Manager->UpdateCommodityPrices(5.0f);

	// Check that price changed (at least once the random fluctuation hit a 0.1 diff threshold)
	// or that supply/demand was visibly modified. We can't guarantee a price-change event
	// (random fluctuation might miss the 0.1 threshold), but UpdateCommodityPrices SHOULD
	// have been called and should have modified supply/demand.
	TestTrue(TEXT("Supply/demand touched by update"),
		(Food->CurrentSupply != SupplyBefore) || (Food->CurrentDemand != DemandBefore));

	return true;
}

// ==================================================================
// GetCommodityByName returns nullptr for nonexistent commodities.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEconomy_GetCommodityByName_HandlesNotFound,
	"ChimeraTests.Acceptance.Economy.GetCommodityByName_HandlesNotFound",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FEconomy_GetCommodityByName_HandlesNotFound::RunTest(const FString& Parameters)
{
	UEconomyManager* Manager = NewObject<UEconomyManager>();
	UEconomyInitializer::BuildEconomy(Manager);

	UCommodityData* NotFound = Manager->GetCommodityByName(TEXT("NonexistentCommodity"));
	TestNull(TEXT("Nonexistent commodity returns nullptr"), NotFound);

	float PriceNotFound = Manager->GetCommodityPrice(TEXT("NonexistentCommodity"));
	TestEqual(TEXT("Price for nonexistent commodity = 0.0"), PriceNotFound, 0.0f);

	return true;
}

// ==================================================================
// AdjustCommoditySupply clamps to zero (no negative supply).
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEconomy_AdjustCommoditySupply_ClampsToZero,
	"ChimeraTests.Acceptance.Economy.AdjustCommoditySupply_ClampsToZero",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FEconomy_AdjustCommoditySupply_ClampsToZero::RunTest(const FString& Parameters)
{
	UEconomyManager* Manager = NewObject<UEconomyManager>();
	UEconomyInitializer::BuildEconomy(Manager);

	UCommodityData* Food = Manager->GetCommodityByName(TEXT("Synthetic_Food"));
	TestNotNull(TEXT("Synthetic_Food exists"), Food);

	// Try to reduce supply below zero; should clamp to 0
	Manager->AdjustCommoditySupply(TEXT("Synthetic_Food"), -2000.0f);
	TestEqual(TEXT("Supply clamped to 0"), Food->CurrentSupply, 0.0f);

	// Price should respond to zero supply (max multiplier = 4.0x)
	float PriceAtZeroSupply = Manager->GetCommodityPrice(TEXT("Synthetic_Food"));
	TestTrue(TEXT("Price at zero supply is multiplied up"), PriceAtZeroSupply > 15.0f);

	return true;
}

// ==================================================================
// CommodityData CalculateCurrentPrice uses supply/demand ratio correctly.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEconomy_CalculateCurrentPrice_UsesRatio,
	"ChimeraTests.Acceptance.Economy.CalculateCurrentPrice_UsesRatio",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FEconomy_CalculateCurrentPrice_UsesRatio::RunTest(const FString& Parameters)
{
	UCommodityData* Commodity = NewObject<UCommodityData>();
	Commodity->CommodityName = TEXT("TestCommodity");
	Commodity->BasePrice = 100.0f;
	Commodity->CurrentSupply = 1000.0f;
	Commodity->CurrentDemand = 1000.0f;
	Commodity->SupplyMultiplier = 0.5f;
	Commodity->DemandMultiplier = 0.5f;

	// At equilibrium (ratio = 1.0), price multiplier = 1.0^elasticity = 1.0
	float EquilibriumPrice = Commodity->CalculateCurrentPrice();
	TestEqual(TEXT("Equilibrium price = base price"), EquilibriumPrice, 100.0f, 0.1f);

	// Double demand: ratio = 2.0, elasticity = 1.0, multiplier = 2.0^1.0 = 2.0
	Commodity->CurrentDemand = 2000.0f;
	float HighDemandPrice = Commodity->CalculateCurrentPrice();
	TestTrue(TEXT("Price doubles with 2x demand"), HighDemandPrice >= 199.0f && HighDemandPrice <= 201.0f);

	// Halve supply: ratio = 2.0 / 0.5 = 4.0, multiplier = 4.0^1.0 = 4.0 (clamped to 4.0)
	Commodity->CurrentDemand = 1000.0f;
	Commodity->CurrentSupply = 500.0f;
	float LowSupplyPrice = Commodity->CalculateCurrentPrice();
	TestTrue(TEXT("Price at 2x demand/supply ratio ≈ 200"), LowSupplyPrice >= 195.0f && LowSupplyPrice <= 205.0f);

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
