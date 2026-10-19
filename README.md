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

## GPU matter workspace (2026-10-19)

Open **Chimera → GPU Matter** in the right sidebar. The existing rigid construction tools remain in the expandable **Rigid Construction** panel.

- **Membrane:** Add Membrane GPU Fixture → Build Membrane on GPU → Apply Center Load. The pinned seven-vertex fixture exercises the existing Vulkan surface-energy/deformation path. To author your own supported membrane, use a single closed triangular fan, apply modifiers, select exactly one center vertex in Edit Mode, then build. The native law pins every other vertex and moves the center on a world-Z rail. Surface tension is J/m², not a generic stiffness or a validated wood/steel model.
- **CA water:** select one triangle on an edge-connected mesh, then Build CA Water Field and Advance Native GPU Step. Blender shows the original native `water_depth`, `water_color`, and `water_occ` field as per-face colors; it does not integrate the field in Python. The boundary is closed, initial volume is conserved, and the pipe height and `c_local=0.05` are explicitly authored demonstration parameters. This is not free-surface fluid qualification or pressure coupling to the membrane.
- **Saving and replay:** ordinary `.blend` saves embed the last confirmed native checkpoint; Save/Open GPU Matter Trial exchanges `.matter.json`. Reopen displays the saved state without allocating GPU memory. **Resume Saved GPU Matter** explicitly starts a fresh private engine and restores/reproduces the physical state. Replay Native Checkpoint branches the trial. The animation timeline remains presentation only.
- **Memory:** Release Studio GPU Memory closes only Studio's helper and retains the confirmed checkpoint. Return to Matter Authoring also restores editable source visibility and hides the simulated preview. Closing/crashing Blender closes its private child through a Windows job. Slow calls run off the UI thread; a lost native connection retains the last confirmed state and never silently retries a mutation.

The native CA batch API records at most **64 steps (0.64 simulated seconds)**. The editor refuses further advancement instead of dropping steps or resetting flow. A water checkpoint includes the initial substrate, step count, final integer volumes and their hash; replay repeats the same one-step native sequence from the initial state. This is necessary because `/water_state` does not export the internal edge-flow `q_e`. Reinitializing only current volume would change future behavior. A native full-field checkpoint/continuous stepping seam is the next useful extension, not an alternative Python solver.

`GPU_SOURCE_LOCK.json` pins the executable, SPIR-V, protocol client and fixture bytes. The included source is an audit snapshot of the working tree; it is not a claim that an unpublished binary was built from precisely that snapshot. The private helper uses a unique local port and private working directory; the adapter checks listener ownership before sending mutations. Startup requires 384 MiB reported free on the primary GPU and refuses when unavailable; this is a conservative admission guard for these small checks, not a measured large-scene budget. It never unloads models or talks to the agents' engine/model endpoints.

`evidence/gpu-integration.json` records four integration scenarios in the actual custom Blender: fixture energy against the existing independent reference, displayed native geometry under load, exact membrane replay, `.blend`/trial reopening through a new native process, CA conservation and continuation after replay (including the hidden flux state), and refusal/recovery boundaries. `gpu-gui.json` and `gpu-viewport.png` record a real-window native load. `owned-child-test.json` records GPU-child exit after its test parent was terminated. Ten original rigid-workshop checks and the application-template check also pass.

Run `./tools/Test-Studio.ps1 -Gpu` for the real Blender GPU tests (small shared-GPU checks, no model unloading); `tests/test_gpu_lifetime.py` is the Windows lifetime test and needs a Python environment with NumPy. A saved file is validated before replacing the current workshop. Checkpoints are bounded to 240 samples and 8 MiB.

## Current boundary

The two GPU paths and rigid-region bridge have separate native state owners. This increment does **not** couple membrane deformation to water pressure, rigid contacts, artificial-protein admission, fracture or trained response catalogs. The membrane interface has one free center, and the CA field has the native 64-step trial cap. It does not establish full-game frame rate, unrestricted deformable materials or player usability. Blender displays native results; it does not replace the solver. Full-resolution GPU buffer sharing remains future work; this small editor transfers a snapshot only after an explicit operation, never every render frame.

The source build keeps Blender modeling, editing and the workbench viewport. Cycles, OpenImageDenoise, USD/Hydra, OpenVDB/fluid/NanoVDB and upstream GTests are disabled in this initial build. This saves build cost and avoids a second simulation/render stack being mistaken for Chimera's engine. The ordinary installed Blender remains available for those workflows.

## Rebuild and checks

From this directory, `./tools/Build-Native.ps1` builds the private DLL. `./tools/Test-Studio.ps1` runs actual Blender-background integration and application-template tests. `./tools/Build-Fork.ps1` configures/builds the already cloned Blender fork with two compiler jobs. `./tools/Test-Studio.ps1 -Gui` also opens a small visible viewport test and closes it automatically. Visual interaction testing is recorded separately; a headless pass is not a GUI performance claim.

`SOURCE_LOCK.json` pins actual source bytes copied from the agents' dirty checkout; `source_head` alone is not sufficient to reproduce them. Do not overwrite `vendor/chimera` from a moving checkout automatically. A future engine update must intentionally refresh the snapshot and rerun the boundary checks. `evidence/headless_integration.json` contains results, including native timing on the small fixture. `evidence/first-run-input-precision.json` retains the initial failure which exposed float32 transform precision loss; the adapter now transforms in float64.

## Source ownership

Blender fork: `../blender`, branch `chimera/studio-v5.0.1`, upstream tag `v5.0.1` (a3db93c5b2595a79f65f304114c23aeef8c2139f). Source edits are window branding and a Chimera application template. Integration: this directory. Build output: `../build-blender`; no shared engine build directory is used. No public fork/release is implied by these local repositories.

`LICENSE` preserves the source project's AGPL-3.0 license. Original Blender license files remain in its fork. `vendor/chimera` is an unchanged attributed snapshot; see `SOURCE_LOCK.json`. Integration source is AGPL-3.0-or-later. Application template and Blender edits retain Blender-compatible GPL-3.0-or-later headers. Keep these notices and source available with any later distribution.

## Installed build result

The custom executable was built and tested from Blender fork commit `68c79f03362ebc6e41d16a10b77c8f794097e644` and integration source commit `09471402e501619a923c7d516af1d54234897a8a`. Ten background integration checks, the installed application-template check (including configuration isolation), and a short real-window viewport/native-play check passed. See `evidence/build-manifest.json` for exact executable/DLL identities and `evidence/viewport.png` for the actual view. Full scene throughput and human usability remain unmeasured.
