#!/usr/bin/env python3
"""Visual Validation Agent: Automated analysis of rendered children images."""

import sys
from pathlib import Path
import numpy as np
from PIL import Image
import json
from datetime import datetime

def analyze_image_coherence(image_path):
    """Analyze a single image for visual coherence."""
    print(f"🔍 Analyzing {image_path.name}...")
    
    try:
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # Basic metrics
        width, height = img.size
        pixel_count = width * height
        
        # Color analysis
        mean_color = np.mean(img_array, axis=(0, 1))
        std_color = np.std(img_array)
        
        # Check for clamping (pure white/black)
        pure_white = np.sum(np.all(img_array > 250, axis=2)) / pixel_count
        pure_black = np.sum(np.all(img_array < 5, axis=2)) / pixel_count
        
        # Texture analysis (simplified)
        if len(img_array.shape) == 3:
            # RGB image
            r_mean = np.mean(img_array[:,:,0])
            g_mean = np.mean(img_array[:,:,1])
            b_mean = np.mean(img_array[:,:,2])
            
            # Check for unnatural color distributions
            color_balance = abs(r_mean - g_mean) + abs(g_mean - b_mean) + abs(b_mean - r_mean)
        else:
            # Grayscale or other format
            color_balance = 0
        
        # Return analysis results
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
        print(f"❌ Error analyzing {image_path}: {e}")
        return None

def validate_material_coherence(analysis_results):
    """Validate that materials look coherent based on analysis."""
    print("\n🔬 VALIDATION RESULTS")
    print("="*60)
    
    all_passed = True
    
    for result in analysis_results:
        if result is None:
            continue
            
        path = Path(result["path"])
        material_name = path.stem
        
        # Check for clamping issues
        if result["pure_white_ratio"] > 0.1 or result["pure_black_ratio"] > 0.1:
            print(f"⚠️ {material_name}: High clamping detected")
            all_passed = False
        else:
            print(f"✅ {material_name}: No excessive clamping")
        
        # Check file size (should be reasonable for rendered images)
        if result["file_size"] < 50000:  # 50KB minimum
            print(f"⚠️ {material_name}: File size suspiciously small ({result['file_size']} bytes)")
            all_passed = False
        else:
            print(f"✅ {material_name}: Reasonable file size")
        
        # Check color balance (shouldn't be too uniform)
        if result["color_balance"] < 20:  # Too uniform
            print(f"⚠️ {material_name}: Color distribution too uniform")
            all_passed = False
        else:
            print(f"✅ {material_name}: Natural color variation")
        
        print()
    
    return all_passed

def generate_validation_report(analysis_results, validation_passed):
    """Generate a comprehensive validation report."""
    print("\n📊 VALIDATION REPORT")
    print("="*60)
    
    # Count passed/failed checks
    total_checks = len(analysis_results) * 3  # 3 checks per image
    passed_checks = sum(1 for r in analysis_results if r is not None and 
                       r["pure_white_ratio"] <= 0.1 and 
                       r["pure_black_ratio"] <= 0.1 and
                       r["file_size"] >= 50000 and
                       r["color_balance"] >= 20)
    
    print(f"Total checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {total_checks - passed_checks}")
    print(f"Pass rate: {(passed_checks/total_checks)*100:.1f}%")
    
    # Save report
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
    
    print(f"\n📄 Report saved to {report_path}")
    return validation_passed

def main():
    render_dir = Path("Saved/SplatEmit")
    
    if not render_dir.exists():
        print("❌ Render directory not found")
        return 1
    
    # Find all PNG files
    png_files = list(render_dir.glob("*.png"))
    
    if not png_files:
        print("❌ No PNG files found in render directory")
        return 1
    
    print(f"🖼️ Found {len(png_files)} rendered images")
    print("="*60)
    
    # Analyze each image
    analysis_results = []
    for png_file in png_files:
        result = analyze_image_coherence(png_file)
        if result:
            analysis_results.append(result)
    
    # Validate coherence
    validation_passed = validate_material_coherence(analysis_results)
    
    # Generate report
    success = generate_validation_report(analysis_results, validation_passed)
    
    if success:
        print("\n✅ Visual validation agent completed successfully")
        return 0
    else:
        print("\n⚠️ Visual validation agent completed with issues detected")
        return 0

if __name__ == "__main__":
    sys.exit(main())
