"""
Chimera Engine: Hierarchical Membrane System

Implements hierarchical membranes for 3D Gaussian splat data labeling.
Hierarchy levels:
  Level 1: Object/Scene (e.g., "Oak Tree", "Garden Scene")
  Level 2: Major Component (e.g., "Trunk/Bark", "Canopy/Leaves", "Branches")
  Level 3: Specific Pattern Membrane (e.g., "bark_oak_rough", "leaves_deciduous_green_cluster")

Core Principle: Computational Irreducibility
- Labels emerge from pattern clustering through direct visual observation
- Hierarchy reflects the physical and game development structure of objects
"""

import numpy as np
from typing import Dict, List, Optional

class HierarchicalMembraneSystem:
    """
    Manages hierarchical membranes with parent-child relationships.
    """
    
    # Hierarchy levels
    LEVEL_OBJECT = "object"       # Level 1: Whole object/scene (e.g., Oak Tree)
    LEVEL_COMPONENT = "component" # Level 2: Major component (e.g., Trunk/Bark, Canopy/Leaves)
    LEVEL_SUBCOMPONENT = "sub-component" # Level 3: Specific pattern instance (e.g., bark_oak_rough)
    
    def __init__(self):
        self.membranes: Dict[str, Dict] = {}
        self.hierarchy: Dict[str, Dict] = {}
        self.serial_counter = 0
        
    def create_membrane(self, label: str, level: str = LEVEL_COMPONENT, parent_serial: Optional[str] = None) -> str:
        """
        Create a new membrane with hierarchical context.
        
        Args:
            label: Descriptive label for the membrane
            level: Hierarchy level (object, component, sub-component)
            parent_serial: Serial number of the parent membrane
            
        Returns:
            Serial number in MEM-000xxx format
        """
        self.serial_counter += 1
        serial = f"MEM-{self.serial_counter:06d}"
        
        membrane_data = {
            'serial': serial,
            'label': label,
            'level': level,
            'parent_serial': parent_serial,
            'children_serials': [],
            'patterns': {},
            'created_at': self.serial_counter
        }
        
        self.membranes[serial] = membrane_data
        
        # Setup hierarchy links
        if serial not in self.hierarchy:
            self.hierarchy[serial] = {
                'parent': parent_serial,
                'children': []
            }
            
        if parent_serial and parent_serial in self.hierarchy:
            self.hierarchy[parent_serial]['children'].append(serial)
            
        return serial
    
    def add_pattern_to_membrane(self, membrane_serial: str, pattern_data: Dict):
        """Add visual patterns to a specific membrane."""
        if membrane_serial in self.membranes:
            if 'patterns' not in self.membranes[membrane_serial]:
                self.membranes[membrane_serial]['patterns'] = {}
            self.membranes[membrane_serial]['patterns'].update(pattern_data)
            
    def get_membrane_hierarchy(self, membrane_serial: str) -> List[str]:
        """Get the full hierarchy path for a given membrane."""
        path = []
        current = membrane_serial
        
        while current and current in self.hierarchy:
            path.append(current)
            parent = self.hierarchy[current]['parent']
            if not parent or parent not in self.hierarchy:
                break
            current = parent
            
        return path[::-1] # Return from root to leaf
    
    def get_sub_membranes(self, membrane_serial: str) -> List[str]:
        """Get all child membranes of a given membrane."""
        if membrane_serial in self.hierarchy:
            return self.hierarchy[membrane_serial]['children']
        return []
    
    def get_hierarchy_summary(self) -> Dict:
        """Get a summary of the hierarchical membrane system."""
        summary = {
            'total_membranes': self.serial_counter,
            'levels': {
                self.LEVEL_OBJECT: 0,
                self.LEVEL_COMPONENT: 0,
                self.LEVEL_SUBCOMPONENT: 0
            },
            'root_membranes': []
        }
        
        for serial, data in self.membranes.items():
            level = data.get('level', 'unknown')
            if level in summary['levels']:
                summary['levels'][level] += 1
                
            if not data.get('parent_serial'):
                summary['root_membranes'].append(serial)
                
        return summary

