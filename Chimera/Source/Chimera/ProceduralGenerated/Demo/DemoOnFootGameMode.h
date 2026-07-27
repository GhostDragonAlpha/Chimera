#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "DemoOnFootGameMode.generated.h"

/**
 * Demo-lane on-foot game mode for the Regolith Yard (DEMO_ARCHITECTURE.md).
 * Pairs GameModeBase behavior with ADemoPlayerController. Spawns no default
 * pawn — the level-placed BP_Astronaut_Character auto-possesses (verified:
 * AutoPossess preempts the default-pawn spawn in this engine build).
 */
UCLASS()
class CHIMERA_API ADemoOnFootGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ADemoOnFootGameMode();
};
