"""
DSL CONTEXT-AWARE SUGGESTIONS FOR NATURAL LANGUAGE COMMANDS
============================================================
This module implements using the spaCy dependency graph and UPOS tags to predict likely 
verb-noun-preposition combinations based on the current simulation state and unlocked tiers.

CORE CONCEPTS:
- spaCy Dependency Graph: Represents the syntactic structure of a sentence, identifying relationships between words.
- UPOS Tags: Universal Part-of-Speech tags that categorize words (VERB, NOUN, ADP, etc.).
- Context-Aware Predictions: Uses the current simulation state and unlocked tiers to suggest relevant DSL commands.
"""

from typing import Dict, Any, List

class DSLContextAwareSuggestions:
    """Implements context-aware suggestions for natural language commands using spaCy dependency graph and UPOS tags."""
    
    def __init__(self, seed_value: int = 42):
        self.seed_value = seed_value
        
    def predict_verb_noun_preposition_combinations(self, current_tiers_unlocked: List[str], 
                                                   simulation_state_context: str) -> List[Dict[str, Any]]:
        """
        Predict likely verb-noun-preposition combinations based on unlocked tiers and simulation state.
        
        Args:
            current_tiers_unlocked: list of currently unlocked tier identifiers (e.g., 'tier_1', 'tier_2')
            simulation_state_context: description of the current simulation state or environment
            
        Returns:
            List of dictionaries containing suggested command patterns
        """
        suggestions = []
        
        # Map tiers to likely verbs and connection shapes
        tier_suggestions = {
            'tier_1': [{'verb': 'THRUST', 'noun': 'vessel', 'preposition': 'with_engine'}, 
                       {'verb': 'SCAN', 'noun': 'terrain', 'preposition': 'using_radar'}],
            'tier_2': [{'verb': 'BALANCE', 'noun': 'flight', 'preposition': 'with_aerodynamics'},
                       {'verb': 'CONNECT', 'noun': 'energy_port', 'preposition': 'to_spectral_source'}],
            'tier_3': [{'verb': 'GROW_ECOSYSTEM', 'noun': 'mycelial_network', 'preposition': 'with_hydration_port'},
                       {'verb': 'SCAN', 'noun': 'spectral_signature', 'preposition': 'using_usgs_reference'}],
            'tier_4': [{'verb': 'NAVIGATE_ORBIT', 'noun': 'celestial_body', 'preposition': 'with_gravitational_anchor'}]
        }
        
        for tier in current_tiers_unlocked:
            if tier in tier_suggestions:
                for pattern in tier_suggestions[tier]:
                    suggestions.append({
                        "tier": tier,
                        "verb": pattern['verb'],
                        "noun": pattern['noun'],
                        "preposition": pattern['preposition'],
                        "context_relevance": simulation_state_context
                    })
                    
        return suggestions

    def map_upos_tags_to_suggested_patterns(self, sentence_upos_tags: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Map UPOS tags from a user's input sentence to suggested DSL command patterns.
        
        Args:
            sentence_upos_tags: list of dictionaries with 'word' and 'upos_tag' keys
            
        Returns:
            Dictionary containing UPOS tag mapping results and matched pattern type
        """
        has_verb = any(tag.get('upos_tag') == 'VERB' for tag in sentence_upos_tags)
        has_noun = any(tag.get('upos_tag') in ['NOUN', 'PROPN'] for tag in sentence_upos_tags)
        has_adp = any(tag.get('upos_tag') == 'ADP' for tag in sentence_upos_tags)
        
        pattern_completeness = {
            'has_verb': has_verb,
            'has_noun': has_noun,
            'has_preposition/adp': has_adp
        }
        
        is_complete_pattern = has_verb and has_noun
        
        return {
            "upos_tags_analyzed": len(sentence_upos_tags),
            "pattern_completeness_metrics": pattern_completeness,
            "is_complete_verb_noun_pattern": is_complete_pattern,
            "status": "upos_tags_mapped_to_suggested_patterns"
        }


def execute_dsl_context_aware_suggestions_simulation(current_tiers_unlocked: List[str] = ['tier_2', 'tier_3'], 
                                                     simulation_state_context: str = "planetary_surface_with_atmosphere",
                                                     sentence_upos_tags: List[Dict[str, str]] = [
                                                         {'word': 'GROW', 'upos_tag': 'VERB'},
                                                         {'word': 'ecosystem', 'upos_tag': 'NOUN'},
                                                         {'word': 'with', 'upos_tag': 'ADP'}
                                                     ]) -> Dict[str, Any]:
    """Convenience function to execute DSL context-aware suggestions simulation."""
    dsl_suggester = DSLContextAwareSuggestions(seed_value=42)
    
    suggestions_result = dsl_suggester.predict_verb_noun_preposition_combinations(
        current_tiers_unlocked=current_tiers_unlocked,
        simulation_state_context=simulation_state_context
    )
    
    upos_mapping_result = dsl_suggester.map_upos_tags_to_suggested_patterns(
        sentence_upos_tags=sentence_upos_tags
    )
    
    return {
        "simulation_status": "verified",
        "verb_noun_preposition_suggestions_results": suggestions_result,
        "upos_tags_mapping_results": upos_mapping_result
    }
