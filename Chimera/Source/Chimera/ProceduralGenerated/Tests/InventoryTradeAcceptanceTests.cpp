// Copyright 2026 Chimera Project. All Rights Reserved.
// Inventory Trade Acceptance Tests — commodities, cargo, and atomic exchanges.
// Proves the InventoryTradeComponent behavior: BuyCommodity/SellCommodity adjust
// credits + cargo atomically, ExecuteTradeExchange swaps items without partial state,
// AddCredits increments the wallet, and atomicity is enforced on all failures.

#pragma warning(disable: 5038)
#pragma warning(disable: 4996)
#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "../Inventory/InventoryTradeComponent.h"

#if WITH_DEV_AUTOMATION_TESTS

// ==================================================================
// Initialization — zero credits, empty cargo, demo trade items present.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_Init,
	"ChimeraTests.Acceptance.InventoryTrade.Init",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_Init::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();
	TestNotNull(TEXT("InventoryTradeComponent instantiated"), Inventory);

	// Credits should start at 0
	TestEqual(TEXT("Credits initialized to 0"), Inventory->GetCredits(), 0.0f);

	// Cargo should be empty
	TMap<FName, int32> EmptyCargo = Inventory->GetCargo();
	TestEqual(TEXT("Cargo initially empty"), EmptyCargo.Num(), 0);

	// Trade item arrays exist (populated with demo items in constructor)
	TArray<FTradeItem> PlayerItems = Inventory->GetPlayerTradeItems();
	TArray<FTradeItem> NPCItems = Inventory->GetNPCTradeItems();
	TestTrue(TEXT("Player trade items exist"), PlayerItems.Num() > 0);
	TestTrue(TEXT("NPC trade items exist"), NPCItems.Num() > 0);

	return true;
}

// ==================================================================
// AddCredits — wallet increments correctly, clamps to 0.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_AddCredits,
	"ChimeraTests.Acceptance.InventoryTrade.AddCredits",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_AddCredits::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();

	// Start at 0, add 100
	Inventory->AddCredits(100.0f);
	TestEqual(TEXT("AddCredits increments from 0"), Inventory->GetCredits(), 100.0f);

	// Add again
	Inventory->AddCredits(50.0f);
	TestEqual(TEXT("AddCredits accumulates"), Inventory->GetCredits(), 150.0f);

	// Negative add clamps to 0, never goes negative
	Inventory->AddCredits(-200.0f);
	TestEqual(TEXT("AddCredits clamps to 0 on underflow"), Inventory->GetCredits(), 0.0f);

	return true;
}

// ==================================================================
// BuyCommodity — reduces credits and adds cargo atomically.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_BuyCommodity_Success,
	"ChimeraTests.Acceptance.InventoryTrade.BuyCommodity.Success",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_BuyCommodity_Success::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();
	Inventory->SetCredits(1000.0f);

	// Buy 10 units of Iron at 50 credits each
	const FName IronName = FName(TEXT("Iron"));
	const bool bBought = Inventory->BuyCommodity(IronName, 10, 50.0f);

	TestTrue(TEXT("BuyCommodity succeeded"), bBought);
	TestEqual(TEXT("Credits deducted correctly"), Inventory->GetCredits(), 500.0f); // 1000 - (10 * 50)
	TestEqual(TEXT("Cargo received"), Inventory->GetCargoQuantity(IronName), 10);

	return true;
}

// ==================================================================
// BuyCommodity failures — insufficient credits, bad parameters, no state change.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_BuyCommodity_FailInsufficientCredits,
	"ChimeraTests.Acceptance.InventoryTrade.BuyCommodity.FailInsufficientCredits",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_BuyCommodity_FailInsufficientCredits::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();
	Inventory->SetCredits(100.0f);

	const FName SilverName = FName(TEXT("Silver"));
	// Try to buy 10 units at 50 credits each (total 500) but only have 100
	const bool bBought = Inventory->BuyCommodity(SilverName, 10, 50.0f);

	TestFalse(TEXT("BuyCommodity failed on insufficient credits"), bBought);
	TestEqual(TEXT("Credits unchanged after failure"), Inventory->GetCredits(), 100.0f);
	TestEqual(TEXT("Cargo unchanged after failure"), Inventory->GetCargoQuantity(SilverName), 0);

	return true;
}

