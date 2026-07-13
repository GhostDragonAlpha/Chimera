// Copyright 2026 Chimera Project. All Rights Reserved.
// Suit Life-Support Acceptance Tests — the EVA survival loop as hard facts,
// world-independently (NewObject, no PIE). Proves the seed's USuitAttributeSet
// behaviour: O2 drains by exertion, regenerates in a garden, the suit dies at 0,
// the low-O2 alarm fires on its threshold edge, and storms clog / shelters scrub.

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "../Suit/SuitLifeSupportComponent.h"

#if WITH_DEV_AUTOMATION_TESTS

// ==================================================================
// Initialization — full tank, seed rates, alive.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSuitLifeSupport_Init,
	"ChimeraTests.Acceptance.SuitLifeSupport.Init",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FSuitLifeSupport_Init::RunTest(const FString& Parameters)
{
	USuitLifeSupportComponent* Suit = NewObject<USuitLifeSupportComponent>();
	TestNotNull(TEXT("Suit instantiated"), Suit);
	Suit->ResetLifeSupport();

	TestEqual(TEXT("O2 full"), Suit->O2, 100.0f);
	TestEqual(TEXT("MaxO2"), Suit->MaxO2, 100.0f);
	TestEqual(TEXT("Battery full"), Suit->Battery, 100.0f);
	TestEqual(TEXT("DustClog empty"), Suit->DustClog, 0.0f);
	TestFalse(TEXT("not dead"), Suit->IsDead());
	TestFalse(TEXT("not low-O2"), Suit->IsLowO2());
	TestTrue(TEXT("walk drain positive"), Suit->O2DrainWalkPerMin > 0.0f);
	TestTrue(TEXT("sprint drains harder than walk than idle"),
		Suit->O2DrainSprintPerMin > Suit->O2DrainWalkPerMin &&
		Suit->O2DrainWalkPerMin > Suit->O2DrainIdlePerMin);
	return true;
}

// ==================================================================
// O2 drains by exertion — the core survival clock. Walking one game-minute
// spends exactly the walk rate; sprinting spends more than idling.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSuitLifeSupport_O2DrainByExertion,
	"ChimeraTests.Acceptance.SuitLifeSupport.O2DrainByExertion",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FSuitLifeSupport_O2DrainByExertion::RunTest(const FString& Parameters)
{
	// Walk one game-minute (60 s) -> O2 drops by exactly the walk rate (1.0).
	USuitLifeSupportComponent* Walker = NewObject<USuitLifeSupportComponent>();
	Walker->ResetLifeSupport();
	Walker->bOverrideExertion = true;
	Walker->SetExertion(ESuitExertion::Walk);
	Walker->AdvanceLifeSupport(60.0f);
	TestEqual(TEXT("walk 60s spends ~1.0 O2"), Walker->O2, 99.0f, 0.05f);
	TestTrue(TEXT("O2 actually decreased"), Walker->O2 < 100.0f);

	// Sprinting outspends idling over the same minute.
	USuitLifeSupportComponent* Sprinter = NewObject<USuitLifeSupportComponent>();
	Sprinter->ResetLifeSupport();
	Sprinter->bOverrideExertion = true;
	Sprinter->SetExertion(ESuitExertion::Sprint);
	Sprinter->AdvanceLifeSupport(60.0f);

	USuitLifeSupportComponent* Idler = NewObject<USuitLifeSupportComponent>();
	Idler->ResetLifeSupport();
	Idler->bOverrideExertion = true;
	Idler->SetExertion(ESuitExertion::Idle);
	Idler->AdvanceLifeSupport(60.0f);

	TestTrue(TEXT("sprint burns more O2 than idle"), Sprinter->O2 < Idler->O2);
	TestTrue(TEXT("idle still burns some O2"), Idler->O2 < 100.0f);
	return true;
}

// ==================================================================
// Death at zero O2 — the suit fails once, and only once.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSuitLifeSupport_DeathAtZero,
	"ChimeraTests.Acceptance.SuitLifeSupport.DeathAtZero",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FSuitLifeSupport_DeathAtZero::RunTest(const FString& Parameters)
{
	USuitLifeSupportComponent* Suit = NewObject<USuitLifeSupportComponent>();
	Suit->ResetLifeSupport();
	Suit->SetO2(1.0f);                 // one breath left
	Suit->bOverrideExertion = true;
	Suit->SetExertion(ESuitExertion::Sprint); // 3.0/min -> overruns in a minute
	TestFalse(TEXT("alive before"), Suit->IsDead());

	Suit->AdvanceLifeSupport(60.0f);
	TestTrue(TEXT("dead after O2 hit zero"), Suit->IsDead());
	TestEqual(TEXT("O2 clamped to zero"), Suit->O2, 0.0f);
	TestEqual(TEXT("depletion counted once"), Suit->TimesDepleted, 1);

	// Already dead: further advance must not re-fire the death edge.
	Suit->AdvanceLifeSupport(60.0f);
	TestEqual(TEXT("still one depletion"), Suit->TimesDepleted, 1);
	return true;
}

// ==================================================================
// Low-O2 alarm edge — fires crossing 25%, clears when refilled.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSuitLifeSupport_LowO2Edge,
	"ChimeraTests.Acceptance.SuitLifeSupport.LowO2Edge",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FSuitLifeSupport_LowO2Edge::RunTest(const FString& Parameters)
{
	USuitLifeSupportComponent* Suit = NewObject<USuitLifeSupportComponent>();
	Suit->ResetLifeSupport();
	TestFalse(TEXT("not low at full"), Suit->IsLowO2());

	Suit->SetO2(20.0f);               // below the 25 threshold
	TestTrue(TEXT("alarm on below threshold"), Suit->IsLowO2());

	Suit->SetO2(50.0f);               // refilled above threshold
	TestFalse(TEXT("alarm clears above threshold"), Suit->IsLowO2());

	TestEqual(TEXT("O2 fraction tracks value"), Suit->GetO2Fraction(), 0.5f, 0.001f);
	return true;
}

// ==================================================================
// Environment: oxygen garden regenerates, storms clog, shelters scrub.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSuitLifeSupport_Environment,
	"ChimeraTests.Acceptance.SuitLifeSupport.Environment",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FSuitLifeSupport_Environment::RunTest(const FString& Parameters)
{
	// Oxygen garden regen outpaces idle drain -> O2 climbs.
	USuitLifeSupportComponent* Garden = NewObject<USuitLifeSupportComponent>();
	Garden->ResetLifeSupport();
	Garden->SetO2(50.0f);
	Garden->bOverrideExertion = true;
	Garden->SetExertion(ESuitExertion::Idle);
	Garden->bAtOxygenGarden = true;
	Garden->AdvanceLifeSupport(60.0f);
	TestTrue(TEXT("garden regen raises O2 above idle drain"), Garden->O2 > 50.0f);

	// Storm exposure clogs the suit; then shelter scrubs it back down.
	USuitLifeSupportComponent* Storm = NewObject<USuitLifeSupportComponent>();
	Storm->ResetLifeSupport();
	Storm->bExposedToStorm = true;
	Storm->AdvanceLifeSupport(60.0f);
	const float CloggedTo = Storm->DustClog;
	TestTrue(TEXT("storm clogs the suit"), CloggedTo > 3.9f);

	Storm->bExposedToStorm = false;
	Storm->bInShelter = true;
	Storm->AdvanceLifeSupport(60.0f);
	TestTrue(TEXT("shelter scrubs dust back down"), Storm->DustClog < CloggedTo);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
