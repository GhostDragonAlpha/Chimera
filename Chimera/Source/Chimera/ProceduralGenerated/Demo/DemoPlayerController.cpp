#include "DemoPlayerController.h"
#include "GameFramework/Character.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "Engine/World.h"
#include "../Interactions/PickupInteractionComponent.h"
#include "../Interactions/PickupActor.h"

ADemoPlayerController::ADemoPlayerController()
{
	PickupInteraction = CreateDefaultSubobject<UPickupInteractionComponent>(TEXT("PickupInteraction"));
	bDemoPickupSpawned = false;
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
