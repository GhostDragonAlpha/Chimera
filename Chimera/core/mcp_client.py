"""MCP HTTP transport client for Chimera — CHECK YOUR TRANSPORT FIRST.

!! REALITY CHECK (2026-07-14, measured live): the McpAutomationBridge plugin in
this project serves **WebSocket on 127.0.0.1:8090/8091** (editor log:
"FMcpBridgeWebSocket::RunServer ... port=8090"). There is NO HTTP endpoint on
:3000 in this build — this client's :3000 default refused connections for 30+
minutes of debugging. THE PROVEN CLIENT is `core.telemetry_probe.MCPStdioClient`
(spawns the chiR24 node CLI, which speaks the bridge's WebSocket):

    from core.telemetry_probe import MCPStdioClient
    c = MCPStdioClient()
    c.call("control_editor", {"action": "screenshot",
                              "mode": "editor_viewport", "filename": "x.png"})
    c.close()

This HTTP client is kept ONLY for a build whose plugin exposes Streamable HTTP.
If initialize() gets 'actively refused', you are on the WebSocket build — use
MCPStdioClient (docs/MCP_PATHWAYS.md).
"""

import json
import urllib.request


class MCPError(Exception):
    pass


class MCPClient:
    """HTTP transport client for the native MCP server on localhost:3000."""

    def __init__(self, host: str = "localhost", port: int = 3000):
        self._base_url = f"http://{host}:{port}/mcp"
        self._session_id: str | None = None
        self._next_id: int = 1

    def _post(self, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        # Add session ID for all requests after initialize
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        req = urllib.request.Request(
            self._base_url,
            data=data,
            headers=headers,
            method="POST",
        )
        resp = urllib.request.urlopen(req)

        # Capture session ID from response header (on initialize or first call)
        sid = resp.headers.get("Mcp-Session-Id")
        if sid:
            self._session_id = sid

        body = resp.read().decode("utf-8")

        # Parse SSE format: "event: message\ndata: {...}"
        if "data:" in body:
            json_str = body.split("data:")[-1].strip()
        else:
            json_str = body.strip()

        result = json.loads(json_str)

        # Check for JSON-RPC errors
        if "error" in result:
            err = result["error"]
            raise MCPError(f"{err.get('code')}: {err.get('message')}")

        return result

    def initialize(self) -> dict:
        """Initialize the MCP session. Must be called first."""
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "chimera-agent", "version": "1.0"},
            },
        }
        return self._post(payload)

    def _ensure_session(self):
        if not self._session_id:
            raise RuntimeError("No session — call initialize() first")

    def list_tools(self) -> dict:
        """List all available MCP tools."""
        self._ensure_session()
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id,
            "method": "tools/list",
            "params": {},
        }
        return self._post(payload)

    def call_tool(self, name: str, arguments: dict) -> dict:
        """Call an MCP tool by name with arguments."""
        self._ensure_session()
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
        return self._post(payload)

    # ---- Convenience methods ----

    def inspect(self, action: str) -> dict:
        """inspect.<action> wrapper."""
        return self.call_tool("inspect", {"action": action})

    def control_editor(self, _action: str, **kwargs) -> dict:
        """control_editor.<action> wrapper."""
        args = {"action": _action}
        args.update(kwargs)
        return self.call_tool("control_editor", args)

    def control_actor(self, actor_name: str, _action: str, **kwargs) -> dict:
        """control_actor.<action> wrapper."""
        args = {"actorName": actor_name, "action": _action}
        args.update(kwargs)
        return self.call_tool("control_actor", args)

    def manage_geometry(self, _action: str, **kwargs) -> dict:
        """manage_geometry.<action> wrapper."""
        args = {"action": _action}
        args.update(kwargs)
        return self.call_tool("manage_geometry", args)

    def manage_asset(self, _action: str, **kwargs) -> dict:
        """manage_asset.<action> wrapper."""
        args = {"action": _action}
        args.update(kwargs)
        return self.call_tool("manage_asset", args)

    def manage_level(self, _action: str, **kwargs) -> dict:
        """manage_level.<action> wrapper."""
        args = {"action": _action}
        args.update(kwargs)
        return self.call_tool("manage_level", args)

    def manage_effect(self, _action: str, **kwargs) -> dict:
        """manage_effect.<action> wrapper (Niagara particles, GPU sims)."""
        args = {"action": _action}
        args.update(kwargs)
        return self.call_tool("manage_effect", args)

    def animation_physics(self, _action: str, **kwargs) -> dict:
        """animation_physics.<action> wrapper (animations, physics rigs)."""
        args = {"action": _action}
        args.update(kwargs)
        return self.call_tool("animation_physics", args)

    def manage_character(self, _action: str, **kwargs) -> dict:
        """manage_character.<action> wrapper (character blueprints, mesh config)."""
        args = {"action": _action}
        args.update(kwargs)
        return self.call_tool("manage_character", args)


