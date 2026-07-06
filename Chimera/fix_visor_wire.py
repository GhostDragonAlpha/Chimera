"""Create properly wired visor material with constant nodes connected to output."""
import unreal

# Load existing material
mat = unreal.EditorAssetLibrary.load_asset("/Game/Chimera/Materials/MAT_Player_Character_Suit_Visor/MAT_Player_Character_Suit_Visor")
if not mat:
    print("FATAL: Could not load material")
    exit(1)

# Set blend mode and two-sided
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
mat.set_editor_property("two_sided", True)
print("Set Translucent, TwoSided")

# Delete orphaned parameter nodes by removing all expressions
exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
for e in exprs:
    unreal.MaterialEditingLibrary.delete_material_expression(mat, e)
print(f"Deleted {len(exprs)} old expressions")

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

# Rebuild and save
unreal.MaterialEditingLibrary.rebuild_material_instance_editor_only(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
print("Material saved!")

# Also update the instance to use the wired material
inst = unreal.EditorAssetLibrary.load_asset("/Game/Chimera/Materials/MAT_Player_Character_Suit_Visor/MI_Player_Character_Suit_Visor")
if inst:
    inst.set_editor_property("parent", mat)
    unreal.EditorAssetLibrary.save_loaded_asset(inst)
    print("Instance updated")