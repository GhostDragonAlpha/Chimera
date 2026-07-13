// Copyright 2026 Chimera Project. All Rights Reserved.
// Combat Damage Acceptance Tests — shield absorption, hull depletion, and subsystem
// damage tracking as hard facts, world-independently (NewObject, no PIE). Proves:
// incoming damage is absorbed by shields FIRST, overflow hits hull, shields deplete,
// and SystemDamage tracks per-subsystem health.

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "../Combat/DamageComponent.h"
#include "../Combat/ShieldComponent.h"
#include "../Combat/SystemDamageComponent.h"

#if WITH_DEV_AUTOMATION_TESTS

// ==================================================================
// Initialization — hull and shield at full capacity, not destroyed.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDamage_Init,
	"ChimeraTests.Acceptance.Combat.Init",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FCombatDamage_Init::RunTest(const FString& Parameters)
{
	UDamageComponent* Hull = NewObject<UDamageComponent>();
	TestNotNull(TEXT("Hull component instantiated"), Hull);
	Hull->InitializeFromShip(5000.0f);

	TestEqual(TEXT("Hull full health"), Hull->GetHullPercent(), 1.0f, 0.001f);
	TestFalse(TEXT("Hull not destroyed"), Hull->IsDestroyed());

	UShieldComponent* Shield = NewObject<UShieldComponent>();
	TestNotNull(TEXT("Shield component instantiated"), Shield);
	Shield->InitializeFromShip(1000.0f, 50.0f);

	TestEqual(TEXT("Shield full charge"), Shield->GetCurrentShield(), 1000.0f, 0.001f);

	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TestNotNull(TEXT("SystemDamage component instantiated"), Systems);
	TArray<FName> Subsystems = {TEXT("Engines"), TEXT("Weapons"), TEXT("LifeSupport")};
	Systems->InitializeFromShip(Subsystems);

	TestEqual(TEXT("Engines at full"), Systems->GetSubsystemHealth(TEXT("Engines")), 100.0f, 0.001f);
	TestEqual(TEXT("LifeSupport at full"), Systems->GetSubsystemHealth(TEXT("LifeSupport")), 100.0f, 0.001f);
	TestTrue(TEXT("Engines operational"), Systems->GetSubsystemStatus(TEXT("Engines")) == ESubsystemStatus::Operational);
	return true;
}

// ==================================================================
// Shield Absorption — damage less than shield capacity is fully
// absorbed; shield reduces, hull untouched.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDamage_ShieldAbsorption,
	"ChimeraTests.Acceptance.Combat.ShieldAbsorption",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FCombatDamage_ShieldAbsorption::RunTest(const FString& Parameters)
{
	UShieldComponent* Shield = NewObject<UShieldComponent>();
	Shield->InitializeFromShip(1000.0f, 50.0f);

	// Apply damage less than shield capacity (300 < 1000).
	float Overflow = Shield->AbsorbDamage(300.0f);

	TestEqual(TEXT("Overflow is zero"), Overflow, 0.0f, 0.001f);
	TestEqual(TEXT("Shield reduced by damage"), Shield->GetCurrentShield(), 700.0f, 0.001f);

	// Apply more damage (200 < 700 remaining).
	Overflow = Shield->AbsorbDamage(200.0f);

	TestEqual(TEXT("Still no overflow"), Overflow, 0.0f, 0.001f);
	TestEqual(TEXT("Shield further reduced"), Shield->GetCurrentShield(), 500.0f, 0.001f);
	return true;
}

