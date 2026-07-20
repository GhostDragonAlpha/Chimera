#include "DemoPlayerController.h"
#pragma warning(disable: 4996)
#pragma warning(disable: 5038)
#include "GameFramework/Character.h"
#include "GameFramework/SpringArmComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Camera/CameraComponent.h"
#include "Engine/World.h"
#include "../Interactions/PickupInteractionComponent.h"
#include "../Interactions/PickupActor.h"
#include "../Environment/FootprintComponent.h"
#include "../ChimeraMovementComponent.h"
#include "../Suit/SuitLifeSupportComponent.h"
#include "../Shelter/ShelterHabitatComponent.h"
#include "../UI/WID_O2HUD.h"
#include "../VFX/ErisaidResonanceVFXComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"
#include "../UI/GestureWheel.h"

ADemoPlayerController::ADemoPlayerController()
{
	// CreateDefaultSubobject already owns the component's registration lifecycle
	// (it registers through the normal actor-spawn path once the actor has a valid
	// World). Do NOT call RegisterComponent() here: at CDO/class-default construction
	// there is no owning World, which trips a "MyOwnerWorld" ensure on every editor
	// boot / Live-Coding reload — harmless but log-noise that erodes trust.
	PickupInteraction = CreateDefaultSubobject<UPickupInteractionComponent>(TEXT("PickupInteraction"));
	bDemoPickupSpawned = false;
	bDemoHabitatSpawned = false;
	// Create the GestureWheel widget (radial social verb menu)
	GestureWheelWidget = CreateDefaultSubobject<UGestureWheel>(TEXT("GestureWheelWidget"));

	// Placeholder habitat hull (P1: the O2/battery refill destination). Cached here
	// because ConstructorHelpers::FObjectFinder only works inside a constructor; the
	// actual actor is spawned later, at possess time, by SpawnDemoHabitatIfNeeded —
	// same idiom FootprintComponent uses for its footprint plane mesh.
	static ConstructorHelpers::FObjectFinder<UStaticMesh> HabitatMeshFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (HabitatMeshFinder.Succeeded())
	{
		HabitatHullMesh = HabitatMeshFinder.Object;
	}

	// Enable mouse look: show cursor for UI.
	bShowMouseCursor = true;
}

void ADemoPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();
	InputComponent->BindAxis(TEXT("DemoMoveForward"), this, &ADemoPlayerController::MoveForward);
	InputComponent->BindAxis(TEXT("DemoMoveRight"), this, &ADemoPlayerController::MoveRight);
	InputComponent->BindAxis(TEXT("DemoTurn"), this, &ADemoPlayerController::Turn);
	InputComponent->BindAxis(TEXT("DemoLookUp"), this, &ADemoPlayerController::LookUp);
	InputComponent->BindAction(TEXT("DemoJump"), IE_Pressed, this, &ADemoPlayerController::StartJump);
	InputComponent->BindAction(TEXT("DemoJump"), IE_Released, this, &ADemoPlayerController::StopJump);
	InputComponent->BindAction(TEXT("DemoCrouch"), IE_Pressed, this, &ADemoPlayerController::StartCrouch);
	InputComponent->BindAction(TEXT("DemoCrouch"), IE_Released, this, &ADemoPlayerController::StopCrouch);
	InputComponent->BindAction(TEXT("DemoInteract"), IE_Pressed, this, &ADemoPlayerController::Interact);
	InputComponent->BindAction(TEXT("DemoDrop"), IE_Pressed, this, &ADemoPlayerController::DropItem);
	// TAB input binding for GestureWheel: key_down TAB -> OpenWheel, key_up TAB -> CommitGesture+CloseWheel.
	// "DemoGestureWheel" must exist as an ActionMapping in Config/DefaultInput.ini —
	// binding a bare key name ("Tab") maps to NO action (simtest_457320c3449e9c1f).
	InputComponent->BindAction(TEXT("DemoGestureWheel"), IE_Pressed, this, &ADemoPlayerController::OnTabPressed);
	InputComponent->BindAction(TEXT("DemoGestureWheel"), IE_Released, this, &ADemoPlayerController::OnTabReleased);
	UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] DemoPlayerController input bound (WASD/mouse/space/C/interact/drop/TAB-gesture-wheel)"));
}

void ADemoPlayerController::OnTabPressed()
{
	if (GestureWheelWidget)
	{
		GestureWheelWidget->OpenWheel();
	}
}

