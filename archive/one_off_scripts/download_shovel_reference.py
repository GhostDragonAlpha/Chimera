import urllib.request
import os

# Create research directory relative to workspace root (e:/PythonChimera)
research_dir = r'Chimera\research\loop4\Tool_Shovel_Model'
os.makedirs(research_dir, exist_ok=True)

# Try to download a canonical reference image from Wikimedia Commons (public domain shovel image)
reference_url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Garden_shovel.jpg/800px-Garden_shovel.jpg'
canonical_ref_path = os.path.join(research_dir, 'CANONICAL_REFERENCE.jpg')

try:
    urllib.request.urlretrieve(reference_url, canonical_ref_path)
    print(f'Successfully downloaded reference image to: {canonical_ref_path}')
except Exception as e:
    print(f'Failed to download reference image: {e}')
    # Create a placeholder file if download fails
    with open(canonical_ref_path, 'w') as f:
        f.write('CANONICAL_REFERENCE_PLACEHOLDER - Garden Shovel Reference from Wikimedia Commons or Hardware Store Sources')
    print(f'Created placeholder reference at: {canonical_ref_path}')
