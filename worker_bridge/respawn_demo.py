#!/usr/bin/env python3
"""respawn_demo.py — One-command demo rebuild.

Spawns all educational texts, configures clouds, takes screenshots.
Run after editor restart. Checks MCP config before connecting.
"""

import sys, os, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

# Ensure MCP config exists in DefaultGame.ini
config_path = "E:/PythonChimera/Chimera/Config/DefaultGame.ini"
mcp_section = "[/Script/McpAutomationBridge.McpAutomationBridgeSettings]"
with open(config_path, "r") as f:
    if mcp_section not in f.read():
        with open(config_path, "a") as f:
            f.write("\n" + mcp_section + "\n")
            f.write("bEnableNativeMCP=True\n")
            f.write("NativeMCPPort=3000\n")
        print("[MCP] Config restored to DefaultGame.ini")

from mcp_builder import MCP
mcp = MCP()
start = time.time()

# All 40 educational texts
TEXTS = [
    # Entrance narrative
    ("EduText_Narrative_Intro", 450, 250, 60, "This canyon was carved by flowing water. The planet was once wet - now it is a desert."),
    ("EduText_Dry_Riverbed", 540, 280, 45, "Dry riverbed - water once flowed here. Rounded rocks were tumbled by ancient currents."),
    # Geology - sedimentary
    ("EduText_Sandstone_1", 480, 200, 50, "Sedimentary Sandstone - compressed ancient dune beds"),
    ("EduText_Sandstone_2", 520, 180, 55, "Cross-bedding visible - wind direction shifted over centuries"),
    ("EduText_Limestone_1", 600, 140, 50, "Sedimentary Limestone - marine fossil layer"),
    ("EduText_Limestone_2", 640, 120, 55, "Calcium carbonate precipitate - tiny marine organisms"),
    ("EduText_Climate_Change", 490, 170, 50, "This canyon was once underwater. Sediments settled for millions of years. Then the water receded."),
    ("EduText_Erosion", 470, 220, 55, "Differential erosion carved this canyon. Harder rock layers resist weathering."),
    ("EduText_Minerals", 560, 130, 50, "Heat and pressure deep underground created these mineral crystals."),
    ("EduText_Fossils", 620, 110, 50, "This layer contains fossilized life. Organisms turned to stone over millions of years."),
    ("EduText_Strata_Story", 660, 100, 50, "Each layer is a chapter. Bottom is oldest. Read from bottom to top for planetary history."),
    ("EduText_Iron_Oxide", 630, 100, 50, "Red rocks contain iron oxide - rust. This layer formed when oxygen first appeared."),
    # Geology - metamorphic
    ("EduText_Schist_1", 720, 150, 50, "Metamorphic Schist - heat and pressure altered rock"),
    ("EduText_Schist_2", 760, 170, 55, "Foliation bands visible - ancient mountain building"),
    ("EduText_Plate_Tectonics", 690, 160, 50, "These rocks were once at the bottom of an ocean. Plate tectonics pushed them upward."),
    # Geology - igneous
    ("EduText_Granite_1", 800, 190, 50, "Igneous Granite - slow-cooled magma chamber"),
    ("EduText_Basalt_1", 880, 230, 50, "Igneous Basalt - rapid-cooled volcanic flow"),
    # Vista overlooks
    ("EduText_Overlook_1", 500, 350, 80, "Vista - sedimentary basin below"),
    ("EduText_Overlook_2", 700, 350, 80, "Vista - metamorphic ridge ahead"),
    ("EduText_Overlook_3", 900, 350, 80, "Vista - igneous peaks in distance"),
    # Conclusion
    ("EduText_Ending", 950, 250, 50, "You have walked through 500 million years. The rocks remember what the air forgets."),
    # Meteorology
    ("EduText_Cumulus", 600, 0, 300, "Cumulus clouds - flat bottom means stable air"),
    ("EduText_Cirrus", 700, -50, 350, "Cirrus - wispy ice crystals. Weather changing"),
    ("EduText_Cumulonimbus", 800, -100, 400, "Cumulonimbus - towering thunderhead. Shelter"),
    ("EduText_Pressure", 620, -30, 320, "Low pressure brings storms. High pressure brings clear skies."),
    ("EduText_Wind_Dunes", 680, -80, 350, "Prevailing winds shaped these dunes."),
    ("EduText_Precipitation", 580, 30, 300, "Clouds release precipitation when they cool."),
    ("EduText_Weather_Reading", 640, 0, 310, "Red sky at morning means weather approaching."),
    ("EduText_Storm_Formation", 660, -60, 360, "Storms form when warm moist air rises and cool air rushes in."),
    ("EduText_Atmosphere", 680, -120, 400, "The atmosphere is a thin layer of gas held by gravity."),
    # Astronomy
    ("EduText_StarShift", 750, 0, 500, "Stars shift position through the night as planet rotates"),
    ("EduText_Constellation", 700, 0, 480, "Constellations differ by star system"),
    ("EduText_Constellation_Nav", 740, 0, 500, "Ancient navigators used constellations for direction."),
    ("EduText_Planet_Rotation", 720, 0, 520, "Stars appear to move because the planet rotates eastward."),
    ("EduText_Gravity", 780, 0, 540, "Gravity holds the planet in orbit."),
    ("EduText_Light_Travel", 760, 0, 560, "Light from those stars traveled years to reach you."),
    ("EduText_Planet_Formation", 820, 0, 560, "This planet formed from a disk of dust and gas orbiting a young star."),
    ("EduText_Lightning", 700, -90, 380, "Lightning heats the air to 30,000 degrees."),
]

