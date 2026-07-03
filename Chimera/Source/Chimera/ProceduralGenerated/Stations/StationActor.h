// StationActor.h — Base class for orbital station actors with procedural mesh, lighting, and materials
#pragma once

#include "CoreTypes.h"
#include "GameFramework/Actor.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "StationActor.generated.h"

UCLASS()
class CHIMERA_API AStationActor : public AActor
{
	GENERATED_BODY()

public:
	AStationActor();

protected:
	virtual void BeginPlay() override;

public:

	UPROPERTY(EditAnywhere, Category = "Station")
	FString StationName;

	UPROPERTY(EditAnywhere, Category = "Station|Appearance")
	FLinearColor HullColor;

	UPROPERTY(EditAnywhere, Category = "Station|Appearance")
	float Roughness;

	UPROPERTY(EditAnywhere, Category = "Station|Appearance")
	float Metallic;

	UPROPERTY(EditAnywhere, Category = "Station|Lighting")
	float LightIntensity;

	UPROPERTY(EditAnywhere, Category = "Station|Lighting")
	FLinearColor LightColor;

	UPROPERTY(EditAnywhere, Category = "Station|Structure")
	int32 ModuleCount;

	UPROPERTY(EditAnywhere, Category = "Station|Structure")
	float ModuleRadius;

	UPROPERTY(EditAnywhere, Category = "Station|Structure")
	float ModuleLength;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TArray<UStaticMeshComponent*> HullSegments;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TArray<UPointLightComponent*> InteriorLights;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	UStaticMeshComponent* RootSegment;

	UFUNCTION(BlueprintCallable, Category = "Station|Build")
	void BuildModularHull();

	UFUNCTION(BlueprintCallable, Category = "Station|Lighting")
	void InstallInteriorLighting();

	UFUNCTION(BlueprintCallable, Category = "Station|Materials")
	void ApplyMetallicMaterial(UStaticMeshComponent* Target, const FLinearColor& BaseColor, float InRoughness, float InMetallic);

	UFUNCTION(BlueprintCallable, Category = "Station|Details")
	void AddWearDetails(UStaticMeshComponent* Target);

	UFUNCTION(BlueprintCallable, Category = "Station|Docking")
	void AddDockingPorts();
};
