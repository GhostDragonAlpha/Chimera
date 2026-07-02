print("PCG SCRIPT STARTED")
import unreal

print("Getting asset tools...")
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
print("Got asset tools")
editor_asset_lib = unreal.EditorAssetLibrary
print("Got editor asset lib")

pcg_content_path = "/Game/ProceduralGenerated/PCG"
print(f"PCG content path: {pcg_content_path}")

print(f"Checking if directory exists: {pcg_content_path}")
if not unreal.EditorAssetLibrary.does_directory_exist(pcg_content_path):
    print(f"Making directory: {pcg_content_path}")
    unreal.EditorAssetLibrary.make_directory(pcg_content_path)
    print(f"Made directory: {pcg_content_path}")

created_count = 0

print("Looking for factory classes...")
for factory_class_name in ["PCGGraphFactory", "BlueprintFactory", "Factory"]:
    factory_class = getattr(unreal, factory_class_name, None)
    if factory_class is not None:
        print(f"Found factory: {factory_class_name}")
        break

if hasattr(unreal, "PCGGraphFactory"):
    print("PCGGraphFactory available, creating factory...")
    factory = unreal.PCGGraphFactory()
    
    # Create clutter graph asset
    print("Creating clutter graph asset...")
    pcg_graph_asset_clutter = asset_tools.create_asset(
        asset_name="UPCG_Graph_Environment_Clutter_Graph",
        package_path=pcg_content_path,
        asset_class=unreal.PCGGraph,
        factory=factory
    )
    print(f"Clutter graph asset result: {pcg_graph_asset_clutter}")
    if pcg_graph_asset_clutter:
        save_path = pcg_graph_asset_clutter.get_path_name()
        print(f"Saving clutter graph asset to: {save_path}")
        unreal.EditorAssetLibrary.save_asset(save_path, only_if_is_dirty=False)
        print(f"Created PCGGraph: {save_path}")
        created_count += 1
    
    # Create planet surface graph asset
    print("Creating planet surface graph asset...")
    pcg_graph_asset_planet = asset_tools.create_asset(
        asset_name="UPCG_Graph_Planet_Surface_Generation",
        package_path=pcg_content_path,
        asset_class=unreal.PCGGraph,
        factory=factory
    )
    print(f"Planet surface graph asset result: {pcg_graph_asset_planet}")
    if pcg_graph_asset_planet:
        save_path = pcg_graph_asset_planet.get_path_name()
        print(f"Saving planet surface graph asset to: {save_path}")
        unreal.EditorAssetLibrary.save_asset(save_path, only_if_is_dirty=False)
        print(f"Created PCGGraph: {save_path}")
        created_count += 1
        
else:
    print("PCGGraphFactory not available, trying alternative approach")
    package_path_clutter = f"{pcg_content_path}/UPCG_Graph_Environment_Clutter_Graph"
    print(f"Creating clutter package at: {package_path_clutter}")
    package_clutter = unreal.PackageTools.create_package(package_path_clutter)
    if package_clutter:
        pcg_graph_clutter = unreal.new_object(unreal.PCGGraph, package_clutter)
        if pcg_graph_clutter:
            save_path = pcg_graph_clutter.get_path_name()
            print(f"Saving clutter graph via new_object to: {save_path}")
            unreal.EditorAssetLibrary.save_asset(save_path, only_if_is_dirty=False)
            print(f"Created PCGGraph via new_object: {save_path}")
            created_count += 1
    
    package_path_planet = f"{pcg_content_path}/UPCG_Graph_Planet_Surface_Generation"
    print(f"Creating planet surface package at: {package_path_planet}")
    package_planet = unreal.PackageTools.create_package(package_path_planet)
    if package_planet:
        pcg_graph_planet = unreal.new_object(unreal.PCGGraph, package_planet)
        if pcg_graph_planet:
            save_path = pcg_graph_planet.get_path_name()
            print(f"Saving planet surface graph via new_object to: {save_path}")
            unreal.EditorAssetLibrary.save_asset(save_path, only_if_is_dirty=False)
            print(f"Created PCGGraph via new_object: {save_path}")
            created_count += 1

if hasattr(unreal, "PCGDataAsset"):
    try:
        print("Creating PCGDataAsset...")
        pcg_data_asset = asset_tools.create_asset(
            asset_name="UPCG_Data_Environment_Clutter",
            package_path=pcg_content_path,
            asset_class=unreal.PCGDataAsset,
            factory=None
        )
        if pcg_data_asset:
            save_path = pcg_data_asset.get_path_name()
            print(f"Saving PCGDataAsset to: {save_path}")
            unreal.EditorAssetLibrary.save_asset(save_path, only_if_is_dirty=False)
            print(f"Created PCGDataAsset: {save_path}")
            created_count += 1
    except Exception as e:
        print(f"Could not create PCGDataAsset: {e}")

if hasattr(unreal, "PCGSettings"):
    try:
        print("Creating PCGSettings...")
        pcg_settings_asset = asset_tools.create_asset(
            asset_name="UPCG_Settings_Default",
            package_path=pcg_content_path,
            asset_class=unreal.PCGSettings,
            factory=None
        )
        if pcg_settings_asset:
            save_path = pcg_settings_asset.get_path_name()
            print(f"Saving PCGSettings to: {save_path}")
            unreal.EditorAssetLibrary.save_asset(save_path, only_if_is_dirty=False)
            print(f"Created PCGSettings: {save_path}")
            created_count += 1
    except Exception as e:
        print(f"Could not create PCGSettings: {e}")

print("Listing assets...")
found_assets = unreal.EditorAssetLibrary.list_assets(pcg_content_path, recursive=True)
for asset_path in found_assets:
    print(f"Found asset: {asset_path}")

print(f"PCG asset creation complete. {created_count} assets created, {len(found_assets)} total in {pcg_content_path}")
print("PCG SCRIPT FINISHED")
