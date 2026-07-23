#!/usr/bin/env python3
"""Research Agent - Search for missing material scans."""

import sys
from pathlib import Path

MATERIALS_TO_FIND = [
    {"name": "grass_tuft", "keywords": ["grass", "turf", "lawn"]},
    {"name": "rock_sample", "keywords": ["rock", "stone", "boulder"]},
    {"name": "pure_metal", "keywords": ["metal", "steel", "aluminum"]},
    {"name": "ice_block", "keywords": ["ice", "frozen", "snow"]}
]

def search_existing_scans():
    print("Searching existing scan data...")
    
    training_data = Path("WorldModel/training_data")
    if not training_data.exists():
        print("Training data directory not found")
        return []
    
    splat_files = list(training_data.rglob("*.splat")) + list(training_data.rglob("*.ksplat"))
    print(f"Found {len(splat_files)} scan files in training data")
    
    categorized = []
    for file_path in splat_files:
        rel_path = str(file_path.relative_to(training_data))
        
        if any(keyword in rel_path.lower() for keyword in ["grass", "turf", "lawn"]):
            categorized.append({"name": "grass_tuft", "path": str(file_path), "confidence": 0.8})
        elif any(keyword in rel_path.lower() for keyword in ["rock", "stone", "boulder"]):
            categorized.append({"name": "rock_sample", "path": str(file_path), "confidence": 0.8})
        elif any(keyword in rel_path.lower() for keyword in ["metal", "steel", "aluminum"]):
            categorized.append({"name": "pure_metal", "path": str(file_path), "confidence": 0.7})
        elif any(keyword in rel_path.lower() for keyword in ["ice", "frozen", "snow"]):
            categorized.append({"name": "ice_block", "path": str(file_path), "confidence": 0.8})
    
    return categorized

def main():
    print("Material Research Agent")
    print("="*60)
    
    existing_scans = search_existing_scans()
    
    if not existing_scans:
        print("No matching scans found for target materials")
        print("Recommendation: Plan real-world scanning when human approval granted")
        return 0
    
    print("\nFound candidate scans:")
    for scan in existing_scans:
        print(f"  {scan['name']}: {scan['path']} (confidence: {scan['confidence']})")
    
    print("\nResearch agent completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
