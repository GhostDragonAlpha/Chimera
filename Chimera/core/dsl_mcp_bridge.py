"""
DSL-MCP Bridge — Connects DSL Parser to MCP Unreal Server via Graphify mutation logging.

Three systems. Three connections. One unified workflow:
  DSL Parser → Knows what the game IS
  MCP Unreal Server → Knows how to BUILD
  Graphify → Knows what HAPPENED

Usage:
  python core/dsl_mcp_bridge.py <path_to_dsl_file>
  
Defaults to: tests/dsl_grammar/deep_space_trader.chimera (relative to Chimera root)
"""

import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional

# Local imports
try:
    from core.dsl_game_parser import DSLGameParser
except ImportError:
    try:
        from dsl_game_parser import DSLGameParser
    except ImportError:
        print("ERROR: Cannot find dsl_game_parser module.")
        sys.exit(1)


# ─── Graphify Mutation Logger ──────────────────────────────────────────────

class GraphifyLogger:
    """Records every bridge operation as a mutation in the knowledge graph."""

    def __init__(self, graph_path: Path):
        self.graph_path = graph_path
        self.graph = self._load()

    def _load(self) -> dict:
        if self.graph_path.exists():
            with open(self.graph_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"nodes": [], "edges": [], "metadata": {}}

    def save(self):
        with open(self.graph_path, 'w', encoding='utf-8') as f:
            json.dump(self.graph, f, indent=2)

    def mutate(self, operation: str, target: str, result: str = "success",
               details: Optional[Dict[str, Any]] = None, error: str = "") -> str:
        """Record a mutation node and return its ID."""
        now = datetime.now(timezone.utc).isoformat()
        node_id = f"bridge_{hashlib.sha256(f'{operation}_{target}_{now}'.encode()).hexdigest()[:12]}"

        node = {
            "id": node_id,
            "type": "Mutation",
            "timestamp": now,
            "error_signature": f"bridge_{operation}" if result != "success" else "bridge_success",
            "template_file": f"dsl_mcp_bridge:{operation}",
            "template_line": 0,
            "error_category": "none" if result == "success" else f"bridge_{operation}_failure",
            "fix_description": f"{operation} on {target}: {result}",
            "fix_diff": json.dumps(details or {}, default=str),
            "compilation_result": result,
            "links": []
        }

        if error:
            node["error_message"] = error
            node["error_category"] = f"bridge_{operation}_error"

        self.graph["nodes"].append(node)
        self.save()
        return node_id


# ─── MCP Unreal Client via PowerShell run_powershell ──────────────────────

class MCPUnrealClient:
    """Calls chiR24-unreal-mcp tools via PowerShell subprocess.
    
    The chiR24-unreal-mcp server runs as an MCP stdio server. We invoke it
    through Node.js using the CLI that's already configured in the MCP settings.
    """

    def __init__(self):
        self.mcp_server = "chiR24-unreal-mcp"

    def _call_tool_ps(self, tool_name: str, arguments: dict) -> Tuple[bool, str]:
        """Call an MCP tool using PowerShell + node CLI.
        
        Uses the chiR24-unreal-mcp server at E:/ChiR24-Unreal_mcp-test/dist/cli.js
        which exposes tools like control_actor, inspect, etc.
        """
        import subprocess

        # Use PowerShell to run a Node.js script that connects via MCP stdio
        mcp_cli = "E:\\ChiR24-Unreal_mcp-test\\dist\\cli.js"
        
        ps_cmd = (
            f'node "{mcp_cli}" --tool {tool_name} '
            f'--args "{json.dumps(arguments)}"'
        )

        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return True, result.stdout.strip()
            else:
                err = result.stderr or "no output"
                return False, err
        except Exception as e:
            return False, str(e)

    def spawn_actor(self, actor_class: str, location: List[float], name: str = "") -> Tuple[bool, str]:
        """Spawn an actor of the given class at the given location."""
        return self._call_tool_ps("control_actor", {
            "action": "spawn",
            "actorName": name or actor_class,
            "classPath": f"/Game/{actor_class}",
            "location": {"x": location[0], "y": location[1], "z": location[2]}
        })

    def set_actor_property(self, actor_name: str, property_name: str, value: Any) -> Tuple[bool, str]:
        """Set a property on an existing actor."""
        return self._call_tool_ps("inspect", {
            "action": "set_property",
            "actorName": actor_name,
            "propertyName": property_name,
            "value": value
        })

    def list_actors(self) -> Tuple[bool, List[dict]]:
        """List all actors in the current level."""
        return self._call_tool_ps("inspect", {"action": "list_objects"})

    def clear_level(self) -> Tuple[bool, str]:
        """Remove all actors from the current level."""
        return False, "clear_level requires MCP stdio transport"


