// Copyright 2026 Chimera Project. All Rights Reserved.
// Mission System Acceptance Tests — hardwired DSL mission board as hard facts,
// world-independently (NewObject, no PIE). Proves the seed's UMissionComponent
// behaviour: InitializeMissionBoardFromDSL populates the board; accepting a
// mission moves it to active; UpdateObjective advances progress; completing all
// objectives removes the mission from active and adds it to completed.

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "../Missions/MissionComponent.h"

#if WITH_DEV_AUTOMATION_TESTS

// ==================================================================
// Initialization — DSL board loads three hardwired missions available.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMission_Init,
	"ChimeraTests.Acceptance.Missions.Init",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FMission_Init::RunTest(const FString& Parameters)
{
	UMissionComponent* Board = NewObject<UMissionComponent>();
	TestNotNull(TEXT("Mission board instantiated"), Board);

	TestEqual(TEXT("Available missions initially empty"), Board->AvailableMissions.Num(), 0);
	TestEqual(TEXT("Active missions initially empty"), Board->ActiveMissions.Num(), 0);
	TestEqual(TEXT("Completed missions initially empty"), Board->CompletedMissions.Num(), 0);

	Board->InitializeMissionBoardFromDSL();

	TestEqual(TEXT("DSL loads three available missions"), Board->AvailableMissions.Num(), 3);
	TestEqual(TEXT("Active still empty after DSL load"), Board->ActiveMissions.Num(), 0);

	// Verify the first mission (Delivery_Titanium_Batch_1) exists and has correct properties
	const FMissionData& M1 = Board->AvailableMissions[0];
	TestEqual(TEXT("First mission ID"), M1.MissionID, FName(TEXT("Delivery_Titanium_Batch_1")));
	TestEqual(TEXT("First mission type"), M1.Type, FString(TEXT("delivery")));
	TestEqual(TEXT("First mission reward"), M1.RewardCredits, 25000.0f);
	TestEqual(TEXT("First mission faction"), M1.FactionID, FName(TEXT("faction_titan_miners")));
	TestTrue(TEXT("First mission has objectives"), M1.Objectives.Num() > 0);

	return true;
}

// ==================================================================
// Accept a mission — move it from available to active.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMission_Accept,
	"ChimeraTests.Acceptance.Missions.Accept",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FMission_Accept::RunTest(const FString& Parameters)
{
	UMissionComponent* Board = NewObject<UMissionComponent>();
	Board->InitializeMissionBoardFromDSL();

	TestEqual(TEXT("Start with three available"), Board->AvailableMissions.Num(), 3);
	TestEqual(TEXT("No active missions yet"), Board->ActiveMissions.Num(), 0);

	// Accept the first mission
	FName MissionID = Board->AvailableMissions[0].MissionID;
	Board->AcceptMission(MissionID);

	TestEqual(TEXT("Available missions decreased"), Board->AvailableMissions.Num(), 2);
	TestEqual(TEXT("Active missions increased"), Board->ActiveMissions.Num(), 1);

	// Verify the accepted mission is in active
	FMissionData AcceptedMission = Board->ActiveMissions[0];
	TestEqual(TEXT("Accepted mission has correct ID"), AcceptedMission.MissionID, MissionID);
	TestEqual(TEXT("Accepted mission status is Active"), AcceptedMission.Status, FString(TEXT("Active")));

	// Accept another mission
	FName SecondID = Board->AvailableMissions[0].MissionID;
	Board->AcceptMission(SecondID);

	TestEqual(TEXT("Available down to one"), Board->AvailableMissions.Num(), 1);
	TestEqual(TEXT("Active now has two"), Board->ActiveMissions.Num(), 2);

	return true;
}

// ==================================================================
// Update objectives — complete one objective, then all objectives.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMission_UpdateObjective,
	"ChimeraTests.Acceptance.Missions.UpdateObjective",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FMission_UpdateObjective::RunTest(const FString& Parameters)
{
	UMissionComponent* Board = NewObject<UMissionComponent>();
	Board->InitializeMissionBoardFromDSL();

	// Accept the first mission: Delivery_Titanium_Batch_1
	// It has two objectives: Deliver Titanium, then Dock
	FName MissionID = FName(TEXT("Delivery_Titanium_Batch_1"));
	Board->AcceptMission(MissionID);

	TestEqual(TEXT("One active mission"), Board->ActiveMissions.Num(), 1);
	const FMissionData& Mission = Board->ActiveMissions[0];
	TestEqual(TEXT("Two objectives in mission"), Mission.Objectives.Num(), 2);
	TestEqual(TEXT("CurrentObjectiveIndex starts at 0"), Mission.CurrentObjectiveIndex, 0);

	// First objective is Deliver Titanium
	TestEqual(TEXT("First objective type is Deliver"), Mission.Objectives[0].Type, FString(TEXT("Deliver")));
	TestEqual(TEXT("First objective commodity is Titanium"), Mission.Objectives[0].Commodity, FName(TEXT("Titanium")));
	TestFalse(TEXT("First objective not complete yet"), Mission.Objectives[0].bComplete);

	// Complete the first objective (deliver titanium)
	Board->UpdateObjective(FString(TEXT("Deliver")), FString(TEXT("Titanium")));

	TestEqual(TEXT("Mission still active after first objective"), Board->ActiveMissions.Num(), 1);
	TestEqual(TEXT("Mission not yet completed"), Board->CompletedMissions.Num(), 0);

	const FMissionData& MissionAfter1 = Board->ActiveMissions[0];
	TestTrue(TEXT("First objective now complete"), MissionAfter1.Objectives[0].bComplete);
	TestEqual(TEXT("CurrentObjectiveIndex advanced to 1"), MissionAfter1.CurrentObjectiveIndex, 1);
	TestFalse(TEXT("Second objective still incomplete"), MissionAfter1.Objectives[1].bComplete);

	// Complete the second objective (dock)
	Board->UpdateObjective(FString(TEXT("Dock")), FString(TEXT("")));

	TestEqual(TEXT("Mission removed from active after all objectives"), Board->ActiveMissions.Num(), 0);
	TestEqual(TEXT("Mission added to completed"), Board->CompletedMissions.Num(), 1);
	TestEqual(TEXT("Completed mission ID correct"), Board->CompletedMissions[0], MissionID);

	return true;
}

