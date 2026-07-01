"""
Flight Physics Engine — Adds Star Citizen-style thrust vectoring and attitude control.
Generates updated C++ files for ChimeraPawn with advanced flight systems.
"""

import os


def generate_thrust_vectoring():
    """Generate ThrustVectoringComponent.h/.cpp for directional thrust."""
    
    source_dir = r"E:\PythonChimera\Chimera\Source\Chimera"
    
    header = '''// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ThrustVectoringComponent.generated.h"

UCLASS(ClassNoGenerateOptions, meta=(BlueprintType, Category="Flight"))
class CHIMERA_API UThrustVectoringComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UThrustVectoringComponent(const FObjectInitializer& ObjectInitializer);

protected:
	// Thrust vectoring angle in degrees (0 = straight, max = full deflection)
	UPROPERTY(EditAnywhere, Category="Flight|Vectoring")
	float MaxVectorAngle = 45.0f;

	// Vectoring response speed (degrees per second)
	UPROPERTY(EditAnywhere, Category="Flight|Vectoring")
	float VectorResponseSpeed = 180.0f;

public:
	UFUNCTION(BlueprintCallable, Category="Flight|Input")
	void SetThrustAngle(float PitchAngle, float YawAngle);

	UFUNCTION(BlueprintCallable, Category="Flight|Physics")
	FVector GetThrustDirection() const;

protected:
	virtual void TickComponent(float DeltaTime, enum ETickType TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	// Current thrust vector angles (degrees)
	float CurrentPitchAngle = 0.0f;
	float CurrentYawAngle = 0.0f;

	// Target angles for smooth interpolation
	float TargetPitchAngle = 0.0f;
	float TargetYawAngle = 0.0f;
};
'''

    source = '''// Copyright Epic Games, Inc. All Rights Reserved.

#include "ThrustVectoringComponent.h"
#include "GameFramework/Actor.h"
#include "Math/UnrealMathFunctions.h"

UThrustVectoringComponent::UThrustVectoringComponent(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UThrustVectoringComponent::SetThrustAngle(float PitchAngle, float YawAngle)
{
	TargetPitchAngle = FMath::Clamp(PitchAngle, -MaxVectorAngle, MaxVectorAngle);
	TargetYawAngle = FMath::Clamp(YawAngle, -MaxVectorAngle, MaxVectorAngle);
}

FVector UThrustVectoringComponent::GetThrustDirection() const
{
	if (!GetOwner()) return FVector::ZeroVector;
	
	UActor* Owner = GetOwner();
	FVector ForwardDir = Owner->GetActorForwardVector();
	FVector RightDir = Owner->GetActorRightVector();
	FVector UpDir = Owner->GetActorUpVector();

	// Apply pitch (rotation around right axis) and yaw (rotation around up axis)
	float PitchRad = FMath::DegreesToRadians(CurrentPitchAngle);
	float YawRad = FMath::DegreesToRadians(CurrentYawAngle);

	FVector ThrustDir = ForwardDir;
	ThrustDir += RightDir * FMath::Sin(PitchRad);
	ThrustDir += UpDir * FMath::Sin(YawRad);
	ThrustDir = ThrustDir.GetSafeNormal();

	return ThrustDir;
}

void UThrustVectoringComponent::TickComponent(float DeltaTime, enum ETickType TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!GetOwner()) return;

	// Smoothly interpolate current angles toward target angles
	float InterpSpeed = VectorResponseSpeed * DeltaTime;
	CurrentPitchAngle = FMath::FInterpTo(CurrentPitchAngle, TargetPitchAngle, DeltaTime, 10.0f);
	CurrentYawAngle = FMath::FInterpTo(CurrentYawAngle, TargetYawAngle, DeltaTime, 10.0f);
}
'''

    header_path = os.path.join(source_dir, "ThrustVectoringComponent.h")
    source_path = os.path.join(source_dir, "ThrustVectoringComponent.cpp")

    with open(header_path, 'w', encoding='utf-8') as f:
        f.write(header)

    with open(source_path, 'w', encoding='utf-8') as f:
        f.write(source)

    print(f"[OK] Generated ThrustVectoringComponent.h")
    print(f"[OK] Generated ThrustVectoringComponent.cpp")


def generate_attitude_stabilizer():
    """Generate AttitudeStabilizerComponent for automatic orientation control."""
    
    source_dir = r"E:\PythonChimera\Chimera\Source\Chimera"
    
    header = '''// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AttitudeStabilizerComponent.generated.h"

UCLASS(ClassNoGenerateOptions, meta=(BlueprintType, Category="Flight"))
class CHIMERA_API UAttitudeStabilizerComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UAttitudeStabilizerComponent(const FObjectInitializer& ObjectInitializer);

protected:
	// Enable/disable automatic stabilization
	UPROPERTY(EditAnywhere, Category="Flight|Stabilization")
	bool bAutoStabilize = false;

	// Stabilization strength (0 = none, 1 = full)
	UPROPERTY(EditAnywhere, Category="Flight|Stabilization", meta=(ClampMin="0.0", ClampMax="1.0"))
	float StabilizationStrength = 0.5f;

public:
	UFUNCTION(BlueprintCallable, Category="Flight")
	void ToggleAutoStabilize();

	UFUNCTION(BlueprintCallable, Category="Flight")
	bool IsAutoStabilizing() const { return bAutoStabilize; }

protected:
	virtual void TickComponent(float DeltaTime, enum ETickType TickType, FActorComponentTickFunction* ThisTickFunction) override;
};
'''

    source = '''// Copyright Epic Games, Inc. All Rights Reserved.

#include "AttitudeStabilizerComponent.h"
#include "GameFramework/Actor.h"
#include "Math/UnrealMathFunctions.h"

UAttitudeStabilizerComponent::UAttitudeStabilizerComponent(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UAttitudeStabilizerComponent::ToggleAutoStabilize()
{
	bAutoStabilize = !bAutoStabilize;
}

void UAttitudeStabilizerComponent::TickComponent(float DeltaTime, enum ETickType TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!bAutoStabilize || !GetOwner()) return;

	UActor* Owner = GetOwner();
	if (UPrimitiveComponent* PrimComp = Owner->GetRootPrimitiveComponent())
	{
		FVector CurrentAngVel = PrimComp->GetAngularVelocity();

		// Dampen angular velocity to stabilize orientation
		float DampingFactor = 1.0f - (StabilizationStrength * DeltaTime * 5.0f);
		DampingFactor = FMath::Clamp(DampingFactor, 0.0f, 1.0f);

		CurrentAngVel *= DampingFactor;

		PrimComp->SetAngularVelocity(CurrentAngVel, false);
	}
}
'''

    header_path = os.path.join(source_dir, "AttitudeStabilizerComponent.h")
    source_path = os.path.join(source_dir, "AttitudeStabilizerComponent.cpp")

    with open(header_path, 'w', encoding='utf-8') as f:
        f.write(header)

    with open(source_path, 'w', encoding='utf-8') as f:
        f.write(source)

    print(f"[OK] Generated AttitudeStabilizerComponent.h")
    print(f"[OK] Generated AttitudeStabilizerComponent.cpp")


def run_all():
    """Generate all flight system components."""
    print("=" * 60)
    print("GENERATING ADVANCED FLIGHT SYSTEM COMPONENTS")
    print("=" * 60)

    generate_thrust_vectoring()
    generate_attitude_stabilizer()

    print("\n" + "=" * 60)
    print("ALL COMPONENTS GENERATED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    run_all()
