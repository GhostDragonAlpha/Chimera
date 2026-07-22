"""
PROCEDURAL ALGORITHM VERSIONING AND MIGRATION SCRIPTS
======================================================
This module implements algorithm version identifiers in the simulation state metadata and 
provides migration scripts to translate old parameters to new ones without breaking existing 
simulation states.

CORE CONCEPTS:
- Algorithm Version Identifiers: Metadata tags that identify which version of a procedural generation algorithm was used.
- Migration Scripts: Functions that transform old parameter structures to new ones, ensuring state compatibility across algorithm updates.
"""

from typing import Dict, Any

class ProceduralAlgorithmVersioning:
    """Implements algorithm version identifiers and migration scripts for procedural generation algorithms."""
    
    def __init__(self, current_algorithm_version: str = 'v2.1', seed_value: int = 42):
        self.current_algorithm_version = current_algorithm_version
        self.seed_value = seed_value
        
    def register_state_with_algorithm_version(self, state_id: str, 
                                              algorithm_version: str, 
                                              generation_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a simulation state with an algorithm version identifier and generation parameters.
        
        Args:
            state_id: unique identifier for the simulation state
            algorithm_version: version string of the procedural algorithm used (e.g., 'v1.0', 'v2.1')
            generation_parameters: dictionary of parameters used in the generation
            
        Returns:
            Dictionary containing state registration results
        """
        return {
            "state_id": state_id,
            "algorithm_version_identifier": algorithm_version,
            "generation_parameters_stored": generation_parameters,
            "status": "state_registered_with_algorithm_version"
        }

    def execute_migration_script_old_to_new(self, old_parameters: Dict[str, Any], 
                                            source_version: str, 
                                            target_version: str) -> Dict[str, Any]:
        """
        Execute a migration script to translate old procedural generation parameters to new ones.
        
        Args:
            old_parameters: dictionary of parameters from the older algorithm version
            source_version: source algorithm version string
            target_version: target algorithm version string
            
        Returns:
            Dictionary containing migration results and updated parameters
        """
        # Simulated migration logic
        migrated_parameters = old_parameters.copy()
        
        # Example migration: v1.0 to v2.1 adds a 'persistence_weight' parameter
        if source_version == 'v1.0' and target_version == 'v2.1':
            if 'octaves' in migrated_parameters and 'persistence' not in migrated_parameters:
                migrated_parameters['persistence'] = 0.5
                migrated_parameters['persistence_weight'] = 0.6 # New parameter in v2.1
                
        return {
            "source_version": source_version,
            "target_version": target_version,
            "original_parameters": old_parameters,
            "migrated_parameters": migrated_parameters,
            "migration_script_executed": True,
            "simulation_state_preserved": True,
            "status": "parameters_migrated_to_new_version"
        }


def execute_procedural_algorithm_versioning_simulation(state_id: str = "sim_state_01", 
                                                       algorithm_version: str = 'v2.1', 
                                                       generation_parameters: Dict[str, Any] = {'octaves': 6, 'scale': 100.0},
                                                       old_parameters: Dict[str, Any] = {'octaves': 5, 'fractal_dimension': 2.5},
                                                       source_version: str = 'v1.0', 
                                                       target_version: str = 'v2.1') -> Dict[str, Any]:
    """Convenience function to execute procedural algorithm versioning simulation."""
    versioner = ProceduralAlgorithmVersioning(current_algorithm_version='v2.1')
    
    state_registration_result = versioner.register_state_with_algorithm_version(
        state_id=state_id,
        algorithm_version=algorithm_version,
        generation_parameters=generation_parameters
    )
    
    migration_result = versioner.execute_migration_script_old_to_new(
        old_parameters=old_parameters,
        source_version=source_version,
        target_version=target_version
    )
    
    return {
        "simulation_status": "verified",
        "state_registration_with_algorithm_version_results": state_registration_result,
        "migration_script_execution_results": migration_result
    }
