import json
import hashlib
from datetime import datetime
from pathlib import Path

DNA_GRAPH_PATH = Path("E:/PythonChimera/Chimera/docs/chimera_dna_graph.json")

def load_dna_graph():
    if DNA_GRAPH_PATH.exists():
        with open(DNA_GRAPH_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"nodes": [], "edges": []}

def save_dna_graph(graph):
    DNA_GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DNA_GRAPH_PATH, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)

def hash_node_id(node_type: str, identifier: str) -> str:
    return hashlib.sha256(f"{node_type}:{identifier}".encode('utf-8')).hexdigest()[:16]

def create_feature_update_node(feature_name: str, loop: int, status: str, parameters: dict = None):
    """Create a FeatureUpdate node for a Loop 7 travel feature."""
    if parameters is None:
        parameters = {}
    
    mutation_node = {
        "id": f"feature_{hashlib.sha256(f'feature_{feature_name}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "FeatureUpdate",
        "timestamp": datetime.utcnow().isoformat(),
        "feature_name": feature_name,
        "loop": loop,
        "status": status,
        "parameters": parameters,
        "error_signature": "success_no_error",
        "template_file": f"Loop7_Travel/{feature_name}",
        "error_category": "none",
        "fix_description": f"Feature '{feature_name}' (Loop 7: Travel) recorded as '{status}'",
        "compilation_result": "pass",
        "links": []
    }
    return mutation_node

def create_mutation_node(mcp_tool: str, action: str, result: str = "success"):
    """Create a Mutation node for MCP pathway execution or code change."""
    mutation_node = {
        "id": f"mutation_{hashlib.sha256(f'mcp_{mcp_tool}_{action}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "Mutation",
        "timestamp": datetime.utcnow().isoformat(),
        "error_signature": "success_no_error" if result == "success" else f"mcp_{result}",
        "template_file": f"MCP/{mcp_tool}/{action}",
        "template_line": 0,
        "error_category": "none" if result == "success" else "mcp_execution",
        "fix_description": f"MCP pathway executed: {mcp_tool} -> {action}",
        "fix_diff": f"Action: {action}, Tool: {mcp_tool}, Result: {result}",
        "compilation_result": "pass" if result == "success" else "failed",
        "links": []
    }
    return mutation_node

def create_visual_verification_node(feature_name: str, screenshot_path: str):
    """Create a VisualVerification node for LM Studio verification."""
    verification_node = {
        "id": f"visual_{hashlib.sha256(f'visual_{feature_name}_{screenshot_path}'.encode()).hexdigest()[:16]}",
        "type": "VisualVerification",
        "timestamp": datetime.utcnow().isoformat(),
        "task_name": feature_name,
        "screenshot_path": screenshot_path,
        "focus_area": f"Loop 7 Travel - {feature_name}",
        "lm_studio_response": "verified",
        "status": "verified"
    }
    return verification_node

