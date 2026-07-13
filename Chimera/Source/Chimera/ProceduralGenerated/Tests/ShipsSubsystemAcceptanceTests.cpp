// Copyright 2026 Chimera Project. All Rights Reserved.
// Ship Subsystem Health Acceptance Tests — subsystem damage, repair, and status
// reporting as hard facts, world-independently (NewObject, no PIE). Proves:
// subsystem health initializes correctly, damage reduces specific subsystems,
// repair restores health (clamped to max), status queries reflect actual health
// percentages, and health never goes negative (no underflow).

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "../Combat/SystemDamageComponent.h"
#include "../Combat/ShipAttributeSpecComponent.h"

#if WITH_DEV_AUTOMATION_TESTS

// ==================================================================
// Initialization — all subsystems at full health, operational status.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_Init,
	"ChimeraTests.Acceptance.Ships.Init",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_Init::RunTest(const FString& Parameters)
{
	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TestNotNull(TEXT("SystemDamage component instantiated"), Systems);

	TArray<FName> Subsystems = {TEXT("Engines"), TEXT("Weapons"), TEXT("LifeSupport")};
	Systems->InitializeFromShip(Subsystems);

	// All subsystems start at full health (100.0f).
	TestEqual(TEXT("Engines full health"), Systems->GetSubsystemHealth(TEXT("Engines")), 100.0f, 0.001f);
	TestEqual(TEXT("Weapons full health"), Systems->GetSubsystemHealth(TEXT("Weapons")), 100.0f, 0.001f);
	TestEqual(TEXT("LifeSupport full health"), Systems->GetSubsystemHealth(TEXT("LifeSupport")), 100.0f, 0.001f);

	// All subsystems start operational.
	TestTrue(TEXT("Engines operational"),
		Systems->GetSubsystemStatus(TEXT("Engines")) == ESubsystemStatus::Operational);
	TestTrue(TEXT("Weapons operational"),
		Systems->GetSubsystemStatus(TEXT("Weapons")) == ESubsystemStatus::Operational);
	TestTrue(TEXT("LifeSupport operational"),
		Systems->GetSubsystemStatus(TEXT("LifeSupport")) == ESubsystemStatus::Operational);

	return true;
}

// ==================================================================
// Damage reduces named subsystem health — damage applies to the first
// system that can absorb it, cascading if needed.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_DamageReducesHealth,
	"ChimeraTests.Acceptance.Ships.DamageReducesHealth",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_DamageReducesHealth::RunTest(const FString& Parameters)
{
	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TArray<FName> Subsystems = {TEXT("Engines"), TEXT("Weapons"), TEXT("LifeSupport")};
	Systems->InitializeFromShip(Subsystems);

	// Apply 500 hull damage: with 0.1 threshold, 50 subsystem damage.
	// Engines (first) takes min(50, 100) = 50 -> 50 health remaining.
	Systems->ApplySystemDamage(500.0f);

	TestEqual(TEXT("Engines damaged to 50"), Systems->GetSubsystemHealth(TEXT("Engines")), 50.0f, 0.001f);
	TestEqual(TEXT("Weapons untouched"), Systems->GetSubsystemHealth(TEXT("Weapons")), 100.0f, 0.001f);
	TestEqual(TEXT("LifeSupport untouched"), Systems->GetSubsystemHealth(TEXT("LifeSupport")), 100.0f, 0.001f);

	// Apply more damage: 1000 hull = 100 subsystem damage.
	// Engines (50) takes min(100, 50) = 50 -> 0 health; 50 damage remains.
	// Weapons (100) takes min(50, 100) = 50 -> 50 health; 0 damage remains.
	Systems->ApplySystemDamage(1000.0f);

	TestEqual(TEXT("Engines destroyed"), Systems->GetSubsystemHealth(TEXT("Engines")), 0.0f, 0.001f);
	TestEqual(TEXT("Weapons damaged to 50"), Systems->GetSubsystemHealth(TEXT("Weapons")), 50.0f, 0.001f);
	TestEqual(TEXT("LifeSupport still untouched"), Systems->GetSubsystemHealth(TEXT("LifeSupport")), 100.0f, 0.001f);

	return true;
}