void ADemoPlayerController::OnTabReleased()
{
	if (GestureWheelWidget)
	{
		// Commit the gesture and close the wheel
		if (APawn* P = GetPawn())
		{
			GestureWheelWidget->CommitGesture(P);
		}
		GestureWheelWidget->CloseWheel();
	}
}

void ADemoPlayerController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);
	EnsureThirdPersonCamera(InPawn);
	SpawnDemoPickupIfNeeded(InPawn);
	SpawnDemoHabitatIfNeeded(InPawn);
	ConfigureCrouchCapsule(InPawn);
	EnsureFootprints(InPawn);
	EnsureChimeraMovement(InPawn);
	EnsureSuitLifeSupport(InPawn);
	EnsureResonanceVFX(InPawn);
	EnsureO2HUD(InPawn);
	if (GestureWheelWidget && !GestureWheelWidget->IsInViewport())
	{
		GestureWheelWidget->AddToViewport();
	}
	UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] Possessed %s"), *GetNameSafe(InPawn));
}

void ADemoPlayerController::EnsureO2HUD(APawn* InPawn)
{
	// P0 fix (2026-07-13): the diegetic wrist gauge was diagnosed as a GOTCHA —
	// WID_O2HUD's UPROPERTY(meta=(BindWidget)) members bound to nothing because this
	// project cannot author the paired UMG Blueprint (WBP) asset, so a bare
	// CreateWidget<UWID_O2HUD>() rendered an empty widget. WID_O2HUD now builds its
	// own widget tree in C++ (NativeOnInitialized -> BuildWidgetTree), so creating and
	// showing it here is now sufficient to put real, live gauges on screen.
	if (!InPawn)
	{
		return;
	}

	if (!O2HUDWidget)
	{
		O2HUDWidget = CreateWidget<UWID_O2HUD>(this, UWID_O2HUD::StaticClass());
		if (O2HUDWidget)
		{
			UE_LOG(LogTemp, Display, TEXT("[O2HUD] Diegetic O2/battery/dust HUD created for %s"), *GetNameSafe(InPawn));
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("[O2HUD] CreateWidget<UWID_O2HUD> failed for %s"), *GetNameSafe(InPawn));
		}
	}

	if (O2HUDWidget && !O2HUDWidget->IsInViewport())
	{
		O2HUDWidget->ShowO2HUD();
	}
}

void ADemoPlayerController::EnsureSuitLifeSupport(APawn* InPawn)
{
	// The EVA suit's survival sim (O2/battery/dust). Attach it to the possessed
	// pawn so O2 drains by exertion the moment the player exists (H-34). The wrist
	// gauge / HUD reads this; shelters set its bInShelter flag.
	if (!InPawn || InPawn->FindComponentByClass<USuitLifeSupportComponent>())
	{
		return;
	}
	USuitLifeSupportComponent* Suit =
		NewObject<USuitLifeSupportComponent>(InPawn, TEXT("SuitLifeSupportComponent"));
	if (Suit)
	{
		Suit->RegisterComponent();
		UE_LOG(LogTemp, Display,
			TEXT("[SUIT] runtime-attached USuitLifeSupportComponent to %s (H-34)"),
			*GetNameSafe(InPawn));
	}
}

void ADemoPlayerController::EnsureResonanceVFX(APawn* InPawn)
{
	// Erisaid Resonance VFX � the visual feedback layer for the player's suit.
	// Attach it to the possessed pawn so resonance visuals are live from first possess (H-34).
	if (!InPawn || InPawn->FindComponentByClass<UErisaidResonanceVFXComponent>())
	{
		return;
	}
	UErisaidResonanceVFXComponent* VFX =
		NewObject<UErisaidResonanceVFXComponent>(InPawn, TEXT("ErisaidResonanceVFXComponent"));
	if (VFX)
	{
		VFX->RegisterComponent();
		UE_LOG(LogTemp, Display,
			TEXT("[VFX] runtime-attached UErisaidResonanceVFXComponent to %s (H-34)"),
			*GetNameSafe(InPawn));
	}
}

void ADemoPlayerController::MoveForward(float Value)
{
	APawn* P = GetPawn();
	if (P && Value != 0.0f)
	{
		const FRotator YawOnly(0.0f, GetControlRotation().Yaw, 0.0f);
		P->AddMovementInput(FRotationMatrix(YawOnly).GetUnitAxis(EAxis::X), Value);
	}
}

void ADemoPlayerController::MoveRight(float Value)
{
	APawn* P = GetPawn();
	if (P && Value != 0.0f)
	{
		const FRotator YawOnly(0.0f, GetControlRotation().Yaw, 0.0f);
		P->AddMovementInput(FRotationMatrix(YawOnly).GetUnitAxis(EAxis::Y), Value);
	}
}