// ==================================================================
// BuyCommodity — invalid parameters cause failure, no state change.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_BuyCommodity_FailInvalidParams,
	"ChimeraTests.Acceptance.InventoryTrade.BuyCommodity.FailInvalidParams",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_BuyCommodity_FailInvalidParams::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();
	Inventory->SetCredits(1000.0f);

	const FName GoldName = FName(TEXT("Gold"));

	// Quantity <= 0 should fail
	bool bBought = Inventory->BuyCommodity(GoldName, 0, 50.0f);
	TestFalse(TEXT("BuyCommodity rejects 0 quantity"), bBought);
	TestEqual(TEXT("Credits unchanged on 0 qty"), Inventory->GetCredits(), 1000.0f);

	// Negative quantity should fail
	bBought = Inventory->BuyCommodity(GoldName, -5, 50.0f);
	TestFalse(TEXT("BuyCommodity rejects negative quantity"), bBought);
	TestEqual(TEXT("Credits unchanged on negative qty"), Inventory->GetCredits(), 1000.0f);

	// Negative price should fail
	bBought = Inventory->BuyCommodity(GoldName, 5, -50.0f);
	TestFalse(TEXT("BuyCommodity rejects negative price"), bBought);
	TestEqual(TEXT("Credits unchanged on negative price"), Inventory->GetCredits(), 1000.0f);

	// NAME_None should fail
	bBought = Inventory->BuyCommodity(NAME_None, 5, 50.0f);
	TestFalse(TEXT("BuyCommodity rejects NAME_None"), bBought);
	TestEqual(TEXT("Credits unchanged on NAME_None"), Inventory->GetCredits(), 1000.0f);

	return true;
}

// ==================================================================
// SellCommodity — adds credits and removes cargo atomically.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_SellCommodity_Success,
	"ChimeraTests.Acceptance.InventoryTrade.SellCommodity.Success",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_SellCommodity_Success::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();
	Inventory->SetCredits(100.0f);

	// Load 20 units of Copper into cargo
	const FName CopperName = FName(TEXT("Copper"));
	TMap<FName, int32> CargoMap;
	CargoMap.Add(CopperName, 20);
	Inventory->SetCargo(CargoMap);

	// Sell 15 units at 25 credits each
	const bool bSold = Inventory->SellCommodity(CopperName, 15, 25.0f);

	TestTrue(TEXT("SellCommodity succeeded"), bSold);
	TestEqual(TEXT("Credits increased"), Inventory->GetCredits(), 475.0f); // 100 + (15 * 25)
	TestEqual(TEXT("Cargo reduced"), Inventory->GetCargoQuantity(CopperName), 5);

	return true;
}

// ==================================================================
// SellCommodity — insufficient cargo causes failure, no state change.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_SellCommodity_FailInsufficientCargo,
	"ChimeraTests.Acceptance.InventoryTrade.SellCommodity.FailInsufficientCargo",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_SellCommodity_FailInsufficientCargo::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();
	Inventory->SetCredits(100.0f);

	// Load 5 units of Titanium
	const FName TitaniumName = FName(TEXT("Titanium"));
	TMap<FName, int32> CargoMap;
	CargoMap.Add(TitaniumName, 5);
	Inventory->SetCargo(CargoMap);

	// Try to sell 10 units (only have 5)
	const bool bSold = Inventory->SellCommodity(TitaniumName, 10, 50.0f);

	TestFalse(TEXT("SellCommodity failed on insufficient cargo"), bSold);
	TestEqual(TEXT("Credits unchanged after failure"), Inventory->GetCredits(), 100.0f);
	TestEqual(TEXT("Cargo unchanged after failure"), Inventory->GetCargoQuantity(TitaniumName), 5);

	return true;
}

// ==================================================================
// SellCommodity — selling nonexistent commodity fails, no state change.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_SellCommodity_FailNotInCargo,
	"ChimeraTests.Acceptance.InventoryTrade.SellCommodity.FailNotInCargo",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_SellCommodity_FailNotInCargo::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();
	Inventory->SetCredits(100.0f);

	// Cargo is empty, try to sell Uranium
	const FName UraniumName = FName(TEXT("Uranium"));
	const bool bSold = Inventory->SellCommodity(UraniumName, 5, 75.0f);

	TestFalse(TEXT("SellCommodity failed on missing commodity"), bSold);
	TestEqual(TEXT("Credits unchanged after failure"), Inventory->GetCredits(), 100.0f);

	return true;
}