# ─── DSL-to-MCP Translator ────────────────────────────────────────────────

class DSLMCPTranslator:
    """Translates parsed DSL blocks into MCP Unreal operations."""

    def __init__(self, dsl_data: Dict[str, Any]):
        self.dsl = dsl_data

    def translate_ship(self) -> List[Dict[str, Any]]:
        """Translate ship_systems → spawn_actor + set_property calls."""
        ops = []
        ships = self.dsl.get("ship_systems", {}).get("ships", [])
        if not ships:
            return ops

        # Use the first ship as the player ship
        player_ship = ships[0]
        ship_name = player_ship.get("name", "Trader_Vessel_Alpha")

        # Spawn at player_start location from level block
        level_data = self.dsl.get("level", {})
        player_start = level_data.get("player_start", {})
        location = player_start.get("location", [0, 0, 100])

        ops.append({
            "action": "spawn_actor",
            "target": f"AShip_{ship_name}",
            "location": location,
            "name": f"{ship_name}_Spawned"
        })

        # Set flight model properties if available
        flight_model = self.dsl.get("flight_model", {})
        if flight_model:
            for key, val in flight_model.items():
                ops.append({
                    "action": "set_property",
                    "target": f"{ship_name}_Spawned",
                    "property": key,
                    "value": val
                })

        # Set ship system properties
        shield_cap = player_ship.get("shield_capacity")
        if shield_cap is not None:
            ops.append({"action": "set_property", "target": f"{ship_name}_Spawned",
                        "property": "shield_capacity", "value": shield_cap})

        hull_health = player_ship.get("hull_health")
        if hull_health is not None:
            ops.append({"action": "set_property", "target": f"{ship_name}_Spawned",
                        "property": "hull_health", "value": hull_health})

        return ops

    def translate_stations(self) -> List[Dict[str, Any]]:
        """Translate level.station_placements → spawn_actor calls."""
        ops = []
        stations = self.dsl.get("level", {}).get("station_placements", [])

        for station in stations:
            name = station.get("name", station.get("station_name"))
            location = station.get("location")

            if not name or not location:
                continue

            ops.append({
                "action": "spawn_actor",
                "target": f"AStationActor",
                "location": location,
                "name": name
            })

        return ops

    def translate_planets(self) -> List[Dict[str, Any]]:
        """Translate level.planet_placements → spawn_actor calls."""
        ops = []
        planets = self.dsl.get("level", {}).get("planet_placements", [])

        for planet in planets:
            name = planet.get("name", planet.get("planet_name"))
            location = planet.get("location")
            scale = planet.get("scale", 1.0)

            if not name or not location:
                continue

            ops.append({
                "action": "spawn_actor",
                "target": f"APlanetActor",
                "location": location,
                "name": name,
                "scale": scale
            })

        return ops

    def translate_lights(self) -> List[Dict[str, Any]]:
        """Translate level.lights → spawn_actor calls."""
        ops = []
        lights = self.dsl.get("level", {}).get("lights", [])

        for light in lights:
            light_type = light.get("type", "DirectionalLight")
            position = light.get("position", [0, 0, 1000])
            intensity = light.get("intensity", 1.0)
            color = light.get("color", "white")

            ops.append({
                "action": "spawn_light",
                "target": light_type,
                "location": position,
                "name": f"{light_type}_{len(ops)}",
                "intensity": intensity,
                "color": color
            })

        return ops

    def translate_all(self) -> List[Dict[str, Any]]:
        """Translate all DSL blocks and merge into a single operation list."""
        all_ops = []
        all_ops.extend(self.translate_ship())
        all_ops.extend(self.translate_stations())
        all_ops.extend(self.translate_planets())
        all_ops.extend(self.translate_lights())
        return all_ops


