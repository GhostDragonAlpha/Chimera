"""
Earth Celestial Body Automation — Loop 3, Step 2

Creates SM_Earth static mesh (Nanite-enabled sphere) and MAT_Earth PBR material,
then places the Earth sphere in the current level at a sky position.

Emotional anchor: "Awe" + "Lonely" — Earth as a distant, beautiful, unreachable blue marble.
Reference: Apollo 8 "Earthrise" photo.

Usage (from UE Editor Python Console):
    import create_earth_celestial_automation
    create_earth_celestial_automation.create_earth_celestial_body()
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CHIMERA_CONTENT_DIR


def create_earth_celestial_body():
    """Create SM_Earth static mesh, MAT_Earth material, and place in level.

    Returns:
        dict: Paths to created assets (mesh, material), or None if UE Editor not available.
    """
    try:
        import unreal

        content_dir = str(CHIMERA_CONTENT_DIR)

        # ============================================================================
        # Step 1: Ensure Celestial directory exists
        # ============================================================================
        celestial_dir = "/Game/Celestial"
        materials_dir = "/Game/Celestial/Materials"

        if not unreal.EditorAssetLibrary.does_directory_exist(celestial_dir):
            unreal.EditorAssetLibrary.make_directory(celestial_dir)
            print(f"[Earth] Created directory: {celestial_dir}")

        if not unreal.EditorAssetLibrary.does_directory_exist(materials_dir):
            unreal.EditorAssetLibrary.make_directory(materials_dir)
            print(f"[Earth] Created directory: {materials_dir}")

        # ============================================================================
        # Step 2: Create SM_Earth static mesh using SphereFactory
        # ============================================================================
        print("[Earth] Creating SM_Earth Nanite-enabled sphere...")

        sphere_factory = unreal.SphereFactory()
        sphere_factory.set_editor_property("radius", 500)
        sphere_factory.set_editor_property("sphere_groups", 64)

        sm_earth_path = "/Game/Celestial/SM_Earth"

        # Use AssetTools to create the asset properly
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        sm_earth = asset_tools.create_asset(
            "SM_Earth",
            "/Game/Celestial",
            None,
            unreal.StaticMesh,
            sphere_factory
        )

        if sm_earth:
            print(f"[Earth] SM_Earth created at: {sm_earth_path}")

            # Enable Nanite rendering
            mesh_editor_subsystem = unreal.StaticMeshEditorSubsystem()
            success = mesh_editor_subsystem.set_nanite_settings(
                sm_earth,
                True,  # enabled
                0.5    # fallback triangle percentage
            )
            if success:
                print("[Earth] Nanite enabled on SM_Earth")
            else:
                print("[Earth] Warning: Could not enable Nanite (may not be supported on this mesh)")

            # Build the mesh
            mesh_editor_subsystem.build_simple_collision(sm_earth)

        # Save the mesh asset
        unreal.EditorAssetLibrary.save_asset(sm_earth_path)
        print(f"[Earth] SM_Earth saved.")

        # ============================================================================
        # Step 3: Create MAT_Earth material
        # ============================================================================
        print("[Earth] Creating MAT_Earth PBR material...")

        mat_earth_path = "/Game/Celestial/Materials/MAT_Earth"

        # Create material asset
        material_factory = unreal.MaterialFactoryNew()
        mat_earth = asset_tools.create_asset(
            "MAT_Earth",
            "/Game/Celestial/Materials",
            None,
            unreal.Material,
            material_factory
        )

        if mat_earth:
            print(f"[Earth] MAT_Earth created at: {mat_earth_path}")

            # ========================================================================
            # Step 3a: Configure material properties
            # ========================================================================
            # Set blend mode to Opaque
            mat_earth.set_editor_property("blend_mode", unreal.BlendMode.BLEND_Opaque)

            # Create material editing session
            material_edit = unreal.MaterialEditingLibrary

            # Clear default expressions
            material_edit.delete_all_material_expressions(mat_earth)

            # ========================================================================
            # Step 3b: Create material expression nodes
            # ========================================================================

            # --- Texture Coordinate node (for UV mapping) ---
            tex_coord = material_edit.create_material_expression(
                mat_earth, unreal.MaterialExpressionTextureCoordinate, -400, 0
            )
            tex_coord.set_editor_property("coordinate_index", 0)
            tex_coord.set_editor_property("utiling", 1.0)
            tex_coord.set_editor_property("vtiling", 1.0)

            # --- Base Color: Procedural earth colors ---
            # Use a combination of Constant3Vector nodes to simulate ocean and continents.
            # Ocean: deep blue ~(0.02, 0.10, 0.35)
            # Land: brown/green ~(0.25, 0.32, 0.15)
            # We'll use a MaterialFunction or simpler approach with parameters.

            # Create Scalar Parameters for tunable values
            ocean_blue_param = material_edit.create_material_expression(
                mat_earth, unreal.MaterialExpressionVectorParameter, -400, -200
            )
            ocean_blue_param.set_editor_property("parameter_name", "OceanColor")
            ocean_blue_param.set_editor_property("default_value", unreal.LinearColor(0.05, 0.15, 0.4, 1.0))

            land_color_param = material_edit.create_material_expression(
                mat_earth, unreal.MaterialExpressionVectorParameter, -400, 100
            )
            land_color_param.set_editor_property("parameter_name", "LandColor")
            land_color_param.set_editor_property("default_value", unreal.LinearColor(0.25, 0.32, 0.15, 1.0))

            # Roughness parameter
            roughness_param = material_edit.create_material_expression(
                mat_earth, unreal.MaterialExpressionScalarParameter, -400, 300
            )
            roughness_param.set_editor_property("parameter_name", "Roughness")
            roughness_param.set_editor_property("default_value", 0.3)

            # Metallic parameter
            metallic_param = material_edit.create_material_expression(
                mat_earth, unreal.MaterialExpressionScalarParameter, -400, 400
            )
            metallic_param.set_editor_property("parameter_name", "Metallic")
            metallic_param.set_editor_property("default_value", 0.0)

            # Specular parameter (ocean glint)
            specular_param = material_edit.create_material_expression(
                mat_earth, unreal.MaterialExpressionScalarParameter, -400, 500
            )
            specular_param.set_editor_property("parameter_name", "Specular")
            specular_param.set_editor_property("default_value", 0.5)

            # Emissive glow parameter (atmospheric scattering)
            emissive_param = material_edit.create_material_expression(
                mat_earth, unreal.MaterialExpressionScalarParameter, -400, 600
            )
            emissive_param.set_editor_property("parameter_name", "EmissiveGlow")
            emissive_param.set_editor_property("default_value", 0.02)

            # --- Noise-based continent pattern ---
            # Create a Panner node for subtle cloud/continent movement
            panner = material_edit.create_material_expression(
                mat_earth, unreal.MaterialExpressionPanner, -200, 0
            )
            panner.set_editor_property("speed_x", 0.001)
            panner.set_editor_property("speed_y", 0.0)
            material_edit.connect_material_expressions(tex_coord, "", panner, "coordinates")

            # Create noise for continent patterns
            noise = material_edit.create_material_expression(
                mat_earth, unreal.MaterialExpressionNoise, 0, 0
            )
            noise.set_editor_property("scale", 3.0)
            noise.set_editor_property("quality", 3)  # High quality
            noise.set_editor_property("tiling", True)
            noise.set_editor_property("level_of_detail", 0.0)
            material_edit.connect_material_expressions(panner, "", noise, "position")

            # --- Lerp between ocean and land based on noise ---
            lerp = material_edit.create_material_expression(
                mat_earth, unreal.MaterialExpressionLinearInterpolate, 200, -50
            )
            material_edit.connect_material_expressions(ocean_blue_param, "", lerp, "a")
            material_edit.connect_material_expressions(land_color_param, "", lerp, "b")
            material_edit.connect_material_expressions(noise, "", lerp, "alpha")

            # --- Fresnel for atmospheric edge glow ---
            fresnel = material_edit.create_material_expression(
                mat_earth, unreal.MaterialExpressionFresnel, 200, 300
            )
            fresnel.set_editor_property("exponent", 3.0)

            # ========================================================================
            # Step 3c: Connect to material outputs
            # ========================================================================

            # Base Color -> Lerp result
            material_edit.connect_material_property(
                lerp, "",
                unreal.MaterialProperty.MP_BASE_COLOR
            )

            # Roughness -> Scalar parameter
            material_edit.connect_material_property(
                roughness_param, "",
                unreal.MaterialProperty.MP_ROUGHNESS
            )

            # Metallic -> Scalar parameter
            material_edit.connect_material_property(
                metallic_param, "",
                unreal.MaterialProperty.MP_METALLIC
            )

            # Specular -> Scalar parameter
            material_edit.connect_material_property(
                specular_param, "",
                unreal.MaterialProperty.MP_SPECULAR
            )

            # Emissive -> Emissive color (fresnel * emissive glow)
            multiply_emissive = material_edit.create_material_expression(
                mat_earth, unreal.MaterialExpressionMultiply, 200, 500
            )
            material_edit.connect_material_expressions(fresnel, "", multiply_emissive, "a")
            material_edit.connect_material_expressions(emissive_param, "", multiply_emissive, "b")

            emissive_color = material_edit.create_material_expression(
                mat_earth, unreal.MaterialExpressionMultiply, 400, 500
            )
            # Use the ocean blue with emissive
            material_edit.connect_material_expressions(ocean_blue_param, "", emissive_color, "a")
            material_edit.connect_material_expressions(multiply_emissive, "", emissive_color, "b")

            material_edit.connect_material_property(
                emissive_color, "",
                unreal.MaterialProperty.MP_EMISSIVE_COLOR
            )

            print("[Earth] Material expression graph built.")

        # Save the material asset
        unreal.EditorAssetLibrary.save_asset(mat_earth_path)
        print(f"[Earth] MAT_Earth saved.")

        # ============================================================================
        # Step 4: Place Earth sphere in the level
        # ============================================================================
        print("[Earth] Placing SM_Earth in current level...")

        # Get the current world
        world = unreal.EditorLevelLibrary.get_editor_world()
        if world:
            # Spawn a static mesh actor
            earth_actor_location = unreal.Vector(50000.0, 0.0, 30000.0)
            earth_actor_rotation = unreal.Rotator(0.0, 0.0, 0.0)

            # Load the SM_Earth static mesh
            earth_mesh = unreal.load_asset(sm_earth_path)
            if earth_mesh:
                # Spawn the actor
                earth_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
                    earth_mesh,
                    earth_actor_location,
                    earth_actor_rotation
                )

                if earth_actor:
                    earth_actor.set_actor_label("SM_Earth")
                    print(f"[Earth] Earth placed at: ({earth_actor_location.x}, {earth_actor_location.y}, {earth_actor_location.z})")

                    # Scale the sphere to appropriate sky size
                    earth_actor.set_actor_scale3d(unreal.Vector(3.0, 3.0, 3.0))

                    # Apply the material
                    earth_mat = unreal.load_asset(mat_earth_path)
                    if earth_mat:
                        # Get the static mesh component
                        mesh_component = earth_actor.get_component_by_class(unreal.StaticMeshComponent)
                        if mesh_component:
                            mesh_component.set_material(0, earth_mat)
                            print("[Earth] MAT_Earth applied to SM_Earth.")

                    print(f"[Earth] Earth sphere actor created with scale 3.0x")
                else:
                    print("[Earth] Warning: Could not spawn earth actor.")
            else:
                print("[Earth] Warning: Could not load SM_Earth mesh.")
        else:
            print("[Earth] Warning: Could not get editor world.")

        print(f"\n[Earth] ===== CREATION COMPLETE =====")
        print(f"[Earth]   SM_Earth: {sm_earth_path}")
        print(f"[Earth]   MAT_Earth: {mat_earth_path}")
        print(f"[Earth]   Position: (50000, 0, 30000)")
        print(f"[Earth]   Scale: 3.0x")

        return {
            "mesh": sm_earth_path,
            "material": mat_earth_path,
            "position": {"x": 50000, "y": 0, "z": 30000}
        }

    except ImportError as e:
        print(f"[WARN] unreal module not available — running in simulation mode: {e}")
        return _simulate_earth_celestial_body()
    except Exception as e:
        print(f"[ERROR] Failed to create Earth celestial body: {e}")
        import traceback
        traceback.print_exc()
        return None


def _simulate_earth_celestial_body():
    """Simulate Earth celestial body creation for standalone mode (no UE Editor)."""
    # Create Earth static mesh specification
    earth_spec = {
        "mesh_name": "SM_Earth",
        "type": "StaticMesh",
        "geometry": {
            "shape": "Sphere",
            "radius_world_units": 500,
            "sector_count": 64,
            "nanite_enabled": True,
            "lod_group": "WorldLevel"
        },
        "position": {
            "world_position": {"x": 50000, "y": 0, "z": 30000},
            "scale": 3.0
        },
        "rendering": {
            "nanite_enabled": True,
            "frustum_culling": True,
        }
    }

    # Earth material specification
    material_spec = {
        "material_name": "MAT_Earth",
        "type": "Material",
        "parameters": {
            "OceanColor": {"r": 0.05, "g": 0.15, "b": 0.4, "a": 1.0},
            "LandColor": {"r": 0.25, "g": 0.32, "b": 0.15, "a": 1.0},
            "Roughness": 0.3,
            "Metallic": 0.0,
            "Specular": 0.5,
            "EmissiveGlow": 0.02,
        },
        "blend_mode": "Opaque",
        "features": [
            "Noise-based continent pattern",
            "Fresnel edge glow",
            "Scalar/vector parameters for tuning"
        ]
    }

    # Save specifications to JSON files
    content_dir = str(CHIMERA_CONTENT_DIR)
    celestial_dir = os.path.join(content_dir, "Celestial")
    os.makedirs(celestial_dir, exist_ok=True)

    earth_spec_path = os.path.join(celestial_dir, "SM_Earth_Spec.json")
    mat_spec_path = os.path.join(celestial_dir, "MAT_Earth_Spec.json")

    import json
    with open(earth_spec_path, 'w') as f:
        json.dump(earth_spec, f, indent=4)
    with open(mat_spec_path, 'w') as f:
        json.dump(material_spec, f, indent=4)

    print(f"[Earth-SIM] Earth specification saved to: {earth_spec_path}")
    print(f"[Earth-SIM] Material specification saved to: {mat_spec_path}")

    return {"mesh": earth_spec_path, "material": mat_spec_path}


def run_earth_celestial_automation(simulate=False):
    """Run Earth celestial body creation automation.

    Args:
        simulate: If True, runs in simulation mode without UE Editor.
    """
    if simulate:
        print("=" * 60)
        print("EARTH CELESTIAL BODY AUTOMATION (Simulation Mode)")
        print("=" * 60)
        result = _simulate_earth_celestial_body()
        print(f"\n[Earth-SIM] Earth specification created at: {result['mesh']}")
        print(f"[Earth-SIM] Material specification created at: {result['material']}")
    else:
        print("=" * 60)
        print("EARTH CELESTIAL BODY AUTOMATION (UE Editor Mode)")
        print("=" * 60)
        result = create_earth_celestial_body()
        if result:
            print(f"\n[Earth] Assets created:")
            print(f"  - SM_Earth: {result['mesh']}")
            print(f"  - MAT_Earth: {result['material']}")
        else:
            print("\n[Earth] Failed to create Earth celestial body — check UE Editor logs.")


def run_from_editor():
    """Entry point for UE Editor Python console execution."""
    run_earth_celestial_automation(simulate=False)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Earth Celestial Body Automation")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation mode (no UE Editor)")
    args = parser.parse_args()
    run_earth_celestial_automation(simulate=args.simulate)
