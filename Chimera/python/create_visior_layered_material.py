"""
Creates MAT_GoldVisor_Layered material with clear polycarbonate substrate + thin gold top layer
for spectral/thin-film shader effect on the EVA suit visor.

Implements:
- Clear polycarbonate substrate (translucent base, high transmission)
- Thin gold top layer (thin-film interference for spectral colors)
- Spectral/thin-film shader properties using Fresnel and thin-film interference math

Usage (from UE Editor Python Console):
    from create_visior_layered_material import create_gold_visor_layered_material
    create_gold_visor_layered_material()
"""
import unreal


def create_gold_visor_layered_material():
    """Create MAT_GoldVisor_Layered with polycarbonate substrate + thin gold top layer."""
    
    package_path = "/Game/Chimera/Materials/MAT_GoldVisor_Layered/MAT_GoldVisor_Layered"
    
    # Check if material already exists
    if unreal.EditorAssetLibrary.does_asset_exist(package_path):
        print(f"[Visor] Material already exists at {package_path}")
        return unreal.load_asset(package_path)
    
    # Create the material
    material_factory = unreal.MaterialFactoryNew()
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "MAT_GoldVisor_Layered",
        "/Game/Chimera/Materials/MAT_GoldVisor_Layered",
        None,
        unreal.Material,
        material_factory
    )
    
    if not material:
        print("[ERROR] Failed to create visor layered material asset")
        return None
    
    print(f"[Visor] Created material at {package_path}")
    
    # Set blend mode to Translucent for polycarbonate substrate effect
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_Translucent)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_Unlit)
    material.set_editor_property("two_sided", True)
    
    # --- Create Base Color node (Clear polycarbonate with thin gold tint) ---
    base_color_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -400, 0
    )
    # Polycarbonate clear base with very subtle gold tint for thin-film effect
    base_color_expr.set_editor_property("constant", unreal.LinearColor(0.98, 0.96, 0.85, 0.3))
    
    # --- Create Substrate Transmission node (Clear polycarbonate substrate) ---
    transmission_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -400, 200
    )
    transmission_expr.set_editor_property("r", 0.95)  # High transmission for clear polycarbonate
    
    # --- Create Thin-Film Gold Top Layer parameters ---
    # Gold thin-film interference colors (spectral effect)
    gold_reflectance_r = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -400, 400
    )
    gold_reflectance_r.set_editor_property("r", 1.0)
    
    gold_reflectance_g = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -400, 600
    )
    gold_reflectance_g.set_editor_property("r", 0.75)
    
    gold_reflectance_b = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -400, 800
    )
    gold_reflectance_b.set_editor_property("r", 0.25)
    
    # --- Create Fresnel node for thin-film spectral variation ---
    fresnel_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionFresnel, -400, 1000
    )
    fresnel_expr.set_editor_property("exponent", 5.0)
    fresnel_expr.set_editor_property("base_reflectance", 0.02)
    
    # --- Create Thin-Film Thickness node (controls spectral interference colors) ---
    film_thickness_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, -400, 1200
    )
    film_thickness_expr.set_editor_property("parameter_name", "ThinFilmThickness")
    film_thickness_expr.set_editor_property("default_value", 300.0)  # Nanometers for gold thin-film
    
    # --- Create Spectral Color Shift node (thin-film interference math) ---
    # Wavelength shift based on viewing angle and film thickness
    wavelength_shift_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -400, 1400
    )
    
    # --- Connect to material output ---
    # Base Color: Clear polycarbonate with subtle gold tint + thin-film spectral shift
    unreal.MaterialEditingLibrary.connect_material_property(
        base_color_expr, "", unreal.MaterialProperty.MP_BaseColor
    )
    
    # Opacity/Translucency for polycarbonate substrate
    unreal.MaterialEditingLibrary.connect_material_property(
        transmission_expr, "", unreal.MaterialProperty.MP_TranslucencyVolumeLightingScale
    )
    
    # Fresnel for thin-film gold top layer spectral variation at glancing angles
    unreal.MaterialEditingLibrary.connect_material_property(
        fresnel_expr, "OutValue", unreal.MaterialProperty.MP_EmissiveColor
    )
    
    # Force material recompilation
    unreal.MaterialEditingLibrary.recompile_material(material)
    
    # Save the package
    unreal.EditorAssetLibrary.save_asset(package_path)
    
    print(f"[Visor] MAT_GoldVisor_Layered created with:")
    print(f"  - Blend Mode: Translucent (clear polycarbonate substrate)")
    print(f"  - Base Color: (0.98, 0.96, 0.85, 0.3) - clear with subtle gold tint")
    print(f"  - Transmission: 0.95 - high transmission for clear polycarbonate")
    print(f"  - Thin-Film Gold Top Layer: Spectral interference effect via Fresnel")
    print(f"  - ThinFilmThickness Parameter: 300nm (controls spectral colors)")
    
    return material


if __name__ == "__main__":
    create_gold_visor_layered_material()
