"""
Creates MAT_Moon_Regolith material with proper PBR parameters and graph connections.
Run from UE Editor Python Console.
"""
import unreal

def create_moon_regolith_material():
    """Create MAT_Moon_Regolith with PBR lunar regolith parameters."""
    
    package_path = "/Game/Celestial/Materials/MAT_Moon_Regolith"
    
    # Check if material already exists
    if unreal.EditorAssetLibrary.does_asset_exist(package_path):
        print(f"[Moon] Material already exists at {package_path}")
        return unreal.load_asset(package_path)
    
    # Create the material
    material_factory = unreal.MaterialFactoryNew()
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "MAT_Moon_Regolith",
        "/Game/Celestial/Materials",
        None,
        unreal.Material,
        material_factory
    )
    
    if not material:
        print("[ERROR] Failed to create material asset")
        return None
    
    print(f"[Moon] Created material at {package_path}")
    
    # Set blend mode to Opaque
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_Opaque)
    
    # --- Create Base Color node ---
    base_color_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -400, 0
    )
    base_color_expr.set_editor_property("constant", unreal.LinearColor(0.55, 0.50, 0.47, 1.0))
    
    # --- Create Roughness node ---
    roughness_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -400, 200
    )
    roughness_expr.set_editor_property("r", 0.95)
    
    # --- Create Metallic node ---
    metallic_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -400, 400
    )
    metallic_expr.set_editor_property("r", 0.0)
    
    # --- Create Specular node ---
    specular_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -400, 600
    )
    specular_expr.set_editor_property("r", 0.05)
    
    # --- Connect to material output ---
    # Get the material's base material output
    material_output = material.get_expression_collection()
    
    unreal.MaterialEditingLibrary.connect_material_property(
        base_color_expr, "", unreal.MaterialProperty.MP_BaseColor
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        roughness_expr, "", unreal.MaterialProperty.MP_Roughness
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        metallic_expr, "", unreal.MaterialProperty.MP_Metallic
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        specular_expr, "", unreal.MaterialProperty.MP_Specular
    )
    
    # Force material recompilation
    unreal.MaterialEditingLibrary.recompile_material(material)
    
    # Save the package
    unreal.EditorAssetLibrary.save_asset(package_path)
    
    print(f"[Moon] MAT_Moon_Regolith created with:")
    print(f"  - Base Color: (0.55, 0.50, 0.47) - grey-brown lunar regolith")
    print(f"  - Roughness: 0.95 - extremely matte, powdery")
    print(f"  - Metallic: 0.0 - dielectric")
    print(f"  - Specular: 0.05 - very low")
    
    return material

if __name__ == "__main__":
    create_moon_regolith_material()
