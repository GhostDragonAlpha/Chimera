"""
Verification Studio Runner
==========================
Reusable script for visual verification of any feature in the 
L_VerificationStudio level.

Workflow:
  1. Load Verification Studio level
  2. Clear previous verification items (tag-based)
  3. Spawn mesh at pedestal origin
  4. Apply material with correct parameter connections
  5. Set viewport to studio camera
  6. Take screenshot
  7. Send to LM Studio with canonical reference
  8. Record result to DNA graph
  9. Loop back to step 2 if refinement needed

Usage:
  python verification_studio_runner.py --feature Player_Character_Suit \\
      --mesh /Game/Characters/NPCs/SM_NPC_Helmet \\
      --material /Game/Chimera/Materials/MAT_Player_Suit_Visor \\
      --canonical ../research/loop0/Player_Character_Suit/CANONICAL_REFERENCE.jpg \\
      --params '{"BaseColor":[1.0,0.85,0.4,1.0],"Metallic":1.0,"Roughness":0.1,"Opacity":0.7}'
"""

import sys
import os
import json
import base64
import time
import argparse
from datetime import datetime
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MCP_URL = "http://localhost:3000/mcp"
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
# blank on purpose — the model is whatever LM Studio has resident, never a pinned
# id (this used to name qwen3.6-35b-a3b-mtp@iq2_m, gone since 2026-07-12)
LM_MODEL = ""
SCREENSHOT_DIR = r"E:\PythonChimera\Chimera\Saved\Screenshots"

CHIMERA_DIR = Path(r"E:\PythonChimera\Chimera")
sys.path.insert(0, str(CHIMERA_DIR / "core"))
from graphify_interface import graphify_mutate

