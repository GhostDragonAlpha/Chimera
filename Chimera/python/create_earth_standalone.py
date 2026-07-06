"""
Earth Celestial Body - Standalone UE Python Script
Creates SM_Earth static mesh and MAT_Earth material, places in level.
Run inside UE Editor Python Console.
"""

import unreal


def create_earth():
    """Create Earth sphere, material, and place in level."""
    
    # Step 1: Ensure directories exist
    for dir_path in ["/Game/Celestial", "/Game/Celestial/Materials"]:
        if not unreal.EditorAssetLibrary.does_directory_exist(dir_path):
            unreal.EditorAssetLibrary.make_directory(dir_path)
            print(f"[Earth] Created dir: {dir_path}")
    
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    
    # Step 2: Create SM_Earth sphere
    print("[Earth] Creating SM_Earth...")
    sphere_factory = unreal.SphereFactory()
    sphere_factory.set_editor_property("radius", 500)
    sphere_factory.set_editor_property("sphere_groups", 64)
    
    sm_earth = asset_tools.create_asset(
        "SM_Earth", "/Game/Celestial", None, unreal.StaticMesh, sphere_factory
    )
    
    if sm_earth:
        # Enable Nanite
        mesh_edit = unreal.StaticMeshEditorSubsystem()
        mesh_edit.set_nanite_settings(sm_earth, True, 0.5)
        mesh_edit.build_simple_collision(sm_earth)
        unreal.EditorAssetLibrary.save_asset("/Game/Celestial/SM_Earth")
        print("[Earth] SM_Earth created with Nanite")
    else:
        print("[Earth] ERROR: Failed to create SM_Earth")
        return
    
    # Step 3: Create MAT_Earth material with full node graph
    print("[Earth] Creating MAT_Earth...")
    
    mat_factory = unreal.MaterialFactoryNew()
    mat_earth = asset_tools.create_asset(
        "MAT_Earth", "/Game/Celestial/Materials", None, unreal.Material, mat_factory
    )
    
    if not mat_earth:
        print("[Earth] ERROR: Failed to create MAT_Earth")
        return
    
    mat_edit = unreal.MaterialEditingLibrary
    
    # Clear default expressions
    mat_edit.delete_all_material_expressions(mat_earth)
    
    # --- Texture Coordinate ---
    tex_coord = mat_edit.create_material_expression(
        mat_earth, unreal.MaterialExpressionTextureCoordinate, -600, -200
    )
    tex_coord.set_editor_property("coordinate_index", 0)
    
    # --- Noise for continent pattern ---
    noise = mat_edit.create_material_expression(
        mat_earth, unreal.MaterialExpressionNoise, -300, -200
    )
    noise.set_editor_property("scale", 3.0)
    noise.set_editor_property("tiling", True)
    
    # Connect tex_coord -> noise
    mat_edit.connect_material_expressions(tex_coord, "", noise, "position")
    
    # --- Ocean Color (Vector Parameter) ---
    ocean = mat_edit.create_material_expression(
        mat_earth, unreal.MaterialExpressionVectorParameter, -600, 50
    )
    ocean.set_editor_property("parameter_name", "OceanColor")
    ocean.set_editor_property("default_value", unreal.LinearColor(0.05, 0.15, 0.4, 1.0))
    
    # --- Land Color (Vector Parameter) ---
    land = mat_edit.create_material_expression(
        mat_earth, unreal.MaterialExpressionVectorParameter, -600, 200
    )
    land.set_editor_property("parameter_name", "LandColor")
    land.set_editor_property("default_value", unreal.LinearColor(0.25, 0.32, 0.15, 1.0))
    
    # --- Lerp: blend ocean and land based on noise ---
    lerp = mat_edit.create_material_expression(
        mat_earth, unreal.MaterialExpressionLinearInterpolate, 0, 100
    )
    mat_edit.connect_material_expressions(ocean, "", lerp, "a")
    mat_edit.connect_material_expressions(land, "", lerp, "b")
    mat_edit.connect_material_expressions(noise, "", lerp, "alpha")
    
    # --- Connect Lerp to Base Color ---
    mat_edit.connect_material_property(lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
    
    # --- Roughness (Scalar Parameter) ---
    roughness = mat_edit.create_material_expression(
        mat_earth, unreal.MaterialExpressionScalarParameter, -600, 400
    )
    roughness.set_editor_property("parameter_name", "Roughness")
    roughness.set_editor_property("default_value", 0.3)
    mat_edit.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
    
    # --- Metallic (Scalar Parameter) ---
    metallic = mat_edit.create_material_expression(
        mat_earth, unreal.MaterialExpressionScalarParameter, -600, 500
    )
    metallic.set_editor_property("parameter_name", "Metallic")
    metallic.set_editor_property("default_value", 0.0)
    mat_edit.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)
    
    # --- Specular (Scalar Parameter) ---
    specular = mat_edit.create_material_expression(
        mat_earth, unreal.MaterialExpressionScalarParameter, -600, 600
    )
    specular.set_editor_property("parameter_name", "Specular")
    specular.set_editor_property("default_value", 0.5)
    mat_edit.connect_material_property(specular, "", unreal.MaterialProperty.MP_SPECULAR)
    
    # --- Fresnel for atmospheric edge glow ---
    fresnel = mat_edit.create_material_expression(
        mat_earth, unreal.MaterialExpressionFresnel, -300, 700
    )
    fresnel.set_editor_property("exponent", 3.0)
    
    # --- EmissiveGlow (Scalar Parameter) ---
    emissive_glow = mat_edit.create_material_expression(
        mat_earth, unreal.MaterialExpressionScalarParameter, -600, 800
    )
    emissive_glow.set_editor_property("parameter_name", "EmissiveGlow")
    emissive_glow.set_editor_property("default_value", 0.02)
    
    # --- Multiply: Fresnel * EmissiveGlow ---
    mult1 = mat_edit.create_material_expression(
        mat_earth, unreal.MaterialExpressionMultiply, -100, 750
    )
    mat_edit.connect_material_expressions(fresnel, "", mult1, "a")
    mat_edit.connect_material_expressions(emissive_glow, "", mult1, "b")
    
    # --- Multiply: Ocean * (Fresnel * EmissiveGlow) ---
    mult2 = mat_edit.create_material_expression(
        mat_earth, unreal.MaterialExpressionMultiply, 100, 750
    )
    mat_edit.connect_material_expressions(ocean, "", mult2, "a")
    mat_edit.connect_material_expressions(mult1, "", mult2, "b")
    
    # --- Connect to Emissive Color ---
    mat_edit.connect_material_property(mult2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    
    # Save material
    unreal.EditorAssetLibrary.save_asset("/Game/Celestial/Materials/MAT_Earth")
    print("[Earth] MAT_Earth created with full node graph")
    
    # Step 4: Place Earth in level
    print("[Earth] Placing Earth in level...")
    
    earth_mesh = unreal.load_asset("/Game/Celestial/SM_Earth")
    if not earth_mesh:
        print("[Earth] ERROR: Could not load SM_Earth")
        return
    
    earth_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
        earth_mesh,
        unreal.Vector(50000.0, 0.0, 30000.0),
        unreal.Rotator(0.0, 0.0, 0.0)
    )
    
    if earth_actor:
        earth_actor.set_actor_label("SM_Earth")
        earth_actor.set_actor_scale3d(unreal.Vector(3.0, 3.0, 3.0))
        
        # Apply material
        earth_mat = unreal.load_asset("/Game/Celestial/Materials/MAT_Earth")
        if earth_mat:
            mesh_comp = earth_actor.get_component_by_class(unreal.StaticMeshComponent)
            if mesh_comp:
                mesh_comp.set_material(0, earth_mat)
                print("[Earth] MAT_Earth applied to SM_Earth")
        
        print(f"[Earth] Earth placed at (50000, 0, 30000) scale 3.0x")
    else:
        print("[Earth] ERROR: Could not spawn Earth actor")
    
    print("\n[Earth] === COMPLETE ===")
    print("SM_Earth: /Game/Celestial/SM_Earth")
    print("MAT_Earth: /Game/Celestial/Materials/MAT_Earth")


if __name__ == "__main__":
    create_earth()