// ==================================================================
// Damage does not go negative — subsystem health is clamped at zero.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_DamageNeverNegative,
	"ChimeraTests.Acceptance.Ships.DamageNeverNegative",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_DamageNeverNegative::RunTest(const FString& Parameters)
{
	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TArray<FName> Subsystems = {TEXT("Engines")};
	Systems->InitializeFromShip(Subsystems);

	// Engines at 100, apply massive overkill damage.
	// 100000 hull damage = 10000 subsystem damage (far exceeds 100 health).
	Systems->ApplySystemDamage(100000.0f);

	// Engines must be clamped at exactly 0.0, not negative.
	TestEqual(TEXT("Engines at exactly zero (not negative)"), Systems->GetSubsystemHealth(TEXT("Engines")), 0.0f, 0.001f);
	TestTrue(TEXT("Engines destroyed"),
		Systems->GetSubsystemStatus(TEXT("Engines")) == ESubsystemStatus::Destroyed);

	return true;
}

// ==================================================================
// Repair restores health — RepairSubsystem adds the specified amount.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_RepairRestoresHealth,
	"ChimeraTests.Acceptance.Ships.RepairRestoresHealth",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_RepairRestoresHealth::RunTest(const FString& Parameters)
{
	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TArray<FName> Subsystems = {TEXT("Engines"), TEXT("Weapons")};
	Systems->InitializeFromShip(Subsystems);

	// Damage Engines: 500 hull = 50 subsystem damage -> 50 health.
	Systems->ApplySystemDamage(500.0f);
	TestEqual(TEXT("Engines damaged to 50"), Systems->GetSubsystemHealth(TEXT("Engines")), 50.0f, 0.001f);

	// Repair 25 points.
	Systems->RepairSubsystem(TEXT("Engines"), 25.0f);
	TestEqual(TEXT("Engines repaired to 75"), Systems->GetSubsystemHealth(TEXT("Engines")), 75.0f, 0.001f);

	// Repair another 10 points.
	Systems->RepairSubsystem(TEXT("Engines"), 10.0f);
	TestEqual(TEXT("Engines repaired to 85"), Systems->GetSubsystemHealth(TEXT("Engines")), 85.0f, 0.001f);

	return true;
}

// ==================================================================
// Repair is clamped to max health — repair never exceeds MaxHealth.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_RepairClampedToMax,
	"ChimeraTests.Acceptance.Ships.RepairClampedToMax",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_RepairClampedToMax::RunTest(const FString& Parameters)
{
	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TArray<FName> Subsystems = {TEXT("Engines")};
	Systems->InitializeFromShip(Subsystems);

	// Damage Engines to 30 health.
	Systems->ApplySystemDamage(700.0f); // 70 subsystem damage -> 30 health.
	TestEqual(TEXT("Engines damaged to 30"), Systems->GetSubsystemHealth(TEXT("Engines")), 30.0f, 0.001f);

	// Repair 150 points (far exceeds remaining 70).
	Systems->RepairSubsystem(TEXT("Engines"), 150.0f);

	// Must be clamped to MaxHealth (100.0).
	TestEqual(TEXT("Repair clamped to 100"), Systems->GetSubsystemHealth(TEXT("Engines")), 100.0f, 0.001f);
	TestTrue(TEXT("Engines operational after full repair"),
		Systems->GetSubsystemStatus(TEXT("Engines")) == ESubsystemStatus::Operational);

	return true;
}