void ADemoPlayerController::Turn(float Value)
{
	AddYawInput(Value);
}

void ADemoPlayerController::LookUp(float Value)
{
	AddPitchInput(Value);
}

void ADemoPlayerController::StartJump()
{
	if (ACharacter* C = Cast<ACharacter>(GetPawn()))
	{
		C->Jump();
	}
}

void ADemoPlayerController::StopJump()
{
	if (ACharacter* C = Cast<ACharacter>(GetPawn()))
	{
		C->StopJumping();
	}
}

void ADemoPlayerController::StartCrouch()
{
	if (ACharacter* C = Cast<ACharacter>(GetPawn()))
	{
		C->Crouch();
	}
}

void ADemoPlayerController::StopCrouch()
{
	if (ACharacter* C = Cast<ACharacter>(GetPawn()))
	{
		C->UnCrouch();
	}
}

void ADemoPlayerController::Interact()
{
	if (PickupInteraction && PickupInteraction->TryInteract())
		// Witness marker: sleepwalker log_contains expects key on this exact string.
	{
		UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] Interact action triggered - picked up '%s'"), *PickupInteraction->HeldItemName.ToString());
	}
	else
	{
		UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] Interact action triggered - nothing in range to pick up"));
	}
}

void ADemoPlayerController::DropItem()
{
	if (PickupInteraction && PickupInteraction->TryDrop())
	{
		UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] Drop action triggered - item dropped"));
	}
	else
	{
		UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] Drop action triggered - nothing currently held"));
	}
}

void ADemoPlayerController::ConfigureCrouchCapsule(APawn* InPawn)
{
	if (!InPawn) return;

	// Crouch is driven by the real engine API, not by resizing the standing
	// capsule at possess time. ACharacter::Crouch() (bound to C via StartCrouch)
	// is a no-op unless the movement component is allowed to crouch; the
	// crouched half-height then determines how far the view drops.
	ACharacter* Char = Cast<ACharacter>(InPawn);
	if (!Char) return;

	UCharacterMovementComponent* Move = Char->GetCharacterMovement();
	if (!Move) return;

	// Allow crouching. CanEverCrouch() reads this flag live, so setting it at
	// possess time (rather than in the pawn's constructor) is sufficient.
	Move->GetNavAgentPropertiesRef().bCanCrouch = true;

	// Crouched capsule half-height. With a default standing half-height of ~88,
	// 40 yields a visible ~48-unit view drop while C is held.
	Move->SetCrouchedHalfHeight(40.0f);

	const float StandingHalfHeight = Char->GetCapsuleComponent()
		? Char->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight()
		: 0.0f;
	UE_LOG(LogTemp, Display,
		TEXT("[VERB_BEND] Crouch enabled on %s: standing=%.1f crouched=%.1f can_crouch=%d"),
		*GetNameSafe(Char), StandingHalfHeight, Move->GetCrouchedHalfHeight(),
		(int32)Move->GetNavAgentPropertiesRef().bCanCrouch);
	}


void ADemoPlayerController::EnsureFootprints(APawn* InPawn)
{
	if (!InPawn || InPawn->FindComponentByClass<UFootprintComponent>())
	{
		return;
	}

	UFootprintComponent* Footprints = NewObject<UFootprintComponent>(InPawn, TEXT("FootprintComponent"));
	if (Footprints)
	{
		Footprints->RegisterComponent();
		UE_LOG(LogTemp, Display, TEXT("[GROUND_FOOTPRINTS] FootprintComponent attached to %s"), *GetNameSafe(InPawn));
	}
}

void ADemoPlayerController::EnsureChimeraMovement(APawn* InPawn)
{
	if (!InPawn || InPawn->FindComponentByClass<UChimeraMovementComponent>())
	{
		return;
	}

	UChimeraMovementComponent* ChimeraMove = NewObject<UChimeraMovementComponent>(InPawn, TEXT("ChimeraMovementComponent"));
	if (ChimeraMove)
	{
		ChimeraMove->RegisterComponent();
		UE_LOG(LogTemp, Display, TEXT("[GROUND_SOUND] ChimeraMovementComponent attached to %s for telemetry"), *GetNameSafe(InPawn));
	}
}

