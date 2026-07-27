// Copyright 2026 Chimera Project. All Rights Reserved.
// Faction Acceptance Tests — the faction standing and relationship system as hard facts,
// world-independently (NewObject, no PIE). Proves standing adjusts up/down, clamps to
// [-100, 100], tiers resolve correctly (Hostile/Unfriendly/Neutral/Friendly/Allied), and
// notifications apply standing changes according to their formulas.

#pragma warning(disable: 5038)
#pragma warning(disable: 4996)
#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "../Factions/FactionComponent.h"

#if WITH_DEV_AUTOMATION_TESTS

// ==================================================================
// Initialization — seeded factions have correct standing and tiers.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFaction_Init,
	"ChimeraTests.Acceptance.Factions.Init",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FFaction_Init::RunTest(const FString& Parameters)
{
	UFactionComponent* Faction = NewObject<UFactionComponent>();
	TestNotNull(TEXT("Faction instantiated"), Faction);
	Faction->InitializeFromDSL();

	// Three factions seeded: OrbitalCouncil (neutral), TitanMiners (friendly), PirateSyndicate (hostile)
	TestEqual(TEXT("OrbitalCouncil standing"), Faction->GetStanding(FName(TEXT("faction_orbital_council"))), 0.0f);
	TestEqual(TEXT("OrbitalCouncil relationship"), Faction->GetRelationship(FName(TEXT("faction_orbital_council"))), FString(TEXT("Neutral")));

	TestEqual(TEXT("TitanMiners standing"), Faction->GetStanding(FName(TEXT("faction_titan_miners"))), 25.0f);
	TestEqual(TEXT("TitanMiners relationship"), Faction->GetRelationship(FName(TEXT("faction_titan_miners"))), FString(TEXT("Friendly")));

	TestEqual(TEXT("PirateSyndicate standing"), Faction->GetStanding(FName(TEXT("faction_pirate_syndicate"))), -75.0f);
	TestEqual(TEXT("PirateSyndicate relationship"), Faction->GetRelationship(FName(TEXT("faction_pirate_syndicate"))), FString(TEXT("Hostile")));

	return true;
}

// ==================================================================
// Standing adjustment — ModifyStanding raises and lowers reputation.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFaction_StandingAdjustment,
	"ChimeraTests.Acceptance.Factions.StandingAdjustment",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FFaction_StandingAdjustment::RunTest(const FString& Parameters)
{
	UFactionComponent* Faction = NewObject<UFactionComponent>();
	Faction->InitializeFromDSL();

	// Positive adjustment: OrbitalCouncil at 0, raise +10 -> 10.
	FName OrbitalCouncil = FName(TEXT("faction_orbital_council"));
	Faction->ModifyStanding(OrbitalCouncil, 10.0f);
	TestEqual(TEXT("standing raised +10"), Faction->GetStanding(OrbitalCouncil), 10.0f);

	// Negative adjustment: lower -15 -> -5.
	Faction->ModifyStanding(OrbitalCouncil, -15.0f);
	TestEqual(TEXT("standing lowered -15"), Faction->GetStanding(OrbitalCouncil), -5.0f);

	// Multiple adjustments accumulate: +8 -> 3, then +10 -> 13.
	Faction->ModifyStanding(OrbitalCouncil, 8.0f);
	TestEqual(TEXT("standing adjusted +8"), Faction->GetStanding(OrbitalCouncil), 3.0f);
	Faction->ModifyStanding(OrbitalCouncil, 10.0f);
	TestEqual(TEXT("standing accumulated to 13"), Faction->GetStanding(OrbitalCouncil), 13.0f);

	return true;
}

