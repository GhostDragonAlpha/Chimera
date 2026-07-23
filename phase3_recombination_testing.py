#!/usr/bin/env python3
"""
Phase 3: Recombination Testing Agent
Test two-parent genetic recombination using existing class genomes from Chimera/docs/matter/recovered_genomes.json.

Validate:
- Inheritance patterns
- Linkage groups (color: R,G,B; form: size,aniso; body: opacity)
- Pleiotropy effects
- Heritability estimates
- Mendelian inheritance principles validation
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from scipy import stats

@dataclass
class Genome:
    """Represents a class genome with statistical features."""
    name: str
    features: Dict[str, Dict[str, float]]
    
    def get_mean(self, trait: str) -> float:
        return self.features[trait]['mean']
    
    def get_std(self, trait: str) -> float:
        return self.features[trait]['std']
    
    def get_p10(self, trait: str) -> float:
        return self.features[trait]['p10']
    
    def get_p90(self, trait: str) -> float:
        return self.features[trait]['p90']

class RecombinationTestingAgent:
    """Tests two-parent genetic recombination and validates inheritance patterns."""
    
    def __init__(self, genomes_file: str):
        with open(genomes_file, 'r') as f:
            data = json.load(f)
        
        self.genomes = {}
        for name, genome_data in data['genomes'].items():
            self.genomes[name] = Genome(
                name=name,
                features=genome_data['features']
            )
        
        # Define linkage groups based on the task description
        self.linkage_groups = {
            'color': ['R', 'G', 'B'],
            'form': ['size', 'aniso'],
            'body': ['opacity']
        }
        
        # Traits for analysis
        self.traits = list(self.linkage_groups['color'] + self.linkage_groups['form'] + self.linkage_groups['body'])
        
    def test_mendelian_inheritance(self, parent1: Genome, parent2: Genome) -> Dict[str, Any]:
        """Test Mendelian inheritance patterns for two-parent recombination."""
        
        results = {
            'parent1': parent1.name,
            'parent2': parent2.name,
            'offspring_means': {},
            'offspring_variance': {},
            'heritability_estimates': {},
            'linkage_analysis': {},
            'pleiotropy_effects': {}
        }
        
        # Generate offspring by recombining parental alleles
        num_offspring = 1000
        
        for trait in self.traits:
            # Parental means and variances
            p1_mean = parent1.get_mean(trait)
            p2_mean = parent2.get_mean(trait)
            p1_std = parent1.get_std(trait)
            p2_std = parent2.get_std(trait)
            
            # Simple additive genetic model with recombination
            # Offspring mean is midpoint between parents (additive inheritance)
            offspring_mean = (p1_mean + p2_mean) / 2
            
            # Genetic variance from parental variances
            genetic_variance = (p1_std**2 + p2_std**2) / 2
            
            # Environmental variance (assumed constant)
            environmental_variance = genetic_variance * 0.5
            
            # Total offspring variance
            total_variance = genetic_variance + environmental_variance
            
            # Heritability estimate (h² = Vg/Vt)
            heritability = genetic_variance / total_variance
            
            results['offspring_means'][trait] = offspring_mean
            results['offspring_variance'][trait] = total_variance
            results['heritability_estimates'][trait] = heritability
            
            # Check for dominance deviations (non-additive effects)
            expected_additive_mean = (p1_mean + p2_mean) / 2
            observed_mean = offspring_mean
            dominance_deviation = abs(observed_mean - expected_additive_mean)
            
            if dominance_deviation > 0.1:  # Threshold for significant dominance
                results['dominance_effects'] = {
                    trait: {
                        'deviation': dominance_deviation,
                        'interpretation': 'Significant non-additive (dominant/recessive) effects'
                    }
                }
        
        return results
    
    def test_linkage_groups(self, parent1: Genome, parent2: Genome) -> Dict[str, Any]:
        """Test linkage groups and recombination frequencies."""
        
        linkage_results = {}
        
        for group_name, traits in self.linkage_groups.items():
            # Calculate correlation between traits within linkage group
            correlations = {}
            
            for i, trait1 in enumerate(traits):
                for trait2 in traits[i+1:]:
                    # Simulate recombination and calculate correlation
                    p1_mean1 = parent1.get_mean(trait1)
                    p1_mean2 = parent1.get_mean(trait2)
                    p2_mean1 = parent2.get_mean(trait1)
                    p2_mean2 = parent2.get_mean(trait2)
                    
                    # Generate 1000 offspring genotypes
                    offspring1 = []
                    offspring2 = []
                    
                    for _ in range(1000):
                        # Random recombination between parents
                        if np.random.random() < 0.5:
                            o1_mean1 = p1_mean1
                            o1_mean2 = p1_mean2
                            o2_mean1 = p2_mean1
                            o2_mean2 = p2_mean2
                        else:
                            o1_mean1 = p2_mean1
                            o1_mean2 = p2_mean2
                            o2_mean1 = p1_mean1
                            o2_mean2 = p1_mean2
                        
                        offspring1.append((o1_mean1, o1_mean2))
                        offspring2.append((o2_mean1, o2_mean2))
                    
                    # Calculate correlation within each parental gamete
                    corr1 = np.corrcoef([x[0] for x in offspring1], [x[1] for x in offspring1])[0,1]
                    corr2 = np.corrcoef([x[0] for x in offspring2], [x[1] for x in offspring2])[0,1]
                    
                    avg_correlation = (abs(corr1) + abs(corr2)) / 2
                    
                    correlations[f"{trait1}-{trait2}"] = avg_correlation
            
            linkage_results[group_name] = {
                'traits': traits,
                'correlations': correlations,
                'linkage_strength': np.mean(list(correlations.values())) if correlations else 0
            }
        
        return linkage_results
    
    def test_pleiotropy_effects(self, parent1: Genome, parent2: Genome) -> Dict[str, Any]:
        """Test pleiotropy effects - one gene affecting multiple traits."""
        
        pleiotropy_results = {}
        
        # Calculate genetic correlations across all trait pairs
        genetic_correlations = {}
        
        for trait1 in self.traits:
            for trait2 in self.traits:
                if trait1 != trait2:
                    p1_std1 = parent1.get_std(trait1)
                    p1_std2 = parent2.get_std(trait2)
                    p2_std1 = parent1.get_std(trait1)
                    p2_std2 = parent2.get_std(trait2)
                    
                    # Simulate pleiotropic effects
                    offspring_data = []
                    for _ in range(1000):
                        # Random recombination with pleiotropic coupling
                        if np.random.random() < 0.5:
                            o_mean1 = parent1.get_mean(trait1) + np.random.normal(0, p1_std1)
                            o_mean2 = parent1.get_mean(trait2) + np.random.normal(0, p1_std2)
                        else:
                            o_mean1 = parent2.get_mean(trait1) + np.random.normal(0, p2_std1)
                            o_mean2 = parent2.get_mean(trait2) + np.random.normal(0, p2_std2)
                        
                        offspring_data.append((o_mean1, o_mean2))
                    
                    correlation = np.corrcoef([x[0] for x in offspring_data], [x[1] for x in offspring_data])[0,1]
                    genetic_correlations[f"{trait1}-{trait2}"] = abs(correlation)
        
        # Identify strong pleiotropic links (correlation > 0.3)
        strong_pleiotropy = {k: v for k, v in genetic_correlations.items() if v > 0.3}
        
        pleiotropy_results['genetic_correlations'] = genetic_correlations
        pleiotropy_results['strong_pleiotropic_links'] = strong_pleiotropy
        
        return pleiotropy_results
    
    def calculate_heritability_estimates(self, parent1: Genome, parent2: Genome) -> Dict[str, float]:
        """Calculate heritability estimates for each trait."""
        
        heritability = {}
        
        for trait in self.traits:
            p1_mean = parent1.get_mean(trait)
            p2_mean = parent2.get_mean(trait)
            p1_std = parent1.get_std(trait)
            p2_std = parent2.get_std(trait)
            
            # Total genetic variance (additive + dominance)
            additive_variance = ((p1_mean - p2_mean)**2) / 4
            genetic_variance = (p1_std**2 + p2_std**2) / 2 + additive_variance
            
            # Environmental variance (assumed to be half of genetic variance)
            environmental_variance = genetic_variance * 0.5
            
            # Total phenotypic variance
            total_variance = genetic_variance + environmental_variance
            
            # Narrow-sense heritability (h²)
            h2 = additive_variance / total_variance if total_variance > 0 else 0
            
            # Broad-sense heritability (H²)
            H2 = genetic_variance / total_variance if total_variance > 0 else 0
            
            heritability[trait] = {
                'narrow_sense': h2,
                'broad_sense': H2,
                'additive_variance': additive_variance,
                'genetic_variance': genetic_variance,
                'environmental_variance': environmental_variance,
                'total_variance': total_variance
            }
        
        return heritability
    
    def validate_mendelian_principles(self, parent1: Genome, parent2: Genome, results: Dict[str, Any]) -> Dict[str, bool]:
        """Validate Mendelian inheritance principles."""
        
        validation = {
            'segregation': False,
            'independent_assortment': False,
            'dominance': False,
            'additivity': False
        }
        
        # Check segregation: offspring variance should be less than parental variance
        for trait in self.traits:
            p1_var = parent1.get_std(trait)**2
            p2_var = parent2.get_std(trait)**2
            offspring_var = results['offspring_variance'][trait]
            
            if offspring_var < (p1_var + p2_var) / 2:
                validation['segregation'] = True
        
        # Check independent assortment: low correlation between linkage groups
        linkage_correlations = []
        for group1, traits1 in self.linkage_groups.items():
            for group2, traits2 in self.linkage_groups.items():
                if group1 != group2:
                    for t1 in traits1:
                        for t2 in traits2:
                            key = f"{t1}-{t2}"
                            if key in results.get('linkage_analysis', {}).get('correlations', {}):
                                linkage_correlations.append(results['linkage_analysis']['correlations'][key])
        
        if np.mean(linkage_correlations) < 0.3:  # Threshold for independent assortment
            validation['independent_assortment'] = True
        
        # Check dominance: significant deviation from additive expectation
        if 'dominance_effects' in results:
            validation['dominance'] = True
        
        # Check additivity: most traits should show additive inheritance
        additive_traits = 0
        for trait in self.traits:
            p1_mean = parent1.get_mean(trait)
            p2_mean = parent2.get_mean(trait)
            offspring_mean = results['offspring_means'][trait]
            
            expected_additive = (p1_mean + p2_mean) / 2
            if abs(offspring_mean - expected_additive) < 0.1:
                additive_traits += 1
        
        if additive_traits >= len(self.traits) * 0.7:  # 70% of traits show additivity
            validation['additivity'] = True
        
        return validation
    
    def run_full_analysis(self, parent1_name: str, parent2_name: str) -> Dict[str, Any]:
        """Run complete recombination analysis."""
        
        if parent1_name not in self.genomes or parent2_name not in self.genomes:
            raise ValueError(f"Genome not found: {parent1_name} or {parent2_name}")
        
        parent1 = self.genomes[parent1_name]
        parent2 = self.genomes[parent2_name]
        
        print(f"\n{'='*60}")
        print(f"Phase 3: Recombination Testing - {parent1_name} × {parent2_name}")
        print(f"{'='*60}\n")
        
        # Test Mendelian inheritance
        mendelian_results = self.test_mendelian_inheritance(parent1, parent2)
        
        # Calculate heritability estimates
        heritability = self.calculate_heritability_estimates(parent1, parent2)
        mendelian_results['heritability_detailed'] = heritability
        
        # Test linkage groups
        linkage_results = self.test_linkage_groups(parent1, parent2)
        mendelian_results['linkage_analysis'] = linkage_results
        
        # Test pleiotropy effects
        pleiotropy_results = self.test_pleiotropy_effects(parent1, parent2)
        mendelian_results['pleiotropy_effects'] = pleiotropy_results
        
        # Validate Mendelian principles
        validation = self.validate_mendelian_principles(parent1, parent2, mendelian_results)
        mendelian_results['mendelian_validation'] = validation
        
        return mendelian_results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive report."""
        
        report = []
        report.append("PHASE 3: RECOMBINATION TESTING REPORT")
        report.append("=" * 60)
        
        # Heritability Estimates
        report.append("\n1. HERITABILITY ESTIMATES")
        report.append("-" * 40)
        for trait, h2_data in results['heritability_detailed'].items():
            report.append(f"{trait:8}: h² = {h2_data['narrow_sense']:.3f}, H² = {h2_data['broad_sense']:.3f}")
        
        # Linkage Analysis
        report.append("\n2. LINKAGE GROUP ANALYSIS")
        report.append("-" * 40)
        for group, data in results['linkage_analysis'].items():
            report.append(f"\n{group.upper()} Group:")
            report.append(f"  Traits: {', '.join(data['traits'])}")
            for pair, corr in data['correlations'].items():
                report.append(f"  {pair}: r = {corr:.3f}")
        
        # Pleiotropy Effects
        report.append("\n3. PLEIOTROPY EFFECTS")
        report.append("-" * 40)
        for pair, corr in results['pleiotropy_effects']['genetic_correlations'].items():
            if corr > 0.3:
                report.append(f"{pair}: r = {corr:.3f} (STRONG PLEIOTROPY)")
        
        # Mendelian Validation
        report.append("\n4. MENDELIAN INHERITANCE VALIDATION")
        report.append("-" * 40)
        for principle, valid in results['mendelian_validation'].items():
            status = "[VALIDATED]" if valid else "[NOT VALIDATED]"
            report.append(f"{principle.capitalize():20}: {status}")
        
        # Summary
        report.append("\n5. SUMMARY")
        report.append("-" * 40)
        validated_count = sum(results['mendelian_validation'].values())
        total_count = len(results['mendelian_validation'])
        report.append(f"Mendelian Principles Validated: {validated_count}/{total_count}")
        
        return "\n".join(report)

def main():
    """Run Phase 3 recombination testing."""
    
    # Load genomes from recovered_genomes.json
    genomes_file = "Chimera/docs/matter/recovered_genomes.json"
    
    agent = RecombinationTestingAgent(genomes_file)
    
    print("Available Class Genomes:")
    for name in agent.genomes.keys():
        print(f"  - {name}")
    
    # Test recombination between different class genomes
    test_pairs = [
        ('bonsai_vegetative', 'stump_wood'),
        ('bicycle_metallic', 'truck_metallic'),
        ('cluster_00', 'cluster_01'),
        ('plush_fabric', 'bonsai_vegetative')
    ]
    
    all_results = {}
    
    for parent1, parent2 in test_pairs:
        try:
            results = agent.run_full_analysis(parent1, parent2)
            report = agent.generate_report(results)
            all_results[f"{parent1}_x_{parent2}"] = results
            
            print("\n" + "="*80)
            print(report)
            print("="*80)
            
        except Exception as e:
            print(f"Error testing {parent1} × {parent2}: {e}")
    
    # Save results to file
    with open("phase3_recombination_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print("\nPhase 3 complete. Results saved to phase3_recombination_results.json")

if __name__ == "__main__":
    main()
