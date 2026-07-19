"""MCP builder — handles SSE responses properly."""
import json, re, urllib.request, time

MCP_URL = "http://127.0.0.1:3000/mcp"

class MCP:
    def __init__(self):
        self.session_id = None
        self._connect()
    
    def _connect(self):
        body = json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"builder","version":"1.0"}}}).encode()
        req = urllib.request.Request(MCP_URL, data=body, headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req) as resp:
            self.session_id = resp.headers.get("Mcp-Session-Id")
        print(f"[MCP] Session: {self.session_id}")
    
    def call(self, method, params=None):
        if params is None: params = {}
        body = json.dumps({"jsonrpc":"2.0","id":int(time.time()*1000),"method":method,"params":params}).encode()
        req = urllib.request.Request(MCP_URL, data=body, headers={"Content-Type":"application/json","Mcp-Session-Id":self.session_id})
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        # Parse SSE response: extract JSON from data: lines
        for line in raw.split("\n"):
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        return json.loads(raw)
    
    def tool_call(self, tool, action, **args):
        return self.call("tools/call", {"name": tool, "arguments": {"action": action, **args}})
    
    def spawn_actor(self, name, class_path, x=0, y=0, z=0):
        return self.tool_call("control_actor", "spawn_actor", actorName=name, classPath=class_path, location={"x":x,"y":y,"z":z})
    
    def screenshot(self, filename=None):
        if not filename: filename = f"build_{int(time.time())}.png"
        return self.tool_call("control_editor", "screenshot", filename=filename)
    
    def set_camera(self, x=0, y=-500, z=500, pitch=-30, yaw=0, roll=0):
        return self.tool_call("control_editor", "set_camera_position", location={"x":x,"y":y,"z":z}, rotation={"pitch":pitch,"yaw":yaw,"roll":roll})
    
    def search_assets(self, directory="/Game/", class_names=None, limit=20):
        return self.tool_call("manage_asset", "search_assets", directory=directory, classNames=class_names or [], limit=limit)