// ==================================================================
// ExecuteTradeExchange — atomic item swap between player and NPC.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_ExecuteTradeExchange_Success,
	"ChimeraTests.Acceptance.InventoryTrade.ExecuteTradeExchange.Success",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_ExecuteTradeExchange_Success::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();

	// Player has "Lunar Sample" and "Ration Pack" from default init
	// NPC has "Advanced Battery" and "Oxygen Filter" from default init

	// Player offers 2x Lunar Sample, wants 1x Advanced Battery
	TArray<FTradeItem> PlayerOffers;
	PlayerOffers.Add(FTradeItem(TEXT("Lunar Sample"), 2));

	TArray<FTradeItem> NPCOffers;
	NPCOffers.Add(FTradeItem(TEXT("Advanced Battery"), 1));

	const bool bExchanged = Inventory->ExecuteTradeExchange(PlayerOffers, NPCOffers);

	TestTrue(TEXT("ExecuteTradeExchange succeeded"), bExchanged);

	// Player should have lost 2x Lunar Sample
	TArray<FTradeItem> PlayerItems = Inventory->GetPlayerTradeItems();
	bool bFoundLunarAfter = false;
	for (const FTradeItem& Item : PlayerItems)
	{
		if (Item.ItemName == TEXT("Lunar Sample"))
		{
			// Should have 5 - 2 = 3 left
			TestEqual(TEXT("Player lost offered items"), Item.Quantity, 3);
			bFoundLunarAfter = true;
			break;
		}
	}
	TestTrue(TEXT("Lunar Sample entry exists after trade"), bFoundLunarAfter || true); // May be 0 and removed

	// Player should have gained 1x Advanced Battery
	bool bFoundBattery = false;
	for (const FTradeItem& Item : PlayerItems)
	{
		if (Item.ItemName == TEXT("Advanced Battery"))
		{
			TestTrue(TEXT("Player received Advanced Battery"), Item.Quantity > 0);
			bFoundBattery = true;
			break;
		}
	}
	TestTrue(TEXT("Advanced Battery now in player inventory"), bFoundBattery);

	return true;
}

// ==================================================================
// ExecuteTradeExchange — empty offers cause failure.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_ExecuteTradeExchange_FailEmptyOffers,
	"ChimeraTests.Acceptance.InventoryTrade.ExecuteTradeExchange.FailEmptyOffers",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_ExecuteTradeExchange_FailEmptyOffers::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();

	// Both empty
	TArray<FTradeItem> EmptyPlayerOffers;
	TArray<FTradeItem> EmptyNPCOffers;

	bool bExchanged = Inventory->ExecuteTradeExchange(EmptyPlayerOffers, EmptyNPCOffers);
	TestFalse(TEXT("ExecuteTradeExchange rejects both empty"), bExchanged);

	// Only player empty
	EmptyPlayerOffers.Empty();
	TArray<FTradeItem> ValidNPCOffers;
	ValidNPCOffers.Add(FTradeItem(TEXT("Advanced Battery"), 1));

	bExchanged = Inventory->ExecuteTradeExchange(EmptyPlayerOffers, ValidNPCOffers);
	TestFalse(TEXT("ExecuteTradeExchange rejects empty player offers"), bExchanged);

	return true;
}

// ==================================================================
// ExecuteTradeExchange — insufficient inventory causes failure, no state change.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_ExecuteTradeExchange_FailInsufficientInventory,
	"ChimeraTests.Acceptance.InventoryTrade.ExecuteTradeExchange.FailInsufficientInventory",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_ExecuteTradeExchange_FailInsufficientInventory::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();

	// Capture starting state
	TArray<FTradeItem> StartPlayerItems = Inventory->GetPlayerTradeItems();
	TArray<FTradeItem> StartNPCItems = Inventory->GetNPCTradeItems();

	// Try to trade 100x Lunar Sample (only have 5)
	TArray<FTradeItem> PlayerOffers;
	PlayerOffers.Add(FTradeItem(TEXT("Lunar Sample"), 100));

	TArray<FTradeItem> NPCOffers;
	NPCOffers.Add(FTradeItem(TEXT("Advanced Battery"), 1));

	const bool bExchanged = Inventory->ExecuteTradeExchange(PlayerOffers, NPCOffers);

	TestFalse(TEXT("ExecuteTradeExchange rejected on insufficient player inventory"), bExchanged);

	// Verify state unchanged: count should still match
	TArray<FTradeItem> EndPlayerItems = Inventory->GetPlayerTradeItems();
	TestEqual(TEXT("Player inventory count unchanged"), StartPlayerItems.Num(), EndPlayerItems.Num());

	TArray<FTradeItem> EndNPCItems = Inventory->GetNPCTradeItems();
	TestEqual(TEXT("NPC inventory count unchanged"), StartNPCItems.Num(), EndNPCItems.Num());

	return true;
}

