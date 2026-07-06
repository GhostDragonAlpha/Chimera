// Copyright Chimera. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ChimeraMovementComponent.generated.h"

UCLASS(meta = (Blueprintable, Category = "Movement|Walking"))
class CHIMERA_API UChimeraMovementComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UChimeraMovementComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	// === Speed ===
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Walking")
	float WalkSpeed;

	// === Camera offset ===
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Camera")
	float CameraOffsetX;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Camera")
	float CameraOffsetY;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Camera")
	float CameraOffsetZ;

	// === Footsteps ===
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement|Audio")
	float FootstepInterval;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Movement|State")
	FVector CurrentVelocity;

	void SetWalkSpeed(float NewSpeed);
	void GetCameraOffset(FVector& OutOffset) const;

protected:
	float FootstepTimer;
};