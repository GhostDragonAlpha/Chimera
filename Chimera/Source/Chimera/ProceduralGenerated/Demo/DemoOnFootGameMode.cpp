#include "DemoOnFootGameMode.h"
#include "DemoPlayerController.h"

ADemoOnFootGameMode::ADemoOnFootGameMode()
{
	PlayerControllerClass = ADemoPlayerController::StaticClass();
	DefaultPawnClass = nullptr;
	UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] DemoOnFootGameMode: controller=DemoPlayerController, default pawn=none (AutoPossess)"));
}
