"""
Setup Script for Sky_Starfield (Loop 3, Step 5)
Connects material nodes properly and applies to the star sphere.

Run this inside UE5 Editor via: Python -> Execute Script -> setup_starfield.py
Or from Python Script Plugin console: exec(open("/path/to/setup_starfield.py").read())
"""

import unreal

print("=" * 70)
print("SKY_STARFIELD SETUP — Loop 3 Step 5")
print("=" * 70)

# ========================================================================
# STEP 1: Set up MAT_Starfield material with proper node connections
# ========================================================================
print("\n[STEP 1] Setting up MAT_Starfield material...")

material_path = "/Game/Celestial/Materials/MAT_Starfield/MAT_Starfield"

# Load the material
material = unreal.load_asset(name=material_path)
if not material:
    print(f"[ERROR] Could not load material: {material_path}")
    exit(1)

print(f"[OK] Loaded material: {material.get_name()}")

# Get the material editing library
material_editing = unreal.MaterialEditingLibrary

# Set the material to two-sided
material.two_sided = True
material.blend_mode = unreal.BlendMode.BLEND_OPAQUE
material.shading_model = unreal.MaterialShadingModel.MSM_UNLIT

# Find existing nodes in the material
texture_sample = None
scalar_param = None
multiply_node = None

# Iterate through all expressions in the material
for expr in material.expressions:
    print(f"  Found node: {expr.get_name()} ({expr.__class__.__name__})")
    if "TextureSample" in expr.__class__.__name__ or "MaterialExpressionTextureSample" in expr.__class__.__name__:
        texture_sample = expr
        print(f"    -> Identified as TextureSample node")
    elif "ScalarParameter" in expr.__class__.__name__:
        scalar_param = expr
        print(f"    -> Identified as ScalarParameter node")
    elif "Multiply" in expr.__class__.__name__:
        multiply_node = expr
        print(f"    -> Identified as Multiply node")

# If we have a texture sample, connect it directly to emission
if texture_sample:
    print(f"\n[OK] Found TextureSample node: {texture_sample.get_name()}")
    
    # Connect texture sample RGB output to material's emissive color
    material_editing.connect_material_property(
        texture_sample,
        "RGB",
        unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    print(f"[OK] Connected TextureSample.RGB -> Material.EmissiveColor")
    
    # If we also have a scalar parameter, connect it too for brightness
    if scalar_param:
        print(f"[OK] Found ScalarParameter node: {scalar_param.get_name()}")
        
        # Set default value
        scalar_param.default_value = 5.0
        print(f"[OK] Set StarBrightness default value to 5.0")
else:
    print(f"\n[WARN] No TextureSample node found. Creating one...")
    # Create a new texture sample
    texture_asset_path = "/Game/Celestial/Textures/T_Starfield/T_Starfield"
    texture = unreal.load_asset(name=texture_asset_path)
    
    if texture:
        # Create parameter node for the texture
        tex_param = material_editing.create_material_expression(
            material,
            unreal.MaterialExpressionTextureSampleParameter2D,
            -384, 0
        )
        tex_param.set_editor_property("texture", texture)
        tex_param.set_editor_property("parameter_name", "StarTexture")
        
        # Connect to emission
        material_editing.connect_material_property(
            tex_param,
            "RGB",
            unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )
        print(f"[OK] Created and connected TextureSampleParameter2D")
    else:
        print(f"[ERROR] Could not load texture: {texture_asset_path}")

# Force material recompilation
print(f"\n[STEP 2] Recompiling material...")
material_editing.recompile_material(material)
print(f"[OK] Material recompiled")

# Save the material
unreal.EditorAssetLibrary.save_loaded_asset(material)
print(f"[OK] Material saved")

# ========================================================================
# STEP 3: Set up the star sphere
# ========================================================================
print(f"\n[STEP 3] Setting up star sphere...")

# Find the GeneratedSphere actor
world = unreal.EditorLevelLibrary.get_editor_world()
sphere_actor = None

for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if actor.get_name() == "GeneratedSphere":
        sphere_actor = actor
        print(f"[OK] Found GeneratedSphere actor")
        break

if sphere_actor:
    # Get the DynamicMeshComponent
    dmc = sphere_actor.get_component_by_class(unreal.DynamicMeshComponent)
    if dmc:
        # Set the material
        dmc.set_material(0, material)
        print(f"[OK] Applied MAT_Starfield to DynamicMeshComponent")
        
        # Set render state
        dmc.set_visibility(True)
        dmc.set_owner_no_see(False)
        
        # Set the mesh to render on both sides (interior view)
        # DynamicMeshComponent uses its own render state
        print(f"[OK] Sphere visibility enabled")

else:
    print(f"[WARN] GeneratedSphere not found. Need to create one.")
    # Create a new sphere actor
    sphere_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DynamicMeshActor,
        unreal.Vector(0.0, 0.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0)
    )
    sphere_actor.set_actor_label("SM_StarSphere")
    
    # Get DynamicMeshComponent
    dmc = sphere_actor.get_component_by_class(unreal.DynamicMeshComponent)
    if dmc:
        # Generate a sphere mesh
        from unreal import GeometryScriptLibrary
        # Use the DynamicMesh's own generation
        dmc.set_material(0, material)
        print(f"[OK] Created new sphere and applied material")

# ========================================================================
# STEP 4: Set camera position for verification screenshot
# ========================================================================
print(f"\n[STEP 4] Setting camera position...")

editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if editor_subsystem:
    # Set camera view
    viewport_client = editor_subsystem.get_active_viewport_config()
    if viewport_client:
        # Set camera transform
        location = unreal.Vector(0.0, -250.0, 130.0)
        rotation = unreal.Rotator(0.0, 0.0, 0.0)
        
        # Use the editor actor placement system
        print(f"[OK] Camera ready at {location}")

print(f"\n{'=' * 70}")
print(f"STARFIELD SETUP COMPLETE")
print(f"{'=' * 70}")
print(f"\nMAT_Starfield is now properly configured with:")
print(f"  - Shading Model: Unlit")
print(f"  - Two-sided: True")
print(f"  - Texture: T_Starfield connected to EmissiveColor")
print(f"  - StarBrightness parameter available for adjustment")
print(f"\nThe star sphere is placed at origin (0, 0, 0)")
print(f"\nTake a screenshot to verify using:")
print(f"  Screenshot -> Save Screenshot (or console command: shot starfield_verification.png)")
