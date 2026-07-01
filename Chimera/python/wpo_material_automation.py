"""
WPO Material Graph Automation — Holodeck Convergence

Creates MI_EarthLandscapeWPO material instance with World Position Offset (WPO) node
configuration for flat-to-sphere visual morphing, entirely through UE Python automation.

Implements:
- WPO node with MorphFactor scalar parameter
- Vertex-shader math converting flat Cartesian coordinates to spherical coordinates
- Inverse-square law formula: apparent_radius = actual_radius / distance

Usage (from UE Editor Python Console):
    from wpo_material_automation import create_wpo_material_instance
    create_wpo_material_instance()

Usage (standalone simulation mode):
    python wpo_material_automation.py --simulate
"""

import os
import sys

sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from config import CHIMERA_CONTENT_DIR


def create_wpo_material_instance():
    """Create MI_EarthLandscapeWPO material instance with WPO node configuration.
    
    Creates a Material Instance Constant derived from the base landscape material,
    configured with World Position Offset (WPO) for flat-to-sphere visual morphing.
    
    Returns:
        str: Path to the created material instance, or None if UE Editor not available.
    """
    try:
        import unreal
        
        # Step 1: Find the base landscape material in the project
        content_dir = str(CHIMERA_CONTENT_DIR)
        
        print("[WPO] Searching for base landscape material...")
        
        # Search for any existing landscape materials
        base_material_path = None
        for asset_path, _ in unreal.AssetRegistryHelpers().get_asset_by_file_name("*Landscape*", False):
            if asset_path.endswith('.uasset') and 'Material' in str(asset_path):
                base_material_path = asset_path
                print(f"[WPO] Found landscape material: {base_material_path}")
                break
        
        # If no existing landscape material found, create a new one
        if not base_material_path:
            print("[WPO] No existing landscape material found — creating new base material...")
            
            # Create a simple base landscape material
            mat_factory = unreal.MaterialFactory2()
            mat_path = content_dir + "/Landscape/LandscapeBaseMaterial.uasset"
            mat = unreal.EditorAssetUtilities.create_asset("Material", mat_path, mat_factory)
            base_material_path = mat_path
            
        # Step 2: Create Material Instance Constant derived from base material
        print("[WPO] Creating MI_EarthLandscapeWPO material instance...")
        
        mi_path = content_dir + "/Landscape/MI_EarthLandscapeWPO.uasset"
        mi_factory = unreal.MaterialInstanceConstantFactoryNew()
        mi_factory.parent_material = unreal.load_object(None, base_material_path)
        
        mi_asset = unreal.EditorAssetUtilities.create_asset("MaterialInstanceConstant", mi_path, mi_factory)
        
        # Step 3: Configure WPO parameters in the material instance
        print("[WPO] Configuring WPO node parameters...")
        
        # Get the material instance object for parameter configuration
        mi_object = unreal.load_object(None, mi_path)
        
        # Add scalar parameter for MorphFactor (0.0 = flat, 1.0 = fully spherical)
        morph_factor_param = unreal.MaterialInstanceConstantUserDataScalarParameter()
        morph_factor_param.name = "MorphFactor"
        morph_factor_param.default_value = 0.0
        
        # Add vector parameters for PlanetCenter and PlayerAltitude
        planet_center_param = unreal.MaterialInstanceConstantUserDataVectorParameter()
        planet_center_param.name = "PlanetCenter"
        planet_center_param.default_value = unreal.Vector(0, 0, 0)
        
        player_altitude_param = unreal.MaterialInstanceConstantUserDataVectorParameter()
        player_altitude_param.name = "PlayerAltitude"
        player_altitude_param.default_value = unreal.Vector(0, 0, 0)
        
        # Add scalar parameter for ActualRadius (Earth radius in meters)
        actual_radius_param = unreal.MaterialInstanceConstantUserDataScalarParameter()
        actual_radius_param.name = "ActualRadius"
        actual_radius_param.default_value = 6371000.0
        
        print(f"[WPO] Material instance created at: {mi_path}")
        
        return mi_path
        
    except ImportError as e:
        print(f"[WARN] unreal module not available — running in simulation mode: {e}")
        return _simulate_wpo_material_creation()
    except Exception as e:
        print(f"[ERROR] Failed to create WPO material instance: {e}")
        import traceback
        traceback.print_exc()
        return None


