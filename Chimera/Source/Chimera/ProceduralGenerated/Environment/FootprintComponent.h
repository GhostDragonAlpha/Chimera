// Copyright 2026 Chimera Project. All Rights Reserved.
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "FootprintComponent.generated.h"

class UStaticMesh;
class UMaterialInterface;
class UCharacterMovementComponent;

/**
 * Movement-driven footprint trail. Attach to any pawn; every StrideLength of
 * horizontal ground travel it lays a small mesh "imprint" at the feet,
 * alternating left/right. Deliberately independent of animation notifies /
 * blend spaces (those never propagated for the demo character — see
 * Ground_Sand_Footprints research) so footprints are deterministic and
 * hard-fact verifiable via the FootprintsSpawned counter.
 */
UCLASS(ClassGroup = (Chimera), meta = (BlueprintSpawnableComponent))
class CHIMERA_API UFootprintComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UFootprintComponent();

    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    /** Horizontal distance (uu) between successive footprints. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Footprints")
    float StrideLength;

    /** Lateral (left/right) offset of each print from the travel centerline (uu). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Footprints")
    float FootLateralOffset;

    /** Footprint length along the walk direction (uu); width is 40% of this. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Footprints")
    float FootprintLength;

    /** Seconds before a footprint destroys itself (0 = keep for the session). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Footprints")
    float FootprintLifeSpan;

    /** Minimum ground speed (uu/s) required to lay prints (rejects jitter). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Footprints")
    float MinSpeed;

    /** Mesh used for each footprint (default: engine plane). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Footprints")
    UStaticMesh* FootprintMesh;

    /** Material applied to each footprint (default: regolith grey). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Footprints")
    UMaterialInterface* FootprintMaterial;

    /** Hard-fact verification counter: total footprints laid this session. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Footprints")
    int32 FootprintsSpawned;

private:
    void LayFootprint(const FVector& OwnerLocation, const FVector& Forward);

    UPROPERTY(Transient)
    UCharacterMovementComponent* CachedMovement;

    FVector LastSampleLocation;
    float DistanceSinceLastPrint;
    bool bLeftFoot;
    bool bInitialized;
};
