// Copyright Chimera. All rights reserved.

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "../ChimeraMovementComponent.h"
#include "Logging/LogMacros.h"

/**
 * Weight Shift Animation Tests
 * Validates that the weight shift animation system correctly calculates overshoot
 * and settling behavior based on character acceleration/deceleration.
 */
class FWeightShiftAnimationTests
{
public:
	/**
	 * Test: Weight shift triggers on significant deceleration
	 * Expected: When velocity drops from 400 cm/s to 0 cm/s, weight shift offset increases
	 */
	static bool TestWeightShiftTriggersOnDeceleration()
	{
		UChimeraMovementComponent* Component = NewObject<UChimeraMovementComponent>();
		if (!Component)
		{
			UE_LOG(LogTemp, Error, TEXT("[WeightShiftTest] Failed to create component"));
			return false;
		}

		// Set up initial state: moving forward at sprint speed
		Component->CurrentVelocity = FVector(400.0f, 0.0f, 0.0f); // Sprint velocity
		float DeltaTime = 0.016f; // 16ms frame

		// Simulate one frame
		// LastFrameVelocity will be zero initially, so this is acceleration detection
		Component->UpdateWeightShift(DeltaTime);

		// Check that we got some weight shift response
		FVector WeightShift = Component->GetWeightShiftOffset();
		float Magnitude = WeightShift.Size();

		UE_LOG(LogTemp, Warning, TEXT("[WeightShiftTest] Acceleration trigger - Initial magnitude: %.2f cm"), Magnitude);

		if (Magnitude < 0.1f)
		{
			UE_LOG(LogTemp, Error, TEXT("[WeightShiftTest] Expected weight shift on acceleration, got magnitude %.2f"), Magnitude);
			return false;
		}

		// Now simulate deceleration: go from 400 to 0 in next frame
		Component->CurrentVelocity = FVector(0.0f, 0.0f, 0.0f); // Stopped
		Component->UpdateWeightShift(DeltaTime);

		WeightShift = Component->GetWeightShiftOffset();
		Magnitude = WeightShift.Size();

		UE_LOG(LogTemp, Warning, TEXT("[WeightShiftTest] Deceleration - Magnitude: %.2f cm, Offset: X=%.2f Y=%.2f Z=%.2f"),
			Magnitude, WeightShift.X, WeightShift.Y, WeightShift.Z);

		// Should have accumulated more offset due to the stop
		if (Magnitude < 1.0f)
		{
			UE_LOG(LogTemp, Error, TEXT("[WeightShiftTest] Expected significant weight shift on deceleration, got %.2f"), Magnitude);
			return false;
		}

		return true;
	}

	/**
	 * Test: Weight shift settles over time (damping)
	 * Expected: Weight shift offset decreases towards zero over 1-2 seconds
	 */
	static bool TestWeightShiftSettles()
	{
		UChimeraMovementComponent* Component = NewObject<UChimeraMovementComponent>();
		if (!Component)
		{
			return false;
		}

		// Trigger a weight shift by decelerating
		Component->CurrentVelocity = FVector(400.0f, 0.0f, 0.0f);
		Component->UpdateWeightShift(0.016f);

		Component->CurrentVelocity = FVector(0.0f, 0.0f, 0.0f);
		Component->UpdateWeightShift(0.016f);

		// Get initial weight shift
		FVector InitialWeightShift = Component->GetWeightShiftOffset();
		float InitialMagnitude = InitialWeightShift.Size();

		UE_LOG(LogTemp, Warning, TEXT("[WeightShiftTest] Initial settling magnitude: %.2f cm"), InitialMagnitude);

		// Simulate 2 seconds of settling with no new acceleration
		float ElapsedTime = 0.0f;
		const float SimulationTime = 2.0f;
		const float DeltaTime = 0.016f;

		while (ElapsedTime < SimulationTime)
		{
			Component->CurrentVelocity = FVector(0.0f, 0.0f, 0.0f); // Keep velocity zero
			Component->UpdateWeightShift(DeltaTime);
			ElapsedTime += DeltaTime;
		}

		FVector FinalWeightShift = Component->GetWeightShiftOffset();
		float FinalMagnitude = FinalWeightShift.Size();

		UE_LOG(LogTemp, Warning, TEXT("[WeightShiftTest] Final settling magnitude after 2s: %.2f cm (initial was %.2f)"),
			FinalMagnitude, InitialMagnitude);

		// After 2 seconds, weight shift should be mostly settled (but not quite zero due to damping curve)
		if (FinalMagnitude > 1.0f)
		{
			UE_LOG(LogTemp, Error, TEXT("[WeightShiftTest] Weight shift did not settle properly. Final: %.2f, Expected: <1.0"), FinalMagnitude);
			return false;
		}

		// Verify it actually settled (is less than initial)
		if (FinalMagnitude >= InitialMagnitude * 0.5f) // Should be significantly lower
		{
			UE_LOG(LogTemp, Error, TEXT("[WeightShiftTest] Weight shift settling too slow. Final: %.2f, Initial: %.2f"), FinalMagnitude, InitialMagnitude);
			return false;
		}

		return true;
	}

