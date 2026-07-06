"""Fix visor material: Opaque PBR gold with proper connections."""
import unreal

mat = unreal.EditorAssetLibrary.load_asset("/Game/Chimera/Materials/MAT_Player_Character_Suit_Visor/MAT_Player_Character_Suit_Visor")

# Remove old expressions
for e in unreal.MaterialEditingLibrary.get_material_expressions(mat):
    unreal.MaterialEditingLibrary.delete_material_expression(mat, e)
print("Cleared old expressions")

# BaseColor = Gold reflectance RGB(0.82, 0.70, 0.35) per PBR metal workflow
bc = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
bc.set_editor_property("constant", unreal.LinearColor(0.82, 0.70, 0.35, 1.0))
unreal.MaterialEditingLibrary.connect_material_property(bc, "", unreal.MaterialProperty.MP_BASE_COLOR)
print("BaseColor gold connected")

# Metallic = 1.0
met = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 200)
met.set_editor_property("r", 1.0)
unreal.MaterialEditingLibrary.connect_material_property(met, "", unreal.MaterialProperty.MP_METALLIC)
print("Metallic connected")

# Roughness = 0.1
rough = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 400)
rough.set_editor_property("r", 0.1)
unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
print("Roughness connected")

# Save
unreal.EditorAssetLibrary.save_loaded_asset(mat)
print("Saved!")