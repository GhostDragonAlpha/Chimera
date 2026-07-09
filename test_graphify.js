// Test Graphify MCP server via stdio
const { spawn } = require('child_process');

const GRAPHIFY_EXE = "C:\Users\allen\.local\bin\graphify-mcp.exe";
const GRAPH_JSON = "E:\PythonChimera\Chimera\docs\chimera_knowledge_graph.json";

console.log("=== Starting Graphify MCP Server ===");

const proc = spawn('node', [GRAPHIFY_EXE, GRAPH_JSON], {
  stdio: ['pipe', 'pipe', 'inherit']
});

function sendRequest(id, method, params) {
  const msg = JSON.stringify({
    jsonrpc: "2.0",
    id: id,
    method: method,
    params: params || {}
  });
  proc.stdin.write(msg + '
');
}

proc.on('data', (data) => {
  try {
    const lines = data.toString().split('
').filter(l => l.trim());
    for (const line of lines) {
      const msg = JSON.parse(line);
      if (msg.result && msg.id === 1) {
        console.log("✓ Graphify initialized:", msg.result.serverInfo?.name || "OK");
        
        // List tools
        sendRequest(2, 'tools/list', {});
      } else if (msg.result && msg.id === 2) {
        const tools = msg.result.tools || [];
        console.log("
=== Graphify Tools (" + tools.length + ") ===");
        for (const t of tools) {
          console.log("- " + t.name + " (" + (t.category || 'core') + ")");
        }
        
        // Test query_graph
        sendRequest(3, 'tools/call', {
          name: 'query_graph',
          arguments: { query: 'Verb_Look' }
        });
      } else if (msg.result && msg.id === 3) {
        const content = msg.result.content || [];
        console.log("
=== Query Result for Verb_Look ===");
        for (const c of content) {
          if (c.type === 'text') {
            console.log(c.text.substring(0, 500));
          }
        }
      } else if (msg.error) {
        console.log("Error:", msg.error);
      }
    }
  } catch(e) {
    // ignore parse errors for non-JSON data
  }
});

proc.on('error', (err) => {
  console.error("Process error:", err.message);
});

setTimeout(() => {
  proc.kill();
  process.exit(0);
}, 15000);

// Initialize first
sendRequest(1, 'initialize', {
  protocolVersion: "2024-11-05",
  capabilities: {},
  clientInfo: { name: "chimera-agent", version: "1.0" }
});
