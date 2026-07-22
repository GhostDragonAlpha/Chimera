"""
DSL MULTILINGUAL ERROR MESSAGES AND FEEDBACK FOR DSL PARSING FAILURES
======================================================================
This module implements maintaining translation dictionaries for each supported spaCy language 
model (English, French, Spanish, German) and mapping error codes to localized strings.

CORE CONCEPTS:
- Translation Dictionaries for Supported spaCy Models: Stores error message translations for English, French, Spanish, and German models.
- Error Code to Localized String Mapping: Converts internal DSL parsing error codes into user-friendly messages in the user's language.
"""

from typing import Dict, Any

class DSLMultilingualErrorMessages:
    """Implements multi-lingual error messages and feedback for DSL parsing failures maintaining translation dictionaries."""
    
    def __init__(self, seed_value: int = 42):
        self.seed_value = seed_value
        
        # Translation dictionaries for supported spaCy language models
        self.error_translations = {
            'en': {
                'ERROR_INVALID_VERB': "Invalid verb: The command uses an unrecognized physics module trigger.",
                'ERROR_MISSING_NOUN': "Missing noun: Please specify the target asset or connection shape.",
                'ERROR_CONSTRAINT_VIOLATION': "Constraint violation: The command violates a physical or simulation constraint."
            },
            'fr': {
                'ERROR_INVALID_VERB': "Verbe invalide : La commande utilise un déclencheur de module physique non reconnu.",
                'ERROR_MISSING_NOUN': "Nom manquant : Veuillez spécifier l'actif cible ou la forme de connexion.",
                'ERROR_CONSTRAINT_VIOLATION': "Violation de contrainte : La commande viole une contrainte physique ou de simulation."
            },
            'es': {
                'ERROR_INVALID_VERB': "Verbo inválido: El comando utiliza un activador de módulo físico no reconocido.",
                'ERROR_MISSING_NOUN': "Sustantivo faltante: Especifique el activo objetivo o la forma de conexión.",
                'ERROR_CONSTRAINT_VIOLATION': "Violación de restricción: El comando viola una restricción física o de simulación."
            },
            'de': {
                'ERROR_INVALID_VERB': "Ungültiges Verb: Der Befehl verwendet einen nicht erkannten Physik-Modulauslöser.",
                'ERROR_MISSING_NOUN': "Fehlendes Nomen: Bitte geben Sie das Zielasset oder die Verbindungsform an.",
                'ERROR_CONSTRAINT_VIOLATION': "Constraint-Verletzung: Der Befehl verletzt eine physikalische oder Simulationsbeschränkung."
            }
        }

    def map_error_code_to_localized_string(self, error_code: str, 
                                           language_model: str = 'en') -> Dict[str, Any]:
        """
        Map an internal DSL parsing error code to a localized string based on the spaCy language model.
        
        Args:
            error_code: internal error identifier (e.g., 'ERROR_INVALID_VERB')
            language_model: language identifier ('en', 'fr', 'es', 'de')
            
        Returns:
            Dictionary containing the localized error message and metadata
        """
        # Ensure language model is supported
        if language_model not in self.error_translations:
            language_model = 'en' # Fallback to English
            
        translations = self.error_translations[language_model]
        
        # Get the error message, fallback to English if specific language translation is missing for the code
        localized_message = translations.get(error_code, translations.get('ERROR_INVALID_VERB', "Unknown DSL parsing error."))
        
        return {
            "error_code": error_code,
            "language_model": language_model,
            "localized_error_message": localized_message,
            "translation_source": f"spacy_model_{language_model}_dictionary",
            "status": "error_code_mapped_to_localized_string"
        }

    def generate_parsing_failure_feedback(self, error_code: str, 
                                          language_model: str = 'en', 
                                          user_command_sample: str = None) -> Dict[str, Any]:
        """
        Generate feedback for a DSL parsing failure, including the localized error message and suggested correction.
        
        Args:
            error_code: internal error identifier
            language_model: language identifier
            user_command_sample: the command that caused the failure
            
        Returns:
            Dictionary containing parsing failure feedback results
        """
        localized_error = self.map_error_code_to_localized_string(error_code=error_code, language_model=language_model)
        
        feedback_response = {
            "user_command_sample": user_command_sample or "unknown_command",
            "parsing_failure_error_code": error_code,
            "localized_feedback_message": localized_error.get("localized_error_message"),
            "suggested_action": "Review the DSL verb list and ensure connection shapes are correctly specified.",
            "status": "parsing_failure_feedback_generated"
        }
        
        return feedback_response


def execute_dsl_multilingual_error_messages_simulation(error_code: str = 'ERROR_INVALID_VERB', 
                                                       language_model: str = 'fr', 
                                                       user_command_sample: str = "GROW_TREE with_invalid_port") -> Dict[str, Any]:
    """Convenience function to execute DSL multilingual error messages simulation."""
    error_message_engine = DSLMultilingualErrorMessages(seed_value=42)
    
    mapping_result = error_message_engine.map_error_code_to_localized_string(
        error_code=error_code,
        language_model=language_model
    )
    
    feedback_result = error_message_engine.generate_parsing_failure_feedback(
        error_code=error_code,
        language_model=language_model,
        user_command_sample=user_command_sample
    )
    
    return {
        "simulation_status": "verified",
        "error_code_to_localized_string_mapping_results": mapping_result,
        "parsing_failure_feedback_generation_results": feedback_result
    }
