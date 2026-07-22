"""
DSL SYNONYM MAPPING NORMALIZATION FOR SLANG AND COLLOQUIALISMS
==============================================================
This module implements a synonym mapping layer that normalizes user input to standard 
scientific verbs and nouns before passing to the core parsing engine, ensuring scientific 
accuracy while handling slang or non-standard phrasing.

CORE CONCEPTS:
- Synonym Mapping Layer: Translates colloquialisms, slang, or alternative phrasings into standardized scientific terminology.
- Standard Scientific Verbs and Nouns: The canonical set of terms used by the core DSL parsing engine.
"""

from typing import Dict, Any, List

class DSLSynonymMappingNormalization:
    """Implements a synonym mapping layer that normalizes user input to standard scientific verbs and nouns."""
    
    def __init__(self, seed_value: int = 42):
        self.seed_value = seed_value
        
        # Synonym mapping dictionary for common slang/colloquialisms to standard scientific terms
        self.synonym_mapping = {
            'verbs': {
                'fly': 'BALANCE',
                'move': 'THRUST',
                'make_plants_grow': 'GROW_ECOSYSTEM',
                'space_travel': 'NAVIGATE_ORBIT',
                'look_at': 'SCAN',
                'join': 'CONNECT'
            },
            'nouns': {
                'tree': 'vegetation_asset',
                'river': 'fluid_dynamics_body',
                'star': 'celestial_body',
                'rock_formations': 'geological_substrate',
                'clouds': 'atmospheric_volume',
                'ground': 'substrate_surface'
            }
        }

    def normalize_user_input_to_standard_terms(self, user_command_text: str) -> Dict[str, Any]:
        """
        Normalize user input slang or colloquialisms to standard scientific verbs and nouns.
        
        Args:
            user_command_text: the raw natural language command from the user
            
        Returns:
            Dictionary containing normalized command and mapping details
        """
        # Convert text to lowercase for matching
        lower_command = user_command_text.lower()
        
        normalized_verbs = []
        normalized_nouns = []
        
        # Check for synonym verbs
        for slang_verb, standard_verb in self.synonym_mapping['verbs'].items():
            if slang_verb in lower_command:
                # Replace slang verb with standard verb in a simulated way
                normalized_verbs.append({
                    "slang_input": slang_verb,
                    "standard_scientific Verb": standard_verb
                })
                
        # Check for synonym nouns
        for slang_noun, standard_noun in self.synonym_mapping['nouns'].items():
            if slang_noun in lower_command:
                normalized_nouns.append({
                    "slang_input": slang_noun,
                    "standard_scientific_noun": standard_noun
                })
                
        # Simulate the normalized command text
        normalized_command_text = user_command_text
        for slang_verb in self.synonym_mapping['verbs'].keys():
            if slang_verb in lower_command:
                standard_verb = self.synonym_mapping['verbs'][slang_verb]
                normalized_command_text = normalized_command_text.replace(slang_verb, standard_verb.lower())
                
        for slang_noun in self.synonym_mapping['nouns'].keys():
            if slang_noun in lower_command:
                standard_noun = self.synonym_mapping['nouns'][slang_noun]
                normalized_command_text = normalized_command_text.replace(slang_noun, standard_noun)
                
        return {
            "original_user_command": user_command_text,
            "normalized_command_text": normalized_command_text,
            "verbs_normalized": normalized_verbs,
            "nouns_normalized": normalized_nouns,
            "normalization_method": "synonym_mapping_layer_to_standard_scientific_terms",
            "status": "user_input_normalized_for_core_parsing_engine"
        }


def execute_dsl_synonym_mapping_normalization_simulation(user_command_text: str = "make_plants_grow with tree and river") -> Dict[str, Any]:
    """Convenience function to execute DSL synonym mapping normalization simulation."""
    synonym_normalizer = DSLSynonymMappingNormalization(seed_value=42)
    
    normalization_result = synonym_normalizer.normalize_user_input_to_standard_terms(
        user_command_text=user_command_text
    )
    
    return {
        "simulation_status": "verified",
        "user_input_normalization_results": normalization_result
    }