// ==================================================================
// Multiple missions active — update one without affecting others.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMission_MultipleActive,
	"ChimeraTests.Acceptance.Missions.MultipleActive",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FMission_MultipleActive::RunTest(const FString& Parameters)
{
	UMissionComponent* Board = NewObject<UMissionComponent>();
	Board->InitializeMissionBoardFromDSL();

	// Accept all three missions
	FName Mission1 = FName(TEXT("Delivery_Titanium_Batch_1"));
	FName Mission2 = FName(TEXT("Smuggle_Quantum_Cores"));
	FName Mission3 = FName(TEXT("Escort_Convoy"));

	Board->AcceptMission(Mission1);
	Board->AcceptMission(Mission2);
	Board->AcceptMission(Mission3);

	TestEqual(TEXT("Three active missions"), Board->ActiveMissions.Num(), 3);
	TestEqual(TEXT("No available missions left"), Board->AvailableMissions.Num(), 0);

	// Complete mission 1 (Titanium delivery)
	Board->UpdateObjective(FString(TEXT("Deliver")), FString(TEXT("Titanium")));
	Board->UpdateObjective(FString(TEXT("Dock")), FString(TEXT("")));

	TestEqual(TEXT("Two active missions after completing one"), Board->ActiveMissions.Num(), 2);
	TestEqual(TEXT("One mission completed"), Board->CompletedMissions.Num(), 1);
	TestEqual(TEXT("Completed mission is #1"), Board->CompletedMissions[0], Mission1);

	// Verify the other two are still active
	bool bHasMission2 = false;
	bool bHasMission3 = false;
	for (const FMissionData& M : Board->ActiveMissions)
	{
		if (M.MissionID == Mission2) bHasMission2 = true;
		if (M.MissionID == Mission3) bHasMission3 = true;
	}
	TestTrue(TEXT("Mission 2 still active"), bHasMission2);
	TestTrue(TEXT("Mission 3 still active"), bHasMission3);

	return true;
}

// ==================================================================
// Objective matching — Deliver objectives match on commodity parameter,
// Dock objectives match on type alone.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMission_ObjectiveMatching,
	"ChimeraTests.Acceptance.Missions.ObjectiveMatching",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FMission_ObjectiveMatching::RunTest(const FString& Parameters)
{
	UMissionComponent* Board = NewObject<UMissionComponent>();
	Board->InitializeMissionBoardFromDSL();

	// Accept the smuggling mission (Smuggle_Quantum_Cores)
	// Objectives: Deliver Quantum_Cores, then Dock
	Board->AcceptMission(FName(TEXT("Smuggle_Quantum_Cores")));

	// Try to update with wrong commodity — should not advance
	Board->UpdateObjective(FString(TEXT("Deliver")), FString(TEXT("Titanium")));
	TestEqual(TEXT("Wrong commodity doesn't advance"), Board->ActiveMissions.Num(), 1);
	TestEqual(TEXT("No missions completed on wrong commodity"), Board->CompletedMissions.Num(), 0);
	TestFalse(TEXT("First objective still incomplete"), Board->ActiveMissions[0].Objectives[0].bComplete);

	// Update with correct commodity
	Board->UpdateObjective(FString(TEXT("Deliver")), FString(TEXT("Quantum_Cores")));
	TestTrue(TEXT("Correct commodity completes objective"), Board->ActiveMissions[0].Objectives[0].bComplete);
	TestEqual(TEXT("Still active (second objective pending)"), Board->ActiveMissions.Num(), 1);

	// Dock objective matches on type alone (no parameter matching)
	Board->UpdateObjective(FString(TEXT("Dock")), FString(TEXT("")));
	TestEqual(TEXT("Mission complete after dock"), Board->ActiveMissions.Num(), 0);
	TestEqual(TEXT("Mission in completed"), Board->CompletedMissions.Num(), 1);

	return true;
}

// ==================================================================
// Edge case: Trying to accept a non-existent mission does nothing.
// ==================================================================
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMission_AcceptNonExistent,
	"ChimeraTests.Acceptance.Missions.AcceptNonExistent",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FMission_AcceptNonExistent::RunTest(const FString& Parameters)
{
	UMissionComponent* Board = NewObject<UMissionComponent>();
	Board->InitializeMissionBoardFromDSL();

	TestEqual(TEXT("Three available initially"), Board->AvailableMissions.Num(), 3);
	TestEqual(TEXT("No active initially"), Board->ActiveMissions.Num(), 0);

	// Try to accept a mission that doesn't exist
	Board->AcceptMission(FName(TEXT("NonExistent_Mission")));

	TestEqual(TEXT("Available count unchanged"), Board->AvailableMissions.Num(), 3);
	TestEqual(TEXT("Active count unchanged"), Board->ActiveMissions.Num(), 0);

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