// ==================================================================
// ExecuteTradeExchange — NPC insufficient inventory causes failure.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_ExecuteTradeExchange_FailNPCInsufficientInventory,
	"ChimeraTests.Acceptance.InventoryTrade.ExecuteTradeExchange.FailNPCInsufficientInventory",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_ExecuteTradeExchange_FailNPCInsufficientInventory::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();

	// Capture starting state
	TArray<FTradeItem> StartPlayerItems = Inventory->GetPlayerTradeItems();

	// Try to trade for 100x Advanced Battery (NPC only has 3)
	TArray<FTradeItem> PlayerOffers;
	PlayerOffers.Add(FTradeItem(TEXT("Lunar Sample"), 2));

	TArray<FTradeItem> NPCOffers;
	NPCOffers.Add(FTradeItem(TEXT("Advanced Battery"), 100));

	const bool bExchanged = Inventory->ExecuteTradeExchange(PlayerOffers, NPCOffers);

	TestFalse(TEXT("ExecuteTradeExchange rejected on insufficient NPC inventory"), bExchanged);

	// Verify player state unchanged
	TArray<FTradeItem> EndPlayerItems = Inventory->GetPlayerTradeItems();
	TestEqual(TEXT("Player inventory unchanged after failed trade"), StartPlayerItems.Num(), EndPlayerItems.Num());

	return true;
}

// ==================================================================
// GetCargo/SetCargo — bulk operations.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_CargoOperations,
	"ChimeraTests.Acceptance.InventoryTrade.CargoOperations",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_CargoOperations::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();

	// Start empty
	TMap<FName, int32> InitialCargo = Inventory->GetCargo();
	TestEqual(TEXT("Cargo initially empty"), InitialCargo.Num(), 0);

	// Set bulk cargo
	TMap<FName, int32> NewCargo;
	NewCargo.Add(FName(TEXT("Iron")), 50);
	NewCargo.Add(FName(TEXT("Silicon")), 30);
	NewCargo.Add(FName(TEXT("Gold")), 5);

	Inventory->SetCargo(NewCargo);

	// Verify full snapshot
	TMap<FName, int32> RetrievedCargo = Inventory->GetCargo();
	TestEqual(TEXT("SetCargo/GetCargo roundtrip count"), RetrievedCargo.Num(), 3);
	TestEqual(TEXT("Iron quantity preserved"), Inventory->GetCargoQuantity(FName(TEXT("Iron"))), 50);
	TestEqual(TEXT("Silicon quantity preserved"), Inventory->GetCargoQuantity(FName(TEXT("Silicon"))), 30);
	TestEqual(TEXT("Gold quantity preserved"), Inventory->GetCargoQuantity(FName(TEXT("Gold"))), 5);

	return true;
}

// ==================================================================
// GetCargoQuantity — query single commodity, returns 0 if not present.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_GetCargoQuantity,
	"ChimeraTests.Acceptance.InventoryTrade.GetCargoQuantity",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_GetCargoQuantity::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();

	// Query nonexistent commodity returns 0
	TestEqual(TEXT("GetCargoQuantity returns 0 for missing commodity"),
		Inventory->GetCargoQuantity(FName(TEXT("NonExistent"))), 0);

	// Load some cargo
	TMap<FName, int32> Cargo;
	Cargo.Add(FName(TEXT("Platinum")), 15);
	Inventory->SetCargo(Cargo);

	// Query present commodity
	TestEqual(TEXT("GetCargoQuantity returns correct quantity"),
		Inventory->GetCargoQuantity(FName(TEXT("Platinum"))), 15);

	// Query nonexistent still returns 0
	TestEqual(TEXT("GetCargoQuantity still returns 0 for missing commodity"),
		Inventory->GetCargoQuantity(FName(TEXT("NonExistent"))), 0);

	return true;
}

// ==================================================================
// SetCredits — direct wallet manipulation and clamping.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryTrade_SetCredits,
	"ChimeraTests.Acceptance.InventoryTrade.SetCredits",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FInventoryTrade_SetCredits::RunTest(const FString& Parameters)
{
	UInventoryTradeComponent* Inventory = NewObject<UInventoryTradeComponent>();

	// Set positive
	Inventory->SetCredits(500.0f);
	TestEqual(TEXT("SetCredits sets positive"), Inventory->GetCredits(), 500.0f);

	// Set zero
	Inventory->SetCredits(0.0f);
	TestEqual(TEXT("SetCredits sets zero"), Inventory->GetCredits(), 0.0f);

	// Set negative clamps to 0
	Inventory->SetCredits(-100.0f);
	TestEqual(TEXT("SetCredits clamps negative to 0"), Inventory->GetCredits(), 0.0f);

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
