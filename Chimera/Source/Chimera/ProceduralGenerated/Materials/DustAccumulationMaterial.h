// Procedural dust-accumulation mask material using procedural noise functions (Perlin/Voronoi), vertex normal-based masking, and crevice accumulation logic.
#pragma once

#include "CoreMinimal.h"
#include "Materials/MaterialInterface.h"
#include "DustAccumulationMaterial.generated.h"

/**
 * Procedural dust-accumulation mask material using procedural noise functions (Perlin/Voronoi) and vertex normal-based masking.
 * 
 * Material Expression Nodes Used:
 * - add_vertex_normal: UMaterialExpressionVertexNormalWS for world-space surface normals
 * - DotProduct: Compare vertex normal with world Z-axis (0,0,1) or down vector (0,0,-1)
 * - add_noise / add_voronoi: Procedural noise for organic variation
 * - Lerp/Multiply: Combine normal factor and noise mask
 * 
 * Vertex Normal Utilization:
 * - Upward surfaces (normal.z > 0.3) skip accumulation -> 0.0x multiplier
 * - Downward-facing horizontal surfaces (|normal.z| > 0.8 and normal.z < -0.8) -> full 1.0x
 * - Downward-facing surfaces (normal.z < -0.3 but >= -0.8) -> 0.8x multiplier
 * - Transitional zone (normal.z in [-0.3, 0.3]) -> linear interpolation from 0.8 to 0.0
 * Formula: accumulation_density = saturate(1.0 - normal.z) * noise_mask
 */
UCLASS()
class CHIMERA_API UDustAccumulationMaterial : public UMaterialInterface
{
	GENERATED_BODY()

public:
	UDustAccumulationMaterial();

public:
	/** Get dust accumulation intensity based on vertex normal and time */
	UFUNCTION(BlueprintCallable, Category = "Materials|Dust")
	float GetDustIntensity(FVector VertexNormal, float Time);

	/** Calculate surface angle-based dust factor using threshold logic */
	UFUNCTION(BlueprintCallable, Category = "Materials|Dust")
	float CalculateSurfaceAngleFactor(float NormalZ, float SurfaceAngleBias);

	/** Apply procedural noise mask for dust accumulation (2-octave Perlin + 1-octave Cellular) */
	UFUNCTION(BlueprintCallable, Category = "Materials|Dust")
	float GenerateProceduralNoise(float X, float Y, float Time, bool bUseCellular);

	/** Get combined dust intensity: surface angle factor + procedural noise */
	UFUNCTION(BlueprintCallable, Category = "Materials|Dust")
	float GetCombinedDustIntensity(FVector VertexNormal, float Time, float InNoiseScale, bool bUseCellular);

	/** Apply procedural noise mask to dust accumulation */
	UFUNCTION(BlueprintCallable, Category = "Materials|Dust")
	void ApplyNoiseMask(float NoiseScale, float AccumulationStrength);

	// Parameters for dust-accumulation material
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Materials|Dust")
	float NoiseScale;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Materials|Dust")
	float AccumulationStrength;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Materials|Dust")
	float SurfaceAngleBias;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Materials|Dust")
	FLinearColor DustColor;

private:
	float CurrentAccumulation;
};
