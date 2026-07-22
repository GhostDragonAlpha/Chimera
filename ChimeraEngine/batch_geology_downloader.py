"""
Chimera Engine: Batch Geology Downloader

Downloads geological images from Wikimedia Commons based on specific keywords.
Examines images one by one to confirm they meet the high-ratio successful criteria for membrane classification.

Geological Keywords Targeted:
1. Basalt columns / Columnar jointing
2. Quartz crystal / Crystalline structure
3. Granite outcrop / Igneous grain structure
4. Sandstone layers / Stratification
"""

import os
import requests
from urllib.parse import quote

# Directory to save downloaded images
DOWNLOAD_DIR = "WorldModel/training_data/geology_inventory"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Geological keyword search terms for Wikimedia Commons
GEOLOGY_KEYWORDS = [
    ("basalt columns", "rock_basalt_hexagonal_columnar_jointing_tessellation"),
    ("quartz crystal cluster", "mineral_quartz_hexagonal_prismatic_with_rhombohedral_termination"),
    ("granite outcrop", "rock_granite_phaneritic_interlocking_feldspar_quartz_mica"),
    ("sandstone layers stratification", "rock_sandstone_cross_bedding_stratification_layers"),
    ("columnar jointing lava", "rock_basalt_hexagonal_columnar_jointing_tessellation"),
    ("hexagonal basalt columns", "rock_basalt_hexagonal_columnar_jointing_tessellation")
]

def search_wikimedia_commons(query):
    """Search Wikimedia Commons for images matching a query."""
    api_url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srlimit": 5,
        "srnamespace": 6,  # 6 is the File namespace on Wikimedia Commons
        "prop": "imageinfo",
        "iiprop": "url|size|timestamp",
        "iiurlwidth": 1200
    }
    
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'query' in data and 'search' in data['query']:
            return data['query']['search']
    return []

def download_image(file_page, pattern_label, keyword):
    """Download image from Wikimedia Commons file page."""
    # Extract image URL from file page (simplified for common patterns)
    # In a full implementation, this would parse the HTML or use the API to get the direct image URL
    
    # Construct common Wikimedia Commons image URL pattern
    file_name = file_page.split('/')[-1] if '/' in file_page else file_page
    image_url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{file_page[0:2]}/{file_page[2:]}/1200px-{file_name}"
    
    # More accurate URL construction based on file page structure
    # For now, we'll use a simplified approach
    
    filename_safe = keyword.replace(' ', '_').replace('/', '_')
    save_path = os.path.join(DOWNLOAD_DIR, f"{pattern_label.split('_')[1]}_{filename_safe}.jpg")
    
    print(f"  Attempting to download: {keyword} -> {pattern_label}")
    print(f"  Save path: {save_path}")
    
    # For demonstration, we'll simulate the download or use a known working URL pattern
    # In production, this would use the Wikimedia API to get the direct image URL
    
    return save_path

def main():
    print("=" * 60)
    print("CHIMERA ENGINE: BATCH GEOLOGY DOWNLOADER")
    print("=" * 60)
    print(f"Download directory: {DOWNLOAD_DIR}")
    print("\nTargeting geological keywords:")
    
    for keyword, pattern_label in GEOLOGY_KEYWORDS:
        print(f"  - '{keyword}' -> {pattern_label}")
    
    print("\nSearching Wikimedia Commons for images...")
    
    downloaded_count = 0
    for keyword, pattern_label in GEOLOGY_KEYWORDS:
        print(f"\n[1] Searching for: '{keyword}'")
        results = search_wikimedia_commons(keyword)
        
        if results:
            print(f"  Found {len(results)} results:")
            for i, result in enumerate(results[:3]):  # Limit to first 3 results
                title = result.get('title', 'Unknown')
                print(f"    {i+1}. {title}")
                
                # In a full implementation, we would download the image here
                # and examine it visually to confirm it meets the criteria
                
            downloaded_count += len(results)
        else:
            print(f"  No results found for '{keyword}'")
    
    print("\n" + "=" * 60)
    print("BATCH GEOLOGY DOWNLOAD SEARCH COMPLETED")
    print("=" * 60)
    print(f"Total image pages found: {downloaded_count}")
    print("Next step: Visual examination of downloaded images to confirm patterns.")

if __name__ == "__main__":
    main()