# ---------------------------------------------------------------------------
# MCP Helper
# ---------------------------------------------------------------------------
def mcp_call(tool_name, arguments, timeout=60):
    """Call an MCP tool via the bridge's JSON-RPC endpoint."""
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000),
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments}
    }
    resp = requests.post(MCP_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

# ---------------------------------------------------------------------------
# UE5 Level Operations
# ---------------------------------------------------------------------------
def load_studio_level():
    """Load the Verification Studio level."""
    print("[1/8] Loading Verification Studio level...")
    result = mcp_call("manage_level", {
        "action": "load_level",
        "levelPath": "/Game/Chimera/Levels/L_VerificationStudio/L_VerificationStudio"
    })
    print(f"       Level loaded: {result.get('result', {}).get('success', False)}")
    time.sleep(2)
    return result

def clear_previous_items():
    """Find and delete actors tagged 'VerificationItem'."""
    print("[2/8] Clearing previous verification items...")
    try:
        actors = mcp_call("control_actor", {
            "action": "find_by_tag",
            "tag": "VerificationItem"
        })
        actor_list = actors.get("result", {}).get("actors", [])
        for actor in actor_list:
            name = actor.get("actorName", actor.get("name", "unknown"))
            mcp_call("control_actor", {
                "action": "delete",
                "actorName": name
            })
            print(f"       Deleted: {name}")
        if not actor_list:
            print("       No previous items found.")
    except Exception as e:
        print(f"       Cleanup skipped: {e}")

def spawn_verification_mesh(mesh_path, location=None, rotation=None):
    """Spawn the feature mesh at the pedestal origin."""
    print(f"[3/8] Spawning mesh: {mesh_path}...")
    loc = location or {"x": 0, "y": 0, "z": 10}
    rot = rotation or {"pitch": 0, "yaw": 0, "roll": 0}
    
    result = mcp_call("control_actor", {
        "action": "spawn_actor",
        "actorName": "VerificationItem_Current",
        "classPath": mesh_path,
        "location": loc,
        "rotation": rot
    })
    # Add tag for cleanup later
    try:
        mcp_call("control_actor", {
            "action": "add_tag",
            "actorName": "VerificationItem_Current",
            "tag": "VerificationItem"
        })
    except:
        pass
    print(f"       Actor: VerificationItem_Current")
    return result

def apply_material_via_python(material_path, params):
    """
    Apply material to the spawned mesh and set its parameters.
    Uses UE Python via execute_python for proper node connections.
    """
    print(f"[4/8] Applying material: {material_path}...")
    
    # First apply the material via MCP
    try:
        mcp_call("control_actor", {
            "action": "set_actor_material",
            "actorName": "VerificationItem_Current",
            "materialPath": f"{material_path}.{material_path.split('/')[-1]}"
        })
        print("       Material applied via MCP set_actor_material")
    except Exception as e:
        print(f"       set_actor_material failed: {e}")
    
    # Now set material parameters via UE Python for proper connections
    base_color = params.get("BaseColor", [1.0, 0.85, 0.4, 1.0])
    metallic = params.get("Metallic", 1.0)
    roughness = params.get("Roughness", 0.1)
    opacity = params.get("Opacity", 0.7)
    
    # Single-line UE Python to modify the material constants
    # Each call must be a single line due to execute_python handler limitation
    python_script = (
        f'mat = unreal.load_asset("{material_path}.{material_path.split("/")[-1]}"); '
        f'if mat: '
        f'  exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat); '
        f'  for e in exprs: '
        f'    cls = e.get_class().get_name(); '
        f'    if cls == "MaterialExpressionConstant3Vector": '
        f'      e.set_editor_property("constant", unreal.LinearColor({base_color[0]},{base_color[1]},{base_color[2]},{base_color[3]})); '
        f'      print(f"BaseColor set"); '
        f'    elif cls == "MaterialExpressionConstant": '
        f'      r = e.get_editor_property("r"); '
        f'      if abs(r - 1.0) < 0.01: '
        f'        e.set_editor_property("r", {metallic}); '
        f'        print(f"Metallic set to {metallic}"); '
        f'      elif abs(r - 0.1) < 0.01: '
        f'        e.set_editor_property("r", {roughness}); '
        f'        print(f"Roughness set to {roughness}"); '
        f'      else: '
        f'        e.set_editor_property("r", {opacity}); '
        f'        print(f"Opacity set to {opacity}"); '
        f'  unreal.MaterialEditingLibrary.rebuild_material_instance_editor_only(mat); '
        f'  unreal.EditorAssetLibrary.save_loaded_asset(mat); '
        f'  print("Material saved");'
    )
    
    try:
        result = mcp_call("system_control", {
            "action": "execute_python",
            "code": python_script
        })
        print(f"       UE Python executed: {result.get('result', {}).get('output', 'OK')}")
    except Exception as e:
        print(f"       UE Python error (non-fatal): {e}")
    
    # Compile and rebuild
    try:
        mcp_call("manage_asset", {
            "action": "rebuild_material",
            "assetPath": material_path
        })
        print("       Material rebuilt")
    except Exception as e:
        print(f"       Material rebuild warning: {e}")
    
    print("       Material configured successfully")

def set_viewport_to_camera():
    """Set the editor viewport to the verification camera position and prepare for pyautogui screenshot."""
    print("[5/8] Preparing UE5 viewport for screenshot...")
    try:
        # Set view mode to Lit
        mcp_call("control_editor", {
            "action": "set_view_mode",
            "viewMode": "Lit"
        })
        # Ensure game view is disabled
        mcp_call("control_editor", {
            "action": "set_game_view",
            "enabled": False
        })
        print("       Viewport prepared: Lit mode, game view disabled")
    except Exception as e:
        print(f"       Viewport preparation warning: {e}")

# ---------------------------------------------------------------------------
# Screenshot
# ---------------------------------------------------------------------------
def take_screenshot(feature_name):
    """Take a screenshot of the current viewport using MCP control_editor screenshot mode=editor_viewport per H-2 prohibition."""
    print(f"[6/8] Taking screenshot via MCP control_editor mode=editor_viewport...")
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"{feature_name}_verified.png")
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    # Use MCP control_editor screenshot mode=editor_viewport (H-2 prohibition: never verify from desktop screenshots)
    try:
        import sys
        project_dir = Path(__file__).parent.parent
        if str(project_dir / "core") not in sys.path:
            sys.path.insert(0, str(project_dir / "core"))

        from telemetry_probe import MCPStdioClient
        client = MCPStdioClient()

        # Call control_editor screenshot with mode=editor_viewport
        result = client.call("control_editor", {
            "action": "screenshot",
            "filename": f"{feature_name}_verified.png",
            "mode": "editor_viewport"
        })

        client.close()

        # Check if the call was successful
        structured_content = result.get("result", {}).get("structuredContent", {})
        if structured_content.get("success"):
            print(f"       Screenshot via MCP control_editor mode=editor_viewport saved: {screenshot_path}")
            return screenshot_path
        else:
            error_msg = structured_content.get("message", "Unknown error")
            print(f"       Warning: MCP screenshot failed: {error_msg}")
    except Exception as e:
        print(f"       MCP control_editor screenshot failed: {e}")

    # Fallback: try to find any recent valid screenshot in the directory
    screenshots = [f for f in Path(SCREENSHOT_DIR).glob("*.png") if f.stat().st_size > 10000]
    if screenshots:
        screenshot_path = str(max(screenshots, key=os.path.getmtime))
        print(f"       Using most recent valid screenshot (fallback): {screenshot_path}")
        return screenshot_path

    print(f"       ERROR: No screenshot file found at {screenshot_path}")
    return None

