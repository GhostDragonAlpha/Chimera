#include "DemoPlayerController.h"
#include "GameFramework/Character.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"

void ADemoPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();
	InputComponent->BindAxis(TEXT("DemoMoveForward"), this, &ADemoPlayerController::MoveForward);
	InputComponent->BindAxis(TEXT("DemoMoveRight"), this, &ADemoPlayerController::MoveRight);
	InputComponent->BindAxis(TEXT("DemoTurn"), this, &ADemoPlayerController::Turn);
	InputComponent->BindAxis(TEXT("DemoLookUp"), this, &ADemoPlayerController::LookUp);
	InputComponent->BindAction(TEXT("DemoJump"), IE_Pressed, this, &ADemoPlayerController::StartJump);
	InputComponent->BindAction(TEXT("DemoJump"), IE_Released, this, &ADemoPlayerController::StopJump);
	UE_LOG(LogTemp, Display, TEXT("[DEMOBEAT] DemoPlayerController input bound (WASD/mouse/space)"));
}

void ADemoPlayerController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);
	EnsureThirdPersonCamera(InPawn);
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
