// Copyright 2026 Chimera Project. All Rights Reserved.
// Sacrifice Log Acceptance Tests — Design Law 2 (dead players become
// memorials/stars). Proves USacrificeLogComponent's own behaviours, plus the
// cross-component integration with UStarMemorialComponent (world-independently
// via NewObject, no PIE).
//
// PROVENANCE (tb-0158, 2026-07-18): extracted VERBATIM from the original
// StarMemorialAcceptanceTests.cpp (commit 859d453), which bundled these
// SacrificeLog-only tests together with StarMemorial tests in one file. tb-0158
// brought StarMemorialComponent under generator ownership
// (core/game_code_generator.py::generate_star_memorial_files) in a NEW plain-
// function test idiom (mirroring WeatherAcceptanceTests.cpp) that now owns
// StarMemorialAcceptanceTests.cpp outright — regenerating that file would have
// silently deleted this unrelated coverage on first regen. USacrificeLogComponent
// itself has no generate_* method (out of tb-0158's scope; its shipped API does
// not yet match the seed's weight-keyed Record()/WeightForGeneration() shape —
// see generate_star_memorial_files' docstring), so this file stays loop-built
// (hand-edits safe) exactly as before, just relocated to its own file named for
// its actual subject. No test logic changed.

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "../Save/SacrificeLogComponent.h"
#include "../Save/StarMemorialComponent.h"

#if WITH_DEV_AUTOMATION_TESTS

// ==================================================================
// SacrificeLogComponent: Initialization & Basic Recording
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSacrificeLog_Init,
	"ChimeraTests.Acceptance.SacrificeLog.Init",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FSacrificeLog_Init::RunTest(const FString& Parameters)
{
	USacrificeLogComponent* Log = NewObject<USacrificeLogComponent>();
	TestNotNull(TEXT("SacrificeLog instantiated"), Log);

	TestFalse(TEXT("initially no sacrifices"), Log->HasAnySacrifices());
	TestEqual(TEXT("initial sacrifice count is zero"), Log->GetSacrificeCount(), 0);

	TArray<FString> Descriptions = Log->GetSacrificeDescriptions();
	TestEqual(TEXT("initial description array empty"), Descriptions.Num(), 0);
	return true;
}

// ==================================================================
// RecordProtectionAtCost: Records a single sacrifice entry
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSacrificeLog_RecordProtectionAtCost,
	"ChimeraTests.Acceptance.SacrificeLog.RecordProtectionAtCost",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FSacrificeLog_RecordProtectionAtCost::RunTest(const FString& Parameters)
{
	USacrificeLogComponent* Log = NewObject<USacrificeLogComponent>();

	// Record first sacrifice
	Log->RecordProtectionAtCost(TEXT("Saved stranded miner"), 500.0f);
	TestEqual(TEXT("sacrifice count incremented to 1"), Log->GetSacrificeCount(), 1);
	TestTrue(TEXT("HasAnySacrifices now true"), Log->HasAnySacrifices());

	TArray<FString> Desc1 = Log->GetSacrificeDescriptions();
	TestEqual(TEXT("description array has 1 entry"), Desc1.Num(), 1);
	TestEqual(TEXT("description text recorded"), Desc1[0], TEXT("Saved stranded miner"));

	// Record second sacrifice
	Log->RecordProtectionAtCost(TEXT("Shared O2 with wounded crew"), 250.0f);
	TestEqual(TEXT("sacrifice count is 2"), Log->GetSacrificeCount(), 2);

	TArray<FString> Desc2 = Log->GetSacrificeDescriptions();
	TestEqual(TEXT("description array has 2 entries"), Desc2.Num(), 2);
	TestEqual(TEXT("first entry unchanged"), Desc2[0], TEXT("Saved stranded miner"));
	TestEqual(TEXT("second entry recorded"), Desc2[1], TEXT("Shared O2 with wounded crew"));
	return true;
}

// ==================================================================
// RecordProtectionAtCost: Empty descriptions are rejected
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSacrificeLog_EmptyDescriptionRejected,
	"ChimeraTests.Acceptance.SacrificeLog.EmptyDescriptionRejected",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FSacrificeLog_EmptyDescriptionRejected::RunTest(const FString& Parameters)
{
	USacrificeLogComponent* Log = NewObject<USacrificeLogComponent>();

	// Attempt to record empty description
	Log->RecordProtectionAtCost(TEXT(""), 100.0f);
	TestEqual(TEXT("empty description not recorded"), Log->GetSacrificeCount(), 0);
	TestFalse(TEXT("HasAnySacrifices still false"), Log->HasAnySacrifices());

	// Add a real entry
	Log->RecordProtectionAtCost(TEXT("Valid entry"), 50.0f);
	TestEqual(TEXT("valid entry counted"), Log->GetSacrificeCount(), 1);

	// Try empty again
	Log->RecordProtectionAtCost(TEXT(""), 75.0f);
	TestEqual(TEXT("count unchanged by empty"), Log->GetSacrificeCount(), 1);

	TArray<FString> Desc = Log->GetSacrificeDescriptions();
	TestEqual(TEXT("only valid entry in array"), Desc.Num(), 1);
	return true;
}

