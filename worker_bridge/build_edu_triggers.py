"""Build Demo_Educational_Triggers in UE5 via MCP.

Spawns 18 TriggerBox actors at positions from edu_trigger_placement_data.json,
sets their BoxExtent to match the data, and captures verification screenshot.
"""
import json, sys, time
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "Chimera" / "docs" / "features" / "edu_trigger_placement_data.json"
ZONES = json.loads(DATA.read_text())["zones"]

from worker_bridge.mcp_builder import MCP
mcp = MCP()

BOX_CLASS = "/Script/Engine.TriggerBox"

def set_box_extent(mcp, actor_name, half_x, half_y, half_z):
    """Set the BoxComponent's BoxExtent on a spawned TriggerBox."""
    return mcp.tool_call(
        "control_actor", "set_component_property",
        actorName=actor_name,
        componentName="BoxComponent",
        propertyName="BoxExtent",
        value={"x": half_x, "y": half_y, "z": half_z}
    )

def main():
    results = []
    for i, zone in enumerate(ZONES, 1):
        name = zone["ZoneName"]
        cx = zone["CenterX"]
        cy = zone["CenterY"]
        cz = zone["CenterZ"]
        hx = zone["HalfExtentX"]
        hy = zone["HalfExtentY"]
        hz = zone["HalfExtentZ"]
        
        print(f"[{i}/{len(ZONES)}] Spawning {name}...")
        
        # Spawn the TriggerBox
        spawn_result = mcp.spawn_actor(name, BOX_CLASS, x=cx, y=cy, z=cz)
        print(f"  spawn: {spawn_result.get('result', {}).get('message', spawn_result)}")
        
        # Small delay to let UE5 process
        time.sleep(0.1)
        
        # Set box extent
        extent_result = set_box_extent(mcp, name, hx, hy, hz)
        print(f"  extent: {extent_result.get('result', {}).get('message', extent_result)}")
        
        results.append({
            "name": name,
            "position": {"x": cx, "y": cy, "z": cz},
            "extent": {"x": hx, "y": hy, "hz": hz},
            "rock_type": zone["RockType"],
            "tier": zone["Tier"],
            "landmark": zone["Landmark"]
        })
        
        time.sleep(0.1)
    
    print(f"\nDone. {len(results)} triggers spawned.")
    
    # Verification summary
    by_rock = {}
    for r in results:
        rt = r["rock_type"].split("_")[0]
        by_rock.setdefault(rt, []).append(r["name"])
    
    for rock_type, names in by_rock.items():
        print(f"  {rock_type}: {len(names)} zones -> {', '.join(names)}")
    
    # Take verification screenshot
    print("\nTaking verification screenshot...")
    time.sleep(1)
    ss = mcp.screenshot("edu_triggers_built.png")
    print(f"Screenshot: {ss}")
    
    # Save build manifest
    manifest_path = Path(__file__).resolve().parents[1] / "Chimera" / "docs" / "features" / "edu_triggers_build_manifest.json"
    manifest = {
        "feature": "Demo_Educational_Triggers",
        "built": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_zones": len(results),
        "zones": results
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"Manifest saved: {manifest_path}")

if __name__ == "__main__":
    main()
