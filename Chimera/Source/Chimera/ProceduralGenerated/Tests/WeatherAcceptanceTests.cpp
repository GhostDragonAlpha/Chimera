// Copyright 2026 Chimera Project. All Rights Reserved.
#include "CoreMinimal.h"
#include "../Environment/WeatherComponent.h"

/**
 * Weather System Acceptance Tests
 * Verifies the meteorology authority (seed UWeatherSubsystem) as hard facts,
 * world-independently (NewObject, no PIE), matching the WindSystem test style:
 *   1. Initializes with the seed's WIND bands and a calm start.
 *   2. Seeded RNG is deterministic — same seed replays the same storm calendar.
 *   3. Night bands match ASun::IsNight (day-fraction < 0.20 or > 0.80).
 *   4. The storm STATE MACHINE runs: ForceStorm raises it, the clock passes it,
 *      the passed-count and StormsPassed telemetry increment (the world-wide
 *      footprint erasure itself is proven in PIE — see the beat follow-up).
 *   5. Between storms wind eases toward the day band and the velocity vector
 *      tracks the scalar speed.
 */

void TestWeather_Initialization()
{
	UWeatherComponent* Weather = NewObject<UWeatherComponent>();
	check(Weather != nullptr);
	Weather->ResetWeather();

	check(FMath::IsNearlyEqual(Weather->CalmWindSpeed, 2.0f));
	check(FMath::IsNearlyEqual(Weather->BreezeWindSpeed, 6.0f));
	check(FMath::IsNearlyEqual(Weather->GustWindSpeed, 12.0f));
	check(FMath::IsNearlyEqual(Weather->StormWindSpeed, 24.0f));
	check(FMath::IsNearlyEqual(Weather->DayLengthHours, 27.0f));
	check(FMath::IsNearlyEqual(Weather->WindSpeed, Weather->CalmWindSpeed));
	check(!Weather->IsStormActive());
	check(Weather->StormsPassed == 0);
	check(Weather->DayNumber == 0);

	UE_LOG(LogTemp, Display, TEXT("[WEATHER TEST] Initialization: PASS"));
}

void TestWeather_Determinism()
{
	UWeatherComponent* A = NewObject<UWeatherComponent>();
	UWeatherComponent* B = NewObject<UWeatherComponent>();
	UWeatherComponent* C = NewObject<UWeatherComponent>();
	A->WeatherSeed = 1337;
	B->WeatherSeed = 1337;
	C->WeatherSeed = 4242;
	A->ResetWeather();
	B->ResetWeather();
	C->ResetWeather();

	// Same seed -> identical RNG-derived initial wind heading; different seed diverges.
	check(FMath::IsNearlyEqual(A->WindDirectionRadians, B->WindDirectionRadians, 1e-4f));
	check(!FMath::IsNearlyEqual(A->WindDirectionRadians, C->WindDirectionRadians, 1e-3f));

	UE_LOG(LogTemp, Display, TEXT("[WEATHER TEST] Determinism: PASS"));
}

void TestWeather_NightBands()
{
	UWeatherComponent* Weather = NewObject<UWeatherComponent>();
	Weather->ResetWeather();

	Weather->TimeOfDayHours = 1.0f;   // t=0.037 < 0.20 -> night
	check(Weather->IsNight());
	Weather->TimeOfDayHours = 13.5f;  // t=0.50 -> day
	check(!Weather->IsNight());
	Weather->TimeOfDayHours = 24.0f;  // t=0.889 > 0.80 -> night
	check(Weather->IsNight());

	UE_LOG(LogTemp, Display, TEXT("[WEATHER TEST] NightBands: PASS"));
}

void TestWeather_StormCycle()
{
	UWeatherComponent* Weather = NewObject<UWeatherComponent>();
	Weather->ResetWeather();
	check(!Weather->IsStormActive());

	// Raise a storm on demand; a second request is refused while one runs.
	check(Weather->ForceStorm() == true);
	check(Weather->IsStormActive());
	check(Weather->ForceStorm() == false);

	// Fast-forward the clock until the storm passes (bounded so a logic bug
	// can't hang the suite). At 100 game-hours per tick a 45-min storm ends fast.
	Weather->HoursPerRealSecond = 100.0f;
	int32 Guard = 0;
	while (Weather->IsStormActive() && Guard < 100)
	{
		Weather->AdvanceWeather(1.0f);
		++Guard;
	}

	check(!Weather->IsStormActive());
	check(Weather->StormsPassed == 1);
	check(FMath::IsNearlyEqual(Weather->StormIntensity, 0.0f));
	check(Weather->LastStormFootprintsErased == 0); // no world/prints in this harness

	UE_LOG(LogTemp, Display, TEXT("[WEATHER TEST] StormCycle: PASS (passed in %d tick(s))"), Guard);
}

void TestWeather_WindBandResponse()
{
	UWeatherComponent* Weather = NewObject<UWeatherComponent>();
	Weather->ResetWeather();
	Weather->TimeOfDayHours = 8.0f; // daytime -> breeze band target

	// Ease over ~2 s of small steps; no storm can trigger (next is 5-9 days out).
	for (int32 i = 0; i < 20; ++i)
	{
		Weather->AdvanceWeather(0.1f);
	}

	check(!Weather->IsStormActive());
	check(Weather->WindSpeed > Weather->CalmWindSpeed);          // rose off calm toward breeze
	check(Weather->WindSpeed <= Weather->GustWindSpeed * 1.2f);  // stayed in the ambient range

	const FVector Velocity = Weather->GetWindVelocity();
	check(FMath::IsNearlyEqual(Velocity.Size(), Weather->WindSpeed, 0.01f));

	UE_LOG(LogTemp, Display, TEXT("[WEATHER TEST] WindBandResponse: PASS (speed=%.2f)"), Weather->WindSpeed);
}

// Helper function to run all weather system tests
void RunWeatherSystemTests()
{
	UE_LOG(LogTemp, Warning, TEXT("\n====== WEATHER SYSTEM ACCEPTANCE TESTS ======\n"));

	try
	{
		TestWeather_Initialization();
		TestWeather_Determinism();
		TestWeather_NightBands();
		TestWeather_StormCycle();
		TestWeather_WindBandResponse();

		UE_LOG(LogTemp, Warning, TEXT("\n====== ALL WEATHER SYSTEM TESTS PASSED ======\n"));
	}
	catch (const std::exception& e)
	{
		UE_LOG(LogTemp, Error, TEXT("Weather system test failed: %s"), ANSI_TO_TCHAR(e.what()));
	}
}