// ==================================================================
// RecordTradeRefused: Records a formatted trade refusal
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSacrificeLog_RecordTradeRefused,
	"ChimeraTests.Acceptance.SacrificeLog.RecordTradeRefused",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FSacrificeLog_RecordTradeRefused::RunTest(const FString& Parameters)
{
	USacrificeLogComponent* Log = NewObject<USacrificeLogComponent>();

	// Record a trade refusal
	Log->RecordTradeRefused(TEXT("Cargo of medical supplies"), 2500.0f);
	TestEqual(TEXT("trade refusal recorded as sacrifice"), Log->GetSacrificeCount(), 1);
	TestTrue(TEXT("HasAnySacrifices true"), Log->HasAnySacrifices());

	TArray<FString> Desc = Log->GetSacrificeDescriptions();
	TestEqual(TEXT("one entry in descriptions"), Desc.Num(), 1);

	// Verify formatted string contains both description and value
	TestTrue(TEXT("formatted entry contains 'Trade refused'"), Desc[0].Contains(TEXT("Trade refused")));
	TestTrue(TEXT("formatted entry contains description"), Desc[0].Contains(TEXT("Cargo of medical supplies")));
	TestTrue(TEXT("formatted entry contains value"), Desc[0].Contains(TEXT("2500.00")));

	// Record another with different value
	Log->RecordTradeRefused(TEXT("Rare ore shipment"), 5000.0f);
	TestEqual(TEXT("second trade refusal recorded"), Log->GetSacrificeCount(), 2);

	TArray<FString> Desc2 = Log->GetSacrificeDescriptions();
	TestTrue(TEXT("second entry formatted correctly"), Desc2[1].Contains(TEXT("Rare ore shipment")));
	TestTrue(TEXT("second entry has correct value"), Desc2[1].Contains(TEXT("5000.00")));
	return true;
}

// ==================================================================
// Integration: Both components working together
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStarMemorial_FullNarrativeFlow,
	"ChimeraTests.Acceptance.StarMemorial.FullNarrativeFlow",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FStarMemorial_FullNarrativeFlow::RunTest(const FString& Parameters)
{
	// Simulate a full generation: player makes sacrifices, then dies
	USacrificeLogComponent* Sacrifices = NewObject<USacrificeLogComponent>();
	UStarMemorialComponent* Memorial = NewObject<UStarMemorialComponent>();

	// Player makes two sacrifices during their run
	Sacrifices->RecordProtectionAtCost(TEXT("Saved colony from solar flare"), 1000.0f);
	Sacrifices->RecordTradeRefused(TEXT("Refused to abandon injured worker"), 3000.0f);

	TestEqual(TEXT("player recorded 2 sacrifices"), Sacrifices->GetSacrificeCount(), 2);

	// Player dies; the sacrifice log becomes the basis for their memorial star
	int32 SacrificeCount = Sacrifices->GetSacrificeCount();
	float TotalSacrificeValue = 1000.0f + 3000.0f; // simplified
	int32 UnresolvedPains = 1; // e.g., from pending narrative choices

	// Add life to memorial using sacrifice data
	FStarEntry MemoryStar = Memorial->AddLife(
		TEXT("Explorer_Gen1"),
		1,
		TotalSacrificeValue,
		UnresolvedPains
	);

	TestEqual(TEXT("memorial records the life"), Memorial->GetStarCount(), 1);
	TestEqual(TEXT("star name matches"), MemoryStar.LifeName, TEXT("Explorer_Gen1"));
	TestEqual(TEXT("star generation is 1"), MemoryStar.Generation, 1);
	TestTrue(TEXT("star twinkles from unresolved pain"), MemoryStar.bTwinkle);
	TestTrue(TEXT("star brightness reflects sacrifice"), MemoryStar.Brightness > 0.5f);

	// Next generation can query the memorial
	TestEqual(TEXT("memorial visible to next gen"), Memorial->GetStarCount(), 1);
	TestTrue(TEXT("night light contributed by ancestor"), Memorial->GetNightLightLevel() > 0.0f);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
