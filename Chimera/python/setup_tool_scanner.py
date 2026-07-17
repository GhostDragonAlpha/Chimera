# Setup script for Tool Scanner Model
# Spawns a StaticMeshActor 'ATool_Scanner' carrying /Game/Tools/Geometry/SM_ScannerBody with MAT_ScannerBody

import unreal

def setup_tool_scanner():
    # Get the editor level library
    editor_level_lib = unreal.EditorLevelLibrary()
    
    # Create a StaticMeshActor for the scanner body
    static_mesh_actor_class = unreal.StaticMeshActor
    
    # Spawn the actor at the default location
    spawn_location = unreal.Vector(0.0, 400.0, 130.0)
    spawn_rotator = unreal.Rotator(0, 0, 0)
    
    scanner_actor = editor_level_lib.spawn_actor_from_class(
        static_mesh_actor_class,
        spawn_location,
        spawn_rotator
    )
    
    if scanner_actor:
        # Set the actor name to ATool_Scanner
        scanner_actor.set_actor_label("ATool_Scanner")
        
        # Get the body mesh component
        body_mesh_component = None
        for comp in scanner_actor.get_components():
            if isinstance(comp, unreal.StaticMeshComponent):
                body_mesh_component = comp
                break
        
        if body_mesh_component:
            # Set the static mesh to SM_ScannerBody
            mesh_finder = unreal.EditorAssetLibrary().load_asset("/Game/Tools/Geometry/SM_ScannerBody")
            if mesh_finder:
                body_mesh_component.set_static_mesh(mesh_finder)
            
            # Set the material to MAT_ScannerBody
            mat_finder = unreal.EditorAssetLibrary().load_asset("/Game/Tools/Materials/MAT_ScannerBody")
            if mat_finder:
                body_mesh_component.set_material(0, mat_finder)
        
        print(f"Created ATool_Scanner at {spawn_location}")
        
        # Save the level
        unreal.EditorLevelLibrary().save_all_current_packages()
        print("Level saved with ATool_Scanner")

if __name__ == "__main__":
    setup_tool_scanner()
