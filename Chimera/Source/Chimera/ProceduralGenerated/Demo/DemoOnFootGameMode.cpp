#include "DemoOnFootGameMode.h"
#pragma warning(disable: 4996)
#pragma warning(disable: 5038)
#include "DemoPlayerController.h"

ADemoOnFootGameMode::ADemoOnFootGameMode()
{
	PlayerControllerClass = ADemoPlayerController::StaticClass();
	DefaultPawnClass = nullptr;
	UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] DemoOnFootGameMode: controller=DemoPlayerController, default pawn=none (AutoPossess)"));
}
