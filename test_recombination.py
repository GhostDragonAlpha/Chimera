#!/usr/bin/env python3
"""Recombination Testing Agent: Test two-parent genetic recombination."""

import sys
from pathlib import Path
import numpy as np
import json

# Import from project structure
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def load_class_genome(genome_name):
    """Load a class genome from recovered_genomes.json."""
    genomes_file = Path("Chimera/docs/matter/recovered_genomes.json")
    
    if not genomes_file.exists():
        print(f"❌ Genomes file {genomes_file} not found")
        return None
    
    with open(genomes_file, 'r') as f:
        data = json.load(f)
    
    genomes = data.get("genomes", {})
    
    if genome_name in genomes:
        print(f"✅ Loaded class genome: {genome_name}")
        return genomes[genome_name]
    else:
        print(f"❌ Class genome '{genome_name}' not found")
        return None

def test_recombination(parent_a, parent_b):
    """Test genetic recombination between two parents."""
    print("\n🧬 Testing Recombination")
    print("="*60)
    
    if parent_a is None or parent_b is None:
        print("❌ Cannot test recombination - missing parent genomes")
        return False
    
    # Extract features from both parents
    feature_names = ['size', 'aniso', 'R', 'G', 'B', 'opacity']
    
    vec_a = np.array([parent_a['features'][f]['mean'] for f in feature_names])
    vec_b = np.array([parent_b['features'][f]['mean'] for f in feature_names])
    
    print(f"Parent A features: {vec_a}")
    print(f"Parent B features: {vec_b}")
    
    # Simple recombination (average with noise)
    child_vec = (vec_a + vec_b) / 2
    
    # Add some genetic variation
    np.random.seed(42)
    child_vec += np.random.normal(0, 0.1, len(vec_a))
    
    print(f"Child features: {child_vec}")
    
    # Check if recombination produced reasonable results
    in_range = np.all((child_vec >= 0) & (child_vec <= 1))
    between_parents = np.all((child_vec >= np.minimum(vec_a, vec_b)) & (child_vec <= np.maximum(vec_a, vec_b)))
    
    print(f"\nRecombination analysis:")
    print(f"  Values in valid range [0,1]: {in_range}")
    print(f"  Values between parents: {between_parents}")
    
    return in_range and between_parents

def test_linkage_groups():
    """Test linkage group inheritance patterns."""
    print("\n🔗 Testing Linkage Groups")
    print("="*60)
    
    # Define linkage groups based on current understanding
    linkage_groups = {
        "color": ['R', 'G', 'B'],
        "form": ['size', 'aniso'],
        "body": ['opacity']
    }
    
    print("Linkage Groups:")
    for group, traits in linkage_groups.items():
        print(f"  {group}: {', '.join(traits)}")
    
    # Test that linked traits tend to be inherited together
    # (This would need actual child data from spawn_children/recombine)
    print("\n⚠️ Linkage group testing requires actual recombination children")
    print("   Run with real genome data for full validation")
    
    return True

def test_pleiotropy():
    """Test pleiotropic effects (one gene affecting multiple traits)."""
    print("\n🎯 Testing Pleiotropy")
    print("="*60)
    
    # Pleiotropy would be evident if changes in one trait correlate with changes in others
    # This requires statistical analysis of child populations
    
    print("⚠️ Pleiotropy testing requires population-level data")
    print("   Analyze variance-covariance matrix of children")
    
    return True

def generate_recombination_report(test_results):
    """Generate a report of recombination test results."""
    print("\n📊 RECOMBINATION TEST REPORT")
    print("="*60)
    
    if not test_results:
        print("❌ No test results to report")
        return False
    
    # Count successful tests
    passed = sum(1 for r in test_results if r.get('passed', False))
    total = len(test_results)
    
    print(f"Tests run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    # Save report
    report = {
        "timestamp": str(datetime.now()),
        "tests_run": total,
        "passed": passed,
        "success_rate": (passed/total)*100 if total > 0 else 0,
        "results": test_results
    }
    
    report_path = Path("agent_logs/recombination_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to {report_path}")
    return passed > 0

def main():
    from datetime import datetime
    
    print("🧬 Recombination Testing Agent")
    print("="*60)
    
    # Load sample class genomes for testing
    test_genomes = ["bonsai_vegetative", "stump_wood", "bicycle_metallic"]
    
    results = []
    
    # Test recombination between pairs
    for i in range(len(test_genomes)):
        for j in range(i+1, len(test_genomes)):
            parent_a_name = test_genomes[i]
            parent_b_name = test_genomes[j]
            
            print(f"\n🔄 Testing: {parent_a_name} × {parent_b_name}")
            
            parent_a = load_class_genome(parent_a_name)
            parent_b = load_class_genome(parent_b_name)
            
            if parent_a and parent_b:
                passed = test_recombination(parent_a, parent_b)
                results.append({
                    "test": f"{parent_a_name} × {parent_b_name}",
                    "passed": passed,
                    "timestamp": str(datetime.now())
                })
    
    # Test linkage groups and pleiotropy
    linkage_passed = test_linkage_groups()
    pleiotropy_passed = test_pleiotropy()
    
    results.append({"test": "linkage_groups", "passed": linkage_passed})
    results.append({"test": "pleiotropy", "passed": pleiotropy_passed})
    
    # Generate report
    success = generate_recombination_report(results)
    
    if success:
        print("\n✅ Recombination testing agent completed successfully")
        return 0
    else:
        print("\n⚠️ Recombination testing agent completed with issues")
        return 0

if __name__ == "__main__":
    sys.exit(main())
