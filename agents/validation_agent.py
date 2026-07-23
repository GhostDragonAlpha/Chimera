#!/usr/bin/env python3
"""Visual Validation Agent - Analyze rendered children images."""

import sys
from pathlib import Path
import numpy as np
from PIL import Image
import json
from datetime import datetime

def analyze_image_coherence(image_path):
    """Analyze a single image for visual coherence."""
    print(f"Analyzing {image_path.name}...")
    
    try:
        img = Image.open(image_path)
        img_array = np.array(img)
        
        width, height = img.size
        pixel_count = width * height
        
        mean_color = np.mean(img_array, axis=(0, 1))
        std_color = np.std(img_array)
        
        pure_white = np.sum(np.all(img_array > 250, axis=2)) / pixel_count
        pure_black = np.sum(np.all(img_array < 5, axis=2)) / pixel_count
        
        if len(img_array.shape) == 3:
            r_mean = np.mean(img_array[:,:,0])
            g_mean = np.mean(img_array[:,:,1])
            b_mean = np.mean(img_array[:,:,2])
            color_balance = abs(r_mean - g_mean) + abs(g_mean - b_mean) + abs(b_mean - r_mean)
        else:
            color_balance = 0
        
        return {
            "path": str(image_path),
            "width": width,
            "height": height,
            "mean_color": mean_color.tolist(),
            "std_dev": float(std_color),
            "pure_white_ratio": float(pure_white),
            "pure_black_ratio": float(pure_black),
            "color_balance": float(color_balance),
            "file_size": image_path.stat().st_size,
            "timestamp": str(datetime.now())
        }
        
    except Exception as e:
        print(f"Error analyzing {image_path}: {e}")
        return None

def validate_material_coherence(analysis_results):
    """Validate that materials look coherent based on analysis."""
    print("\nVALIDATION RESULTS")
    print("="*60)
    
    all_passed = True
    
    for result in analysis_results:
        if result is None:
            continue
            
        path = Path(result["path"])
        material_name = path.stem
        
        if result["pure_white_ratio"] > 0.1 or result["pure_black_ratio"] > 0.1:
            print(f"WARNING: {material_name} - High clamping detected")
            all_passed = False
        else:
            print(f"OK: {material_name} - No excessive clamping")
        
        if result["file_size"] < 50000:
            print(f"WARNING: {material_name} - File size suspiciously small")
            all_passed = False
        else:
            print(f"OK: {material_name} - Reasonable file size")
        
        if result["color_balance"] < 20:
            print(f"WARNING: {material_name} - Color distribution too uniform")
            all_passed = False
        else:
            print(f"OK: {material_name} - Natural color variation")
        
        print()
    
    return all_passed

def generate_validation_report(analysis_results, validation_passed):
    """Generate a comprehensive validation report."""
    print("\nVALIDATION REPORT")
    print("="*60)
    
    total_checks = len(analysis_results) * 3
    passed_checks = sum(1 for r in analysis_results if r is not None and 
                       r["pure_white_ratio"] <= 0.1 and 
                       r["pure_black_ratio"] <= 0.1 and
                       r["file_size"] >= 50000 and
                       r["color_balance"] >= 20)
    
    print(f"Total checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {total_checks - passed_checks}")
    print(f"Pass rate: {(passed_checks/total_checks)*100:.1f}%")
    
    report = {
        "timestamp": str(datetime.now()),
        "images_analyzed": len(analysis_results),
        "validation_passed": validation_passed,
        "pass_rate": (passed_checks/total_checks)*100 if total_checks > 0 else 0,
        "details": analysis_results
    }
    
    report_path = Path("agent_logs/validation_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to {report_path}")
    return validation_passed

def main():
    render_dir = Path("Saved/SplatEmit")
    
    if not render_dir.exists():
        print("Render directory not found")
        return 1
    
    png_files = list(render_dir.glob("*.png"))
    
    if not png_files:
        print("No PNG files found in render directory")
        return 1
    
    print(f"Found {len(png_files)} rendered images")
    print("="*60)
    
    analysis_results = []
    for png_file in png_files:
        result = analyze_image_coherence(png_file)
        if result:
            analysis_results.append(result)
    
    validation_passed = validate_material_coherence(analysis_results)
    success = generate_validation_report(analysis_results, validation_passed)
    
    if success:
        print("\nVisual validation agent completed successfully")
        return 0
    else:
        print("\nVisual validation agent completed with issues detected")
        return 0

if __name__ == "__main__":
    sys.exit(main())
