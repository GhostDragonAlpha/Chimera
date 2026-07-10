#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "DemoPlayerController.generated.h"

/**
 * Demo-lane player controller: drives ANY possessed ACharacter with legacy
 * axis bindings (mappings live in Config/DefaultInput.ini) and guarantees a
 * third-person view by attaching a spring-arm camera at possession time when
 * the pawn has none. Exists because BP_Astronaut_Character carries no input
 * graph (bridge cannot author Blueprint graphs) — see surprise_2b3d79676e3d4206.
 */
UCLASS()
class CHIMERA_API ADemoPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	ADemoPlayerController();

protected:
	virtual void SetupInputComponent() override;
	virtual void OnPossess(APawn* InPawn) override;

	/** Owns pickup/drop detection and "currently held item" state. Lives on the controller (not the Blueprint character) because BP_Astronaut_Character carries no input/component graph the bridge can author into — see the class comment above. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Interactions")
	class UPickupInteractionComponent* PickupInteraction;

private:
	void MoveForward(float Value);
	void MoveRight(float Value);
	void Turn(float Value);
	void LookUp(float Value);
	void StartJump();
	void StopJump();
	void StartCrouch();
	void StopCrouch();
	void Interact();
	void DropItem();

	void EnsureThirdPersonCamera(APawn* InPawn);

	/** Spawns one demo APickupActor near the possessed pawn, once per controller lifetime, so there is always something real to test Interact/Drop against. */
	void SpawnDemoPickupIfNeeded(APawn* InPawn);
	void ConfigureCrouchCapsule(APawn* InPawn);
	void EnsureFootprints(APawn* InPawn);

	bool bDemoPickupSpawned;
};
