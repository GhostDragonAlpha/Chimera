#!/usr/bin/env python3
"""
Phase 2: Visual Validation Agent - Phenotypic Analysis of Genetic Experiments
Analyzes rendered children images for clamping artifacts, color distribution uniformity, file size rationality, and overall coherence.
"""

import os
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from collections import defaultdict
import json
from datetime import datetime

class VisualValidationAgent:
    def __init__(self, image_dir):
        self.image_dir = image_dir
        self.results = []

    def analyze_image(self, filepath):
        """Perform comprehensive visual analysis on a single image."""
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)

        # Load image
        img = Image.open(filepath)
        img_array = np.array(img)

        # Basic metrics
        height, width = img_array.shape[:2]
        total_pixels = height * width

        # Convert to RGB if RGBA
        if img_array.shape[2] == 4:
            rgb_array = img_array[:, :, :3]
        else:
            rgb_array = img_array

        # Normalize to [0, 1]
        rgb_normalized = rgb_array.astype(np.float32) / 255.0

        # Color distribution analysis
        r_mean = np.mean(rgb_normalized[:, :, 0])
        g_mean = np.mean(rgb_normalized[:, :, 1])
        b_mean = np.mean(rgb_normalized[:, :, 2])

        r_std = np.std(rgb_normalized[:, :, 0])
        g_std = np.std(rgb_normalized[:, :, 1])
        b_std = np.std(rgb_normalized[:, :, 2])

        # Check for clamping artifacts (extreme values)
        clamp_r = np.sum(rgb_normalized[:, :, 0] >= 0.99) / total_pixels * 100
        clamp_g = np.sum(rgb_normalized[:, :, 1] >= 0.99) / total_pixels * 100
        clamp_b = np.sum(rgb_normalized[:, :, 2] >= 0.99) / total_pixels * 100

        # Black clamping (near zero)
        black_r = np.sum(rgb_normalized[:, :, 0] <= 0.01) / total_pixels * 100
        black_g = np.sum(rgb_normalized[:, :, 1] <= 0.01) / total_pixels * 100
        black_b = np.sum(rgb_normalized[:, :, 2] <= 0.01) / total_pixels * 100

        # Color uniformity (coefficient of variation)
        r_cv = r_std / r_mean if r_mean > 0 else 0
        g_cv = g_std / g_mean if g_mean > 0 else 0
        b_cv = b_std / b_mean if b_mean > 0 else 0

        # Overall uniformity score (lower is more uniform)
        uniformity_score = (r_cv + g_cv + b_cv) / 3

        # File size rationality check
        expected_size = total_pixels * 3 * 1.5  # RGB + compression overhead
        size_ratio = file_size / expected_size
        size_rational = 0.8 < size_ratio < 2.0  # Reasonable compression ratio

        # Coherence assessment (visual inspection via color variance)
        # Higher variance suggests more detail/variation, but too high may indicate noise
        total_variance = r_std**2 + g_std**2 + b_std**2
        coherence_score = np.log1p(total_variance) / 10  # Scaled log score

        # Background analysis (assuming black background)
        bg_mask = np.all(rgb_normalized < 0.05, axis=2)
        bg_ratio = np.sum(bg_mask) / total_pixels

        return {
            'filename': filename,
            'dimensions': f"{width}x{height}",
            'file_size_bytes': file_size,
            'file_size_kb': round(file_size / 1024, 2),
            'color_mean': {
                'R': round(r_mean, 4),
                'G': round(g_mean, 4),
                'B': round(b_mean, 4)
            },
            'color_std': {
                'R': round(r_std, 4),
                'G': round(g_std, 4),
                'B': round(b_std, 4)
            },
            'clamping_artifacts': {
                'high_clamp_R_pct': round(clamp_r, 2),
                'high_clamp_G_pct': round(clamp_g, 2),
                'high_clamp_B_pct': round(clamp_b, 2),
                'black_clamp_R_pct': round(black_r, 2),
                'black_clamp_G_pct': round(black_g, 2),
                'black_clamp_B_pct': round(black_b, 2)
            },
            'uniformity_score': round(uniformity_score, 4),
            'coherence_score': round(coherence_score, 4),
            'size_rationality': size_rational,
            'background_ratio': round(bg_ratio, 4),
            'timestamp': datetime.now().isoformat()
        }

    def run_analysis(self):
        """Run analysis on all PNG files in directory."""
        png_files = [f for f in os.listdir(self.image_dir) if f.endswith('.png')]

        print("=" * 80)
        print("PHASE 2: VISUAL VALIDATION AGENT - PHENOTYPIC ANALYSIS REPORT")
        print("=" * 80)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Image Directory: {self.image_dir}")
        print(f"Total Images Analyzed: {len(png_files)}\n")

        for filename in png_files:
            filepath = os.path.join(self.image_dir, filename)
            analysis = self.analyze_image(filepath)
            self.results.append(analysis)

            # Print detailed report for each image
            print(f"[ANALYSIS] {filename}")
            print("-" * 60)
            print(f"Dimensions: {analysis['dimensions']}")
            print(f"File Size: {analysis['file_size_kb']} KB")
            print(f"\nColor Distribution:")
            print(f"  Mean RGB: ({analysis['color_mean']['R']:.2f}, {analysis['color_mean']['G']:.2f}, {analysis['color_mean']['B']:.2f})")
            print(f"  Std Dev RGB: ({analysis['color_std']['R']:.2f}, {analysis['color_std']['G']:.2f}, {analysis['color_std']['B']:.2f})")
            print(f"\nClamping Artifacts:")
            print(f"  High Clamp (>0.99): R={analysis['clamping_artifacts']['high_clamp_R_pct']:.1f}%, G={analysis['clamping_artifacts']['high_clamp_G_pct']:.1f}%, B={analysis['clamping_artifacts']['high_clamp_B_pct']:.1f}%")
            print(f"  Black Clamp (<0.01): R={analysis['clamping_artifacts']['black_clamp_R_pct']:.1f}%, G={analysis['clamping_artifacts']['black_clamp_G_pct']:.1f}%, B={analysis['clamping_artifacts']['black_clamp_B_pct']:.1f}%")
            print(f"\nQuality Metrics:")
            print(f"  Uniformity Score: {analysis['uniformity_score']:.4f} (lower = more uniform)")
            print(f"  Coherence Score: {analysis['coherence_score']:.4f}")
            print(f"  Size Rationality: {'[PASS]' if analysis['size_rationality'] else '[WARN]'}")
            print(f"  Background Ratio: {analysis['background_ratio']:.2%}")
            print("\n")

        # Generate summary statistics
        self.generate_summary()

    def generate_summary(self):
        """Generate overall summary and recommendations."""
        print("=" * 80)
        print("SUMMARY STATISTICS & RECOMMENDATIONS")
        print("=" * 80)

        if not self.results:
            print("No images analyzed.")
            return

        # Aggregate metrics
        avg_file_size = np.mean([r['file_size_bytes'] for r in self.results])
        avg_uniformity = np.mean([r['uniformity_score'] for r in self.results])
        avg_coherence = np.mean([r['coherence_score'] for r in self.results])
        avg_clamp_high = np.mean([
            (r['clamping_artifacts']['high_clamp_R_pct'] +
             r['clamping_artifacts']['high_clamp_G_pct'] +
             r['clamping_artifacts']['high_clamp_B_pct']) / 3
            for r in self.results
        ])

        # Color averages
        avg_r_mean = np.mean([r['color_mean']['R'] for r in self.results])
        avg_g_mean = np.mean([r['color_mean']['G'] for r in self.results])
        avg_b_mean = np.mean([r['color_mean']['B'] for r in self.results])

        print("\nAGGREGATE METRICS:")
        print(f"  Average File Size: {avg_file_size/1024:.1f} KB")
        print(f"  Average Uniformity Score: {avg_uniformity:.4f}")
        print(f"  Average Coherence Score: {avg_coherence:.4f}")
        print(f"  Average High Clamp Artifacts: {avg_clamp_high:.2f}%")
        print(f"  Overall Color Tint: RGB({avg_r_mean:.2f}, {avg_g_mean:.2f}, {avg_b_mean:.2f})")

        # Quality assessment
        print("\nQUALITY ASSESSMENT:")

        if avg_clamp_high < 5.0:
            print("  [PASS] Clamping artifacts are minimal (<5%)")
        else:
            print(f"  [WARN] High clamping artifacts detected ({avg_clamp_high:.1f}%)")

        if avg_uniformity < 0.3:
            print("  [PASS] Color distribution is reasonably uniform")
        else:
            print(f"  [WARN] Color variation may be excessive (uniformity={avg_uniformity:.2f})")

        size_issues = [r for r in self.results if not r['size_rationality']]
        if not size_issues:
            print("  [PASS] All file sizes are within expected range")
        else:
            print(f"  [WARN] {len(size_issues)} image(s) have unusual file sizes")

        # Material-specific insights
        print("\nMATERIAL-SPECIFIC INSIGHTS:")
        for result in self.results:
            filename = result['filename']
            if 'bonsai' in filename:
                print(f"  [VEGETATIVE] {filename}: Vegetative material - expect green-dominant colors")
            elif 'stump' in filename or 'wood' in filename:
                print(f"  [WOOD] {filename}: Wood material - expect brown/earthy tones")
            elif 'bicycle' in filename or 'metallic' in filename:
                print(f"  [METALLIC] {filename}: Metallic material - may show high reflectivity")
            elif 'plush' in filename or 'fabric' in filename:
                print(f"  [FABRIC] {filename}: Fabric material - expect soft, diffuse appearance")
            elif 'truck' in filename:
                print(f"  [VEHICLE] {filename}: Vehicle material - likely metallic with varied colors")

        # Recommendations
        print("\nRECOMMENDATIONS:")
        if avg_clamp_high > 10.0:
            print("  • Consider adjusting rendering pipeline to reduce extreme value clamping")
        if avg_uniformity > 0.5:
            print("  • Review color distribution algorithms for better uniformity")
        if len([r for r in self.results if r['coherence_score'] < 0.1]) > 0:
            print("  • Investigate low coherence scores - may indicate rendering issues")

        # Convert numpy types to Python native types for JSON serialization
        serializable_results = []
        for r in self.results:
            serializable_r = {
                'filename': r['filename'],
                'dimensions': r['dimensions'],
                'file_size_bytes': int(r['file_size_bytes']),
                'file_size_kb': float(r['file_size_kb']),
                'color_mean': {
                    'R': float(r['color_mean']['R']),
                    'G': float(r['color_mean']['G']),
                    'B': float(r['color_mean']['B'])
                },
                'color_std': {
                    'R': float(r['color_std']['R']),
                    'G': float(r['color_std']['G']),
                    'B': float(r['color_std']['B'])
                },
                'clamping_artifacts': {
                    'high_clamp_R_pct': float(r['clamping_artifacts']['high_clamp_R_pct']),
                    'high_clamp_G_pct': float(r['clamping_artifacts']['high_clamp_G_pct']),
                    'high_clamp_B_pct': float(r['clamping_artifacts']['high_clamp_B_pct']),
                    'black_clamp_R_pct': float(r['clamping_artifacts']['black_clamp_R_pct']),
                    'black_clamp_G_pct': float(r['clamping_artifacts']['black_clamp_G_pct']),
                    'black_clamp_B_pct': float(r['clamping_artifacts']['black_clamp_B_pct'])
                },
                'uniformity_score': float(r['uniformity_score']),
                'coherence_score': float(r['coherence_score']),
                'size_rationality': bool(r['size_rationality']),
                'background_ratio': float(r['background_ratio']),
                'timestamp': r['timestamp']
            }
            serializable_results.append(serializable_r)

        report = {
            'timestamp': datetime.now().isoformat(),
            'directory': self.image_dir,
            'total_images': len(self.results),
            'results': serializable_results,
            'summary': {
                'avg_file_size_bytes': float(avg_file_size),
                'avg_uniformity_score': float(avg_uniformity),
                'avg_coherence_score': float(avg_coherence),
                'avg_clamp_artifacts_pct': float(avg_clamp_high),
                'overall_color_tint': [float(avg_r_mean), float(avg_g_mean), float(avg_b_mean)]
            }
        }

        report_path = os.path.join(self.image_dir, 'visual_validation_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        print(f"\nDetailed JSON report saved to: {report_path}")
        print("=" * 80)

if __name__ == "__main__":
    image_directory = r"E:\PythonChimera\Saved\SplatEmit"
    agent = VisualValidationAgent(image_directory)
    agent.run_analysis()
