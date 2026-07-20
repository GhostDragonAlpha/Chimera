// Procedural dust-accumulation mask material implementation
#include "DustAccumulationMaterial.h"

UDustAccumulationMaterial::UDustAccumulationMaterial()
	: AccumulationRate(0.5f), DecayRate(0.2f), NoiseScale(1.0f), NormalThreshold(0.7f), NoiseFrequency(3.0f), CurrentAccumulation(0.0f)
{
	// Dust tuning knobs (previously declared but unwired): neutral strength, no
	// angle bias, and a dusty-tan tint by default — all assignable in BP.
	AccumulationStrength = 1.0f;
	SurfaceAngleBias = 0.0f;
	DustColor = FLinearColor(0.55f, 0.45f, 0.35f, 1.0f);
}

float UDustAccumulationMaterial::GetDustIntensity(FVector VertexNormal, float Time)
{
	// Calculate dust intensity based on vertex normal and procedural noise
	float NormalFactor = FMath::Max(0.0f, VertexNormal.Z); // Z component for horizontal surfaces

	// Simple procedural noise using sin/cos for variation
	float NoiseValue = FMath::Sin(VertexNormal.X * 3.0f + Time) * FMath::Cos(VertexNormal.Y * 5.0f + Time);
	NoiseValue = (NoiseValue + 1.0f) * 0.5f; // Normalize to [0, 1]

	// Combine normal factor and noise for final intensity, scaled by the
	// configured accumulation strength (previously dead config).
	float Intensity = ((NormalFactor * AccumulationRate) + (NoiseValue * 0.3f)) * AccumulationStrength;
	Intensity = FMath::Clamp(Intensity, 0.0f, 1.0f);

	return Intensity;
}

float UDustAccumulationMaterial::CalculateNormalFactor(const FVector& VertexNormal, float Threshold)
{
	// Calculate dot product with world down vector (0,0,-1) for downward-facing surfaces
	// Or use world up vector (0,0,1) for upward-facing horizontal surfaces

	// For dust accumulation: surfaces facing DOWNWARD (negative Z) or HORIZONTAL (Z near 0)
	// Calculate the "up-facing" factor: dot(VertexNormal, (0,0,1))
	float UpFacingFactor = FVector::DotProduct(VertexNormal, FVector(0.0f, 0.0f, 1.0f));

	// Dust accumulates on surfaces that are NOT facing up (i.e., facing down or sideways)
	// So we use: max(0, 1 - UpFacingFactor) which gives:
	// - 0 for perfectly upward-facing (Normal=(0,0,1)) -> no dust
	// - 1 for perfectly downward-facing (Normal=(0,0,-1)) -> full dust accumulation
	// - ~0.5 for horizontal surfaces (Normal=(1,0,0) or similar with Z=0) -> moderate dust

	// SurfaceAngleBias shifts how readily an angled surface collects dust
	// (previously dead config): positive bias = more dust on shallower angles.
	float DownFacingFactor = FMath::Clamp(FMath::Max(0.0f, 1.0f - UpFacingFactor) + SurfaceAngleBias, 0.0f, 1.0f);

	// Apply threshold to create sharp transition for horizontal vs vertical surfaces
	if (UpFacingFactor > Threshold)
	{
		return 0.0f; // No dust on upward-facing surfaces above threshold
	}

	// Smooth falloff below threshold
	float NormalFactor = DownFacingFactor * (1.0f - FMath::Max(0.0f, UpFacingFactor));
	return FMath::Clamp(NormalFactor, 0.0f, 1.0f);
}

float UDustAccumulationMaterial::GenerateProceduralNoise(float X, float Y, float Time, bool bUseVoronoi)
{
	if (bUseVoronoi)
	{
		// Voronoi/Worley noise implementation using cell-based distance calculation
		int32 Xi = FMath::FloorToInt(X * NoiseFrequency);
		int32 Yi = FMath::FloorToInt(Y * NoiseFrequency);

		float MinDistance = 1000.0f;

		// Check neighboring cells (3x3 grid for Voronoi)
		for (int32 ix = -1; ix <= 1; ++ix)
		{
			for (int32 iy = -1; iy <= 1; ++iy)
			{
				// Pseudo-random point in cell using hash function
				int32 seed = (Xi + ix) * 73856093 ^ (Yi + iy) * 19349663 ^ FMath::TruncToInt(Time * 1000);

				float fx = FMath::Frac(FMath::Sin(float(seed)) * 43758.5453f);
				float fy = FMath::Frac(FMath::Cos(float(seed + 12345)) * 23421.341f);

				FVector2D CellPoint(fx, fy);
				FVector2D SamplePos(X * NoiseFrequency - float(Xi + ix), Y * NoiseFrequency - float(Yi + iy));

				float Dist = (SamplePos - CellPoint).Size();
				MinDistance = FMath::Min(MinDistance, Dist);
			}
		}

		// Normalize to [0, 1] range
		return FMath::Clamp(MinDistance * 2.0f, 0.0f, 1.0f);
	}
	else
	{
		// Perlin-like gradient noise using layered sine waves (Simplex approximation)
		float Value = 0.0f;
		float Amplitude = 1.0f;
		float Frequency = NoiseFrequency;

		// 3 octaves for organic variation
		for (int i = 0; i < 3; ++i)
		{
			Value += FMath::Sin(X * Frequency + Time * 0.5f) * FMath::Cos(Y * Frequency * 1.3f + Time * 0.3f);
			Frequency *= 2.0f;
			Amplitude *= 0.5f;
		}

		// Normalize to [0, 1] range
		Value = (Value + 1.0f) * 0.5f * Amplitude; // Scale by last amplitude
		return FMath::Clamp(Value, 0.0f, 1.0f);
	}
}

float UDustAccumulationMaterial::GetCombinedDustIntensity(FVector VertexNormal, float Time, float InNoiseScale, bool bUseVoronoi)
{
	// Step 1: Calculate normal-based factor using dot product with down vector
	float NormalFactor = CalculateNormalFactor(VertexNormal, NormalThreshold);

	// Step 2: Generate procedural noise for organic variation
	float X = VertexNormal.X * InNoiseScale;
	float Y = VertexNormal.Y * InNoiseScale;
	float NoiseMask = GenerateProceduralNoise(X, Y, Time, bUseVoronoi);

	// Step 3: Combine normal factor and noise using Lerp-like approach
	// Base accumulation from normal + organic variation from noise
	float CombinedIntensity = FMath::Lerp(
		NormalFactor, // Base value when no noise (0 to NormalFactor)
		NormalFactor * NoiseMask, // Noisy value
		InNoiseScale // Blend between them based on InNoiseScale parameter
	);

	// Apply accumulation rate + configured strength, then clamp.
	CombinedIntensity = CombinedIntensity * AccumulationRate * AccumulationStrength;
	return FMath::Clamp(CombinedIntensity, 0.0f, 1.0f);
}

void UDustAccumulationMaterial::ApplyNoiseMask(float InNoiseScale, float InNoiseFrequency)
{
	// Apply and validate procedural noise parameters
	NoiseScale = FMath::Clamp(InNoiseScale, 0.0f, 10.0f);
	NoiseFrequency = FMath::Clamp(InNoiseFrequency, 0.1f, 20.0f);
}

FLinearColor UDustAccumulationMaterial::GetDustColorAt(FVector VertexNormal, float Time)
{
	// The dust tint (previously dead config) scaled by the accumulation at this
	// point — what a material param-setter or renderer samples.
	const float Intensity = GetCombinedDustIntensity(VertexNormal, Time, NoiseScale, false);
	return DustColor * Intensity;
}