// ==================================================================
// Clamping — standing clamps to [-100, 100] bounds.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFaction_Clamping,
	"ChimeraTests.Acceptance.Factions.Clamping",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FFaction_Clamping::RunTest(const FString& Parameters)
{
	UFactionComponent* Faction = NewObject<UFactionComponent>();
	Faction->InitializeFromDSL();

	FName TestFaction = FName(TEXT("faction_test_clamp"));

	// Start unseeded at 0, push to +150 (clamped to +100).
	Faction->ModifyStanding(TestFaction, 150.0f);
	TestEqual(TEXT("standing clamped to max 100"), Faction->GetStanding(TestFaction), 100.0f);

	// Push down: -250 (clamped to -100).
	Faction->ModifyStanding(TestFaction, -250.0f);
	TestEqual(TEXT("standing clamped to min -100"), Faction->GetStanding(TestFaction), -100.0f);

	// Clamp from below zero: at -100, +80 -> -20.
	Faction->ModifyStanding(TestFaction, 80.0f);
	TestEqual(TEXT("standing adjusted in clamped range"), Faction->GetStanding(TestFaction), -20.0f);

	// Hit upper bound: at -20, +200 -> +100.
	Faction->ModifyStanding(TestFaction, 200.0f);
	TestEqual(TEXT("standing clamped at +100 upper bound"), Faction->GetStanding(TestFaction), 100.0f);

	return true;
}

// ==================================================================
// Tier boundaries — each tier resolves from standing correctly.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFaction_TierBoundaries,
	"ChimeraTests.Acceptance.Factions.TierBoundaries",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FFaction_TierBoundaries::RunTest(const FString& Parameters)
{
	UFactionComponent* Faction = NewObject<UFactionComponent>();
	Faction->InitializeFromDSL();

	FName TestFaction = FName(TEXT("faction_tier_test"));

	// Hostile: standing <= -75.
	Faction->ModifyStanding(TestFaction, -75.0f);
	TestEqual(TEXT("hostile at -75"), Faction->GetRelationship(TestFaction), FString(TEXT("Hostile")));
	TestTrue(TEXT("IsHostile returns true at -75"), Faction->IsHostile(TestFaction));

	Faction->ModifyStanding(TestFaction, -1.0f);  // -76
	TestEqual(TEXT("hostile at -76"), Faction->GetRelationship(TestFaction), FString(TEXT("Hostile")));

	// Unfriendly: -75 < standing <= -25.
	Faction->ModifyStanding(TestFaction, 51.0f);  // -25
	TestEqual(TEXT("unfriendly at -25"), Faction->GetRelationship(TestFaction), FString(TEXT("Unfriendly")));
	TestFalse(TEXT("IsHostile false at -25"), Faction->IsHostile(TestFaction));

	Faction->ModifyStanding(TestFaction, -25.0f); // -50
	TestEqual(TEXT("unfriendly at -50"), Faction->GetRelationship(TestFaction), FString(TEXT("Unfriendly")));

	// Neutral: -25 < standing <= 24.
	Faction->ModifyStanding(TestFaction, 26.0f);  // -24
	TestEqual(TEXT("neutral at -24"), Faction->GetRelationship(TestFaction), FString(TEXT("Neutral")));

	Faction->ModifyStanding(TestFaction, 48.0f);  // 24
	TestEqual(TEXT("neutral at 24"), Faction->GetRelationship(TestFaction), FString(TEXT("Neutral")));

	// Friendly: 24 < standing <= 74.
	Faction->ModifyStanding(TestFaction, 1.0f);   // 25
	TestEqual(TEXT("friendly at 25"), Faction->GetRelationship(TestFaction), FString(TEXT("Friendly")));

	Faction->ModifyStanding(TestFaction, 49.0f);  // 74
	TestEqual(TEXT("friendly at 74"), Faction->GetRelationship(TestFaction), FString(TEXT("Friendly")));

	// Allied: standing > 74.
	Faction->ModifyStanding(TestFaction, 1.0f);   // 75
	TestEqual(TEXT("allied at 75"), Faction->GetRelationship(TestFaction), FString(TEXT("Allied")));

	Faction->ModifyStanding(TestFaction, 25.0f);  // 100 (clamped)
	TestEqual(TEXT("allied at 100"), Faction->GetRelationship(TestFaction), FString(TEXT("Allied")));

	return true;
}

