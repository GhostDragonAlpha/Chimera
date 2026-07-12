#include "DemoPlayerController.h"
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

ADemoPlayerController::ADemoPlayerController()
{
	PickupInteraction = CreateDefaultSubobject<UPickupInteractionComponent>(TEXT("PickupInteraction"));
	if (PickupInteraction)
	{
		PickupInteraction->RegisterComponent();
	}
	bDemoPickupSpawned = false;
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
	UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] DemoPlayerController input bound (WASD/mouse/space/C/interact/drop)"));
}

void ADemoPlayerController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);
	EnsureThirdPersonCamera(InPawn);
	SpawnDemoPickupIfNeeded(InPawn);
	ConfigureCrouchCapsule(InPawn);
	EnsureFootprints(InPawn);
	EnsureChimeraMovement(InPawn);
	UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] Possessed %s"), *GetNameSafe(InPawn));
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
