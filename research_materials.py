#!/usr/bin/env python3
"""Research Agent: Locate scan data for missing materials."""

import sys
from pathlib import Path
import subprocess

# Materials to research
MATERIALS_TO_FIND = [
    {"name": "grass_tuft", "keywords": ["grass", "turf", "lawn", "vegetative"]},
    {"name": "rock_sample", "keywords": ["rock", "stone", "boulder", "mineral"]},
    {"name": "pure_metal", "keywords": ["metal", "steel", "aluminum", "copper", "silver"]},
    {"name": "ice_block", "keywords": ["ice", "frozen", "snow", "crystal"]}
]

def search_existing_scans():
    """Search existing training data for relevant scans."""
    print(" Searching existing scan data...")
    
    training_data = Path("WorldModel/training_data")
    if not training_data.exists():
        print(" Training data directory not found")
        return []
    
    # List all .splat and .ksplat files
    splat_files = list(training_data.rglob("*.splat")) + list(training_data.rglob("*.ksplat"))
    
    print(f"Found {len(splat_files)} scan files in training data")
    
    # Categorize by material type based on path names
    categorized = []
    for file_path in splat_files:
        rel_path = str(file_path.relative_to(training_data))
        
        if any(keyword in rel_path.lower() for keyword in ["grass", "turf", "lawn"]):
            categorized.append({"name": "grass_tuft", "path": str(file_path), "confidence": 0.8})
        elif any(keyword in rel_path.lower() for keyword in ["rock", "stone", "boulder"]):
            categorized.append({"name": "rock_sample", "path": str(file_path), "confidence": 0.8})
        elif any(keyword in rel_path.lower() for keyword in ["metal", "steel", "aluminum", "copper", "silver"]):
            categorized.append({"name": "pure_metal", "path": str(file_path), "confidence": 0.7})
        elif any(keyword in rel_path.lower() for keyword in ["ice", "frozen", "snow", "crystal"]):
            categorized.append({"name": "ice_block", "path": str(file_path), "confidence": 0.8})
    
    return categorized

def search_web_resources():
    """Search web resources for scan data (placeholder for future implementation)."""
    print(" Searching web resources...")
    # This would use web_search_real or similar tools in a real implementation
    print("️ Web search not yet implemented - manual scanning recommended")
    return []

def generate_research_report(existing_scans, web_results):
    """Generate a report of available materials and recommendations."""
    print("\n RESEARCH REPORT")
    print("="*60)
    
    # Count by material type
    counts = {}
    for scan in existing_scans + web_results:
        name = scan["name"]
        counts[name] = counts.get(name, 0) + 1
    
    print("Available Scans by Material Type:")
    for material, count in sorted(counts.items()):
        print(f"  {material}: {count} candidate(s)")
    
    # Check which materials are still missing
    missing = [m["name"] for m in MATERIALS_TO_FIND if m["name"] not in counts]
    
    if missing:
        print("\n️ Missing Materials:")
        for material in missing:
            print(f"  - {material}")
        
        print("\n RECOMMENDATIONS:")
        print("  1. Use existing similar materials as proxies")
        print("  2. Plan real-world scanning when human approval granted")
        print("  3. Consider synthetic generation for missing types")
    else:
        print("\n All target materials have candidate scans!")
    
    # Save report to file
    report = {
        "timestamp": str(datetime.now()),
        "existing_scans": existing_scans,
        "web_results": web_results,
        "missing_materials": missing,
        "recommendations": [
            "Use existing similar materials as proxies",
            "Plan real-world scanning when human approval granted", 
            "Consider synthetic generation for missing types"
        ]
    }
    
    report_path = Path("agent_logs/research_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n Report saved to {report_path}")
    return len(missing) == 0

def main():
    from datetime import datetime
    
    print(" Material Research Agent")
    print("="*60)
    
    # Search existing scans
    existing_scans = search_existing_scans()
    
    # Search web resources (placeholder)
    web_results = search_web_resources()
    
    # Generate report
    success = generate_research_report(existing_scans, web_results)
    
    if success:
        print("\n Research agent completed successfully")
        return 0
    else:
        print("\n️ Research agent completed with missing materials")
        return 0  # Not a failure, just incomplete

if __name__ == "__main__":
    sys.exit(main())