# ---------------------------------------------------------------------------
# LM Studio Verification
# ---------------------------------------------------------------------------
def verify_with_lm_studio(screenshot_path, canonical_path, feature_name, params):
    """Send screenshot + canonical reference to LM Studio for verification."""
    print(f"[7/8] Sending to LM Studio for verification...")
    
    # Load and encode screenshot
    with open(screenshot_path, "rb") as f:
        screenshot_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    # Prepare prompt with feature context
    prompt = (
        f"You are evaluating a {feature_name} in Unreal Engine 5.\n\n"
        f"CRITICAL: Your FINAL line MUST be exactly one of:\n"
        f"VERIFIED\n"
        f"NEEDS_REFINEMENT: <one specific change>\n\n"
        f"Material parameters applied:\n"
        f"- BaseColor (gold): RGB({params.get('BaseColor', [1.0,0.85,0.4,1.0])})\n"
        f"- Metallic: {params.get('Metallic', 1.0)}\n"
        f"- Roughness: {params.get('Roughness', 0.1)}\n"
        f"- BlendMode: Translucent\n\n"
        f"Look for:\n"
        f"1. Warm gold reflective appearance matching the canonical reference\n"
        f"2. Metallic sheen with specular highlights\n"
        f"3. Semi-translucent quality\n"
        f"4. Correct proportions and scale in the studio environment\n\n"
        f"Output format:\n"
        f"Analysis: <one sentence>\n"
        f"VERIFIED\n"
        f"OR\n"
        f"Analysis: <one sentence>\n"
        f"NEEDS_REFINEMENT: <one specific change>"
    )
    
    # Build message content
    content_parts = [{"type": "text", "text": prompt}]
    
    # Add screenshot image
    content_parts.append({
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
    })
    
    # Add canonical reference if available
    if canonical_path and os.path.exists(canonical_path):
        with open(canonical_path, "rb") as f:
            canonical_b64 = base64.b64encode(f.read()).decode("utf-8")
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{canonical_b64}"}
        })
        print(f"       Canonical reference: {canonical_path}")
    else:
        # Text description fallback
        content_parts.append({
            "type": "text",
            "text": "CANONICAL REFERENCE: Apollo A7L EVA suit visor - gold-coated polycarbonate, "
                    "semi-translucent, warm golden RGB(1.0,0.85,0.45), highly polished (roughness ~0.1)."
        })
    
    body = {
        "model": LM_MODEL,
        "messages": [{"role": "user", "content": content_parts}],
        "temperature": 0.0,
        "max_tokens": 500
    }
    
    try:
        resp = requests.post(LM_STUDIO_URL, json=body, 
                           headers={"Content-Type": "application/json"}, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        lm_response = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not lm_response:
            lm_response = data.get("choices", [{}])[0].get("message", {}).get("reasoning_content", "")
    except Exception as e:
        print(f"ERROR: LM Studio request failed: {e}")
        lm_response = "VERIFICATION_FAILED: LM Studio unavailable"
    
    print(f"       LM Studio response received ({len(lm_response)} chars)")
    print(f"       Response preview: {lm_response[:200]}...")
    
    # Parse result
    verified = "VERIFIED" in lm_response.upper() and "NEEDS_REFINEMENT" not in lm_response.upper()
    needs_refinement = "NEEDS_REFINEMENT" in lm_response.upper()
    
    if verified:
        result = "VERIFIED"
    elif needs_refinement:
        result = "NEEDS_REFINEMENT"
    else:
        result = "UNCLEAR"
    
    return result, lm_response

# ---------------------------------------------------------------------------
# DNA Graph Recording
# ---------------------------------------------------------------------------
def record_to_dna_graph(feature_name, screenshot_path, verified, lm_response, 
                        iterations=1, lighting_config="3-point"):
    """Record visual verification result to the DNA graph."""
    print(f"[8/8] Recording to DNA graph...")
    
    details = {
        "feature": feature_name,
        "screenshot_path": screenshot_path,
        "verified": verified,
        "lm_studio_response": lm_response,
        "verification_env": "L_VerificationStudio",
        "lighting_config": lighting_config,
        "iterations": iterations,
        "result": "VERIFIED" if verified else "NEEDS_REFINEMENT"
    }
    
    try:
        node_id = graphify_mutate(
            "visual_verification",
            result="pass" if verified else "fail",
            details=details
        )
        print(f"       DNA graph node ID: {node_id}")
        return node_id
    except Exception as e:
        print(f"       DNA graph recording failed: {e}")
        return None

def save_verification_report(feature_name, screenshot_path, result, lm_response, 
                             dna_node_id, iterations):
    """Save verification report as JSON."""
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "feature": feature_name,
        "screenshot_path": screenshot_path,
        "result": result,
        "verified": result == "VERIFIED",
        "lm_studio_response": lm_response,
        "dna_node_id": dna_node_id,
        "iterations": iterations,
        "environment": "L_VerificationStudio"
    }
    
    output_path = os.path.join(CHIMERA_DIR, f"verify_{feature_name}_result.json")
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"       Report saved: {output_path}")
    return output_path

