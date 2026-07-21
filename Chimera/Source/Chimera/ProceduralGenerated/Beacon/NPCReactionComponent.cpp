// NPCReactionComponent — NPCs turn toward the player when approached.
#include "NPCReactionComponent.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"
#include "Math/UnrealMathUtility.h"

UNPCReactionComponent::UNPCReactionComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickGroup = TG_PrePhysics;
    DetectionRadius = 500.0f;
    RotationSpeed = 3.0f;
}

void UNPCReactionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    AActor* Owner = GetOwner();
    if (!Owner || !GetWorld()) return;
    APlayerController* PC = GetWorld()->GetFirstPlayerController();
    if (!PC || !PC->GetPawn()) return;
    APawn* PlayerPawn = PC->GetPawn();
    float Dist = FVector::Dist(Owner->GetActorLocation(), PlayerPawn->GetActorLocation());
    if (Dist < DetectionRadius)
    {
        FVector Dir = PlayerPawn->GetActorLocation() - Owner->GetActorLocation();
        Dir.Z = 0.0f;
        Dir.Normalize();
        FRotator TargetRot = Dir.Rotation();
        FRotator CurrentRot = Owner->GetActorRotation();
        FRotator NewRot = FMath::RInterpTo(CurrentRot, TargetRot, DeltaTime, RotationSpeed);
        Owner->SetActorRotation(NewRot);
    }
}