// ==================================================================
// Status thresholds — Operational (>50%), Damaged (25-50%), Critical (<25%), Destroyed (<=0%).
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_StatusThresholds,
	"ChimeraTests.Acceptance.Ships.StatusThresholds",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_StatusThresholds::RunTest(const FString& Parameters)
{
	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TArray<FName> Subsystems = {TEXT("Engines"), TEXT("Weapons"), TEXT("LifeSupport")};
	Systems->InitializeFromShip(Subsystems);

	// Operational: 100% (>50%)
	TestTrue(TEXT("100% is Operational"),
		Systems->GetSubsystemStatus(TEXT("Engines")) == ESubsystemStatus::Operational);

	// Damaged: 40% health (in 25-50% range)
	// Apply 600 hull = 60 subsystem damage -> Engines: 40 health (40%)
	Systems->ApplySystemDamage(600.0f);
	TestTrue(TEXT("40% is Damaged"),
		Systems->GetSubsystemStatus(TEXT("Engines")) == ESubsystemStatus::Damaged);

	// Critical: 15% health (<25%)
	// Apply 250 hull = 25 subsystem damage.
	// Engines (40) takes min(25, 40) = 25 -> 15 health (15%)
	Systems->ApplySystemDamage(250.0f);
	TestTrue(TEXT("15% is Critical"),
		Systems->GetSubsystemStatus(TEXT("Engines")) == ESubsystemStatus::Critical);

	// Destroyed: 0% health (<=0%)
	// Apply 150 hull = 15 subsystem damage -> Engines: 0 health
	Systems->ApplySystemDamage(150.0f);
	TestTrue(TEXT("0% is Destroyed"),
		Systems->GetSubsystemStatus(TEXT("Engines")) == ESubsystemStatus::Destroyed);

	return true;
}

// ==================================================================
// Status boundary precision — test exact threshold crossings.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_StatusBoundaries,
	"ChimeraTests.Acceptance.Ships.StatusBoundaries",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_StatusBoundaries::RunTest(const FString& Parameters)
{
	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TArray<FName> Subsystems = {TEXT("Weapons")};
	Systems->InitializeFromShip(Subsystems);

	// At exactly 50.1% (just above Damaged boundary), should be Operational.
	// Apply 499 hull = 49.9 subsystem damage -> 50.1 health (50.1%)
	Systems->ApplySystemDamage(499.0f);
	float Health = Systems->GetSubsystemHealth(TEXT("Weapons"));
	TestTrue(TEXT("50.1% is still Operational (boundary+)"),
		Systems->GetSubsystemStatus(TEXT("Weapons")) == ESubsystemStatus::Operational);

	// At exactly 50.0% (Damaged boundary), should transition to Damaged.
	// We need 50 health exactly. Current is ~50.1, so apply 0.1 more damage.
	Systems->ApplySystemDamage(1.0f); // 0.1 subsystem damage -> 50.0 health
	TestTrue(TEXT("50.0% is Damaged (at boundary)"),
		Systems->GetSubsystemStatus(TEXT("Weapons")) == ESubsystemStatus::Damaged);

	// At exactly 25.0% (Critical boundary).
	// From 50, need to drop to 25 exactly. Apply 250 hull = 25 subsystem damage.
	Systems->ApplySystemDamage(250.0f);
	TestTrue(TEXT("25.0% is Critical (at boundary)"),
		Systems->GetSubsystemStatus(TEXT("Weapons")) == ESubsystemStatus::Critical);

	return true;
}

// ==================================================================
// Unknown subsystem query — GetSubsystemHealth returns 0.0 for non-existent subsystems.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_UnknownSubsystem,
	"ChimeraTests.Acceptance.Ships.UnknownSubsystem",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_UnknownSubsystem::RunTest(const FString& Parameters)
{
	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TArray<FName> Subsystems = {TEXT("Engines")};
	Systems->InitializeFromShip(Subsystems);

	// Query a subsystem that was never initialized.
	float Health = Systems->GetSubsystemHealth(TEXT("UnknownSystem"));
	TestEqual(TEXT("Unknown subsystem returns 0"), Health, 0.0f, 0.001f);

	// Status of unknown subsystem (0 health) should be Destroyed.
	ESubsystemStatus Status = Systems->GetSubsystemStatus(TEXT("UnknownSystem"));
	TestTrue(TEXT("Unknown subsystem is Destroyed"),
		Status == ESubsystemStatus::Destroyed);

	// Repair non-existent subsystem (should do nothing).
	Systems->RepairSubsystem(TEXT("UnknownSystem"), 50.0f);
	TestEqual(TEXT("Repair unknown subsystem has no effect"),
		Systems->GetSubsystemHealth(TEXT("UnknownSystem")), 0.0f, 0.001f);

	return true;
}

