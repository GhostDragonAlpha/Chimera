"""
Complete visor material fix: Delete old material, create fresh one with proper connections.
Execute via MCP execute_python.
"""
import unreal

# STEP 1: Delete old material and instance
old_paths = [
    "/Game/Chimera/Materials/MAT_Player_Suit_Visor.MAT_Player_Suit_Visor",
    "/Game/Chimera/Materials/MI_Player_Suit_Visor.MI_Player_Suit_Visor"
]
for p in old_paths:
    if unreal.EditorAssetLibrary.does_asset_exist(p):
        unreal.EditorAssetLibrary.delete_asset(p)
        print(f"Deleted: {p}")

# STEP 2: Create new material
mat_pkg = "/Game/Chimera/Materials/MAT_Player_Suit_Visor"
unreal.EditorAssetLibrary.make_directory("/Game/Chimera/Materials")
mat_factory = unreal.MaterialFactoryNew()
mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset("MAT_Player_Suit_Visor", "/Game/Chimera/Materials", None, mat_factory)
if not mat:
    print("FATAL: Could not create material")
    exit(1)
print(f"Created material: {mat.get_name()}")

# STEP 3: Set blend mode to Translucent
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
mat.set_editor_property("two_sided", True)
print("Set Translucent, TwoSided")

# STEP 4: Create constant nodes and connect them
# BaseColor = Gold (1.0, 0.85, 0.4)
bc_node = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
bc_node.set_editor_property("constant", unreal.LinearColor(1.0, 0.85, 0.4, 1.0))
unreal.MaterialEditingLibrary.connect_material_property(bc_node, "", unreal.MaterialProperty.MP_BASE_COLOR)
print("Connected BaseColor = gold")

# Metallic = 1.0
met_node = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 200)
met_node.set_editor_property("r", 1.0)
unreal.MaterialEditingLibrary.connect_material_property(met_node, "", unreal.MaterialProperty.MP_METALLIC)
print("Connected Metallic = 1.0")

# Roughness = 0.1
rough_node = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 400)
rough_node.set_editor_property("r", 0.1)
unreal.MaterialEditingLibrary.connect_material_property(rough_node, "", unreal.MaterialProperty.MP_ROUGHNESS)
print("Connected Roughness = 0.1")

# Opacity = 0.7
op_node = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 600)
op_node.set_editor_property("r", 0.7)
unreal.MaterialEditingLibrary.connect_material_property(op_node, "", unreal.MaterialProperty.MP_OPACITY)
print("Connected Opacity = 0.7")

# STEP 5: Save
unreal.EditorAssetLibrary.save_loaded_asset(mat)
print(f"Material saved")

# STEP 6: Create material instance
mi_factory = unreal.MaterialInstanceConstantFactoryNew()
mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset("MI_Player_Suit_Visor", "/Game/Chimera/Materials", None, mi_factory)
mi.set_editor_property("parent", mat)
unreal.EditorAssetLibrary.save_loaded_asset(mi)
print(f"Material instance created and saved")

print("\n=== FIX COMPLETE ===")
print("MAT_Player_Suit_Visor: Translucent, Gold BaseColor, Metallic 1.0, Roughness 0.1, Opacity 0.7")
