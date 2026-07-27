"""
pathway_to_dsl.py — The Ratchet

Converts verified MCP pathways from the DNA graph into DSL fragments that the
Pipeline can consume. Provides the reverse: given a DSL pathway block, return
the MCP calls to execute.

This is the bridge between MCP discovery and Pipeline compilation.
One file. Two directions. The whole ratchet.

Usage:
  python core/pathway_to_dsl.py Player_Character_Suit    # append pathway to DSL
  python core/pathway_to_dsl.py --list                   # list all verified pathways
  python core/pathway_to_dsl.py --from-dsl "pathway_block"  # convert DSL to MCP calls
"""
import json
import sys
import re
from pathlib import Path
from datetime import datetime

# Paths
BASE = Path(__file__).parent.parent
DNA_PATH = BASE / "docs" / "chimera_dna_graph.json"
DSL_PATH = BASE / "tests" / "dsl_grammar" / "deep_space_trader.chimera"


def load_dna():
    if DNA_PATH.exists():
        with open(DNA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"nodes": [], "edges": []}


def find_verified_pathways(feature_name=None):
    """Find all verified/successful pathway nodes, optionally filtered by feature."""
    dna = load_dna()
    nodes = dna.get("nodes", [])
    
    matches = []
    for node in nodes:
        if node.get("type") not in ("pathway_attempt", "Pathway"):
            continue
        if node.get("result") not in ("success", "pass", "verified"):
            continue
        
        node_str = json.dumps(node, default=str).lower()
        if feature_name and feature_name.lower() not in node_str:
            continue
            
        matches.append({
            "id": node.get("id"),
            "tool": node.get("tool"),
            "action": node.get("action"),
            "parameters_tried": node.get("parameters_tried", {}),
            "timestamp": node.get("timestamp"),
            "fix_description": node.get("fix_description", "")
        })
    
    return sorted(matches, key=lambda x: x.get("timestamp", ""), reverse=True)


def pathway_to_dsl_fragment(feature_name):
    """Convert the newest verified pathway for a feature into a DSL block."""
    matches = find_verified_pathways(feature_name)
    if not matches:
        return None
    
    latest = matches[0]
    
    fragment = f"""
# Auto-generated pathway mapping for {feature_name}
# Discovered: {latest.get('timestamp', 'unknown')}
# Tool: {latest['tool']}.{latest['action']}
# Parameters: {json.dumps(latest.get('parameters_tried', {}))}
# Notes: {latest.get('fix_description', '')}
feature {feature_name} {{
    pathway "{latest['tool']}.{latest['action']}"
    params {json.dumps(latest.get('parameters_tried', {}))}
}}
"""
    return fragment


def append_pathway_to_dsl(feature_name):
    """Append a discovered pathway to the DSL file so Pipeline can build it."""
    fragment = pathway_to_dsl_fragment(feature_name)
    if not fragment:
        return False, f"No verified pathway found for '{feature_name}'"
    
    # Check if already in DSL file
    existing = ""
    if DSL_PATH.exists():
        existing = DSL_PATH.read_text(encoding='utf-8')
    
    if f"feature {feature_name}" in existing:
        return False, f"Feature '{feature_name}' already exists in DSL file"
    
    # Append to DSL file
    with open(DSL_PATH, 'a', encoding='utf-8') as f:
        f.write(fragment)
    
    return True, f"Appended pathway for '{feature_name}' to {DSL_PATH}"


def dsl_pathway_to_mcp_calls(dsl_block):
    """Parse a DSL pathway block and return the MCP calls to execute."""
    lines = dsl_block.strip().split('\n')
    mcp_calls = []
    
    for line in lines:
        if 'pathway' in line and '"' in line:
            match = re.search(r'"([^"]+)"', line)
            if match:
                parts = match.group(1).split('.')
                if len(parts) >= 2:
                    tool = parts[0]
                    action = parts[1]
                    mcp_calls.append({
                        "tool": tool,
                        "action": action,
                        "full_path": match.group(1)
                    })
    
    # Try to extract params
    params_match = re.search(r'params\s+(\{.*?\})', dsl_block, re.DOTALL)
    if params_match and mcp_calls:
        try:
            params = json.loads(params_match.group(1))
            mcp_calls[0]["params"] = params
        except json.JSONDecodeError:
            pass
    
    return mcp_calls


def list_all_verified():
    """List all verified pathways in the DNA graph."""
    matches = find_verified_pathways()
    tools = {}
    for m in matches:
        key = f"{m['tool']}.{m['action']}"
        if key not in tools:
            tools[key] = m
    
    print(f"Verified pathways: {len(tools)} unique tool.action combinations")
    for key, info in sorted(tools.items()):
        params_preview = json.dumps(info.get('parameters_tried', {}))
        if len(params_preview) > 60:
            params_preview = params_preview[:57] + "..."
        print(f"  {key} — {params_preview}")
    
    return tools


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python pathway_to_dsl.py <feature_name>     # append pathway to DSL")
        print("  python pathway_to_dsl.py --list              # list all verified pathways")
        print("  python pathway_to_dsl.py --from-dsl '<block>' # convert DSL to MCP")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg == "--list":
        list_all_verified()
    elif arg == "--from-dsl":
        dsl_block = sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read()
        calls = dsl_pathway_to_mcp_calls(dsl_block)
        print(json.dumps(calls, indent=2))
    else:
        ok, msg = append_pathway_to_dsl(arg)
        print(msg)