void ADemoPlayerController::EnsureThirdPersonCamera(APawn* InPawn)
{
	if (!InPawn || InPawn->FindComponentByClass<UCameraComponent>())
	{
		return;
	}

	USpringArmComponent* Arm = NewObject<USpringArmComponent>(InPawn, TEXT("DemoSpringArm"));
	Arm->SetupAttachment(InPawn->GetRootComponent());
	Arm->TargetArmLength = 450.0f;
	Arm->SetRelativeLocation(FVector(0.0f, 0.0f, 90.0f));
	Arm->bUsePawnControlRotation = true;
	Arm->RegisterComponent();

	UCameraComponent* Cam = NewObject<UCameraComponent>(InPawn, TEXT("DemoCamera"));
	Cam->SetupAttachment(Arm, USpringArmComponent::SocketName);
	Cam->RegisterComponent();

	UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] Third-person demo camera attached to %s"), *GetNameSafe(InPawn));
}

void ADemoPlayerController::SpawnDemoPickupIfNeeded(APawn* InPawn)
{
	if (bDemoPickupSpawned || !InPawn)
	{
		return;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	// Deterministic, drift-proof placement: always relative to wherever the
	// pawn actually spawned this session, rather than an absolute level
	// coordinate (the level's own spawn point has drifted across sessions).
	// Named PickupSpawnLocation, not SpawnLocation, to avoid shadowing
	// APlayerController::SpawnLocation (a real inherited member).
	const FVector PickupSpawnLocation = InPawn->GetActorLocation() + InPawn->GetActorForwardVector() * 300.0f;

	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	SpawnParams.Name = FName(TEXT("Demo_PickupActor"));

	APickupActor* DemoPickup = World->SpawnActor<APickupActor>(APickupActor::StaticClass(), PickupSpawnLocation, InPawn->GetActorRotation(), SpawnParams);
	if (DemoPickup)
	{
		DemoPickup->ItemName = FText::FromString(TEXT("Multitool"));
		bDemoPickupSpawned = true;
		UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] Demo pickup '%s' spawned at %s"), *DemoPickup->ItemName.ToString(), *PickupSpawnLocation.ToString());
	}
}

void ADemoPlayerController::SpawnDemoHabitatIfNeeded(APawn* InPawn)
{
	if (bDemoHabitatSpawned || !InPawn)
	{
		return;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	// Placed opposite the demo pickup (which sits +300uu forward of spawn) so the two
	// demo props never overlap. Deterministic relative to wherever the pawn actually
	// spawned this session (same drift-proof rationale as SpawnDemoPickupIfNeeded) —
	// this IS the P1 "race back to refill" destination.
	const FVector HabitatSpawnLocation = InPawn->GetActorLocation() - InPawn->GetActorForwardVector() * 500.0f;

	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	SpawnParams.Name = FName(TEXT("Demo_HabitatActor"));

	AStaticMeshActor* Habitat = World->SpawnActor<AStaticMeshActor>(
		AStaticMeshActor::StaticClass(), HabitatSpawnLocation, InPawn->GetActorRotation(), SpawnParams);
	if (!Habitat)
	{
		UE_LOG(LogTemp, Error, TEXT("[HABITAT] Demo_HabitatActor spawn FAILED"));
		return;
	}

	// Visible placeholder hull so the habitat reads as a structure to walk back to,
	// not an invisible trigger volume (a screenshot/witness needs something to see).
	if (UStaticMeshComponent* MeshComp = Habitat->GetStaticMeshComponent())
	{
		MeshComp->SetMobility(EComponentMobility::Movable);
		if (HabitatHullMesh)
		{
			MeshComp->SetStaticMesh(HabitatHullMesh);
			MeshComp->SetWorldScale3D(FVector(4.0f, 4.0f, 2.5f)); // ~400x400x250uu hull
		}
		MeshComp->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	}

	// ShelterHabitatComponent's own BeginPlay fires here (runtime-attached to an actor
	// that has already begun play — the same proven H-34 pattern EnsureSuitLifeSupport
	// uses on the pawn itself). BeginPlay builds its sphere trigger and binds the
	// overlaps that set bInShelter / bAtOxygenGarden / bAtBatteryBank on any
	// overlapping pawn's suit.
	UShelterHabitatComponent* Shelter = NewObject<UShelterHabitatComponent>(Habitat, TEXT("ShelterHabitatComponent"));
	if (Shelter)
	{
		Shelter->RegisterComponent();
		bDemoHabitatSpawned = true;
		UE_LOG(LogTemp, Display,
			TEXT("[HABITAT] Demo_HabitatActor spawned at %s (ShelterHabitatComponent radius %.0f) - O2/battery refill point live"),
			*HabitatSpawnLocation.ToString(), Shelter->ShelterRadius);
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("[HABITAT] Failed to create ShelterHabitatComponent"));
	}
}