def build_env_props(client):
    """Build environmental props for the regolith yard (Loop 0 deepening)."""

    # Props: name, dimensions, position, rotation_y, scale
    props = [
        ("WarningPole1", 5, 80, 5, (-30, 0, 50), 0, (0.1, 0.1, 2.0)),
        ("WarningPole2", 5, 80, 5, (-30, -80, 50), 0, (0.1, 0.1, 2.0)),
        ("Crate1", 40, 30, 50, (4050, -60, 25), 15, (1.5, 0.75, 1.0)),
        ("Crate2", 30, 20, 40, (4080, -30, 20), 45, (1.0, 0.6, 0.8)),
        ("Antenna", 3, 120, 3, (-50, 100, 70), 0, (0.3, 0.3, 2.5)),
        ("Debris1", 15, 10, 20, (4020, -40, 15), 30, (0.3, 0.2, 0.3)),
        ("Debris2", 12, 8, 16, (4060, -70, 15), 60, (0.25, 0.15, 0.25)),
        ("Debris3", 10, 6, 14, (4090, -20, 15), 90, (0.2, 0.1, 0.2)),
        ("WarningSign", 8, 12, 8, (-30, -40, 50), 0, (0.15, 0.15, 1.5)),
    ]

    for name, r, h, d, loc, rot_y, scale in props:
        # create_box at identity (0,0,0) to avoid location double-bake trap
        result = client.manage_geometry("create_box", width=r*2, height=h, depth=d)
        actor_name = result["result"]["structuredContent"]["actorName"]

        # Position and scale via set_transform
        client.control_actor(
            actor_name, "set_transform",
            location={"x": loc[0], "y": loc[1], "z": loc[2]},
            rotation={"pitch": 0, "yaw": rot_y, "roll": 0},
            scale={"x": scale[0], "y": scale[1], "z": scale[2]}
        )

    print(f"Built {len(props)} environmental props")


def main():
    """Demo: connect to editor and build environmental props for the regolith yard."""
    client = MCPClient()
    init = client.initialize()
    info = init["result"]["serverInfo"]
    print(f"Connected: {info['name']} v{info['version']}")

    rt = client.inspect("runtime_report")
    actors = rt["result"]["structuredContent"].get("actors", [])
    print(f"Actors in level: {len(actors)}")

    # Build environmental props (deepens Loop 0 — the player's world)
    build_env_props(client)

    # Verify and save
    rt = client.inspect("runtime_report")
    actors = rt["result"]["structuredContent"].get("actors", [])
    dynamic_meshes = [a for a in actors if "DynamicMeshActor" == a.get("class")]
    print(f"DynamicMeshActors: {len(dynamic_meshes)}")

    save = client.control_editor("save_all")
    sc = save["result"]["structuredContent"] if "structuredContent" in save["result"] else {}
    saved_count = sc.get("savedCount", "?")
    print(f"Saved: {saved_count} actors saved")


if __name__ == "__main__":
    main()
