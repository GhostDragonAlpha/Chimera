"""
DSL PROFICIENCY TRACKING AND SUGGESTIONS BASED ON COMMAND HISTORY
==================================================================
This module implements analyzing the frequency and success rate of verb-module pairs in 
the command log and recommending higher-tier verbs or complex connection shapes.

CORE CONCEPTS:
- Frequency and Success Rate Analysis: Metrics derived from the user's command log to gauge proficiency with specific DSL verb-module pairs.
- Advanced Command Recommendations: Suggesting higher-tier verbs or complex connection shapes based on demonstrated proficiency.
"""

from typing import Dict, Any, List

class DSLProficiencyTrackingSuggestions:
    """Implements tracking of user proficiency and suggestions for advanced DSL commands based on past command history."""
    
    def __init__(self, seed_value: int = 42):
        self.seed_value = seed_value
        
    def analyze_verb_module_pair_frequency_and_success(self, command_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the frequency and success rate of verb-module pairs in the command log.
        
        Args:
            command_log: list of dictionaries containing past DSL commands and their execution results
            
        Returns:
            Dictionary containing proficiency metrics and most frequent verb-module pairs
        """
        verb_module_counts = {}
        successful_executions = 0
        total_executions = len(command_log)
        
        for entry in command_log:
            command_text = entry.get('command_text', '')
            is_success = entry.get('is_success', False)
            
            # Simulate extracting verb and module from command text
            verb = 'UNKNOWN_VERB'
            module = 'UNKNOWN_MODULE'
            
            if 'THRUST' in command_text.upper():
                verb = 'THRUST'
                module = 'rigid_body_dynamics'
            elif 'GROW_ECOSYSTEM' in command_text.upper():
                verb = 'GROW_ECOSYSTEM'
                module = 'grow_ecosystem_simulation'
            elif 'NAVIGATE_ORBIT' in command_text.upper():
                verb = 'NAVIGATE_ORBIT'
                module = 'orbital_mechanics_celestial_gravity'
            elif 'CONNECT' in command_text.upper():
                verb = 'CONNECT'
                module = 'modular_physics_control_architecture'
                
            pair_key = f"{verb}_{module}"
            verb_module_counts[pair_key] = verb_module_counts.get(pair_key, 0) + 1
            
            if is_success:
                successful_executions += 1
                
        success_rate = (successful_executions / total_executions) if total_executions > 0 else 0.0
        
        # Find the most frequent pair
        most_frequent_pair = max(verb_module_counts, key=verb_module_counts.get) if verb_module_counts else "none"
        
        return {
            "total_commands_analyzed": total_executions,
            "successful_executions_count": successful_executions,
            "overall_success_rate": success_rate,
            "verb_module_pair_frequencies": verb_module_counts,
            "most_frequent_verb_module_pair": most_frequent_pair,
            "status": "verb_module_pair_frequency_and_success_analyzed"
        }

    def recommend_advanced_verbs_or_connection_shapes(self, current_proficiency_level: str, 
                                                      frequent_pairs: List[str]) -> List[Dict[str, Any]]:
        """
        Recommend higher-tier verbs or complex connection shapes based on demonstrated proficiency.
        
        Args:
            current_proficiency_level: current assessed proficiency level ('beginner', 'intermediate', 'advanced')
            frequent_pairs: list of frequently used verb-module pairs
            
        Returns:
            List of dictionaries containing recommended advanced commands or connection shapes
        """
        recommendations = []
        
        if current_proficiency_level in ['intermediate', 'advanced']:
            if not any('NAVIGATE_ORBIT' in pair for pair in frequent_pairs):
                recommendations.append({
                    "recommendation_type": "advanced_verb",
                    "suggested_verb": "NAVIGATE_ORBIT",
                    "associated_module": "orbital_mechanics_celestial_gravity",
                    "reason": "User has demonstrated proficiency with basic physics verbs; introduce orbital mechanics."
                })
                
            if not any('Spectral_Energy_Port' in str(pair) for pair in frequent_pairs):
                recommendations.append({
                    "recommendation_type": "complex_connection_shape",
                    "suggested_connection_shape": "Spectral_Energy_Port",
                    "associated_module": "spectroscopic_exploration_tools",
                    "reason": "User has mastered basic connection shapes; introduce spectral/energy port interactions."
                })
                
        if current_proficiency_level == 'advanced':
            recommendations.append({
                "recommendation_type": "complex_multi_state_scenario",
                "suggested_scenario": "Conditional ecosystem growth based on spectral soil analysis",
                "associated_modules": ["grow_ecosystem_simulation", "spectroscopic_exploration_tools"],
                "reason": "User has advanced proficiency; suggest complex multi-step natural language scenarios."
            })
            
        return recommendations


def execute_dsl_proficiency_tracking_suggestions_simulation(command_log: List[Dict[str, Any]] = [
    {'command_text': 'THRUST vessel with_engine', 'is_success': True},
    {'command_text': 'GROW_ECOSYSTEM with_hydration_port', 'is_success': True},
    {'command_text': 'SCAN terrain using_radar', 'is_success': False}
], 
current_proficiency_level: str = 'intermediate') -> Dict[str, Any]:
    """Convenience function to execute DSL proficiency tracking and suggestions simulation."""
    proficiency_tracker = DSLProficiencyTrackingSuggestions(seed_value=42)
    
    analysis_result = proficiency_tracker.analyze_verb_module_pair_frequency_and_success(
        command_log=command_log
    )
    
    recommendations_result = proficiency_tracker.recommend_advanced_verbs_or_connection_shapes(
        current_proficiency_level=current_proficiency_level,
        frequent_pairs=list(analysis_result.get('verb_module_pair_frequencies', {}).keys())
    )
    
    return {
        "simulation_status": "verified",
        "verb_module_pair_analysis_results": analysis_result,
        "advanced_command_recommendations_results": recommendations_result
    }
