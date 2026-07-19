"""MCP builder — direct session management wrapper."""
import json, urllib.request, time

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
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    
    def spawn_actor(self, name, class_path, x=0, y=0, z=0):
        return self.call("tools/call", {"name":"control_actor","arguments":{"action":"spawn_actor","actorName":name,"classPath":class_path,"location":{"x":x,"y":y,"z":z}}})
    
    def capture_viewport(self):
        return self.call("tools/call", {"name":"control_editor","arguments":{"action":"screenshot","filename":f"build_{int(time.time())}.png"}})
    
    def set_camera(self, x=0, y=-500, z=500, pitch=-30, yaw=0, roll=0):
        return self.call("tools/call", {"name":"control_editor","arguments":{"action":"set_camera_position","location":{"x":x,"y":y,"z":z},"rotation":{"pitch":pitch,"yaw":yaw,"roll":roll}}})
