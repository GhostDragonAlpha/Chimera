# Chimera Studio — native construction inside Blender

This is an isolated, working authoring bridge and Blender source fork. The main agents' engine checkout and model services are not used as runtime servers and have not been changed by this integration.

## Start

Double-click **Chimera Blender** on the Windows desktop, or **D:/Chimera-Maintenance/ChimeraStudio/Start Chimera Studio.cmd**.

This opens **D:/Chimera-Maintenance/ChimeraStudio/Projects/Membrane Workshop/Chimera Membrane Workshop.blend**, your working copy of the tested construction. The launcher never replaces your edits. See [BLENDER_WORKFLOW.md](BLENDER_WORKFLOW.md) for the editing loop and integration plan. Use -ProjectFile with a quoted path for another file, or -Empty for a blank workspace.
The launcher uses the completed custom build when available, otherwise the existing Blender 5.0.1 executable with the same integration. It uses private configuration under `integration/.user`; normal Blender preferences are untouched.

1. Open **Chimera → Membrane Assembly** in Blender's viewport sidebar (N).
2. The default project already contains the assembly; choose **Resume Saved GPU Matter** to calculate. In an empty workspace, choose **Add Existing Three-Film Assembly**. These are the existing mechanism-factory A/B/C films, with their two explicit apex connections. Build explicitly after authoring changes; the saved project can resume directly.
3. Set **Center load N** (start with 0.8) and **Apply Center Load**. Select any computed film to inspect its identity and surface tension. Its vertices and custom normals come from the native GPU presentation buffer, checked against the accepted physical state.
4. **Show Native Render in Image Editor** displays the native engine's own raster image in Blender. Shift-F5 returns that area to the 3D editor. This uses a fixed inspection camera; synchronizing Blender's arbitrary cameras is still open.
5. **Replay Native Checkpoint** restores a confirmed physical sample. Continuing branches from that sample. Save normally as `.blend`, or exchange **Save/Open GPU Matter Trial** (`.matter.json`). Reopening shows the confirmed state offline; **Resume Saved GPU Matter** starts only Studio's private helper.
6. **Return to Matter Authoring** reveals the editable source films. Select films and **Assign Surface Material** to change surface tension; select exactly two films to connect/disconnect their marked apices. Rebuild explicitly after changes. Mark a single selected vertex as the apex when preparing another supported fan.

A tested example is `evidence/membrane-assembly.blend`; the exchange document is `evidence/membrane-assembly.matter.json`. Open the `.blend` through Chimera Studio so its integration is registered. Native state survives helper shutdown. Opening a save does not start the native simulation helper; Blender itself uses normal viewport graphics memory.

**Scope:** this is the Blender interface to Chimera's existing matter systems. No game-plan or game-loop changes are part of this work. Blender supplies editing, selection, materials UI, image viewing and persistence; Chimera owns physical evolution and kernel output. Water remains deferred. The integration exposes missing engine capabilities instead of assigning them invented behavior.

## Connected membrane building blocks

The deliberately frozen `vendor/membrane_blocks/star-transaction.json` was produced by the existing validated `tools.mechanism_factory.native_binding.compile_transaction("assembly.star-k2", ...)`. Its source record/compiler/law identities are retained beside it. Studio has no live import from the agents' checkout. The starter has 601 native vertices, 600 triangles and three selectable film regions. The adapter joins coincident apices, with one stable identity per source piece and explicit connection metadata; it adds no physical force or solver.

**Current supported mechanics:** one shared world-Z rail apex, every rim vertex fixed, constant current-area surface energy, and one uniform surface-tension value across the connected assembly. The existing native load solver computes the equilibrium. Assignment changes that actual parameter; colors identify regions and do not invent different material laws. Mixed surface tensions in a joined assembly are refused because the current native material owner is scalar. Wood/steel/cloth strengths, general deformable joints, arbitrary free membrane motion and multiport dynamics are not supplied by this adapter. Edited geometry/materials are experimental instances, not newly qualified entries in the mechanism catalog.