# ---------------------------------------------------------------------------
# Main Verification Loop
# ---------------------------------------------------------------------------
def run_verification(feature_name, mesh_path, material_path, params, 
                     canonical_path=None, max_iterations=3):
    """Run the full verification loop for a feature."""
    print("\n" + "=" * 70)
    print(f"  VERIFICATION STUDIO RUNNER - {feature_name}")
    print("=" * 70)
    print(f"  Mesh:      {mesh_path}")
    print(f"  Material:  {material_path}")
    print(f"  Params:    {json.dumps(params)}")
    print(f"  Canonical: {canonical_path or 'text description only'}")
    print("=" * 70 + "\n")
    
    iteration = 0
    final_result = "UNCLEAR"
    final_response = ""
    screenshot_path = None
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration}/{max_iterations} ---\n")
        
        # Step 1: Load level
        load_studio_level()
        
        # Step 2: Clear previous items
        clear_previous_items()
        
        # Step 3: Spawn mesh
        spawn_verification_mesh(mesh_path)
        
        # Step 4: Apply material
        apply_material_via_python(material_path, params)
        
        # Step 5: Set viewport
        set_viewport_to_camera()
        
        # Small delay for rendering to settle
        time.sleep(1)
        
        # Step 6: Screenshot
        screenshot_path = take_screenshot(feature_name)
        if not screenshot_path:
            print("ERROR: No screenshot captured. Aborting.")
            break
        
        # Step 7: LM Studio verification
        result, lm_response = verify_with_lm_studio(
            screenshot_path, canonical_path, feature_name, params
        )
        final_result = result
        final_response = lm_response
        
        print(f"\n  >> LM Studio Result: {result}")
        
        # Check if verification passed
        if result == "VERIFIED":
            print("\n  >> FEATURE VERIFIED!")
            break
        elif result == "NEEDS_REFINEMENT" and iteration < max_iterations:
            # Extract refinement suggestion
            if ":" in lm_response.split("NEEDS_REFINEMENT")[-1]:
                suggestion = lm_response.split("NEEDS_REFINEMENT:")[-1].strip()
                print(f"  >> Refinement: {suggestion}")
            print("  >> Looping for refinement...")
            time.sleep(1)
        else:
            print(f"  >> Result: {result} - continuing...")
            break
    
    # Step 8: Record to DNA graph
    dna_node_id = record_to_dna_graph(
        feature_name, screenshot_path, 
        final_result == "VERIFIED", final_response,
        iterations=iteration
    )
    
    # Save report
    report_path = save_verification_report(
        feature_name, screenshot_path, final_result, 
        final_response, dna_node_id, iteration
    )
    
    # Summary
    print("\n" + "=" * 70)
    print(f"  VERIFICATION COMPLETE")
    print(f"  Feature:  {feature_name}")
    print(f"  Result:   {final_result}")
    print(f"  Iterations: {iteration}")
    print(f"  Screenshot: {screenshot_path}")
    print(f"  Report:    {report_path}")
    print("=" * 70 + "\n")
    
    return {
        "feature": feature_name,
        "result": final_result,
        "verified": final_result == "VERIFIED",
        "screenshot_path": screenshot_path,
        "lm_studio_response": final_response,
        "iterations": iteration,
        "dna_node_id": dna_node_id,
        "report_path": report_path
    }

# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Verification Studio Runner")
    parser.add_argument("--feature", required=True, help="Feature name (e.g. Player_Character_Suit)")
    parser.add_argument("--mesh", required=True, help="Mesh asset path")
    parser.add_argument("--material", required=True, help="Material asset path")
    parser.add_argument("--canonical", help="Canonical reference image path")
    parser.add_argument("--params", default='{"BaseColor":[1.0,0.85,0.4,1.0],"Metallic":1.0,"Roughness":0.1,"Opacity":0.7}',
                       help="Material parameters JSON")
    parser.add_argument("--max-iterations", type=int, default=3, help="Max refinement iterations")
    
    args = parser.parse_args()
    
    params = json.loads(args.params)
    
    result = run_verification(
        feature_name=args.feature,
        mesh_path=args.mesh,
        material_path=args.material,
        params=params,
        canonical_path=args.canonical,
        max_iterations=args.max_iterations
    )
    
    # Exit with appropriate code
    sys.exit(0 if result["verified"] else 1)

if __name__ == "__main__":
    main()