print(f"Spawning {len(TEXTS)} educational texts...")
success = 0
for name, x, y, z, text in TEXTS:
    try:
        mcp.spawn_actor(name, "/Script/Engine.TextRenderActor", x, y, z)
        mcp.tool_call("control_actor", "set_component_property",
            actorName=name, componentName="NewTextRenderComponent",
            properties={"Text": text, "TextRenderColor": {"R":255,"G":255,"B":200},
                        "WorldSize": 65.0, "bHiddenInGame": False})
        success += 1
        print(f"  [{success}/{len(TEXTS)}] {name}")
    except Exception as e:
        print(f"  [FAIL] {name}")

# Cloud rotation
try:
    mcp.tool_call("control_actor", "set_component_property",
        actorName="DemoClouds", componentName="VolumetricCloudComponent0",
        properties={"LayerRotation": {"Pitch": 0, "Yaw": 0.05, "Roll": 0}})
    print("  Cloud drift configured")
except:
    pass

# Verify
try:
    r = mcp.call("tools/call", {"name": "inspect", "arguments": {"action": "runtime_report"}})
    content = ""
    for c in r.get("result", {}).get("content", []):
        if isinstance(c, dict) and "text" in c:
            content = c["text"]
    found = content.count("EduText_")
    print(f"\nVerified: {found} educational texts in level")
except Exception as e:
    print(f"\nVerification failed: {e}")

# Screenshots
print("\nCapturing screenshots...")
shots = [
    ("canyon_vista.png", 600, 0, 200, -10, 90),
    ("edu_closeup.png", 520, 180, 60, 0, 180),
    ("meteorology_sky.png", 600, 0, 300, -20, 90),
    ("astronomy_night.png", 750, 0, 500, -45, 90),
    ("canyon_overview.png", 600, -200, 400, -30, 90),
]
for name, x, y, z, pitch, yaw in shots:
    try:
        mcp.set_camera(x, y, z, pitch, yaw, 0)
        time.sleep(0.5)
        mcp.screenshot(name)
        print(f"  {name}")
    except:
        pass

elapsed = time.time() - start
print(f"\nDone in {elapsed:.0f}s. {success}/{len(TEXTS)} texts spawned.")