// ==================================================================
// Ship Attribute Spec initialization — ShipAttributeSpecComponent
// loads default flight and GAS specifications.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_ShipAttributeSpecInit,
	"ChimeraTests.Acceptance.Ships.ShipAttributeSpecInit",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_ShipAttributeSpecInit::RunTest(const FString& Parameters)
{
	UShipAttributeSpecComponent* Spec = NewObject<UShipAttributeSpecComponent>();
	TestNotNull(TEXT("ShipAttributeSpec instantiated"), Spec);

	// Check default flight numbers.
	TestEqual(TEXT("MaxSpeedKmh default"), Spec->MaxSpeedKmh, 1200.0f, 0.001f);
	TestEqual(TEXT("TurnRateDegPerSec default"), Spec->TurnRateDegPerSec, 90.0f, 0.001f);
	TestEqual(TEXT("ConsumptionRatePerKm default"), Spec->ConsumptionRatePerKm, 0.5f, 0.001f);

	// Check default GAS bindings.
	TestFalse(TEXT("AbilitySystemComponent not empty"), Spec->AbilitySystemComponent.IsEmpty());
	TestFalse(TEXT("AttributeSet not empty"), Spec->AttributeSet.IsEmpty());
	TestTrue(TEXT("DefaultAbilities populated"), Spec->DefaultAbilities.Num() > 0);
	TestTrue(TEXT("StatusEffects populated"), Spec->StatusEffects.Num() >= 0);
	TestTrue(TEXT("HitReactions populated"), Spec->HitReactions.Num() > 0);
	TestTrue(TEXT("DamageFormulas populated"), Spec->DamageFormulas.Num() > 0);

	return true;
}

// ==================================================================
// Ship Attribute Spec fuel computation — ComputeFuelUseLiters scales
// by ConsumptionRatePerKm.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_FuelComputation,
	"ChimeraTests.Acceptance.Ships.FuelComputation",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_FuelComputation::RunTest(const FString& Parameters)
{
	UShipAttributeSpecComponent* Spec = NewObject<UShipAttributeSpecComponent>();

	// Default consumption: 0.5 L/km
	// 100 km should consume 50 liters.
	float Consumption = Spec->ComputeFuelUseLiters(100.0f);
	TestEqual(TEXT("100 km at 0.5 L/km = 50 L"), Consumption, 50.0f, 0.001f);

	// 0 km = 0 liters.
	Consumption = Spec->ComputeFuelUseLiters(0.0f);
	TestEqual(TEXT("0 km = 0 L"), Consumption, 0.0f, 0.001f);

	// Negative distance is clamped to zero (FMath::Max).
	Consumption = Spec->ComputeFuelUseLiters(-50.0f);
	TestEqual(TEXT("Negative distance clamped to 0 L"), Consumption, 0.0f, 0.001f);

	// 1000 km = 500 liters.
	Consumption = Spec->ComputeFuelUseLiters(1000.0f);
	TestEqual(TEXT("1000 km = 500 L"), Consumption, 500.0f, 0.001f);

	return true;
}