// ==================================================================
// Trade notification — standing gain is 1 per 1000 credits, capped at +5.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFaction_TradeNotification,
	"ChimeraTests.Acceptance.Factions.TradeNotification",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FFaction_TradeNotification::RunTest(const FString& Parameters)
{
	UFactionComponent* Faction = NewObject<UFactionComponent>();
	Faction->InitializeFromDSL();

	FName Trader = FName(TEXT("faction_trader_test"));

	// 1000 credits -> +1 standing.
	Faction->NotifyTradeCompleted(Trader, 1000.0f);
	TestEqual(TEXT("1000 credits = +1 standing"), Faction->GetStanding(Trader), 1.0f);

	// 2500 credits -> +2.5 standing (0.0025 per credit).
	Faction->NotifyTradeCompleted(Trader, 2500.0f);
	TestEqual(TEXT("2500 credits = +2.5 standing"), Faction->GetStanding(Trader), 3.5f, 0.01f);

	// 1000 credits -> +1 standing (3.5 + 1.0 = 4.5).
	Faction->NotifyTradeCompleted(Trader, 1000.0f);
	TestEqual(TEXT("accumulated trade standing"), Faction->GetStanding(Trader), 4.5f, 0.01f);

	// 10000 credits would be +10, but capped at +5.
	float CurrentStanding = Faction->GetStanding(Trader);
	Faction->NotifyTradeCompleted(Trader, 10000.0f);
	TestEqual(TEXT("10000 credits capped at +5"), Faction->GetStanding(Trader), CurrentStanding + 5.0f, 0.01f);

	// 0 credits -> 0 standing.
	float Before = Faction->GetStanding(Trader);
	Faction->NotifyTradeCompleted(Trader, 0.0f);
	TestEqual(TEXT("0 credits = no standing change"), Faction->GetStanding(Trader), Before);

	// Negative trade value (refund scenario) would compute negative, but Clamp(0, -inf, +inf) allows it.
	// The formula is FMath::Clamp(TradeValue / 1000.0f, 0.0f, 5.0f), so negatives clamp to 0.
	Before = Faction->GetStanding(Trader);
	Faction->NotifyTradeCompleted(Trader, -1000.0f);
	TestEqual(TEXT("negative trade = 0 standing change"), Faction->GetStanding(Trader), Before);

	return true;
}

// ==================================================================
// Mission notification — standing change is exactly as specified.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFaction_MissionNotification,
	"ChimeraTests.Acceptance.Factions.MissionNotification",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FFaction_MissionNotification::RunTest(const FString& Parameters)
{
	UFactionComponent* Faction = NewObject<UFactionComponent>();
	Faction->InitializeFromDSL();

	FName Contractor = FName(TEXT("faction_mission_test"));

	// Mission with +10 standing reward.
	Faction->NotifyMissionCompleted(Contractor, 10.0f);
	TestEqual(TEXT("mission +10 standing"), Faction->GetStanding(Contractor), 10.0f);

	// Mission with -5 standing penalty (betrayal).
	Faction->NotifyMissionCompleted(Contractor, -5.0f);
	TestEqual(TEXT("mission -5 standing"), Faction->GetStanding(Contractor), 5.0f);

	// Mission with +30 standing (epic reward), but accumulates and clamps.
	Faction->NotifyMissionCompleted(Contractor, 100.0f);
	TestEqual(TEXT("mission +100 clamped at +100"), Faction->GetStanding(Contractor), 100.0f);

	// Faction at max; mission with -50 standing penalty.
	Faction->NotifyMissionCompleted(Contractor, -50.0f);
	TestEqual(TEXT("mission -50 from max"), Faction->GetStanding(Contractor), 50.0f);

	return true;
}

