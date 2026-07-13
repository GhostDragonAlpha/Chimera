// Copyright 2026 Chimera Project. All Rights Reserved.
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "FootprintComponent.generated.h"

class UStaticMesh;
class UMaterialInterface;
class UCharacterMovementComponent;
class USoundBase;
class AStaticMeshActor;
struct FHitResult;

/**
 * Movement-driven footprint trail. Attach to any pawn; every StrideLength of
 * horizontal ground travel it lays a small mesh "imprint" at the feet,
 * alternating left/right. Deliberately independent of animation notifies /
 * blend spaces (those never propagated for the demo character — see
 * Ground_Sand_Footprints research) so footprints are deterministic and
 * hard-fact verifiable via the FootprintsSpawned counter.
 *
 * Ground_Sand_Sound: each footfall also plays a surface-aware footstep sound
 * (CC0 Fantozzi pack, see Content/Audio/Footsteps/SOURCES.md) selected from
 * per-foot variant pools with pitch jitter and speed-scaled volume. Sand
 * surfaces get the sand set; everything else falls back to the stone set
 * (generic hard-contact) until metal/water CC0 sources are added. Hard-fact
 * verifiable via the FootstepsPlayed counter and [DEMOBEAT] [GROUND_SOUND]
 * log lines (sleepwalker log_contains / pawn_property_min).
 */
UCLASS(ClassGroup = (Chimera), meta = (BlueprintSpawnableComponent))
class CHIMERA_API UFootprintComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UFootprintComponent();

    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
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

    /**
     * Whether these prints are impermanent (sand — erased by the ~weekly storm,
     * the memento mori of Design Law 4) or durable (metal grating / dug pits —
     * survive storms). Sand is the default surface, so prints are impermanent
     * unless a durable-surface layer flips this. Read by UWeatherComponent's
     * storm-pass sweep (EraseAllImpermanent).
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Footprints")
    bool bImpermanentPrints;

    /** Hard-fact verification counter: prints erased by storms this session. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Footprints")
    int32 FootprintsErased;

    /**
     * Destroy every still-living print this component laid, iff it lays
     * impermanent (sand) prints. Returns the number erased. Durable-surface
     * components return 0 and keep their prints. Called by the storm.
     */
    UFUNCTION(BlueprintCallable, Category = "Footprints")
    int32 EraseImpermanent();

    /**
     * Storm authority: erase impermanent prints across EVERY footprint
     * component alive in World (the single global sweep the seed models as
     * `game.footprints = [fp for fp in game.footprints if fp.surface=="METAL"]`).
     * Returns the total erased. Static so UWeatherComponent needs no handle to
     * each pawn's trail — the registry is maintained on BeginPlay/EndPlay.
     */
    static int32 EraseAllImpermanent(const UWorld* World);

private:
    void LayFootprint(const FVector& OwnerLocation, const FVector& Forward);

    /** Live prints this component laid (weak — self-destruct via LifeSpan is fine). */
    UPROPERTY(Transient)
    TArray<TWeakObjectPtr<AStaticMeshActor>> LiveFootprints;

    /** Every registered footprint component, for the storm's world-wide sweep. */
    static TArray<TWeakObjectPtr<UFootprintComponent>> LiveComponents;

    UPROPERTY(Transient)
    UCharacterMovementComponent* CachedMovement;

    FVector LastSampleLocation;
    float DistanceSinceLastPrint;
    bool bLeftFoot;
    bool bInitialized;
};
