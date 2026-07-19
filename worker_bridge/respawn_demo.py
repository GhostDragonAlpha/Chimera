#!/usr/bin/env python3
"""respawn_demo.py — Rebuild the entire educational demo from scratch.

One command rebuilds all MCP-spawned educational content after an editor restart.
Run this after starting the UE5 editor with MCP enabled.

Usage:
    cd E:\PythonChimera\worker_bridge
    python respawn_demo.py
"""

import sys
import time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from mcp_builder import MCP

mcp = MCP()
start = time.time()

# ─── Educational texts ───────────────────────────────────────────────────

TEXTS = [
    # Geology — sedimentary (east entrance)
    ("EduText_Sandstone_1", 480, 200, 50, "Sedimentary Sandstone - compressed ancient dune beds"),
    ("EduText_Sandstone_2", 520, 180, 55, "Cross-bedding visible - wind direction shifted over centuries"),
    ("EduText_Limestone_1", 600, 140, 50, "Sedimentary Limestone - marine fossil layer"),
    ("EduText_Limestone_2", 640, 120, 55, "Calcium carbonate precipitate - tiny marine organisms"),
    # Geology — metamorphic (mid-canyon)
    ("EduText_Schist_1", 720, 150, 50, "Metamorphic Schist - heat and pressure altered rock"),
    ("EduText_Schist_2", 760, 170, 55, "Foliation bands visible - ancient mountain building"),
    # Geology — igneous (west)
    ("EduText_Granite_1", 800, 190, 50, "Igneous Granite - slow-cooled magma chamber"),
    ("EduText_Basalt_1", 880, 230, 50, "Igneous Basalt - rapid-cooled volcanic flow"),
    # Vista overlooks
    ("EduText_Overlook_1", 500, 350, 80, "Vista - sedimentary basin below"),
    ("EduText_Overlook_2", 700, 350, 80, "Vista - metamorphic ridge ahead"),
    ("EduText_Overlook_3", 900, 350, 80, "Vista - igneous peaks in distance"),
    # Meteorology (above canyon, pointing at sky)
    ("EduText_Cumulus", 600, 0, 300, "Cumulus clouds - flat bottom means stable air"),
    ("EduText_Cirrus", 700, -50, 350, "Cirrus - wispy ice crystals. Weather changing"),
    ("EduText_Cumulonimbus", 800, -100, 400, "Cumulonimbus - towering thunderhead. Shelter"),
    # Astronomy (high point, looking at night sky)
    ("EduText_StarShift", 750, 0, 500, "Stars shift position through the night as planet rotates"),
    ("EduText_Constellation", 700, 0, 480, "Constellations differ by star system"),
]

print(f"Spawning {len(TEXTS)} educational texts...")
success = 0
for name, x, y, z, text in TEXTS:
    try:
        mcp.spawn_actor(name, "/Script/Engine.TextRenderActor", x, y, z)
        mcp.tool_call("control_actor", "set_component_property",
            actorName=name, componentName="NewTextRenderComponent",
            properties={"Text": text, "TextRenderColor": {"R": 255, "G": 255, "B": 200},
                        "WorldSize": 70.0, "bHiddenInGame": False})
        success += 1
        print(f"  [{success}/{len(TEXTS)}] {name}")
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")

# ─── Cloud rotation ──────────────────────────────────────────────────────
print("Configuring cloud drift...")
try:
    mcp.tool_call("control_actor", "set_component_property",
        actorName="DemoClouds", componentName="VolumetricCloudComponent0",
        properties={"LayerRotation": {"Pitch": 0, "Yaw": 0.05, "Roll": 0}})
    print("  Cloud rotation set")
except Exception as e:
    print(f"  Cloud rotation failed: {e}")

# ─── Verification ────────────────────────────────────────────────────────
print("Verifying...")
try:
    r = mcp.call("tools/call", {"name": "inspect", "arguments": {"action": "runtime_report"}})
    content = ""
    for c in r.get("result", {}).get("content", []):
        if isinstance(c, dict) and "text" in c:
            content = c["text"]
    found = content.count("EduText_")
    print(f"  {found}/{len(TEXTS)} texts verified in level")
except Exception as e:
    print(f"  Verification failed: {e}")

# ─── Screenshots ─────────────────────────────────────────────────────────
print("Capturing screenshots...")
shots = [
    ("canyon_vista.png", 600, 0, 200, -10, 90),
    ("edu_closeup.png", 520, 180, 60, 0, 180),
    ("meteorology.png", 600, 0, 300, -20, 90),
    ("astronomy.png", 750, 0, 500, -45, 90),
    ("cloud_view.png", 600, -200, 400, -30, 90),
]
for name, x, y, z, pitch, yaw in shots:
    try:
        mcp.set_camera(x, y, z, pitch, yaw, 0)
        time.sleep(0.5)
        mcp.screenshot(name)
        print(f"  {name}")
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")

elapsed = time.time() - start
print(f"\nDone in {elapsed:.0f}s. {success}/{len(TEXTS)} texts spawned.")
print("Educational demo rebuilt. Screenshots in Saved/Screenshots/.")
