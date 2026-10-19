# Chimera Studio — native construction inside Blender

This is an isolated, working authoring bridge and Blender source fork. The main agents' engine checkout and model services are not used as runtime servers and have not been changed by this integration.

## Start

Double-click **D:/Chimera-Maintenance/ChimeraStudio/Start Chimera Studio.cmd**.
The launcher uses the completed custom build when available, otherwise the existing Blender 5.0.1 executable with the same integration. It uses private configuration under `integration/.user`; normal Blender preferences are untouched.

1. Open the **Chimera** tab in the viewport's right sidebar (N toggles it).
2. Choose **Add Starter Workshop**, then **Build Selected Regions**.
3. The starter regions have aligned marked faces. Optionally choose **Join Two Marked Mounts** before advancing. Choose **Step 20 ms** or **Play / Pause**. Blender displays poses produced by the pinned native Chimera solver.
4. Choose **Inspect Recorded State** to restore a recorded physical checkpoint; continuing branches from that state. **Restore Built State** resets the trial.
5. Save the project normally as a `.blend`. Its editable geometry, material properties and current native physical state are retained. Reopening with this launcher restores the trial paused. You can also exchange a separate `.chimera.json` using **Save/Open Physical Trial**.
6. **Return to Authoring** restores your editable objects. Rebuild explicitly after editing. Saving in authoring mode removes the embedded old physical trial.

## Materials and connections

Each separate mesh is one material region. Select an object, pick a profile and choose **Assign Physical Material**. Density and friction are editable. Timber/steel/stone are explicitly authored demonstration values, not validated strength, elasticity or fracture laws. Viewport colors identify these regions; normal render material appearance remains a separate concern.

The first bridge accepts **2–6 closed convex mesh regions**, **4–128 boundary triangles per region**, meters and Unit Scale 1. Open, concave, disconnected, degenerate or excessive geometry is refused; it is never silently replaced by a box. Import through Blender's existing importers, then prepare supported separate regions. Arbitrary CAD solids and layered printer files still need semantic adapters/decomposition.

To connect two regions: apply modifiers, select exactly one mesh face in Edit Mode on each region and use **Mark Selected Face as Mount**. Position the two faces together, opposing each other (within 10 micrometers), switch to Object Mode, select both regions and Build. Use **Join Two Marked Mounts** before stepping. This uses three non-collinear anchor pairs and the existing native finite-area spring/damper connection. Initial fixed demonstration stiffness is 5,000 N/m and damping 30 N·s/m; it is not a universal adhesive/material claim. Only two marked mounts are supported by this initial UI. Native engine pools remain unchanged.

A saved trial requires the same pinned engine-source identity. An incompatible trial is refused; the `.blend` geometry is retained. Replay stores at most 240 snapshots and 32 MiB in memory. Saving stores the current native state and built baseline, not the complete replay history. Blender's ordinary animation timeline does not control native physics.

## What is implemented

- Original material-volume compiler integrates region mass, center of mass and inertia.
- Original C++ `B2Scene` owns rigid motion, gravity, contacts and finite-area connections.
- A small C ABI DLL owns a private scene; Python manages authoring and synchronizes one pose per part.
- Blender's main-thread timer advances every admitted 1/4000 s native substep. A maximum 200-step call limits editor blocking; it does not skip simulation steps. If the editor cannot keep up, simulation falls behind wall time.
- Native checkpoint restore, replay branching, physical trial exchange, and `.blend` reopen work.
- There is no live dependency on the agents' shared renderer process or model servers.

## Deliberate initial boundary

This does **not** yet embed Chimera's full Vulkan renderer, CA/membrane GPU update, deforming tissue, pressure/thermal UI, arbitrary concave decomposition, fracture, or trained response catalogs. Those must reuse their existing engine owners in the next bridge increments. Blender provides the current viewport. These tests qualify two-part construction, not a complete game or large-scene frame rate.

The source build keeps Blender modeling, editing and the workbench viewport. Cycles, OpenImageDenoise, USD/Hydra, OpenVDB/fluid/NanoVDB and upstream GTests are disabled in this initial build. This saves build cost and avoids a second simulation/render stack being mistaken for Chimera's engine. The ordinary installed Blender remains available for those workflows.

## Rebuild and checks

From this directory, `./tools/Build-Native.ps1` builds the private DLL. `./tools/Test-Studio.ps1` runs actual Blender-background integration and application-template tests. `./tools/Build-Fork.ps1` configures/builds the already cloned Blender fork with two compiler jobs. `./tools/Test-Studio.ps1 -Gui` also opens a small visible viewport test and closes it automatically. Visual interaction testing is recorded separately; a headless pass is not a GUI performance claim.

`SOURCE_LOCK.json` pins actual source bytes copied from the agents' dirty checkout; `source_head` alone is not sufficient to reproduce them. Do not overwrite `vendor/chimera` from a moving checkout automatically. A future engine update must intentionally refresh the snapshot and rerun the boundary checks. `evidence/headless_integration.json` contains results, including native timing on the small fixture. `evidence/first-run-input-precision.json` retains the initial failure which exposed float32 transform precision loss; the adapter now transforms in float64.

## Source ownership

Blender fork: `../blender`, branch `chimera/studio-v5.0.1`, upstream tag `v5.0.1` (a3db93c5b2595a79f65f304114c23aeef8c2139f). Source edits are window branding and a Chimera application template. Integration: this directory. Build output: `../build-blender`; no shared engine build directory is used. No public fork/release is implied by these local repositories.

`LICENSE` preserves the source project's AGPL-3.0 license. Original Blender license files remain in its fork. `vendor/chimera` is an unchanged attributed snapshot; see `SOURCE_LOCK.json`. Integration source is AGPL-3.0-or-later. Application template and Blender edits retain Blender-compatible GPL-3.0-or-later headers. Keep these notices and source available with any later distribution.
