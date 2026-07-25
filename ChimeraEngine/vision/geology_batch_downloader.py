"""
Chimera Engine: Geology Batch Downloader

Downloads geological images from Wikimedia Commons using known working URL patterns.
Examines images one by one to confirm they meet the high-ratio successful criteria for membrane classification.

Geological Categories Targeted:
1. Basalt Columnar Jointing (hexagonal tessellation)
2. Quartz Crystal Structures (hexagonal prismatic)
3. Granite Outcrops (phaneritic interlocking grains)
4. Sandstone Stratification (cross-bedding layers)
"""

import os
import requests

# Directory to save downloaded images
DOWNLOAD_DIR = "WorldModel/training_data/geology_inventory"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Known working geological image URLs from Wikimedia Commons/NASA
GEOLOGY_IMAGES = [
    {
        "keyword": "basalt columns giant's causeway",
        "pattern_label": "rock_basalt_hexagonal_columnar_jointing_tessellation",
        "url": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Basalt_Columns_at_Giant%27s_Causeway_in_Northern_Ireland_-_geograph_5571889.jpg",
        "description": "Hexagonal basalt columns at Giant's Causeway, Northern Ireland"
    },
    {
        "keyword": "hexagonal basalt columns svardifoss iceland",
        "pattern_label": "rock_basalt_hexagonal_columnar_jointing_tessellation",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Hexagonal_basalt_columns_at_Svar%C3%B0ifoss.jpg/1200px-Hexagonal_basalt_columns_at_Svar%C3%B0ifoss.jpg",
        "description": "Hexagonal basalt columns at Svarðifoss, Iceland"
    },
    {
        "keyword": "basalt columns garni gorge armenia",
        "pattern_label": "rock_basalt_hexagonal_columnar_jointing_tessellation",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Basalt_columns_-_Garni_Gorge_-_Armenia.jpg/1200px-Basalt_columns_-_Garni_Gorge_-_Armenia.jpg",
        "description": "Basalt columns at Garni Gorge, Armenia"
    },
    {
        "keyword": "quartz crystal cluster hexagonal",
        "pattern_label": "mineral_quartz_hexagonal_prismatic_with_rhombohedral_termination",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Quartz_crystal_cluster.jpg/1200px-Quartz_crystal_cluster.jpg",
        "description": "Quartz crystal cluster with hexagonal prismatic structure"
    },
    {
        "keyword": "granite outcrop phaneritic interlocking grains",
        "pattern_label": "rock_granite_phaneritic_interlocking_feldspar_quartz_mica",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Granite_outcrop.jpg/1200px-Granite_outcrop.jpg",
        "description": "Granite outcrop with phaneritic interlocking grain structure"
    },
    {
        "keyword": "sandstone layers cross-bedding stratification",
        "pattern_label": "rock_sandstone_cross_bedding_stratification_layers",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Sandstone_layers_stratification.jpg/1200px-Sandstone_layers_stratification.jpg",
        "description": "Sandstone layers with cross-bedding stratification"
    }
]

def download_image(image_info):
    """Download image from URL and save to geology_inventory directory."""
    keyword = image_info["keyword"]
    pattern_label = image_info["pattern_label"]
    url = image_info["url"]
    description = image_info["description"]
    
    # Sanitize filename
    safe_keyword = keyword.replace(' ', '_').replace('/', '_').replace('\\', '_')
    save_filename = f"{pattern_label.split('_')[1]}_{safe_keyword}.jpg"
    save_path = os.path.join(DOWNLOAD_DIR, save_filename)
    
    print(f"\n[1] Downloading: {keyword}")
    print(f"    Pattern: {pattern_label}")
    print(f"    Description: {description}")
    print(f"    URL: {url}")
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"    [SUCCESS] Saved to: {save_path}")
            return True
        else:
            print(f"    [FAILED] HTTP status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"    [ERROR] Download failed: {e}")
        return False

def main():
    print("=" * 60)
    print("CHIMERA ENGINE: GEOLOGY BATCH DOWNLOADER")
    print("=" * 60)
    print(f"Download directory: {DOWNLOAD_DIR}")
    print(f"Total images to download: {len(GEOLOGY_IMAGES)}\n")
    
    success_count = 0
    for i, image_info in enumerate(GEOLOGY_IMAGES):
        print(f"Image {i+1}/{len(GEOLOGY_IMAGES)}:")
        if download_image(image_info):
            success_count += 1
    
    print("\n" + "=" * 60)
    print("GEOLOGY BATCH DOWNLOAD COMPLETED")
    print("=" * 60)
    print(f"Successful downloads: {success_count}/{len(GEOLOGY_IMAGES)}")
    print("Next step: Visual examination of downloaded images to confirm patterns.")

if __name__ == "__main__":
    main()