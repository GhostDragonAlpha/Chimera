// Copyright 2026 Chimera Project. All Rights Reserved.

#include "FootprintComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"
#include "CollisionQueryParams.h"
#include "UObject/ConstructorHelpers.h"

UFootprintComponent::UFootprintComponent()
{
    PrimaryComponentTick.bCanEverTick = true;

    StrideLength = 80.0f;
    FootLateralOffset = 16.0f;
    FootprintLength = 26.0f;
    FootprintLifeSpan = 45.0f;
    MinSpeed = 20.0f;
    FootprintsSpawned = 0;

    DistanceSinceLastPrint = 0.0f;
    bLeftFoot = false;
    bInitialized = false;
    CachedMovement = nullptr;

    // Engine plane (100x100, facing +Z) as the footprint quad.
    static ConstructorHelpers::FObjectFinder<UStaticMesh> PlaneMesh(TEXT("/Engine/BasicShapes/Plane.Plane"));
    if (PlaneMesh.Succeeded())
    {
        FootprintMesh = PlaneMesh.Object;
    }

    // Regolith grey reads as a compressed imprint against the tan sand. No
    // deferred-decal material exists project-wide, so a mesh imprint is used;
    // a projected-decal upgrade is a follow-up.
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> RegolithMat(
        TEXT("/Game/Celestial/Materials/MAT_Moon_Regolith.MAT_Moon_Regolith"));
    if (RegolithMat.Succeeded())
    {
        FootprintMaterial = RegolithMat.Object;
    }
}

void UFootprintComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    AActor* Owner = GetOwner();
    if (!Owner)
    {
        return;
    }

    // Self-initialize on the first tick so behaviour is robust regardless of
    // whether the component was added before or after the owner's BeginPlay.
    if (!bInitialized)
    {
        CachedMovement = Owner->FindComponentByClass<UCharacterMovementComponent>();
        LastSampleLocation = Owner->GetActorLocation();
        bInitialized = true;
        return;
    }

    // Only lay prints while grounded — reset the sample point while airborne so
    // jump/fall travel is not counted toward the next stride.
    if (CachedMovement && !CachedMovement->IsMovingOnGround())
    {
        LastSampleLocation = Owner->GetActorLocation();
        return;
    }

    const FVector Current = Owner->GetActorLocation();
    FVector Delta = Current - LastSampleLocation;
    Delta.Z = 0.0f; // horizontal travel only
    const float Step = Delta.Size();

    // Teleport guard: a huge single-tick jump (e.g. a position reset) is not
    // walking — resync the sample point and lay nothing.
    const float MaxStepDistance = 1500.0f;
    if (Step > MaxStepDistance)
    {
        LastSampleLocation = Current;
        return;
    }

    // Speed gate: ignore standing jitter.
    if (DeltaTime > KINDA_SMALL_NUMBER && (Step / DeltaTime) < MinSpeed)
    {
        LastSampleLocation = Current;
        return;
    }

    const FVector StepDir = Delta.GetSafeNormal();
    FVector Forward = StepDir;
    if (Forward.IsNearlyZero())
    {
        Forward = Owner->GetActorForwardVector();
    }

    // Lay one print per StrideLength of path covered THIS frame, interpolated
    // along the step, so count and spacing are frame-rate independent — a single
    // large low-fps step must still yield the correct number of prints, not one.
    const float PrevAccum = DistanceSinceLastPrint;
    int32 Guard = 0;
    for (float D = StrideLength - PrevAccum; D <= Step && Guard < 64; D += StrideLength, ++Guard)
    {
        LayFootprint(LastSampleLocation + StepDir * D, Forward);
    }
    DistanceSinceLastPrint = FMath::Fmod(PrevAccum + Step, StrideLength);
    LastSampleLocation = Current;
}

void UFootprintComponent::LayFootprint(const FVector& OwnerLocation, const FVector& Forward)
{
    UWorld* World = GetWorld();
    if (!World || !FootprintMesh)
    {
        return;
    }

    // Alternate feet: lateral offset perpendicular to travel.
    const FVector Right = FVector(-Forward.Y, Forward.X, 0.0f).GetSafeNormal();
    const float Side = bLeftFoot ? -1.0f : 1.0f;
    bLeftFoot = !bLeftFoot;
    const FVector FootXY = OwnerLocation + Right * (FootLateralOffset * Side);

    // Trace down to the real ground surface to place the print.
    float HalfHeight = 88.0f;
    if (const ACharacter* Char = Cast<ACharacter>(GetOwner()))
    {
        if (Char->GetCapsuleComponent())
        {
            HalfHeight = Char->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
        }
    }
    const FVector TraceStart = FootXY + FVector(0.0f, 0.0f, 10.0f);
    const FVector TraceEnd = FootXY - FVector(0.0f, 0.0f, HalfHeight + 60.0f);
    FVector GroundPoint = FootXY - FVector(0.0f, 0.0f, HalfHeight); // fallback: capsule base

    FHitResult Hit;
    FCollisionQueryParams Params(FName(TEXT("Footprint")), /*bTraceComplex=*/false, GetOwner());
    if (World->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_Visibility, Params))
    {
        GroundPoint = Hit.ImpactPoint;
    }
    GroundPoint.Z += 1.5f; // avoid z-fighting with the ground

    // Flat on the ground, long axis along travel.
    const FRotator Rot(0.0f, Forward.Rotation().Yaw, 0.0f);

    FActorSpawnParameters SpawnParams;
    SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    SpawnParams.ObjectFlags |= RF_Transient; // ephemeral — never serialized into the level

    AStaticMeshActor* Print = World->SpawnActor<AStaticMeshActor>(
        AStaticMeshActor::StaticClass(), GroundPoint, Rot, SpawnParams);
    if (!Print)
    {
        return;
    }

    if (UStaticMeshComponent* MeshComp = Print->GetStaticMeshComponent())
    {
        MeshComp->SetMobility(EComponentMobility::Movable);
        MeshComp->SetStaticMesh(FootprintMesh);
        if (FootprintMaterial)
        {
            MeshComp->SetMaterial(0, FootprintMaterial);
        }
        MeshComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        MeshComp->SetCastShadow(false);

        // Plane is 100uu square; scale to a boot-sized imprint.
        const float SX = FootprintLength / 100.0f;
        const float SY = (FootprintLength * 0.4f) / 100.0f;
        Print->SetActorScale3D(FVector(SX, SY, 1.0f));
    }

    if (FootprintLifeSpan > 0.0f)
    {
        Print->SetLifeSpan(FootprintLifeSpan);
    }

    ++FootprintsSpawned;
}
