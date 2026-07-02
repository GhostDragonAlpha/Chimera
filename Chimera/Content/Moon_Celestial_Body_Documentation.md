# Moon Celestial Body Setup Guide — Holodeck Convergence

## Overview

This guide documents the step-by-step process for creating `SM_Moon`, a Nanite-enabled static mesh actor representing the Moon at realistic scaled distance from Earth. The Moon uses inverse-square apparent size calculations and is managed by `BP_CelestialBodyController` Blueprint for dynamic positioning based on player distance.

## Prerequisites

- **Project**: Chimera (Unreal Engine 5.8) at `E:\PythonChimera\Chimera`
- **Map**: `Lvl_Offroad.umap` / `PlanetEarthSeed.umap` with Earth-scale landscape
- **Existing Components**: `SphericalGravityComponent`, `LagrangeTransitionZone` in `Source/Chimera/`

## Step 1: Create Moon Static Mesh (SM_Moon)

1. Open UE Editor and load the Chimera project.
2. Navigate to **Content** → right-click → **Static Mesh** → create new sphere mesh named `SM_Moon`.
3. In the **Details panel**:
   - Enable **Nanite** (check the Nanite checkbox in the Static Mesh properties).
   - Set **LOD Group** to `WorldLevel` for optimal rendering at distance.
4. Configure the sphere geometry:
   - Radius: `1737400.0` (Moon radius in meters, scaled to world units as needed)
   - Segment count: `64` (high enough detail for Nanite rendering)

## Step 2: Position Moon at Realistic Scaled Distance

1. Create a new Actor Blueprint named `BP_MoonActor` → select **Empty Actor** as parent.
2. Add the `SM_Moon` static mesh as a child component of the actor.
3. Set the actor's world transform:
   - Location: `(0, 384400000.0, 0)` — Moon at realistic scaled distance from Earth center (X,Y in world space).
   - Rotation: `(0, 0, 0)` — No rotation needed for spherical body.

## Step 3: Implement Inverse-Square Apparent Size Calculations

1. Open `BP_MoonActor` in the Blueprint Editor.
2. Add a **Scalar Parameter** variable named `ApparentRadius`:
   - Default Value: `1737400.0` (Moon radius)
3. In the **Event Graph**, add a **Tick** event:
   - Get player location from `GetPlayerPawn()` or owner actor.
   - Calculate distance to Moon center using **Distance** node between player location and Moon location.
   - Divide `ApparentRadius` by the calculated distance using a **Divide** node.
   - Multiply result by `MorphFactor` (from `SphericalGravityComponent`) for smooth scaling.

This implements: `apparent_radius = actual_radius / distance`, matching the WPO material formula.

## Step 4: Create BP_CelestialBodyController Blueprint

1. Create a new Blueprint Class → select **Actor** as parent → name it `BP_CelestialBodyController`.
2. Add variables for celestial body references:
   - `MoonActor` — Type: `BP_MoonActor`, Default: reference to `SM_Moon` actor.
   - `EarthCenterPosition` — Type: `FVector2D`, Default: `(0, 0)`.
3. In the **Event Graph**:
   - On **BeginPlay**, get references to all celestial body actors in the world using **Get All Actors Of Class** node.
   - Store references in a **Array** variable for batch processing.
4. Add a **Tick** event:
   - For each celestial body, calculate distance from player position.
   - Apply inverse-square apparent size formula to scale the mesh.
   - Enable/disable rendering based on frustum culling (only render when visible).

## Step 5: Configure LOD Management and Frustum Culling

1. In `SM_Moon` static mesh properties:
   - Set **LOD Distance** values for multiple levels of detail.
   - Enable **Distance-Based LODs** to reduce polygon count at extreme distances.
2. In `BP_CelestialBodyController`:
   - Add a **Component Visibility** check in the Tick event.
   - Only render celestial bodies when they are within the camera frustum and above a minimum distance threshold (to avoid rendering objects too far away).

## Verification Checklist

- [ ] Static mesh `SM_Moon` is created with Nanite enabled and correct radius.
- [ ] Actor `BP_MoonActor` is positioned at realistic scaled distance `(0, 384400000.0, 0)`.
- [ ] Inverse-square apparent size formula (`apparent_radius = actual_radius / distance`) is implemented in the Blueprint.
- [ ] Blueprint `BP_CelestialBodyController` manages celestial body positioning and LOD management.
- [ ] TES screenshot analysis confirms Moon appears at correct distance with appropriate apparent size.

## Notes

- The Moon's position uses 64-bit double precision math for large-scale coordinate tracking (as implemented in `SphericalGravityComponent`).
- Nanite rendering handles the sphere geometry efficiently even at extreme distances.
- Frustum culling ensures only visible celestial bodies are rendered, optimizing performance.
- For multi-player scenarios, each player's position is used to calculate apparent size independently.
