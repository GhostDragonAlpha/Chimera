"""Fix the MAT_Player_Suit_Visor material by modifying default constants."""
import unreal

mat = unreal.load_asset("/Game/Chimera/Materials/MAT_Player_Suit_Visor.MAT_Player_Suit_Visor")
if not mat:
    print("FATAL: Could not load material")
    exit(1)

exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
print(f"Found {len(exprs)} expressions")

# First, enumerate all expressions
for i, e in enumerate(exprs):
    cls = e.get_class().get_name()
    try:
        pname = str(e.get_editor_property("parameter_name"))
        print(f"[{i}] PARAM: '{pname}' ({cls})")
    except Exception as ex:
        if cls == "MaterialExpressionConstant3Vector":
            c = e.get_editor_property("constant")
            print(f"[{i}] CONST3VEC: R={c.r:.4f} G={c.g:.4f} B={c.b:.4f} A={c.a:.4f} ({cls})")
        elif cls == "MaterialExpressionConstant":
            r = e.get_editor_property("r")
            print(f"[{i}] CONST: R={r:.4f} ({cls})")
        else:
            print(f"[{i}] OTHER: {cls} - {ex}")

print("\n=== Modifying defaults ===")

# Modify Constant3Vector to gold
for e in exprs:
    cls = e.get_class().get_name()
    if cls == "MaterialExpressionConstant3Vector":
        e.set_editor_property("constant", unreal.LinearColor(1.0, 0.85, 0.4, 1.0))
        c = e.get_editor_property("constant")
        print(f"  Constant3Vector -> gold: R={c.r} G={c.g} B={c.b}")

# Modify Constants: set Metallic=1.0, Roughness=0.1
const_idx = 0
for e in exprs:
    cls = e.get_class().get_name()
    if cls == "MaterialExpressionConstant":
        if const_idx == 0:
            old = e.get_editor_property("r")
            e.set_editor_property("r", 1.0)
            print(f"  Constant[{const_idx}] Metallic: {old} -> 1.0")
        elif const_idx == 1:
            old = e.get_editor_property("r")
            e.set_editor_property("r", 0.1)
            print(f"  Constant[{const_idx}] Roughness: {old} -> 0.1")
        const_idx += 1

# Rebuild
print("\nRebuilding material...")
unreal.MaterialEditingLibrary.rebuild_material_instance_editor_only(mat)
print("Rebuild done!")

# Save
unreal.EditorAssetLibrary.save_loaded_asset(mat)
print("Material saved!")

print("\n=== FIX COMPLETE ===")
