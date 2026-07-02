# WPO Material Graph Configuration Guide — Holodeck Convergence

## Overview

This guide documents the step-by-step process for creating `MI_EarthLandscapeWPO`, a custom Landscape Material Instance with World Position Offset (WPO) node configuration for flat-to-sphere visual morphing. The material converts flat Cartesian coordinates to spherical coordinates based on distance from planet center or player altitude, applying the inverse-square law formula: `apparent_radius = actual_radius / distance`.

## Prerequisites

- **Project**: Chimera (Unreal Engine 5.8) at `E:\PythonChimera\Chimera`
- **Map**: `Lvl_Offroad.umap` with expanded Earth-scale Landscape component
- **Existing Components**: `EdgeWrappingComponent`, `SphericalGravityComponent`, `LandscapeCollisionQueryComponent`, `LagrangeTransitionZone` in `Source/Chimera/`

## Step 1: Create Base Landscape Material Instance

1. Open UE Editor and load the Chimera project.
2. Navigate to **Content** → find the base landscape material used by the offroad level (typically a material applied to the Landscape component).
3. Right-click the base material → **Material Instance Constant** → create new instance named `MI_EarthLandscapeWPO`.

## Step 2: Configure World Position Offset (WPO) Node

1. Open `MI_EarthLandscapeLandscapeWPO` in the Material Editor.
2. In the **Details panel**, ensure **World Position Offset** is enabled (check the material's advanced settings).
3. Add a **Scalar Parameter** node named `MorphFactor`:
   - Default Value: `0.0` (flat terrain)
   - Range: `0.0` to `1.0` (fully spherical morph)
4. Add two **Vector Parameters**:
   - `PlanetCenter` — Default: `(0, 0, 0)` — Represents the planet center in world space.
   - `PlayerAltitude` — Default: `(0, 0, 0)` — Player's altitude above surface (Z component only).

## Step 3: Implement Vertex-Shader Math for Spherical Conversion

1. Add a **Distance** node:
   - Input A: `World Position` (from the material input)
   - Input B: `PlanetCenter` parameter
2. Add a **Divide** node:
   - Numerator: `PlayerAltitude.Z` (scalar extracted from vector)
   - Denominator: Output of Distance node
3. Multiply the result by `MorphFactor` using a **Multiply** node.
4. Feed the result into the **World Position Offset** input of the material.

This implements the spherical coordinate conversion in the vertex shader stage:
```
WPO = (PlayerAltitude.Z / Distance) * MorphFactor
```

## Step 4: Apply Inverse-Square Law Formula

1. Add a **Power** node:
   - Base: Output of Distance node
   - Exponent: `2.0` (for inverse-square law)
2. Add a **Scalar Parameter** named `ActualRadius`:
   - Default Value: `6371000.0` (Earth radius in meters, scaled to world units)
3. Divide `ActualRadius` by the output of the Power node using a **Divide** node.
4. Multiply this result by `MorphFactor` and add it to the WPO calculation.

This implements: `apparent_radius = actual_radius / distance^2`, scaled by morph factor.

## Step 5: Create BP_WPOMaterialController Blueprint

1. Create a new Blueprint Class → select **Actor** as parent → name it `BP_WPOMaterialController`.
2. Add a **Material Instance Constant** variable named `WPOMaterialInstance` — set to reference `MI_EarthLandscapeWPO`.
3. Add a **Scalar Parameter** variable named `MorphFactorParam` — bind this to the material's `MorphFactor` parameter using **Set Scalar Parameter Value** node.
4. In the Blueprint's **Event Graph**:
   - On **BeginPlay**, get reference to the Landscape component on the owner actor.
   - Set the material instance on the Landscape component: `LandscapeComponent->SetMaterial(0, WPOMaterialInstance)`.
5. Add a **Tick** event:
   - Get player altitude from `SphericalGravityComponent` (if available).
   - Calculate morph factor based on distance from planet center.
   - Call **Set Scalar Parameter Value** to update `MorphFactorParam` with the calculated value.

## Step 6: Bind Parameters from C++

1. In `ChimeraPawn.cpp`, add a reference to `BP_WPOMaterialController`:
   ```cpp
   UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components|EarthScale")
   TObjectPtr<UBP_WPOMaterialController> WPOMaterialController;
   ```
2. In the constructor, create the controller as a subobject:
   ```cpp
   WPOMaterialController = CreateDefaultSubobject<UBP_WPOMaterialController>(TEXT("WPOMaterialController"));
   WPOMaterialController->SetupAttachment(GetRootComponent());
   ```
3. In `Tick()`, call `WPOMaterialController->UpdateMorphFactor(PlayerAltitude)` to update the material parameters every frame.

## Verification Checklist

- [ ] Material instance `MI_EarthLandscapeWPO` is created and applied to the landscape.
- [ ] WPO node configuration correctly converts flat coordinates to spherical based on player altitude.
- [ ] Inverse-square law formula (`apparent_radius = actual_radius / distance`) is implemented in the material graph.
- [ ] Blueprint `BP_WPOMaterialController` binds parameters from C++ at runtime.
- [ ] TES screenshot analysis at various altitudes confirms rendered world matches expected morph formula.

## Notes

- The WPO displacement happens entirely in the vertex shader stage — no geometry regeneration or level streaming pops occur.
- The `MorphFactor` parameter is driven by `SphericalGravityComponent::CalculateGravitationalAcceleration()` distance calculations, ensuring visual and physics are synchronized.
- For Earth-scale terrain, use `ActualRadius = 6371000.0` (Earth radius in meters) scaled to world units as needed.