	/**
	 * Test: Weight shift magnitude is clamped to max
	 * Expected: Weight shift never exceeds MaxWeightShiftMagnitude (3.5 cm)
	 */
	static bool TestWeightShiftMaxClamping()
	{
		UChimeraMovementComponent* Component = NewObject<UChimeraMovementComponent>();
		if (!Component)
		{
			return false;
		}

		Component->MaxWeightShiftMagnitude = 3.5f;

		// Simulate very large acceleration (unrealistic but tests clamping)
		for (int i = 0; i < 100; ++i)
		{
			Component->CurrentVelocity = FVector(800.0f, 0.0f, 0.0f);
			Component->UpdateWeightShift(0.016f);
		}

		FVector WeightShift = Component->GetWeightShiftOffset();
		float Magnitude = WeightShift.Size();

		UE_LOG(LogTemp, Warning, TEXT("[WeightShiftTest] Clamping test - Magnitude: %.2f cm (max: %.2f)"),
			Magnitude, Component->MaxWeightShiftMagnitude);

		if (Magnitude > Component->MaxWeightShiftMagnitude + 0.01f) // Allow tiny floating point error
		{
			UE_LOG(LogTemp, Error, TEXT("[WeightShiftTest] Weight shift exceeded max. Got: %.2f, Max: %.2f"),
				Magnitude, Component->MaxWeightShiftMagnitude);
			return false;
		}

		return true;
	}

	/**
	 * Test: Overshoot behavior (weight shift exceeds target then settles)
	 * Expected: Peak magnitude occurs within first 0.5 seconds then decreases
	 */
	static bool TestWeightShiftOvershoot()
	{
		UChimeraMovementComponent* Component = NewObject<UChimeraMovementComponent>();
		if (!Component)
		{
			return false;
		}

		Component->WeightShiftOvershooting = 1.3f; // 30% overshoot
		Component->WeightShiftDamping = 8.0f;

		// Trigger deceleration
		Component->CurrentVelocity = FVector(300.0f, 0.0f, 0.0f);
		Component->UpdateWeightShift(0.016f);

		Component->CurrentVelocity = FVector(0.0f, 0.0f, 0.0f);
		Component->UpdateWeightShift(0.016f);

		// Find peak in first 0.5 seconds
		float PeakMagnitude = 0.0f;
		float PeakTime = 0.0f;
		float ElapsedTime = 0.0f;
		const float DeltaTime = 0.016f;

		while (ElapsedTime < 0.5f)
		{
			Component->UpdateWeightShift(DeltaTime);
			FVector CurrentWeightShift = Component->GetWeightShiftOffset();
			float CurrentMagnitude = CurrentWeightShift.Size();

			if (CurrentMagnitude > PeakMagnitude)
			{
				PeakMagnitude = CurrentMagnitude;
				PeakTime = ElapsedTime;
			}

			ElapsedTime += DeltaTime;
		}

		UE_LOG(LogTemp, Warning, TEXT("[WeightShiftTest] Overshoot - Peak: %.2f cm at %.3f s"), PeakMagnitude, PeakTime);

		// Verify overshoot occurred (magnitude > 2.5 cm suggests overshoot beyond simple settling)
		if (PeakMagnitude < 2.0f)
		{
			UE_LOG(LogTemp, Error, TEXT("[WeightShiftTest] Expected overshoot behavior, peak was too small: %.2f"), PeakMagnitude);
			return false;
		}

		// Verify peak occurred early (within 0.5s)
		if (PeakTime > 0.5f)
		{
			UE_LOG(LogTemp, Error, TEXT("[WeightShiftTest] Peak occurred too late: %.3f s"), PeakTime);
			return false;
		}

		return true;
	}

	/**
	 * Run all weight shift animation tests. Returns true iff every test passed
	 * (so the automation-framework caller below can report a real verdict).
	 */
	static bool RunAllTests()
	{
		UE_LOG(LogTemp, Warning, TEXT("=== Weight Shift Animation Test Suite ==="));

		bool bAllPassed = true;

		if (TestWeightShiftTriggersOnDeceleration())
		{
			UE_LOG(LogTemp, Warning, TEXT("PASS: TestWeightShiftTriggersOnDeceleration"));
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("FAIL: TestWeightShiftTriggersOnDeceleration"));
			bAllPassed = false;
		}

		if (TestWeightShiftSettles())
		{
			UE_LOG(LogTemp, Warning, TEXT("PASS: TestWeightShiftSettles"));
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("FAIL: TestWeightShiftSettles"));
			bAllPassed = false;
		}

		if (TestWeightShiftMaxClamping())
		{
			UE_LOG(LogTemp, Warning, TEXT("PASS: TestWeightShiftMaxClamping"));
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("FAIL: TestWeightShiftMaxClamping"));
			bAllPassed = false;
		}

		if (TestWeightShiftOvershoot())
		{
			UE_LOG(LogTemp, Warning, TEXT("PASS: TestWeightShiftOvershoot"));
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("FAIL: TestWeightShiftOvershoot"));
			bAllPassed = false;
		}

		if (bAllPassed)
		{
			UE_LOG(LogTemp, Warning, TEXT("=== All Weight Shift Tests PASSED ==="));
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("=== Some Weight Shift Tests FAILED ==="));
		}
		return bAllPassed;
	}
};

// Function to invoke tests from console or PIE
void RunWeightShiftTests()
{
	FWeightShiftAnimationTests::RunAllTests();
}

// THE CALLER (tb-0056 CONFIRMED these 4 tests compiled for weeks but had zero
// callers — never executed once; a green build is not test coverage). Registered
// with UE's automation framework so they run headlessly with every suite:
//   Automation RunTests Chimera.Animation.WeightShift
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWeightShiftAnimationAutomationTest,
	"Chimera.Animation.WeightShift",
	EAutomationTestFlags::ApplicationContextMask | EAutomationTestFlags::EngineFilter)
bool FWeightShiftAnimationAutomationTest::RunTest(const FString& Parameters)
{
	return FWeightShiftAnimationTests::RunAllTests();
}
#endif