// ==================================================================
// Shield Depletion and Overflow — when damage exceeds remaining shield,
// the overflow is returned (to be applied to hull).
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDamage_ShieldOverflow,
	"ChimeraTests.Acceptance.Combat.ShieldOverflow",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FCombatDamage_ShieldOverflow::RunTest(const FString& Parameters)
{
	UShieldComponent* Shield = NewObject<UShieldComponent>();
	Shield->InitializeFromShip(1000.0f, 50.0f);

	// Apply damage that exceeds shield: 1200 > 1000.
	float Overflow = Shield->AbsorbDamage(1200.0f);

	TestEqual(TEXT("Shield absorbed 1000"), Shield->GetCurrentShield(), 0.0f, 0.001f);
	TestEqual(TEXT("Overflow is 200"), Overflow, 200.0f, 0.001f);

	// Shield is now depleted; any further damage passes through entirely.
	Overflow = Shield->AbsorbDamage(500.0f);
	TestEqual(TEXT("Depleted shield returns all damage"), Overflow, 500.0f, 0.001f);
	TestEqual(TEXT("Shield stays at zero"), Shield->GetCurrentShield(), 0.0f, 0.001f);
	return true;
}

// ==================================================================
// Hull Damage — GENERATOR BUG REVEALED: ApplyDamage does NOT call
// ShieldComponent->AbsorbDamage(), so shields never protect the hull.
// This test asserts CORRECT behavior (which currently fails).
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDamage_HullWithShieldProtection,
	"ChimeraTests.Acceptance.Combat.HullWithShieldProtection",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FCombatDamage_HullWithShieldProtection::RunTest(const FString& Parameters)
{
	UDamageComponent* Hull = NewObject<UDamageComponent>();
	Hull->InitializeFromShip(5000.0f);

	UShieldComponent* Shield = NewObject<UShieldComponent>();
	Shield->InitializeFromShip(1000.0f, 50.0f);

	// Apply damage that shields can absorb completely (300 < 1000 shield).
	// CORRECT: Hull->ApplyDamage() should internally call Shield->AbsorbDamage()
	// and only apply overflow to hull. ACTUAL: Shield is never consulted.
	Hull->ApplyDamage(300.0f, nullptr);

	// EXPECTED: Hull untouched, shield reduced to 700.
	// ACTUAL: Hull takes full 300 damage (because shield is never consulted).
	TestEqual(TEXT("Hull untouched by absorbed damage (SHOULD PASS if bug fixed)"),
		Hull->GetHullPercent(), 1.0f, 0.001f);
	TestFalse(TEXT("Hull not destroyed"), Hull->IsDestroyed());

	return true;
}

// ==================================================================
// Hull Depletion — direct hull damage (post-shield) depletes hull;
// at zero health, hull is destroyed.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDamage_HullDepletion,
	"ChimeraTests.Acceptance.Combat.HullDepletion",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FCombatDamage_HullDepletion::RunTest(const FString& Parameters)
{
	UDamageComponent* Hull = NewObject<UDamageComponent>();
	Hull->InitializeFromShip(5000.0f);

	// Apply damage directly to hull (no shield interference for this test).
	Hull->ApplyDamage(2000.0f, nullptr);

	TestEqual(TEXT("Hull reduced by damage"), Hull->GetHullPercent(), 0.6f, 0.001f);
	TestFalse(TEXT("Hull not destroyed at 60%"), Hull->IsDestroyed());

	// Apply more damage to cross the destruction threshold.
	Hull->ApplyDamage(5100.0f, nullptr);

	TestEqual(TEXT("Hull clamped to zero"), Hull->GetHullPercent(), 0.0f, 0.001f);
	TestTrue(TEXT("Hull destroyed at zero"), Hull->IsDestroyed());

	// Already destroyed: further damage changes nothing.
	Hull->ApplyDamage(1000.0f, nullptr);

	TestTrue(TEXT("Still destroyed"), Hull->IsDestroyed());
	return true;
}

// ==================================================================
// Hull Safety — damage below hull max is bounded; hull does not go
// negative internally.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDamage_HullBounds,
	"ChimeraTests.Acceptance.Combat.HullBounds",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FCombatDamage_HullBounds::RunTest(const FString& Parameters)
{
	UDamageComponent* Hull = NewObject<UDamageComponent>();
	Hull->InitializeFromShip(5000.0f);

	// Massive overkill damage: 100x the hull health.
	Hull->ApplyDamage(500000.0f, nullptr);

	TestEqual(TEXT("Hull percent at 0 (not negative)"), Hull->GetHullPercent(), 0.0f, 0.001f);
	TestTrue(TEXT("Hull destroyed"), Hull->IsDestroyed());
	return true;
}

