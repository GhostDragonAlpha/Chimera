# Chimera in Blender: working project and integration plan

## Product and scope

Chimera's immediate product is its Blender integration: a human and an AI can inspect, assemble and revise the same construction, then see the existing native matter system respond. Blender provides the editing interface; Chimera owns physical state and its native render output. Use the interface to expose missing capabilities. Work in this isolated Studio lane; do not change the agents' engine checkout, model services or game plan as part of editor work. Water remains deferred.

## Open your project

Double-click **Chimera Blender** on the Windows desktop, or **D:/Chimera-Maintenance/ChimeraStudio/Start Chimera Studio.cmd**.

The working file is **D:/Chimera-Maintenance/ChimeraStudio/Projects/Membrane Workshop/Chimera Membrane Workshop.blend**. It starts from the tested three-film construction. This is your working copy; the evidence fixture stays separate. Reinstalling the shortcut never overwrites an existing project.

Opening loads the confirmed native state offline. It does not start Chimera GPU simulation or unload an agent's model. Blender itself still uses graphics memory for its viewport. Use **Resume Saved GPU Matter** when you want to calculate. Save with Ctrl-S; use Save As for another design. To open a different file with the integration, run the launcher with `-ProjectFile "D:/path/design.blend"`, or File > Open inside Chimera Blender. `-Empty` opens a blank workspace.

## Edit, inspect and replay

1. Open the viewport sidebar with **N**, then **Chimera > Membrane Assembly**. The starter already has three films and two apex connections; do not add another starter over it.
2. Inspect the saved construction. **Resume Saved GPU Matter** creates Studio's private helper. Apply a modest center load (the tested starting value is 0.8 N) and inspect its shape.
3. **Show Native Render in Image Editor** displays the native raster output. Shift-F5 returns that area to the 3D viewport. The native camera is currently fixed; arbitrary Blender camera matching is not implemented.
4. Use **Return to Matter Authoring** before editing geometry, assignments or connections. Select source films, assign a common surface tension, and **Build Connected Films**. Viewport colors identify pieces; they do not define material laws. Joined films currently need uniform tension.
5. Mark the free apex for supported fans, connect coincident apices explicitly, and keep rim supports. After duplicating a source, use **Make Selected Films New Instances** before connecting it. Blender performs modeling; the existing compiler decides whether the construction is supported.
6. Use **Replay Native Checkpoint** to compare confirmed samples. Continuing branches from that sample. Rejected edits must leave the confirmed sample intact.
7. Save the .blend. **Save GPU Matter Trial** exports native state and construction; **Open GPU Matter Trial** can reconstruct source films. The starter .matter.json is a recovery example, not an automatically updated sidecar of every save.
8. **Release Studio GPU Memory** closes Studio's helper. The saved checkpoint remains. Closing Blender also closes its owned helper.

The .blend/.matter.json retain the confirmed physical/render sample and construction, not the whole session's checkpoint history. The bounded replay slider is a session tool, not Blender's animation timeline. Reopening does not silently recompute, migrate versions or start simulation.

## Existing capabilities to reuse

| User action | Existing owner | Present limit |
| --- | --- | --- |
| Model, import, select, duplicate, save | Blender tools, Outliner and file menus | Imported geometry must satisfy the compiler's envelope. |
| Assemble membrane pieces | blocks.py, blocks_ui.py; pinned mechanism-factory star | 2-6 closed triangle fans; one apex per film, explicit connected tree. |
| Assign membrane material | Native constant-current-area surface energy | Uniform tension across connected films; not cloth/wood/steel/fracture. |
| Connect and load films | Native membrane solver and accepted-state identity | One shared world-Z rail apex, fixed rims; no arbitrary moving joints. |
| View kernel output | /membrane_demo_render, GPU presentation buffer, Blender preview/Image Editor | Synchronized snapshot after an operation; fixed camera, small raster. |
| Recover/exchange trials | Native checkpoint, .blend payload, .matter.json validator | Same pinned runtime identity; finite session history. |
| Rigid regions | Material-volume compiler, B2Scene, finite-area connection UI | Separate state owner; not coupled to membranes. |
| Editor/model coexistence | Private helper, owned lifetime, GPU launch guard | No large-scene memory guarantee. Never unload working models to launch Studio. |

Existing evidence: membrane-assembly-checks.json, membrane-ui-checks.json, source locks and README. Six membrane/GPU scenarios cover render correspondence and exact fresh-process continuation. The project-entry check added here is offline; it does not extend the GPU/physics envelope.

## Next integration increments, in value order

1. **Dependable view correspondence.** Add deliberate camera/view synchronization between Blender and the native renderer. Acceptance: matching accepted-state identity, transforms, projection and clipping; useful messages for unsupported cameras. Reuse the current render handoff.
2. **Clear authoring state.** Show editable sources versus computed previews and whether changes need rebuilding. Organize existing actions into author -> build -> inspect -> save/resume. Point each refusal at its piece/connection and explain a useful correction. Preserve the last confirmed state.
3. **Shared human/AI operations.** Define inspect/propose/apply commands over existing authoring/compiler/checkpoint APIs, with UUIDs, visible edit previews and recovery boundaries. The human must see what the agent changes. An AI toolbar/remote command bridge is proposed, not implemented.
4. **More useful constructions from admitted engine contracts.** Inventory the engine team's existing recipes/material/connection laws before adding controls. Missing laws become explicit engine requests tied to user actions. Do not create substitute Python physics or describe arbitrary imported machinery as functional.
5. **Animation and larger scenes.** Specify timeline-to-native-time mapping and persistent replay history, then measure transfer cost and UI responsiveness. Snapshot checks do not establish continuous streaming or full-resolution shared GPU buffers.

Color/material layers can organize regions now. Printer slicing, multi-material composites, arbitrary CAD solids and general mechanical parts need later semantic adapters or native capabilities. Geometry alone cannot determine them.

## Agent workflow

Stable intent: **Improve Chimera's Blender integration so the user can construct, inspect, save and resume actual supported matter in the existing editor. Follow the latest BLENDER_WORKFLOW.md and README, preserve progress, reuse existing owners, and leave local agents and model services running.**

For each increment, name the user action, inspect current implementation/evidence, choose one missing connection, and report what the user can do, where to click, what was checked and the remaining limit. The lead can reject low-value criticism and improve the process. Preserve the intent, accepted decisions and pending work through compression. Review physics when a native law or mapping changes; launcher/documentation edits do not justify unrelated GPU experiments.

Never refresh vendor source automatically. Repin engine updates deliberately and run relevant boundary checks. Keep user projects separate from test outputs. Do not overwrite a user's .blend for evidence. This setup does not change the game loop or publish a new public fork.