Supported authoring is 2–6 individually valid closed triangle fans, at most 1,024 combined vertices / 2,048 triangles, meters with Unit Scale 1. Apply modifiers first. Each film has one marked apex. Connect an explicit tree of coincident apices (0.1 micrometer tolerance); rims are supports and cannot be joined by this law. UUID identities survive renaming and saving; duplicated source UUIDs are refused. After duplicating a film, use **Make Selected Films New Instances** and connect its new apex explicitly. Compiled geometry, gamma, regional vertex/face mapping and connection metadata are cross-checked on restore. Standalone `.matter.json` imports reconstruct missing editable source films; existing source objects are preserved rather than overwritten.

## Render-kernel handoff

The native `membrane_demo.comp` presentation stage feeds the same vertex buffer used by the native renderer. Studio's new `GET /membrane_demo_render` requests a synchronized snapshot of that buffer on its owner thread. It includes exact float32 bytes for positions/normals/colors, packed topology, a render-byte hash and the associated accepted-state identity. Blender checks the hash, topology and inverse rigid axis mapping before displaying it. Rejected trial geometry never becomes the accepted preview. Rendering is derived from physics; Blender runs no substitute membrane simulation.

The presentation shader's CSR lookup was repaired: it now selects an adjacent face from the vertex's actual CSR slice, and highlights the declared apex instead of assuming the final vertex. Physics stages 0/1/2/4 are unchanged. Render readback has a five-second native fence deadline and the existing bounded client call; an unresponsive helper exits without discarding Blender's confirmed checkpoint. The helper stays hidden at its requested 384×256 size, without maximizing another window. Full-resolution shared GPU buffers, live camera synchronization, arbitrary Blender shading in the native renderer and continuous native-render viewport streaming remain future integration work.

**Actual checks:** six end-to-end Blender/GPU scenarios and a Blender UI check pass (`evidence/membrane-assembly-checks.json`, `membrane-ui-checks.json`). These exercise the connection operators, material changes, all 601 kernel normals, native image changes after loading, independent edge-length energy/force checks, invalid-input nonmutation, standalone authoring reconstruction and exact fresh-process physical/render continuation. Ten rigid checks, the template check and four offline checkpoint regressions also pass. Initial failed runs are retained with their causes: signed-zero loss in a JSON render stream, test assumptions about Blender float precision/window size, and a UI-test phase exit. Screenshots: `evidence/membrane-blender-viewport.png` and `membrane-blender-native-view.png`.

Run `./tools/Test-Studio.ps1 -Membranes` for the membrane checks plus CPU regressions. Native helper operations stay asynchronous to the Blender UI. Opening saves stays offline, and closing the helper/Blender releases only Studio's owned process. No local agent, model service or live game engine is restarted.

## Rigid-region bridge (separate existing tools)

Expand **Rigid Construction** to use **Add Starter Workshop**, **Build Selected Regions**, **Join Two Marked Mounts**, **Step 20 ms** and **Play / Pause**. Its `.chimera.json` state and native C++ `B2Scene` owner remain separate from the GPU films.

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

**Editor priority:** editable membrane building blocks, material assignment, connections, native kernel output and reliable save/replay inside Blender. Water is an advanced feature and is **experimental/deferred at the user’s direction**. The existing water demonstrator and its completed tests are retained as research evidence; further water development is not a prerequisite for the workshop. Its flow-specific checkpoint API is not a general solid-matter or membrane CA interface.

Open the collapsed **Chimera → Single Membrane / Experimental Fields** panel in the right sidebar. The existing rigid construction tools remain in the expandable **Rigid Construction** panel; connected films have their own **Membrane Assembly** panel above.

