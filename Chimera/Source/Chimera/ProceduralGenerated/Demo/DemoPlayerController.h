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

	/** Spawns one demo habitat actor (AStaticMeshActor + runtime-attached
	 *  ShelterHabitatComponent) near the possessed pawn, once per controller
	 *  lifetime. P1 fix (design directive Section 3, 2026-07-13): ShelterHabitatComponent
	 *  existed in code but was never spawned into any live actor anywhere in the
	 *  project -- the same H-34 gap SuitLifeSupport/Footprints/ChimeraMovement had
	 *  before this controller runtime-attached them. Without a habitat actor in the
	 *  world, the suit's bAtOxygenGarden/bAtBatteryBank/bInShelter flags could never
	 *  flip and the survival loop had no refill destination. */
	void SpawnDemoHabitatIfNeeded(APawn* InPawn);
	void ConfigureCrouchCapsule(APawn* InPawn);
	void EnsureFootprints(APawn* InPawn);
	void EnsureChimeraMovement(APawn* InPawn);
	void EnsureSuitLifeSupport(APawn* InPawn);
	void EnsureResonanceVFX(APawn* InPawn);

	/** Create (once) and show the diegetic O2/battery/dust wrist HUD (P0 fix,
	 *  2026-07-13): WID_O2HUD now builds its own widget tree in C++, so a bare
	 *  CreateWidget here is sufficient — no WBP Blueprint asset required. */
	void EnsureO2HUD(APawn* InPawn);

	bool bDemoPickupSpawned;
	bool bDemoHabitatSpawned;

	/** Cached HUD instance — created once per controller lifetime, shown on every
	 *  possess (guards against duplicate viewport adds via IsInViewport()). */
	UPROPERTY()
	class UWID_O2HUD* O2HUDWidget;

	/** Placeholder habitat hull mesh, cached at construction time (ConstructorHelpers
	 *  only works inside a constructor) — the actual habitat actor is spawned later,
	 *  at possess time, by SpawnDemoHabitatIfNeeded. */
	UPROPERTY()
	class UStaticMesh* HabitatHullMesh;
};