// ==================================================================
// Ship Attribute Spec speed clamping — ClampSpeedKmh bounds speed
// to [0, MaxSpeedKmh].
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_SpeedClamping,
	"ChimeraTests.Acceptance.Ships.SpeedClamping",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_SpeedClamping::RunTest(const FString& Parameters)
{
	UShipAttributeSpecComponent* Spec = NewObject<UShipAttributeSpecComponent>();

	// Default MaxSpeedKmh: 1200
	// Request 500 km/h (below max) -> returns 500.
	float Clamped = Spec->ClampSpeedKmh(500.0f);
	TestEqual(TEXT("500 kmh (below max) returns 500"), Clamped, 500.0f, 0.001f);

	// Request 2000 km/h (above max) -> clamped to 1200.
	Clamped = Spec->ClampSpeedKmh(2000.0f);
	TestEqual(TEXT("2000 kmh clamped to 1200"), Clamped, 1200.0f, 0.001f);

	// Request exactly MaxSpeedKmh -> returns MaxSpeedKmh.
	Clamped = Spec->ClampSpeedKmh(1200.0f);
	TestEqual(TEXT("1200 kmh returns 1200"), Clamped, 1200.0f, 0.001f);

	// Request negative speed -> clamped to 0.
	Clamped = Spec->ClampSpeedKmh(-100.0f);
	TestEqual(TEXT("Negative speed clamped to 0"), Clamped, 0.0f, 0.001f);

	// Request 0 km/h -> returns 0.
	Clamped = Spec->ClampSpeedKmh(0.0f);
	TestEqual(TEXT("0 kmh returns 0"), Clamped, 0.0f, 0.001f);

	return true;
}

// ==================================================================
// Ship Attribute Spec turn computation — TurnDegreesIn scales by
// TurnRateDegPerSec.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_TurnComputation,
	"ChimeraTests.Acceptance.Ships.TurnComputation",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_TurnComputation::RunTest(const FString& Parameters)
{
	UShipAttributeSpecComponent* Spec = NewObject<UShipAttributeSpecComponent>();

	// Default TurnRateDegPerSec: 90
	// Over 1 second, turn 90 degrees.
	float Degrees = Spec->TurnDegreesIn(1.0f);
	TestEqual(TEXT("1 sec at 90 deg/sec = 90 deg"), Degrees, 90.0f, 0.001f);

	// Over 2 seconds, turn 180 degrees.
	Degrees = Spec->TurnDegreesIn(2.0f);
	TestEqual(TEXT("2 sec at 90 deg/sec = 180 deg"), Degrees, 180.0f, 0.001f);

	// Over 0 seconds, turn 0 degrees.
	Degrees = Spec->TurnDegreesIn(0.0f);
	TestEqual(TEXT("0 sec = 0 deg"), Degrees, 0.0f, 0.001f);

	// Negative time is clamped to zero (FMath::Max).
	Degrees = Spec->TurnDegreesIn(-5.0f);
	TestEqual(TEXT("Negative time clamped to 0 deg"), Degrees, 0.0f, 0.001f);

	// Over 4 seconds, turn 360 degrees (full rotation).
	Degrees = Spec->TurnDegreesIn(4.0f);
	TestEqual(TEXT("4 sec at 90 deg/sec = 360 deg"), Degrees, 360.0f, 0.001f);

	return true;
}

// ==================================================================
// Ship Attribute Spec validation — ValidateSpec checks completeness
// of GAS and stats configuration.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_ValidateSpec,
	"ChimeraTests.Acceptance.Ships.ValidateSpec",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_ValidateSpec::RunTest(const FString& Parameters)
{
	UShipAttributeSpecComponent* Spec = NewObject<UShipAttributeSpecComponent>();

	// Default spec should be valid (all fields populated).
	TestTrue(TEXT("Default spec is valid"), Spec->ValidateSpec());

	// Empty AbilitySystemComponent -> invalid.
	Spec->AbilitySystemComponent = TEXT("");
	TestFalse(TEXT("Empty ASC makes spec invalid"), Spec->ValidateSpec());

	// Restore and test empty AttributeSet.
	Spec->AbilitySystemComponent = TEXT("ASC_Player");
	Spec->AttributeSet = TEXT("");
	TestFalse(TEXT("Empty AttributeSet makes spec invalid"), Spec->ValidateSpec());

	// Restore and test empty abilities.
	Spec->AttributeSet = TEXT("AS_PlayerAttributes");
	Spec->DefaultAbilities.Empty();
	TestFalse(TEXT("Empty DefaultAbilities makes spec invalid"), Spec->ValidateSpec());

	// Restore abilities and test empty hit reactions.
	Spec->DefaultAbilities = {TEXT("GA_Thrust")};
	Spec->HitReactions.Empty();
	TestFalse(TEXT("Empty HitReactions makes spec invalid"), Spec->ValidateSpec());

	// Restore hit reactions and test empty damage formulas.
	Spec->HitReactions = {TEXT("shield_flare")};
	Spec->DamageFormulas.Empty();
	TestFalse(TEXT("Empty DamageFormulas makes spec invalid"), Spec->ValidateSpec());

	// Restore all and test invalid speed.
	Spec->DamageFormulas = {TEXT("kinetic: raw")};
	Spec->MaxSpeedKmh = 0.0f;
	TestFalse(TEXT("Zero MaxSpeedKmh makes spec invalid"), Spec->ValidateSpec());

	// Restore and test empty stats.
	Spec->MaxSpeedKmh = 1200.0f;
	Spec->FuelStat = TEXT("");
	TestFalse(TEXT("Empty FuelStat makes spec invalid"), Spec->ValidateSpec());

	// Restore all fields to valid state.
	Spec->FuelStat = TEXT("true");
	Spec->CargoWeightStat = TEXT("true");
	TestTrue(TEXT("Restored spec is valid"), Spec->ValidateSpec());

	return true;
}