# ─── Bridge Orchestrator ──────────────────────────────────────────────────

class DSLMCPBridge:
    """Orchestrates the full DSL → MCP pipeline with Graphify logging."""

    def __init__(self, dsl_path: Path):
        self.dsl_path = dsl_path
        self.graph_logger = GraphifyLogger(Path("E:/PythonChimera/Chimera/docs/chimera_knowledge_graph.json"))
        self.mcp_client = MCPUnrealClient()

        # Resolve schema path relative to Chimera root
        chimera_root = Path(__file__).parent.parent
        schema_path = chimera_root / "schema" / "dsl_game_schema.json"

        # Parse the DSL
        parser = DSLGameParser(str(schema_path))
        is_valid, parsed_dsl, error = parser.parse_and_validate(self.dsl_path.read_text(encoding='utf-8'))

        if not is_valid:
            self.graph_logger.mutate("dsl_parse", str(dsl_path), result="failed", error=error)
            raise ValueError(f"DSL parse failed: {error}")

        self.dsl_data = parsed_dsl
        self.graph_logger.mutate("dsl_parse", str(dsl_path), result="success",
                                 details={"blocks": list(parsed_dsl.keys())})

    def clear_level(self):
        """Clear all actors from the current level."""
        success, msg = self.mcp_client.clear_level()
        if not success:
            # Non-fatal: continue anyway
            print(f"  [WARN] Level clear failed: {msg}")
        return success

    def execute_operations(self, operations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Execute all MCP operations and log each result to Graphify."""
        results = {"success": 0, "failed": 0}

        for i, op in enumerate(operations):
            action = op.get("action", "")
            target = op.get("target", "")
            location = op.get("location")
            name = op.get("name", "")

            success = False
            msg = ""

            if action == "spawn_actor":
                success, msg = self.mcp_client.spawn_actor(target, location or [0, 0, 100], name)
            elif action == "set_property":
                prop_name = op.get("property", "")
                value = op.get("value")
                success, msg = self.mcp_client.set_actor_property(target, prop_name, value)
            elif action == "spawn_light":
                # Lights are handled via spawn_actor with special type
                light_type = target
                location_val = location or [0, 0, 1000]
                success, msg = self.mcp_client.spawn_actor(light_type, location_val, name)

            if success:
                results["success"] += 1
                self.graph_logger.mutate(action, f"{target}:{name}", result="success", details=op)
            else:
                results["failed"] += 1
                self.graph_logger.mutate(action, f"{target}:{name}", result="failed", error=msg)

        return results

    def run(self):
        """Execute the full bridge pipeline."""
        print("=" * 60)
        print("DSL-MCP Bridge — Starting Pipeline")
        print("=" * 60)

        # Step 1: Clear level
        print("\n[Step 1] Clearing current level...")
        self.clear_level()

        # Step 2: Translate DSL to MCP operations
        print("[Step 2] Translating DSL blocks to MCP operations...")
        translator = DSLMCPTranslator(self.dsl_data)
        operations = translator.translate_all()
        print(f"      Generated {len(operations)} operations:")
        for op in operations:
            print(f"        [>] {op['action']} on {op.get('target', '')} ({op.get('name', '')})")

        # Step 3: Execute operations
        print("\n[Step 3] Executing MCP operations...")
        results = self.execute_operations(operations)

        # Step 4: Report
        print(f"\n{'=' * 60}")
        print("DSL-MCP Bridge — Complete")
        print(f"  Successes: {results['success']}")
        print(f"  Failures:  {results['failed']}")
        print(f"{'=' * 60}")

        return results


# ─── Main Entry Point ──────────────────────────────────────────────────────

def main():
    # Resolve DSL path
    chimera_root = Path(__file__).parent.parent  # Chimera/
    default_dsl = chimera_root / "tests" / "dsl_grammar" / "deep_space_trader.chimera"
    dsl_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_dsl

    if not dsl_path.exists():
        print(f"ERROR: DSL file not found: {dsl_path}")
        sys.exit(1)

    bridge = DSLMCPBridge(dsl_path)
    results = bridge.run()

    # Exit with error code if all operations failed
    if results["success"] == 0 and results["failed"] > 0:
        sys.exit(2)


if __name__ == "__main__":
    main()