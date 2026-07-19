"""Set BoxExtent on all 18 spawned TriggerBox actors."""
import json, time
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "Chimera" / "docs" / "features" / "edu_trigger_placement_data.json"
ZONES = json.loads(DATA.read_text())["zones"]

from worker_bridge.mcp_builder import MCP
mcp = MCP()

def set_extent(name, hx, hy, hz):
    return mcp.tool_call(
        "control_actor", "set_component_property",
        actorName=name,
        componentName="BoxComponent",
        propertyName="BoxExtent",
        value={"x": hx, "y": hy, "z": hz}
    )

for i, zone in enumerate(ZONES, 1):
    name = zone["ZoneName"]
    hx, hy, hz = zone["HalfExtentX"], zone["HalfExtentY"], zone["HalfExtentZ"]
    result = set_extent(name, hx, hy, hz)
    err = result.get("isError", False)
    msg = result.get("result", {}).get("structuredContent", result)
    status = "OK" if not err else "FAIL"
    print(f"[{i}/18] {name}: ext({hx},{hy},{hz}) -> {status}")
    time.sleep(0.05)

print("\nExtents set for all 18 triggers.")