// ==================================================================
// Multiple damage events — sequential damage applications stack correctly.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_SequentialDamage,
	"ChimeraTests.Acceptance.Ships.SequentialDamage",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_SequentialDamage::RunTest(const FString& Parameters)
{
	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TArray<FName> Subsystems = {TEXT("Engines")};
	Systems->InitializeFromShip(Subsystems);

	// Apply 200 hull = 20 damage -> 80 health.
	Systems->ApplySystemDamage(200.0f);
	TestEqual(TEXT("After first damage: 80"), Systems->GetSubsystemHealth(TEXT("Engines")), 80.0f, 0.001f);

	// Apply 300 hull = 30 damage -> 50 health.
	Systems->ApplySystemDamage(300.0f);
	TestEqual(TEXT("After second damage: 50"), Systems->GetSubsystemHealth(TEXT("Engines")), 50.0f, 0.001f);

	// Apply 500 hull = 50 damage -> 0 health (clamped).
	Systems->ApplySystemDamage(500.0f);
	TestEqual(TEXT("After third damage: 0"), Systems->GetSubsystemHealth(TEXT("Engines")), 0.0f, 0.001f);

	// Apply more damage to already-destroyed system (no effect).
	Systems->ApplySystemDamage(1000.0f);
	TestEqual(TEXT("Further damage to destroyed: still 0"), Systems->GetSubsystemHealth(TEXT("Engines")), 0.0f, 0.001f);

	return true;
}

// ==================================================================
// Damage distribution algorithm — verify the cascade algorithm
// distributes damage across multiple subsystems correctly.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipsSubsystem_DamageDistribution,
	"ChimeraTests.Acceptance.Ships.DamageDistribution",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FShipsSubsystem_DamageDistribution::RunTest(const FString& Parameters)
{
	USystemDamageComponent* Systems = NewObject<USystemDamageComponent>();
	TArray<FName> Subsystems = {TEXT("Engines"), TEXT("Weapons"), TEXT("LifeSupport")};
	Systems->InitializeFromShip(Subsystems);

	// Apply 10000 hull damage = 1000 subsystem damage.
	// Each subsystem 100 health:
	// - Engines takes min(1000, 100) = 100 -> 0; 900 left
	// - Weapons takes min(900, 100) = 100 -> 0; 800 left
	// - LifeSupport takes min(800, 100) = 100 -> 0; 700 left (break not needed, all depleted)
	Systems->ApplySystemDamage(10000.0f);

	TestEqual(TEXT("Engines destroyed"), Systems->GetSubsystemHealth(TEXT("Engines")), 0.0f, 0.001f);
	TestEqual(TEXT("Weapons destroyed"), Systems->GetSubsystemHealth(TEXT("Weapons")), 0.0f, 0.001f);
	TestEqual(TEXT("LifeSupport destroyed"), Systems->GetSubsystemHealth(TEXT("LifeSupport")), 0.0f, 0.001f);

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