// ==================================================================
// Pirate kill notification — always -10 standing.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFaction_PirateKillNotification,
	"ChimeraTests.Acceptance.Factions.PirateKillNotification",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FFaction_PirateKillNotification::RunTest(const FString& Parameters)
{
	UFactionComponent* Faction = NewObject<UFactionComponent>();
	Faction->InitializeFromDSL();

	FName PirateFaction = FName(TEXT("faction_pirate_test"));

	// Single pirate kill: -10 standing.
	Faction->NotifyPirateKilled(PirateFaction);
	TestEqual(TEXT("pirate kill -10 standing"), Faction->GetStanding(PirateFaction), -10.0f);

	// Second kill: -10 -> -20.
	Faction->NotifyPirateKilled(PirateFaction);
	TestEqual(TEXT("second pirate kill -20"), Faction->GetStanding(PirateFaction), -20.0f);

	// Ten kills: -100 (clamped).
	for (int i = 0; i < 8; ++i)
	{
		Faction->NotifyPirateKilled(PirateFaction);
	}
	TestEqual(TEXT("ten pirate kills clamped at -100"), Faction->GetStanding(PirateFaction), -100.0f);

	// Further kills do not lower standing (at min).
	Faction->NotifyPirateKilled(PirateFaction);
	TestEqual(TEXT("still at -100 after clamp"), Faction->GetStanding(PirateFaction), -100.0f);

	return true;
}

// ==================================================================
// IsHostile check — correctly identifies hostile relationships only.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFaction_IsHostileCheck,
	"ChimeraTests.Acceptance.Factions.IsHostileCheck",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FFaction_IsHostileCheck::RunTest(const FString& Parameters)
{
	UFactionComponent* Faction = NewObject<UFactionComponent>();
	Faction->InitializeFromDSL();

	FName TestFaction = FName(TEXT("faction_hostile_check"));

	// Below -75: hostile.
	Faction->ModifyStanding(TestFaction, -80.0f);
	TestTrue(TEXT("IsHostile true at -80"), Faction->IsHostile(TestFaction));

	// At -75: boundary is hostile.
	Faction->ModifyStanding(TestFaction, 5.0f);  // -75
	TestTrue(TEXT("IsHostile true at -75"), Faction->IsHostile(TestFaction));

	// Just above -75: unfriendly, not hostile.
	Faction->ModifyStanding(TestFaction, 1.0f);  // -74
	TestFalse(TEXT("IsHostile false at -74"), Faction->IsHostile(TestFaction));

	// Neutral, friendly, and allied are all non-hostile.
	Faction->ModifyStanding(TestFaction, 50.0f);  // -24 (neutral)
	TestFalse(TEXT("IsHostile false at neutral"), Faction->IsHostile(TestFaction));

	Faction->ModifyStanding(TestFaction, 50.0f);  // 26 (friendly)
	TestFalse(TEXT("IsHostile false at friendly"), Faction->IsHostile(TestFaction));

	Faction->ModifyStanding(TestFaction, 75.0f);  // 101, clamped to 100 (allied)
	TestFalse(TEXT("IsHostile false at allied"), Faction->IsHostile(TestFaction));

	return true;
}

// ==================================================================
// Unseeded faction behavior — uninitialized factions default to neutral 0.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFaction_UnseededDefault,
	"ChimeraTests.Acceptance.Factions.UnseededDefault",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FFaction_UnseededDefault::RunTest(const FString& Parameters)
{
	UFactionComponent* Faction = NewObject<UFactionComponent>();
	Faction->InitializeFromDSL();

	FName NewFaction = FName(TEXT("faction_unknown_faction"));

	// GetStanding returns 0 for unseeded factions.
	TestEqual(TEXT("unseeded standing defaults to 0"), Faction->GetStanding(NewFaction), 0.0f);

	// GetRelationship returns "Neutral" for unseeded factions.
	TestEqual(TEXT("unseeded relationship defaults to Neutral"), Faction->GetRelationship(NewFaction), FString(TEXT("Neutral")));

	// IsHostile returns false for unseeded factions (neutral is not hostile).
	TestFalse(TEXT("unseeded IsHostile false"), Faction->IsHostile(NewFaction));

	// ModifyStanding on unseeded faction: FindOrAdd creates the entry at 0, then applies the delta.
	Faction->ModifyStanding(NewFaction, 15.0f);
	TestEqual(TEXT("unseeded + 15 = 15"), Faction->GetStanding(NewFaction), 15.0f);
	TestEqual(TEXT("standing 15 is neutral"), Faction->GetRelationship(NewFaction), FString(TEXT("Neutral")));

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