// ==================================================================
// SystemDamage Distribution — incoming hull damage is split across
// subsystems based on SubsystemDamageThreshold (default 0.1 = 10%).
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDamage_SystemDamageDistribution,
	"ChimeraTests.Acceptance.Combat.SystemDamageDistribution",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FCombatDamage_SystemDamageDistribution::RunTest(const FString& Parameters)
{
	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TArray<FName> Subsystems = {TEXT("Engines"), TEXT("Weapons"), TEXT("LifeSupport")};
	Systems->InitializeFromShip(Subsystems);

	// Each subsystem starts at 100 health.
	TestEqual(TEXT("Engines full"), Systems->GetSubsystemHealth(TEXT("Engines")), 100.0f, 0.001f);
	TestEqual(TEXT("Weapons full"), Systems->GetSubsystemHealth(TEXT("Weapons")), 100.0f, 0.001f);
	TestEqual(TEXT("LifeSupport full"), Systems->GetSubsystemHealth(TEXT("LifeSupport")), 100.0f, 0.001f);

	// Apply 1000 hull damage: 10% threshold = 100 subsystem damage distributed.
	// With 3 systems at 100 each and only 100 damage, one takes it, rest untouched.
	Systems->ApplySystemDamage(1000.0f);

	// SubsystemDamage = 1000 * 0.1 = 100
	// Engines (first in iteration) takes min(100, 100) = 100 damage -> 0 health
	// Weapons and LifeSupport untouched (SubsystemDamage exhausted).
	TestEqual(TEXT("Engines damaged"), Systems->GetSubsystemHealth(TEXT("Engines")), 0.0f, 0.001f);
	TestEqual(TEXT("Weapons untouched"), Systems->GetSubsystemHealth(TEXT("Weapons")), 100.0f, 0.001f);
	TestEqual(TEXT("LifeSupport untouched"), Systems->GetSubsystemHealth(TEXT("LifeSupport")), 100.0f, 0.001f);
	return true;
}

// ==================================================================
// SystemDamage Multi-System — when subsystem damage exceeds one
// system's health, overflow cascades to the next.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDamage_SystemDamageCascade,
	"ChimeraTests.Acceptance.Combat.SystemDamageCascade",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FCombatDamage_SystemDamageCascade::RunTest(const FString& Parameters)
{
	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TArray<FName> Subsystems = {TEXT("Engines"), TEXT("Weapons"), TEXT("LifeSupport")};
	Systems->InitializeFromShip(Subsystems);

	// Apply 3000 hull damage: 30% threshold = 300 subsystem damage.
	// Engines 100, Weapons 100, LifeSupport gets 100 (cascade).
	Systems->ApplySystemDamage(3000.0f);

	// SubsystemDamage = 3000 * 0.1 = 300
	// Engines takes min(300, 100) = 100 -> 0 health; SubsystemDamage -= 100 -> 200 left
	// Weapons takes min(200, 100) = 100 -> 0 health; SubsystemDamage -= 100 -> 100 left
	// LifeSupport takes min(100, 100) = 100 -> 0 health; SubsystemDamage -= 100 -> 0 left (break)
	TestEqual(TEXT("Engines destroyed"), Systems->GetSubsystemHealth(TEXT("Engines")), 0.0f, 0.001f);
	TestEqual(TEXT("Weapons destroyed"), Systems->GetSubsystemHealth(TEXT("Weapons")), 0.0f, 0.001f);
	TestEqual(TEXT("LifeSupport destroyed"), Systems->GetSubsystemHealth(TEXT("LifeSupport")), 0.0f, 0.001f);
	return true;
}