- **Membrane:** Add Membrane GPU Fixture → Build Membrane on GPU → Apply Center Load. The pinned seven-vertex fixture exercises the existing Vulkan surface-energy/deformation path. To author your own supported membrane, use a single closed triangular fan, apply modifiers, select exactly one center vertex in Edit Mode, then build. The native law pins every other vertex and moves the center on a world-Z rail. Surface tension is J/m², not a generic stiffness or a validated wood/steel model.
- **Experimental CA water (deferred):** water authoring controls are removed from the panel; existing water save data and research code remain readable. Blender shows the original native `water_depth`, `water_color`, and `water_occ` field as per-face colors; it does not integrate the field in Python. The boundary is closed, initial volume is conserved, and the pipe height and `c_local=0.05` are explicitly authored demonstration parameters. This is not free-surface fluid qualification or pressure coupling to the membrane.
- **Saving and replay:** ordinary `.blend` saves embed the last confirmed native checkpoint; Save/Open GPU Matter Trial exchanges `.matter.json`. Reopen displays the saved state without allocating GPU memory. **Resume Saved GPU Matter** explicitly starts a fresh private engine and restores the physical state. Replay Native Checkpoint branches the trial. The animation timeline remains presentation only.
- **Memory:** Release Studio GPU Memory closes only Studio's helper and retains the confirmed checkpoint. Return to Matter Authoring also restores editable source visibility and hides the simulated preview. Closing/crashing Blender closes its private child through a Windows job. Slow calls run off the UI thread; a lost native connection retains the last confirmed state and never silently retries a mutation.

**Experimental water-CA continuation (2026-10-19): implemented and GPU-tested; further water work deferred.** The isolated native source now advances beyond the former 64-step trial limit. Blender exposes **CA steps per advance** (1–64); each command executes every requested native step. The native endpoint accepts 1–4096 per request and rejects excessive requests without truncation. A 64-bit physical counter and accumulated simulated time are independent of the bounded 65-state volume-history ring. Ring wrap does not restart the injection schedule or flow. No total 64-step cap remains.

Water trials now contain the immutable substrate/coefficients plus a `WCS1` native checkpoint: integer volumes, raw float64 persistent edge flows (`q_e`), depth, absolute step/injection cursor, accumulated time, last timestep and paused automatic-clock configuration/counter. `GET /water_save` and `POST /water_restore` operate on the native owner thread. Restore validates the substrate identity, checksum, dimensions, counters and finite fields before GPU writes; it restores buffers directly without rerunning previous steps. Checkpoint/restore and manual advancement require the automatic clock paused. Observation history starts anew after native restore; Blender's recorded checkpoints remain bounded to 240 samples/8 MiB. Neither path changes the CA shaders or adds a Python physics law.

**Prior CA-runtime checks (before the Blender render-handoff revision):** six integration scenarios passed in the actual Blender executable on the RTX 4090, including 2,310 native water-CA steps, bounded 65-state history, bit-exact fresh-process continuation from a saved checkpoint, nonzero-flow sensitivity, single/batch equivalence, scheduled injections across history wrap, paused-clock restoration and invalid-state refusal. The first run exposed a CA-only helper clock idling without a display mesh; the isolated engine now includes an active CA clock in its frame-work condition, and the full rerun passes. Four CPU-only checkpoint checks, ten rigid-workshop checks and the template check also pass. `evidence/gpu-integration.json` and `ca-continuation-status.json` record the exact scope and runtime; `ca-gpu-first-run.json` retains the failure. These small-fixture results do not qualify water as a product feature, solid-matter behavior or full-game throughput. No local agents or model services were interrupted.

`GPU_SOURCE_LOCK.json` now pins the isolated source-built executable in `runtime/gpu`, compiled SPIR-V, full `native/gpu_engine` source, client and fixture bytes. The latest manifest includes the Blender presentation fixes; earlier CA evidence retains its own tested runtime hash. `GPU_ENGINE_BASE_LOCK.json` records the deliberate source-fork baseline. The original `vendor/gpu` binary/source snapshot and its previous lock remain intact. Rebuild/repin explicitly with `./tools/Build-Gpu.ps1`; no agents build is copied automatically. Trial schema v2 requires the new runtime identity; older v1 trials remain incompatible and are refused, rather than being silently converted or declared exact. Their original bytes/runtime remain available for a separate deliberate migration.

The helper uses its own local port, working directory, and private IPC ring name; it checks listener ownership before mutations. Startup still requires 384 MiB reported free on the primary GPU. This is a conservative small-check admission guard, not a measured large-scene budget. It never unloads models or talks to the agents' engine/model endpoints.

