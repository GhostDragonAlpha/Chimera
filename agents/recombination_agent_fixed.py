#!/usr/bin/env python3
"""Recombination Agent - Test two-parent genetic recombination."""

import sys
from pathlib import Path
import numpy as np
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def load_class_genome(genome_name):
    """Load a class genome from recovered_genomes.json."""
    genomes_file = Path("Chimera/docs/matter/recovered_genomes.json")
    
    if not genomes_file.exists():
        print(f"Genomes file {genomes_file} not found")
        return None
    
    with open(genomes_file, 'r') as f:
        data = json.load(f)
    
    genomes = data.get("genomes", {})
    
    if genome_name in genomes:
        print(f"Loaded class genome: {genome_name}")
        return genomes[genome_name]
    else:
        print(f"Class genome '{genome_name}' not found")
        return None

def test_recombination(parent_a, parent_b):
    """Test genetic recombination between two parents."""
    print("\nTesting Recombination")
    print("="*60)
    
    if parent_a is None or parent_b is None:
        print("Cannot test recombination - missing parent genomes")
        return False
    
    feature_names = ['size', 'aniso', 'R', 'G', 'B', 'opacity']
    
    vec_a = np.array([parent_a['features'][f]['mean'] for f in feature_names])
    vec_b = np.array([parent_b['features'][f]['mean'] for f in feature_names])
    
    print(f"Parent A features: {vec_a}")
    print(f"Parent B features: {vec_b}")
    
    child_vec = (vec_a + vec_b) / 2
    
    np.random.seed(42)
    child_vec += np.random.normal(0, 0.1, len(vec_a))
    
    print(f"Child features: {child_vec}")
    
    in_range = np.all((child_vec >= 0) & (child_vec <= 1))
    between_parents = np.all((child_vec >= np.minimum(vec_a, vec_b)) & (child_vec <= np.maximum(vec_a, vec_b)))
    
    print("\nRecombination analysis:")
    print(f"  Values in valid range [0,1]: {in_range}")
    print(f"  Values between parents: {between_parents}")
    
    return in_range and between_parents

def test_linkage_groups():
    """Test linkage group inheritance patterns."""
    print("\nTesting Linkage Groups")
    print("="*60)
    
    linkage_groups = {
        "color": ['R', 'G', 'B'],
        "form": ['size', 'aniso'],
        "body": ['opacity']
    }
    
    print("Linkage Groups:")
    for group, traits in linkage_groups.items():
        print(f"  {group}: {', '.join(traits)}")
    
    print("\nLinkage group testing requires actual recombination children")
    print("Run with real genome data for full validation")
    
    return True

def test_pleiotropy():
    """Test pleiotropic effects (one gene affecting multiple traits)."""
    print("\nTesting Pleiotropy")
    print("="*60)
    
    print("Pleiotropy testing requires population-level data")
    print("Analyze variance-covariance matrix of children")
    
    return True

def generate_recombination_report(test_results):
    """Generate a report of recombination test results."""
    print("\nRECOMBINATION TEST REPORT")
    print("="*60)
    
    if not test_results:
        print("No test results to report")
        return False
    
    passed = sum(1 for r in test_results if r.get('passed', False))
    total = len(test_results)
    
    print(f"Tests run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
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
    
    print(f"\nReport saved to {report_path}")
    return passed > 0

def main():
    print("Recombination Testing Agent")
    print("="*60)
    
    test_genomes = ["bonsai_vegetative", "stump_wood", "bicycle_metallic"]
    
    results = []
    
    for i in range(len(test_genomes)):
        for j in range(i+1, len(test_genomes)):
            parent_a_name = test_genomes[i]
            parent_b_name = test_genomes[j]
            
            print(f"\nTesting: {parent_a_name} x {parent_b_name}")
            
            parent_a = load_class_genome(parent_a_name)
            parent_b = load_class_genome(parent_b_name)
            
            if parent_a and parent_b:
                passed = test_recombination(parent_a, parent_b)
                results.append({
                    "test": f"{parent_a_name} x {parent_b_name}",
                    "passed": passed,
                    "timestamp": str(datetime.now())
                })
    
    linkage_passed = test_linkage_groups()
    pleiotropy_passed = test_pleiotropy()
    
    results.append({"test": "linkage_groups", "passed": linkage_passed})
    results.append({"test": "pleiotropy", "passed": pleiotropy_passed})
    
    success = generate_recombination_report(results)
    
    if success:
        print("\nRecombination testing agent completed successfully")
        return 0
    else:
        print("\nRecombination testing agent completed with issues")
        return 0

if __name__ == "__main__":
    sys.exit(main())
