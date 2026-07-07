# UE5 Mode — proven MCP call shapes (copy exactly; full registry: Chimera/docs/MCP_PATHWAYS.md)

From python (workdir E:/PythonChimera/Chimera):
`from core.telemetry_probe import MCPStdioClient; c = MCPStdioClient(); c.call(tool, args)`

- Spawn mesh/BP: `control_actor {action: spawn_actor, actorName, classPath}` — BPs use the
  ASSET form `/Game/X/BP_Y.BP_Y`; `/Engine/BasicShapes/Plane.Plane` works.
- Transform: `control_actor {action: set_transform, actorName, location/rotation/scale}`.
- Material: `control_actor {action: set_material, actorName, materialPath, materialSlot}` ->
  read back `get_component_property propertyName=OverrideMaterials`.
- Actor property: `control_actor {action: set_property, objectPath: "<ActorLabel>",
  propertyName, value}` -> read back `inspect {action: get_property, objectPath, propertyName}`.
- PIE: `control_editor {action: play|stop_pie}`; state: `inspect {action: runtime_report}`
  (pawn, playerController, isPIE, actors).
- Input in PIE: `control_editor {action: simulate_input, type: key_down|key_up, key: "W"}`.
- Camera: `control_editor {action: console_command, command: "BugItGo x y z pitch yaw roll"}`.
- Screenshot: `control_editor {action: screenshot, mode: "editor_viewport", filename}`.
- Niagara: `manage_effect {action: spawn_niagara, systemPath, actorName, location}` — SPAWN ONLY.
- Save: `control_editor {action: save_all}` then the save-proof ritual (md5 + mtime + recount).
- Foreground editor (PowerShell, before fps/empty-frame trust):
  `(New-Object -ComObject WScript.Shell).AppActivate((Get-Process UnrealEditor | ? {$_.MainWindowTitle} | select -First 1).Id)`
- Soak: `python -m core.telemetry_probe --out t.json --soak 30`.