`evidence/pre-ca-continuation/gpu-integration.json` records the **previous runtime's** four GPU integration scenarios; its real-window report and build manifest are retained beside it. The current runtime has its own six passing scenarios in `evidence/gpu-integration.json`; the previous runtime's real-window and lifetime checks are historical evidence. `ca-checkpoint-offline.json` records the current four CPU-only Blender checks. `owned-child-test.json` remains prior evidence for the unchanged Windows-job lifetime mechanism.

Run `./tools/Test-Studio.ps1` for CPU-only Blender checks, or add `-Gpu` for the real Blender GPU tests (small shared-GPU checks, no model unloading); `tests/test_gpu_lifetime.py` is the Windows lifetime test and needs a Python environment with NumPy. A saved file is validated before replacing the current workshop. Checkpoints are bounded to 240 samples and 8 MiB.

## Current boundary

The two GPU paths and rigid-region bridge have separate native state owners. This increment does **not** couple membrane deformation to water pressure, rigid contacts, fracture or trained response catalogs. It reuses the existing artificial-protein/mechanism-factory star construction, with one shared free apex; it does not qualify new general-purpose material recipes. The experimental water-CA continuation passed its scoped GPU replay checks; further water work is deferred. It does not establish full-game frame rate, unrestricted deformable materials or player usability. Blender displays native results; it does not replace the solver. Full-resolution GPU buffer sharing remains future work; this small editor transfers a snapshot only after an explicit operation, never every render frame.

The source build keeps Blender modeling, editing and the workbench viewport. Cycles, OpenImageDenoise, USD/Hydra, OpenVDB/fluid/NanoVDB and upstream GTests are disabled in this initial build. This saves build cost and avoids a second simulation/render stack being mistaken for Chimera's engine. The ordinary installed Blender remains available for those workflows.

## Rebuild and checks

From this directory, `./tools/Build-Native.ps1` builds the private DLL. `./tools/Test-Studio.ps1` runs actual Blender-background integration and application-template tests. `./tools/Build-Fork.ps1` configures/builds the already cloned Blender fork with two compiler jobs. `./tools/Test-Studio.ps1 -Gui` also opens a small visible viewport test and closes it automatically. Visual interaction testing is recorded separately; a headless pass is not a GUI performance claim.

`SOURCE_LOCK.json` pins actual source bytes copied from the agents' dirty checkout; `source_head` alone is not sufficient to reproduce them. Do not overwrite `vendor/chimera` from a moving checkout automatically. A future engine update must intentionally refresh the snapshot and rerun the boundary checks. `evidence/headless_integration.json` contains results, including native timing on the small fixture. `evidence/first-run-input-precision.json` retains the initial failure which exposed float32 transform precision loss; the adapter now transforms in float64.

## Source ownership

Blender fork: `../blender`, branch `chimera/studio-v5.0.1`, upstream tag `v5.0.1` (a3db93c5b2595a79f65f304114c23aeef8c2139f). Source edits are window branding and a Chimera application template. Integration: this directory. Build output: `../build-blender`; no shared engine build directory is used. No public fork/release is implied by these local repositories.

`LICENSE` preserves the source project's AGPL-3.0 license. Original Blender license files remain in its fork. `vendor/chimera` is an unchanged attributed snapshot; see `SOURCE_LOCK.json`. Integration source is AGPL-3.0-or-later. Application template and Blender edits retain Blender-compatible GPL-3.0-or-later headers. Keep these notices and source available with any later distribution.

## Installed build result

The custom executable was built and tested from Blender fork commit `68c79f03362ebc6e41d16a10b77c8f794097e644` and integration source commit `09471402e501619a923c7d516af1d54234897a8a`. Ten background integration checks, the installed application-template check (including configuration isolation), and a short real-window viewport/native-play check passed. See `evidence/build-manifest.json` for exact executable/DLL identities and `evidence/viewport.png` for the actual view. Full scene throughput and human usability remain unmeasured.

## Working-project entry check

Run ./tools/Test-Studio.ps1 -ProjectEntry after installing the launcher. It opens the actual working file through the Chimera application template, checks the three source identities/two connections, then saves and reopens a separate test copy. The native physical/render document must stay identical and the working project must remain byte-identical. No GPU helper or model server starts. Evidence: evidence/project-entry.json.