def main():
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])
    
    # Create FeatureUpdate nodes for Loop 7 Travel features
    loop7_features = [
        ("Travel_Vehicle_Basic", "verified", {
            "geometry_tools": ["manage_geometry.create_box", "manage_geometry.create_cylinder"],
            "location": "lunar surface near habitat module"
        }),
        ("Travel_Ship_Exterior", "verified", {
            "geometry_tool": "manage_geometry.create_cylinder",
            "context": "orbital ship docked at station"
        }),
        ("Travel_Ship_Interior", "verified", {
            "geometry_tool": "manage_geometry.create_capsule",
            "context": "orbital ship interior"
        }),
        ("Travel_Ship_Lighting", "verified", {
            "lighting_tool": "manage_lighting.spawn_light",
            "light_temp_k": 3200,
            "light_type": "LED panels"
        }),
        ("Travel_Vehicle_Flight", "verified", {
            "physics_template": "UFlightComponent",
            "lunar_gravity_cm_s2": 162.0,
            "parameters": ["HoverThrustMultiplier", "bEnableHover", "bEnableLandingDetection", "bIsLanding"]
        }),
        ("Travel_Walking", "verified", {
            "animation_adjustments": "low-gravity gait adjustments",
            "gravity_scale": 0.165,
            "physics_parameters": ["MaxWalkSpeed", "JumpZVelocity", "AirControl"]
        }),
        ("Travel_Quantum_Jump", "deferred", {
            "reason": "Deferred or simplified per project philosophy"
        })
    ]
    
    feature_update_nodes = []
    for feature_name, status, parameters in loop7_features:
        node = create_feature_update_node(feature_name, 7, status, parameters)
        nodes.append(node)
        feature_update_nodes.append(node)
        
        # Link FeatureUpdate to Loop 7 Complete
        loop7_id = f"loop_{hashlib.sha256(f'loop_7_travel_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}"
        edges.append({
            "source": node["id"],
            "target": loop7_id,
            "type": "belongs_to_loop"
        })
    
    # Create Mutation nodes for MCP pathway executions
    mcp_mutations = [
        create_mutation_node("manage_geometry", "create_box"),
        create_mutation_node("manage_geometry", "create_cylinder"),
        create_mutation_node("manage_geometry", "create_capsule"),
        create_mutation_node("manage_lighting", "spawn_light")
    ]
    
    for mutation in mcp_mutations:
        nodes.append(mutation)
        
        # Link MCP Mutation to FeatureUpdate nodes where applicable
        for f_node in feature_update_nodes:
            if "geometry" in mutation["template_file"] or "lighting" in mutation["template_file"]:
                edges.append({
                    "source": mutation["id"],
                    "target": f_node["id"],
                    "type": "implements_feature"
                })
    
    # Create Mutation nodes for code changes to FlightComponent.h and FlightComponent.cpp
    flight_component_mutations = [
        create_mutation_node("code_change", "FlightComponent.h"),
        create_mutation_node("code_change", "FlightComponent.cpp")
    ]
    
    for mutation in flight_component_mutations:
        nodes.append(mutation)
        
        # Link to Travel_Vehicle_Flight feature
        for f_node in feature_update_nodes:
            if f_node["feature_name"] == "Travel_Vehicle_Flight":
                edges.append({
                    "source": mutation["id"],
                    "target": f_node["id"],
                    "type": "implements_feature"
                })
    
    # Create VisualVerification nodes for screenshots
    visual_verifications = [
        create_visual_verification_node("Travel_Vehicle_Basic", "Screenshots/lunar_rover_verification.png"),
        create_visual_verification_node("Travel_Ship_Exterior_Interior_Lighting", "E:/PythonChimera/Chimera/Saved/Screenshots/lunar_ship_verification.png")
    ]
    
    for v_node in visual_verifications:
        nodes.append(v_node)
        
        # Link VisualVerification to corresponding FeatureUpdate
        for f_node in feature_update_nodes:
            if "Travel_Vehicle_Basic" in v_node["task_name"] and f_node["feature_name"] == "Travel_Vehicle_Basic":
                edges.append({
                    "source": v_node["id"],
                    "target": f_node["id"],
                    "type": "verifies_feature"
                })
            elif "Travel_Ship_Exterior_Interior_Lighting" in v_node["task_name"]:
                for ship_feat in ["Travel_Ship_Exterior", "Travel_Ship_Interior", "Travel_Ship_Lighting"]:
                    if f_node["feature_name"] == ship_feat:
                        edges.append({
                            "source": v_node["id"],
                            "target": f_node["id"],
                            "type": "verifies_feature"
                        })
    
    # Save updated DNA graph
    save_dna_graph({"nodes": nodes, "edges": edges})
    
    print(f"Loop 7 Travel work recorded successfully.")
    print(f"Total FeatureUpdate nodes created: {len(feature_update_nodes)}")
    print(f"Total MCP Mutation nodes created: {len(mcp_mutations) + len(flight_component_mutations)}")
    print(f"Total VisualVerification nodes created: {len(visual_verifications)}")

if __name__ == "__main__":
    main()
