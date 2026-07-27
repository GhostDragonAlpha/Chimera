"""Connect visor material parameters to output pins using MaterialEditingLibrary."""
import unreal

mat = unreal.EditorAssetLibrary.load_asset("/Game/Chimera/Materials/MAT_Player_Character_Suit_Visor/MAT_Player_Character_Suit_Visor")
if not mat:
    print("FATAL: Could not load material")
    exit(1)

# Set blend mode to Translucent
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_Translucent)
mat.set_editor_property("two_sided", True)

exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
print(f"Found {len(exprs)} expressions")

# Find parameter nodes
base_color_node = None
roughness_node = None
metallic_node = None
opacity_node = None

for e in exprs:
    cls = e.get_class().get_name()
    if cls == "MaterialExpressionVectorParameter":
        base_color_node = e
        e.set_editor_property("default_value", unreal.LinearColor(1.0, 0.85, 0.45, 1.0))
        print(f"  BaseColor: set to gold (1.0, 0.85, 0.45)")
    elif cls == "MaterialExpressionScalarParameter":
        pname = e.get_parameter_name()
        if pname == "Roughness":
            roughness_node = e
            e.set_editor_property("default_value", 0.1)
            print(f"  Roughness: set to 0.1")
        elif pname == "Metallic":
            metallic_node = e
            e.set_editor_property("default_value", 1.0)
            print(f"  Metallic: set to 1.0")
        elif pname == "Opacity":
            opacity_node = e
            e.set_editor_property("default_value", 0.7)
            print(f"  Opacity: set to 0.7")

# Connect nodes to material output
if base_color_node:
    unreal.MaterialEditingLibrary.connect_material_property(base_color_node, "RGBA", unreal.MaterialProperty.MP_BaseColor)
    print("  Connected BaseColor -> MP_BaseColor")

if metallic_node:
    unreal.MaterialEditingLibrary.connect_material_property(metallic_node, "", unreal.MaterialProperty.MP_Metallic)
    print("  Connected Metallic -> MP_Metallic")

if roughness_node:
    unreal.MaterialEditingLibrary.connect_material_property(roughness_node, "", unreal.MaterialProperty.MP_Roughness)
    print("  Connected Roughness -> MP_Roughness")

if opacity_node:
    unreal.MaterialEditingLibrary.connect_material_property(opacity_node, "", unreal.MaterialProperty.MP_Opacity)
    print("  Connected Opacity -> MP_Opacity")

# Rebuild
unreal.MaterialEditingLibrary.rebuild_material_instance_editor_only(mat)
print("Material rebuild done!")

# Save
unreal.EditorAssetLibrary.save_loaded_asset(mat)
print("Material saved!")