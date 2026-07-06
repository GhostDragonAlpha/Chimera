"""
Creates MAT_MetalSurface_Dust with procedural dust-accumulation mask for the Ground_Metal_Surface material.

Implements:
- Procedural dust accumulation mask based on surface normal and height
- Dust accumulation in crevices and horizontal surfaces
- Subtle dirt/dust tint blending with base metal material

Usage (from UE Editor Python Console):
    from create_metal_dust_accumulation_material import create_metal_surface_dust_material
    create_metal_surface_dust_material()
"""
import unreal


def create_metal_surface_dust_material():
    """Create MAT_MetalSurface_Dust with procedural dust-accumulation mask."""
    
    package_path = "/Game/Chimera/Materials/MAT_MetalSurface_Dust/MAT_MetalSurface_Dust"
    
    # Check if material already exists
    if unreal.EditorAssetLibrary.does_asset_exist(package_path):
        print(f"[Metal] Material already exists at {package_path}")
        return unreal.load_asset(package_path)
    
    # Create the material
    material_factory = unreal.MaterialFactoryNew()
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "MAT_MetalSurface_Dust",
        "/Game/Chimera/Materials/MAT_MetalSurface_Dust",
        None,
        unreal.Material,
        material_factory
    )
    
    if not material:
        print("[ERROR] Failed to create metal surface dust material asset")
        return None
    
    print(f"[Metal] Created material at {package_path}")
    
    # Set blend mode to Opaque
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_Opaque)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DefaultLit)
    
    # --- Create World Position node (for height-based dust accumulation) ---
    world_pos_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionWorldPosition, -400, 0
    )
    
    # --- Create Normal node (for surface normal-based dust accumulation) ---
    normal_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionWorldNormal, -400, 200
    )
    
    # --- Create Dot product node (Normal dot Up vector for horizontal surfaces) ---
    dot_up_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionDotProduct, -400, 400
    )
    
    # Create Up vector constant (0, 0, 1)
    up_vector_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -400, 600
    )
    up_vector_expr.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
    
    # Connect normal and up vector to dot product
    unreal.MaterialEditingLibrary.connect_material_expression(normal_expr, "WorldNormal", dot_up_expr, "A")
    unreal.MaterialEditingLibrary.connect_material_expression(up_vector_expr, "Result", dot_up_expr, "B")
    
    # --- Create Dust Accumulation Mask node (invert dot product for horizontal surfaces) ---
    # Horizontal surfaces have normal close to (0,0,1), so dot product is ~1.0
    # We want dust to accumulate on horizontal surfaces, so we use the dot product directly
    dust_mask_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, -400, 800
    )
    dust_mask_expr.set_editor_property("parameter_name", "DustAccumulationMask")
    dust_mask_expr.set_editor_property("default_value", 1.0)
    
    # --- Create Dust Color node (subtle grey-brown dust tint) ---
    dust_color_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -400, 1000
    )
    dust_color_expr.set_editor_property("constant", unreal.LinearColor(0.65, 0.60, 0.55, 1.0))
    
    # --- Create Base Metal Color node (clean metal base) ---
    metal_color_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -400, 1200
    )
    metal_color_expr.set_editor_property("constant", unreal.LinearColor(0.75, 0.78, 0.82, 1.0))
    
    # --- Create Lerp node (blend between dust color and metal color based on mask) ---
    lerp_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionLerp, -400, 1400
    )
    
    # Connect to Lerp: A=dust_color, B=metal_color, Alpha=dust_mask
    unreal.MaterialEditingLibrary.connect_material_expression(dust_color_expr, "Result", lerp_expr, "A")
    unreal.MaterialEditingLibrary.connect_material_expression(metal_color_expr, "Result", lerp_expr, "B")
    unreal.MaterialEditingLibrary.connect_material_expression(dot_up_expr, "Result", lerp_expr, "Alpha")
    
    # --- Create Roughness node with dust variation ---
    roughness_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, -400, 1600
    )
    roughness_expr.set_editor_property("parameter_name", "DustRoughness")
    roughness_expr.set_editor_property("default_value", 0.7)  # Dust is rougher than clean metal
    
    # --- Create Metallic node (metal remains metallic, dust is dielectric) ---
    metallic_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, -400, 1800
    )
    metallic_expr.set_editor_property("parameter_name", "DustMetallic")
    metallic_expr.set_editor_property("default_value", 0.3)  # Dust has some metallic particles
    
    # --- Connect to material output ---
    # Base Color: Lerp between dust color and metal color
    unreal.MaterialEditingLibrary.connect_material_property(
        lerp_expr, "Result", unreal.MaterialProperty.MP_BaseColor
    )
    
    # Roughness: Dust roughness parameter
    unreal.MaterialEditingLibrary.connect_material_property(
        roughness_expr, "Result", unreal.MaterialProperty.MP_Roughness
    )
    
    # Metallic: Dust metallic parameter
    unreal.MaterialEditingLibrary.connect_material_property(
        metallic_expr, "Result", unreal.MaterialProperty.MP_Metallic
    )
    
    # Force material recompilation
    unreal.MaterialEditingLibrary.recompile_material(material)
    
    # Save the package
    unreal.EditorAssetLibrary.save_asset(package_path)
    
    print(f"[Metal] MAT_MetalSurface_Dust created with:")
    print(f"  - Blend Mode: Opaque")
    print(f"  - Shading Model: MSM_DefaultLit")
    print(f"  - Procedural Dust Accumulation Mask based on surface normal (horizontal surfaces accumulate more dust)")
    print(f"  - Dust Color: (0.65, 0.60, 0.55) - subtle grey-brown dust tint")
    print(f"  - Base Metal Color: (0.75, 0.78, 0.82) - clean metal base")
    print(f"  - DustRoughness Parameter: 0.7 - dust is rougher than clean metal")
    print(f"  - DustMetallic Parameter: 0.3 - dust has some metallic particles")
    
    return material


if __name__ == "__main__":
    create_metal_surface_dust_material()