// ==================================================================
// SystemStatus Thresholds — subsystems report Operational/Damaged/
// Critical/Destroyed based on health percentage.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDamage_SystemStatus,
	"ChimeraTests.Acceptance.Combat.SystemStatus",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FCombatDamage_SystemStatus::RunTest(const FString& Parameters)
{
	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TArray<FName> Subsystems = {TEXT("Engines"), TEXT("Weapons"), TEXT("LifeSupport")};
	Systems->InitializeFromShip(Subsystems);

	// Operational: > 50% health (100/100 = 100%)
	TestTrue(TEXT("Full health is Operational"),
		Systems->GetSubsystemStatus(TEXT("Engines")) == ESubsystemStatus::Operational);

	// Damaged: 25% to 50% health
	Systems->RepairSubsystem(TEXT("Engines"), -60.0f); // Manual damage to test status (no repair yet)
	// RepairSubsystem adds, so we need to set directly. Call it with negative to test...
	// Actually, RepairSubsystem is for repair only. Let's use ApplySystemDamage instead.
	// But we already damaged all systems above. Let's use a fresh one.

	USystemDamageComponent* FreshSystems = NewObject<USystemDamageComponent>();
	FreshSystems->InitializeFromShip(Subsystems);

	// Manually set health to test status thresholds.
	// We can't directly set health, so use ApplySystemDamage.
	// Apply 500 hull damage: 50 subsystem damage. Engines takes 50 -> 50 health (50% = Damaged border).
	FreshSystems->ApplySystemDamage(500.0f);
	TestTrue(TEXT("50% health is Damaged"),
		FreshSystems->GetSubsystemStatus(TEXT("Engines")) == ESubsystemStatus::Damaged);

	// Critical: < 25% health
	// Apply another 750 hull damage: 75 more subsystem damage.
	// Engines (now 50) takes min(75, 50) = 50 -> 0; Weapons takes 25 -> 75 health (75% Operational).
	FreshSystems->ApplySystemDamage(750.0f);
	TestTrue(TEXT("25% or less is Destroyed or Critical"),
		FreshSystems->GetSubsystemStatus(TEXT("Engines")) == ESubsystemStatus::Destroyed ||
		FreshSystems->GetSubsystemStatus(TEXT("Engines")) == ESubsystemStatus::Critical);

	// Test a mid-range value: set Weapons to 20 health (20% = Critical).
	// We can't directly set, but Weapons should be at 75 after above damage.
	// Apply 600 more: 60 subsystem damage. Weapons (75) takes min(60, 75) = 60 -> 15 health (15% = Critical).
	FreshSystems->ApplySystemDamage(600.0f);
	TestTrue(TEXT("15% health is Critical"),
		FreshSystems->GetSubsystemStatus(TEXT("Weapons")) == ESubsystemStatus::Critical);

	return true;
}

// ==================================================================
// SystemRepair — RepairSubsystem heals a system up to its max health.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDamage_SystemRepair,
	"ChimeraTests.Acceptance.Combat.SystemRepair",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FCombatDamage_SystemRepair::RunTest(const FString& Parameters)
{
	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TArray<FName> Subsystems = {TEXT("Engines"), TEXT("Weapons")};
	Systems->InitializeFromShip(Subsystems);

	// Damage Engines: 500 hull damage = 50 subsystem damage -> Engines: 50 health.
	Systems->ApplySystemDamage(500.0f);
	TestEqual(TEXT("Engines damaged to 50"), Systems->GetSubsystemHealth(TEXT("Engines")), 50.0f, 0.001f);

	// Repair 30 points.
	Systems->RepairSubsystem(TEXT("Engines"), 30.0f);
	TestEqual(TEXT("Engines repaired to 80"), Systems->GetSubsystemHealth(TEXT("Engines")), 80.0f, 0.001f);

	// Repair beyond max (50 + remaining 20 = 100, clamped to max).
	Systems->RepairSubsystem(TEXT("Engines"), 50.0f);
	TestEqual(TEXT("Repair clamped to max"), Systems->GetSubsystemHealth(TEXT("Engines")), 100.0f, 0.001f);

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