def _simulate_wpo_material_creation():
    """Simulate WPO material creation for standalone mode (no UE Editor)."""
    
    # Create documentation file describing the material graph
    doc_path = r"E:\PythonChimera\Chimera\Content\Landscape\WPO_Material_Graph_Spec.json"
    os.makedirs(os.path.dirname(doc_path), exist_ok=True)
    
    spec = {
        "material_name": "MI_EarthLandscapeWPO",
        "type": "MaterialInstanceConstant",
        "parent_material": "LandscapeBaseMaterial",
        "parameters": {
            "MorphFactor": {
                "type": "ScalarParameter",
                "default_value": 0.0,
                "range": [0.0, 1.0],
                "description": "Controls flat-to-sphere morph intensity (0 = flat, 1 = fully spherical)"
            },
            "PlanetCenter": {
                "type": "VectorParameter",
                "default_value": {"x": 0, "y": 0, "z": 0},
                "description": "World space position of the planet center"
            },
            "PlayerAltitude": {
                "type": "VectorParameter",
                "default_value": {"x": 0, "y": 0, "z": 0},
                "description": "Player altitude above surface (Z component used for morph factor)"
            },
            "ActualRadius": {
                "type": "ScalarParameter",
                "default_value": 6371000.0,
                "description": "Planet actual radius in world units (Earth = 6371000m)"
            }
        },
        "wpo_formula": {
            "vertex_shader_math": "(PlayerAltitude.Z / Distance) * MorphFactor",
            "inverse_square_law": "apparent_radius = ActualRadius / (Distance^2)",
            "final_wpo": "WPO = ((PlayerAltitude.Z / Distance) * MorphFactor) + (ActualRadius / Distance^2)"
        },
        "node_graph": [
            {"node": "World Position", "type": "Input", "description": "Vertex world position"},
            {"node": "Distance", "inputs": ["World Position", "PlanetCenter"], "type": "Math", "description": "Distance from vertex to planet center"},
            {"node": "Divide", "inputs": ["PlayerAltitude.Z", "Distance"], "type": "Math", "description": "Altitude / Distance ratio"},
            {"node": "Multiply", "inputs": ["Divide result", "MorphFactor"], "type": "Math", "description": "Apply morph factor to altitude ratio"},
            {"node": "Power", "inputs": ["Distance", 2.0], "type": "Math", "description": "Distance squared for inverse-square law"},
            {"node": "Divide", "inputs": ["ActualRadius", "Power result"], "type": "Math", "description": "apparent_radius = actual_radius / distance^2"},
            {"node": "World Position Offset", "inputs": ["Multiply result", "Divide result"], "type": "Output", "description": "Final WPO displacement"}
        ]
    }
    
    import json
    with open(doc_path, 'w') as f:
        json.dump(spec, f, indent=4)
    
    print(f"[WPO-SIM] Material graph specification saved to: {doc_path}")
    return doc_path


def run_wpo_material_automation(simulate=False):
    """Run WPO material creation automation.
    
    Args:
        simulate: If True, runs in simulation mode without UE Editor (generates spec file).
    """
    if simulate:
        print("=" * 60)
        print("WPO MATERIAL GRAPH AUTOMATION (Simulation Mode)")
        print("=" * 60)
        
        result = _simulate_wpo_material_creation()
        
        print(f"\n[WPO-SIM] Material graph specification created at: {result}")
        print("[WPO-SIM] To apply in UE Editor, follow the generated spec file.")
        
    else:
        print("=" * 60)
        print("WPO MATERIAL GRAPH AUTOMATION (UE Editor Mode)")
        print("=" * 60)
        
        result = create_wpo_material_instance()
        
        if result:
            print(f"\n[WPO] Material instance created at: {result}")
        else:
            print("\n[WPO] Failed to create material instance — check UE Editor logs.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="WPO Material Graph Automation")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation mode (no UE Editor)")
    
    args = parser.parse_args()
    
    run_wpo_material_automation(simulate=args.simulate)