# Example usage demonstrating hierarchical membranes
def demonstrate_hierarchical_membranes():
    """Demonstrate the hierarchical membrane system."""
    print("=" * 60)
    print("CHIMERA ENGINE: UNIVERSAL HIERARCHICAL MEMBRANE SYSTEM")
    print("=" * 60)
    
    hms = HierarchicalMembraneSystem()
    
    # Level 1: Object/Scene - Biology
    print("\n[1] Creating Biological Object Membranes:")
    oak_tree_obj = hms.create_membrane("Quercus alba (White Oak)", level=hms.LEVEL_OBJECT)
    print(f"  Created: {oak_tree_obj} -> 'Quercus alba (White Oak)' (Object - Biology)")
    
    # Level 1: Object/Scene - Cosmology
    print("\n[2] Creating Cosmological Object Membranes:")
    spiral_galaxy_obj = hms.create_membrane("Spiral Galaxy System", level=hms.LEVEL_OBJECT)
    print(f"  Created: {hms.membranes[list(hms.membranes.keys())[-1]]['serial']} -> 'Spiral Galaxy System' (Object - Cosmology)")
    
    planetary_ring_obj = hms.create_membrane("Planetary Ring System", level=hms.LEVEL_OBJECT)
    print(f"  Created: {hms.membranes[list(hms.membranes.keys())[-1]]['serial']} -> 'Planetary Ring System' (Object - Cosmology)")
    
    nebula_cloud_obj = hms.create_membrane("Nebula Gas Cloud", level=hms.LEVEL_OBJECT)
    print(f"  Created: {hms.membranes[list(hms.membranes.keys())[-1]]['serial']} -> 'Nebula Gas Cloud' (Object - Cosmology)")
    
    # Level 2: Major Components - Biology
    print("\n[3] Creating Biological Component Membranes:")
    trunk_bark_cmp = hms.create_membrane("Trunk/Bark", level=hms.LEVEL_COMPONENT, parent_serial=oak_tree_obj)
    print(f"  Created: {trunk_bark_cmp} -> 'Trunk/Bark' (Component, parent: {oak_tree_obj})")
    
    canopy_leaves_cmp = hms.create_membrane("Canopy/Leaves", level=hms.LEVEL_COMPONENT, parent_serial=oak_tree_obj)
    print(f"  Created: {canopy_leaves_cmp} -> 'Canopy/Leaves' (Component, parent: {oak_tree_obj})")
    
    # Level 3: Specific Pattern Membranes - Biology
    print("\n[4] Creating Biological Sub-Component Membranes:")
    bark_quercus_alba_mem = hms.create_membrane("bark_quercus_alba_gray_scaly_fissures", level=hms.LEVEL_SUBCOMPONENT, parent_serial=trunk_bark_cmp)
    print(f"  Created: {bark_quercus_alba_mem} -> 'bark_quercus_alba_gray_scaly_fissures' (Sub-component, parent: {trunk_bark_cmp})")
    print(f"    Visual patterns: pale gray color, squarish fissures, slightly shaggy small plates, vertical longitudinal furrows")

    leaves_quercus_rubra_mem = hms.create_membrane("leaves_quercus_rubra_deciduous_pointed_bristle_tipped_lobes", level=hms.LEVEL_SUBCOMPONENT, parent_serial=canopy_leaves_cmp)
    print(f"  Created: {leaves_quercus_rubra_mem} -> 'leaves_quercus_rubra_deciduous_pointed_bristle_tipped_lobes' (Sub-component, parent: {canopy_leaves_cmp})")
    
    # Level 3: Specific Pattern Membranes - Cosmology
    print("\n[5] Creating Cosmological Sub-Component Membranes:")
    spiral_arm_mem = hms.create_membrane("astro_spiral_arm_density_wave_logarithmic_spiral_pattern", level=hms.LEVEL_SUBCOMPONENT, parent_serial=list(hms.hierarchy.keys())[2]) # spiral_galaxy_obj
    print(f"  Created: {spiral_arm_mem} -> 'astro_spiral_arm_density_wave_logarithmic_spiral_pattern' (Sub-component - Messier 81 HST)")
    
    ring_gap_mem = hms.create_membrane("astro_ring_particle_cassini_division_gap_density_wave", level=hms.LEVEL_SUBCOMPONENT, parent_serial=list(hms.hierarchy.keys())[3]) # planetary_ring_obj
    print(f"  Created: {ring_gap_mem} -> 'astro_ring_particle_cassini_division_gap_density_wave' (Sub-component - Saturn Cassini)")
    
    nebula_emission_mem = hms.create_membrane("astro_nebula_emission_h_ii_region_ionized_gas_distribution", level=hms.LEVEL_SUBCOMPONENT, parent_serial=list(hms.hierarchy.keys())[4]) # nebula_cloud_obj
    print(f"  Created: {nebula_emission_mem} -> 'astro_nebula_emission_h_ii_region_ionized_gas_distribution' (Sub-component - Orion Nebula Hubble)")
    
    # Add patterns to sub-component membranes
    hms.add_pattern_to_membrane(bark_quercus_alba_mem, {'texture_variance': 892.4, 'edge_density': 0.35, 'fissure_depth': 'deep'})
    hms.add_pattern_to_membrane(leaves_quercus_rubra_mem, {'texture_variance': 654.2, 'boundary_area': 0.55, 'lobe_type': 'pointed_bristle_tipped'})
    
    # Get hierarchy summary
    summary = hms.get_hierarchy_summary()
    print("\n[4] Hierarchical Membrane System Summary:")
    print(f"  Total membranes: {summary['total_membranes']}")
    print(f"  Levels distribution: {summary['levels']}")
    print(f"  Root membranes: {summary['root_membranes']}")
    
    # Get hierarchy path for a sub-component membrane
    path = hms.get_membrane_hierarchy(bark_quercus_alba_mem)
    print(f"\n[5] Hierarchy Path for {bark_quercus_alba_mem}:")
    for i, serial in enumerate(path):
        label = hms.membranes[serial]['label']
        level = hms.membranes[serial]['level']
        print(f"  Level {i+1}: [{level}] {serial} -> '{label}'")
        
    print("\n" + "=" * 60)
    print("HIERARCHICAL MEMBRANE SYSTEM ESTABLISHED")
    print("=" * 60)
    print("Principle: Hierarchy reflects the physical and game development structure")
    print("of objects: Object -> Component -> Sub-component/Pattern.")


if __name__ == "__main__":
    demonstrate_hierarchical_membranes()
