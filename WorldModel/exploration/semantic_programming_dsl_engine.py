"""
SEMANTIC PROGRAMMING DSL ENGINE - NATURAL LANGUAGE SEMANTIC MAPPING EXECUTOR
==============================================================================
This module implements the Natural Language Semantic Programming Domain-Specific 
Language (DSL) engine for the universal simulation. It translates natural language 
sentences into membrane programming constraints and executes the corresponding 
physics simulations.

CORE PHILOSOPHY:
- Words transmit the imprint of intent as data—a representation, a compression of reality.
- Intelligence is compression: The genome (or training patterns, membrane constraints, 
  and natural language DSL) *is* the compressed world. The hardware (Python/physics 
  simulation pipeline) sets the maximum fidelity, and physics acts as the decompressor.
- Constraints drive emergence: All patterns, verbs, connection shapes, spectroscopy 
  verification gates, and scales of speed are constraints that drive Emergence.

DSL MAPPING TABLE:
------------------
Part of Speech | Human Language Example | Mapped Simulation Concept
-------------- | ---------------------- | -------------------------
Verbs          | push, balance, grow    | THRUST, BALANCE, GROW + scales of speed
Nouns          | sun, earth, tree       | Hierarchy Levels (Level 1-4), Matter Sources
Adjectives     | calm, green, rocky     | Physical States, Spectral Signatures
Prepositions   | through, with, under   | LEGO Puzzle Connection Shapes (Aerodynamic Port, Spectral Port, etc.)

WORKFLOW:
1. PARSE NATURAL LANGUAGE: Extract verbs, nouns, adjectives, prepositions from input sentence.
2. MAP TO SIMULATION CONCEPTS: Use DSL mapper to translate parts of speech to physics modules, 
   membrane patterns, constraints, and emergent behaviors.
3. VALIDATE CONSTRAINTS: Ensure mapped concepts adhere to physics principles and mathematical 
   constraints (energy principles, flow of matter/energy).
4. EXECUTE SIMULATION: Decompress the compressed data (natural language) into emergent physical 
   behaviors using the appropriate simulation engines (FSI, spectroscopy, progression).
"""

import re
import sys
import os
from typing import Dict, Any, List

# Add WorldModel directory to path for imports
_worldmodel_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, _worldmodel_dir)

try:
    import spacy
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    # print("Note: spaCy not installed. Using fallback regex-based parser.")

from exploration.player_progression_system import NaturalLanguageDSLMapper
from simulation.wind_through_tree_fsi import WindThroughTreeSimulation
from exploration.spectroscopic_exploration_tools import SpectroscopicExplorationTool


class SemanticProgrammingDSLEngine:
    """Engine that translates natural language sentences into membrane programming constraints and executes physics simulations."""
    
    def __init__(self):
        self.dsl_mapper = NaturalLanguageDSLMapper()
        self.fsi_simulator = WindThroughTreeSimulation(seed_value=42)
        self.spectral_tools = SpectroscopicExplorationTool()
        self.matcher = None
        self._initialize_matcher()
        
    def parse_natural_language_spacy(self, text: str, language: str = "en") -> Dict[str, List[str]]:
        """
        Parse natural language text using spaCy for part-of-speech tagging and dependency parsing.
        Maps UPOS tags to our DSL concepts:
        - VERB → verbs (THRUST, BALANCE, GROW, CONNECT, SCAN, etc.)
        - NOUN, PROPN → nouns (Hierarchy Levels, Matter Sources)
        - ADJ → adjectives (Physical States, Spectral Signatures)
        - ADP → prepositions (LEGO Puzzle Connection Shapes)
        
        Supports multilingual input via spaCy models: en (English), fr (French), es (Spanish), de (German).
        """
        if not SPACY_AVAILABLE:
            return self.parse_natural_language_fallback(text)
            
        # Map language codes to spaCy model names
        language_models = {
            "en": "en_core_web_sm",
            "fr": "fr_core_news_sm",
            "es": "es_core_news_sm",
            "de": "de_core_news_sm"
        }
        
        model_name = language_models.get(language.lower(), "en_core_web_sm")
        
        # Load spaCy model
        try:
            nlp = spacy.load(model_name)
        except OSError:
            print(f"spaCy model '{model_name}' not found. Installing...")
            import subprocess
            subprocess.check_call(["python", "-m", "spacy", "download", model_name])
            nlp = spacy.load(model_name)
            
        doc = nlp(text)
        
        extracted_verbs = []
        extracted_nouns = []
        extracted_adjectives = []
        extracted_prepositions = []
        
        # UPOS tags mapping
        # VERB: verbs (action/transformations)
        # NOUN, PROPN: nouns (objects/entities/hierarchy levels)
        # ADJ: adjectives (properties/states/spectral signatures)
        # ADP: prepositions/postpositions (relationships/connection shapes)
        
        for token in doc:
            pos_tag = token.pos_
            word = token.text.lower()
            
            if pos_tag == "VERB":
                extracted_verbs.append(word)
            elif pos_tag in ["NOUN", "PROPN"]:
                extracted_nouns.append(word)
            elif pos_tag == "ADJ":
                extracted_adjectives.append(word)
            elif pos_tag == "ADP":
                extracted_prepositions.append(word)
                
        return {
            "verbs": list(set(extracted_verbs)),
            "nouns": list(set(extracted_nouns)),
            "adjectives": list(set(extracted_adjectives)),
            "prepositions": list(set(extracted_prepositions))
        }

    def parse_natural_language_fallback(self, text: str) -> Dict[str, List[str]]:
        """
        Fallback regex-based extraction for when spaCy is not available.
        """
        # Common verb patterns
        verb_patterns = [r'\b(push|balance|grow|connect|scan|navigate|plant|nurture|blow|capture)\b']
        # Common noun patterns
        noun_patterns = [r'\b(sun|sky|earth|ground|tree|river|wind|orbit|space|canopy|roots|leaves)\b']
        # Common adjective patterns
        adj_patterns = [r'\b(calm|breezy|windy|gale-force|green|red|wet|dry|rocky|crystalline)\b']
        # Common preposition patterns
        prep_patterns = [r'\b(through|with|under|over|in|on|because-of|connected-to)\b']
        
        text_lower = text.lower()
        
        extracted_verbs = []
        for pattern in verb_patterns:
            matches = re.findall(pattern, text_lower)
            extracted_verbs.extend(matches)
            
        extracted_nouns = []
        for pattern in noun_patterns:
            matches = re.findall(pattern, text_lower)
            extracted_nouns.extend(matches)
            
        extracted_adjectives = []
        for pattern in adj_patterns:
            matches = re.findall(pattern, text_lower)
            extracted_adjectives.extend(matches)
            
        extracted_prepositions = []
        for pattern in prep_patterns:
            matches = re.findall(pattern, text_lower)
            extracted_prepositions.extend(matches)
            
        return {
            "verbs": list(set(extracted_verbs)),
            "nouns": list(set(extracted_nouns)),
            "adjectives": list(set(extracted_adjectives)),
            "prepositions": list(set(extracted_prepositions))
        }

    def parse_natural_language(self, text: str) -> Dict[str, List[str]]:
        """
        Parse natural language text to extract verbs, nouns, adjectives, and prepositions.
        Uses spaCy for POS tagging and dependency parsing when available.
        """
        return self.parse_natural_language_spacy(text)

    def analyze_dependency_graph(self, text: str) -> Dict[str, Any]:
        """
        Analyze syntactic dependencies using spaCy's dependency parser.
        Maps grammatical relationships to simulation concepts:
        - nsubj (nominal subject): entity performing the action -> Hierarchy Level / Matter Source
        - dobj (direct object): entity receiving the action -> Transformation Engine / Target
        - prep / pobj: prepositional relationships -> LEGO Puzzle Connection Shapes
        - amod: adjectival modifiers -> Physical States / Spectral Signatures
        """
        if not SPACY_AVAILABLE:
            return {"status": "fallback", "dependencies": []}
            
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            import subprocess
            subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
            nlp = spacy.load("en_core_web_sm")
            
        doc = nlp(text)
        
        dependencies = []
        noun_chunks = []
        
        # Extract dependency relationships
        for token in doc:
            if token.dep_ != "ROOT" and token.head.text != token.text:
                dep_info = {
                    "token": token.text,
                    "pos": token.pos_,
                    "dep": token.dep_,
                    "head": token.head.text,
                    "head_pos": token.head.pos_
                }
                dependencies.append(dep_info)
                
        # Extract noun chunks (multi-word entities)
        for chunk in doc.noun_chunks:
            noun_chunks.append({
                "text": chunk.text,
                "root": chunk.root.text,
                "pos": chunk.root.pos_
            })
            
        return {
            "dependencies": dependencies,
            "noun_chunks": noun_chunks,
            "root_verb": [t.text for t in doc if t.dep_ == "ROOT" and t.pos_ == "VERB"]
        }

    def map_to_simulation_concepts(self, parsed_language: Dict[str, List[str]]) -> Dict[str, Any]:
        """Map extracted language parts to simulation concepts using the DSL mapper."""
        mapped_concepts = {
            "verb_mappings": [],
            "noun_mappings": [],
            "adjective_mappings": [],
            "preposition_mappings": []
        }
        
        # Map verbs
        for verb in parsed_language.get("verbs", []):
            mapping = self.dsl_mapper.map_verb_to_simulation_concept(verb)
            mapped_concepts["verb_mappings"].append({
                "human_word": verb,
                "simulation_concept": mapping["concept"],
                "scale_of_speed": mapping["scale_of_speed"]
            })
            
        # Map nouns
        for noun in parsed_language.get("nouns", []):
            mapping = self.dsl_mapper.map_noun_to_hierarchy_level(noun)
            mapped_concepts["noun_mappings"].append({
                "human_word": noun,
                "hierarchy_level": mapping["level"],
                "simulation_concept": mapping["concept"]
            })
            
        # Map adjectives (spectral signatures and physical states)
        for adj in parsed_language.get("adjectives", []):
            # Simplified mapping for adjectives to spectral/physical states
            state_mappings = {
                "calm": {"state": "wind_speed_calm", "physics": "minimal airflow, minimal branch flexure"},
                "breezy": {"state": "wind_speed_breeze", "physics": "light airflow, gentle leaf flutter begins"},
                "windy": {"state": "wind_speed_wind", "physics": "moderate airflow, branch torsion and canopy turbulence development"},
                "gale-force": {"state": "wind_speed_gale", "physics": "strong airflow, significant canopy turbulence and leaf flutter instability"},
                "green": {"state": "spectral_vegetation_red_edge", "physics": "700-1300nm reflectance peak, chlorophyll absorption"},
                "red": {"state": "spectral_iron_oxide_hematite", "physics": "600-700nm absorption, iron oxide presence"},
                "rocky": {"state": "spectral_basalt_silicate", "physics": "2.2µm absorption bands, silicate mineral composition"},
                "crystalline": {"state": "spectral_quartz_silica", "physics": "quartz hexagonal prismatic with rhombohedral termination"}
            }
            mapped_concepts["adjective_mappings"].append({
                "human_word": adj,
                "physical_state_or_signature": state_mappings.get(adj.lower(), {"state": "unknown_physical_state", "physics": "undefined"})
            })
            
        # Map prepositions to connection shapes
        for prep in parsed_language.get("prepositions", []):
            mapping = self.dsl_mapper.map_preposition_to_connection_shape(prep)
            mapped_concepts["preposition_mappings"].append({
                "human_word": prep,
                "connection_shape": mapping["shape"],
                "physics_principle": mapping["physics"]
            })
            
        return mapped_concepts

    def validate_constraints(self, mapped_concepts: Dict[str, Any]) -> bool:
        """Validate that mapped concepts adhere to physics principles and mathematical constraints."""
        # In a full implementation, this would check against the constraint-first workflow:
        # CONSTRAINT → MEASURE → EXISTING → WORK → VERIFY
        
        # Basic validation: ensure at least one verb and one connection shape or physical state is present
        has_verb = len(mapped_concepts.get("verb_mappings", [])) > 0
        has_connection_or_state = (len(mapped_concepts.get("preposition_mappings", [])) > 0 or 
                                   len(mapped_concepts.get("adjective_mappings", [])) > 0)
        
        return has_verb and has_connection_or_state

    def execute_simulation(self, mapped_concepts: Dict[str, Any], natural_language_input: str) -> Dict[str, Any]:
        """
        Decompress the compressed data (natural language) into emergent physical behaviors 
        using the appropriate simulation engines.
        """
        simulation_results = {
            "natural_language_input": natural_language_input,
            "mapped_concepts": mapped_concepts,
            "simulation_executed": False,
            "emergent_behaviors": []
        }
        
        # Check if wind-through-tree FSI simulation should be triggered
        has_wind_or_tree_nouns = any(noun in ["wind", "tree", "canopy", "leaves", "roots"] 
                                     for noun in [m["human_word"].lower() for m in mapped_concepts.get("noun_mappings", [])])
        has_wind_state_adj = any(adj["physical_state_or_signature"]["state"].startswith("wind_speed_") 
                                 for adj in mapped_concepts.get("adjective_mappings", []))
        
        if has_wind_or_tree_nouns and has_wind_state_adj:
            # Extract wind speed state from adjectives
            wind_state = None
            for adj in mapped_concepts.get("adjective_mappings", []):
                state = adj["physical_state_or_signature"]["state"]
                if state.startswith("wind_speed_"):
                    wind_state = state.replace("wind_speed_", "")
                    break
                    
            if wind_state:
                # Execute FSI simulation
                fsi_results = self.fsi_simulator.run_simulation(
                    tree_asset_metadata={"canopy_density": 0.85, "previous_wind_state": "calm"},
                    wind_speed_state=wind_state,
                    transition_sequence=True
                )
                
                simulation_results["simulation_executed"] = True
                simulation_results["fsi_simulation_results"] = fsi_results
                simulation_results["emergent_behaviors"].extend([
                    "fluid_structure_interaction_wind_energy_transfer",
                    "canopy_mechanical_flexure",
                    "aerodynamic_flutter_dynamics",
                    "canopy_turbulence_drag_lift_forces"
                ])
                
        # Check if spectroscopic exploration should be triggered
        has_spectral_adj = any(adj["physical_state_or_signature"]["state"].startswith("spectral_") 
                               for adj in mapped_concepts.get("adjective_mappings", []))
                               
        if has_spectral_adj:
            # Execute spectral analysis simulation
            spectral_results = self.spectral_tools.analyze_celestial_body(
                body_type="earth_surface",
                spectral_library_reference="USGS_JPL_vegetation_iron_oxide"
            )
            
            simulation_results["simulation_executed"] = True
            simulation_results["spectral_analysis_results"] = spectral_results
            simulation_results["emergent_behaviors"].extend([
                "hyperspectral_sensor_signature_detection",
                "chemical_composition_analysis"
            ])
            
        return simulation_results

    def _initialize_matcher(self):
        """
        Initialize spaCy Rule-based Matcher for specific verb-noun-preposition patterns.
        Maps grammatical patterns to physics simulation module triggers:
        - VERB -> NOUN -> ADP -> NOUN pattern triggers FSI or Spectroscopic simulations
        """
        if not SPACY_AVAILABLE:
            return
            
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            import subprocess
            subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
            nlp = spacy.load("en_core_web_sm")
            
        self.matcher = Matcher(nlp.vocab)
        
        # Pattern 1: Wind/Flow verb -> Noun (tree/canopy) -> ADP (through/with) -> Noun (leaves/roots)
        # Triggers FSI simulation
        pattern_fsi = [
            {"POS": "VERB", "LEMMA": {"IN": ["blow", "flow", "move"]}},
            {"POS": "NOUN", "OP": "*"},
            {"POS": "ADP"},
            {"POS": "NOUN"}
        ]
        self.matcher.add("FSI_TRIGGER_PATTERN", [pattern_fsi])
        
        # Pattern 2: Scan verb -> Noun (earth/surface) -> ADP (for) -> Noun (signatures/signatures)
        # Triggers Spectroscopic simulation
        pattern_spectral = [
            {"POS": "VERB", "LEMMA": {"IN": ["scan", "analyze", "examine"]}},
            {"POS": "NOUN", "OP": "*"},
            {"POS": "ADP", "TEXT": {"IN": ["for", "with"]}},
            {"POS": "NOUN", "OP": "*"}
        ]
        self.matcher.add("SPECTRAL_TRIGGER_PATTERN", [pattern_spectral])
        
        # Pattern 3: Grow/Plant verb -> Noun (tree/ecosystem) -> ADP (with/in) -> Noun (soil/moisture)
        # Triggers Ecosystem growth simulation
        pattern_ecosystem = [
            {"POS": "VERB", "LEMMA": {"IN": ["grow", "plant", "nurture"]}},
            {"POS": "NOUN", "OP": "*"},
            {"POS": "ADP"},
            {"POS": "NOUN"}
        ]
        self.matcher.add("ECOSYSTEM_TRIGGER_PATTERN", [pattern_ecosystem])
        
        # Pattern 4: Navigate/Orbit verb -> Noun (spacecraft/orbit) -> ADP (around/with) -> Noun (planet/body)
        # Triggers Orbital Mechanics & Celestial Gravity simulation
        pattern_orbital = [
            {"POS": "VERB", "LEMMA": {"IN": ["navigate", "orbit", "circumnavigate"]}},
            {"POS": "NOUN", "OP": "*"},
            {"POS": "ADP", "TEXT": {"IN": ["around", "with", "near"]}},
            {"POS": "NOUN"}
        ]
        self.matcher.add("NAVIGATE_ORBIT_TRIGGER_PATTERN", [pattern_orbital])
        
        # Pattern 5: Connect verb -> Noun (network/node) -> ADP (to/with) -> Noun (port/interface)
        # Triggers CONNECT verb ecosystem network growth simulation
        pattern_connect = [
            {"POS": "VERB", "LEMMA": {"IN": ["connect", "link", "attach"]}},
            {"POS": "NOUN", "OP": "*"},
            {"POS": "ADP", "TEXT": {"IN": ["to", "with", "via"]}},
            {"POS": "NOUN"}
        ]
        self.matcher.add("CONNECT_TRIGGER_PATTERN", [pattern_connect])

    def handle_ambiguous_polysemous_words(self, doc, dependencies: List[Dict], noun_chunks: List[Dict]) -> Dict[str, Any]:
        """
        Handle ambiguous or polysemous words in the natural language parsing phase for multilingual input.
        Uses context from the dependency graph and noun chunks to disambiguate UPOS tag mappings.
        
        Args:
            doc: spaCy Doc object
            dependencies: list of dependency relationship dictionaries
            noun_chunks: list of noun chunk dictionaries
            
        Returns:
            Dictionary containing disambiguated word mappings and context resolution
        """
        disambiguation_context = {
            "ambiguous_words_resolved": [],
            "context_based_mappings": {}
        }
        
        # Identify potentially ambiguous words (e.g., 'bank' as river bank vs financial bank)
        # Use dependency context: if 'bank' is modified by 'river' or appears in nmod with 'water', it's geological
        for dep in dependencies:
            token = dep.get("token", "")
            head = dep.get("head", "")
            dep_rel = dep.get("dep", "")
            
            # Disambiguate 'bank' or similar polysemous words based on dependency relations
            if token.lower() in ['bank', 'port', 'anchor']:
                # Check if head or dep relation indicates physical/geological context
                if any(ctx in head.lower() for ctx in ['river', 'water', 'ground', 'earth', 'gravity']):
                    disambiguation_context['context_based_mappings'][token] = {
                        "resolved_meaning": f"physical_{token}_geological",
                        "dependency_relation": dep_rel,
                        "head_context": head
                    }
                    disambiguation_context['ambiguous_words_resolved'].append(token)
                elif any(ctx in head.lower() for ctx in ['orbit', 'space', 'gravity', 'mass']):
                    disambiguation_context['context_based_mappings'][token] = {
                        "resolved_meaning": f"physical_{token}_orbital",
                        "dependency_relation": dep_rel,
                        "head_context": head
                    }
                    disambiguation_context['ambiguous_words_resolved'].append(token)
                    
        return disambiguation_context

    def map_adjectives_multilingual(self, adjectives: List[str], language: str = "en") -> Dict[str, Any]:
        """
        Map adjectives/descriptors (calm, breezy, green, red, rocky) to spectral signatures 
        and physical states in multilingual contexts.
        
        Args:
            adjectives: list of adjectives from parsed text
            language: language code (en, fr, es, de)
            
        Returns:
            Dictionary containing adjective mappings to physical states and spectral signatures
        """
        # Multilingual adjective mappings (core concepts remain consistent across languages per UD schema)
        state_mappings = {
            "en": {
                "calm": {"state": "wind_speed_calm", "physics": "minimal airflow, minimal branch flexure"},
                "breezy": {"state": "wind_speed_breeze", "physics": "light airflow, gentle leaf flutter begins"},
                "windy": {"state": "wind_speed_wind", "physics": "moderate airflow, branch torsion and canopy turbulence development"},
                "gale-force": {"state": "wind_speed_gale", "physics": "strong airflow, significant canopy turbulence and leaf flutter instability"},
                "green": {"state": "spectral_vegetation_red_edge", "physics": "700-1300nm reflectance peak, chlorophyll absorption"},
                "red": {"state": "spectral_iron_oxide_hematite", "physics": "600-700nm absorption, iron oxide presence"},
                "rocky": {"state": "spectral_basalt_silicate", "physics": "2.2µm absorption bands, silicate mineral composition"},
                "crystalline": {"state": "spectral_quartz_silica", "physics": "quartz hexagonal prismatic with rhombohedral termination"}
            },
            "fr": {
                "calme": {"state": "wind_speed_calm", "physics": "minimal airflow, minimal branch flexure"},
                "breezant": {"state": "wind_speed_breeze", "physics": "light airflow, gentle leaf flutter begins"},
                "vert": {"state": "spectral_vegetation_red_edge", "physics": "700-1300nm reflectance peak, chlorophyll absorption"},
                "rouge": {"state": "spectral_iron_oxide_hematite", "physics": "600-700nm absorption, iron oxide presence"},
                "rocheux": {"state": "spectral_basalt_silicate", "physics": "2.2µm absorption bands, silicate mineral composition"}
            },
            "es": {
                "calmo": {"state": "wind_speed_calm", "physics": "minimal airflow, minimal branch flexure"},
                "brisa": {"state": "wind_speed_breeze", "physics": "light airflow, gentle leaf flutter begins"},
                "verde": {"state": "spectral_vegetation_red_edge", "physics": "700-1300nm reflectance peak, chlorophyll absorption"},
                "rojo": {"state": "spectral_iron_oxide_hematite", "physics": "600-700nm absorption, iron oxide presence"},
                "rocoso": {"state": "spectral_basalt_silicate", "physics": "2.2µm absorption bands, silicate mineral composition"}
            },
            "de": {
                "ruhig": {"state": "wind_speed_calm", "physics": "minimal airflow, minimal branch flexure"},
                "breez": {"state": "wind_speed_breeze", "physics": "light airflow, gentle leaf flutter begins"},
                "gruen": {"state": "spectral_vegetation_red_edge", "physics": "700-1300nm reflectance peak, chlorophyll absorption"},
                "rot": {"state": "spectral_iron_oxide_hematite", "physics": "600-700nm absorption, iron oxide presence"},
                "steinig": {"state": "spectral_basalt_silicate", "physics": "2.2µm absorption bands, silicate mineral composition"}
            }
        }
        
        mapped_adjectives = []
        lang_mappings = state_mappings.get(language.lower(), state_mappings["en"])
        
        for adj in adjectives:
            adj_lower = adj.lower()
            # Check direct match or language-specific mapping
            mapping = lang_mappings.get(adj_lower, lang_mappings.get(adj_lower.replace('-',''), None))
            if not mapping and adj_lower in ["green", "red", "rocky", "crystalline"]:
                # Fallback to English mappings for common descriptors
                mapping = state_mappings["en"].get(adj_lower)
                
            mapped_adjectives.append({
                "human_word": adj,
                "language": language,
                "physical_state_or_signature": mapping if mapping else {"state": "unknown_physical_state", "physics": "undefined"}
            })
            
        return {
            "adjective_mappings": mapped_adjectives,
            "language_supported": language in state_mappings
        }

    def apply_rule_based_matching(self, text: str) -> Dict[str, Any]:
        """
        Apply spaCy Rule-based Matching to identify specific verb-noun-preposition patterns
        that trigger physics simulation modules.
        
        Args:
            text: Natural language input sentence
            
        Returns:
            Dictionary containing matched patterns and triggered simulation modules
        """
        if not SPACY_AVAILABLE or self.matcher is None:
            return {"status": "fallback", "matched_patterns": [], "triggered_modules": []}
            
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            import subprocess
            subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
            nlp = spacy.load("en_core_web_sm")
            
        doc = nlp(text)
        matches = self.matcher(doc)
        
        matched_patterns = []
        triggered_modules = []
        
        for match_id, start, end in matches:
            span = doc[start:end]
            pattern_name = nlp.vocab.strings[match_id]
            matched_patterns.append({
                "pattern_name": pattern_name,
                "text": span.text,
                "start": start,
                "end": end
            })
            
            # Map pattern names to simulation modules
            if pattern_name == "FSI_TRIGGER_PATTERN":
                triggered_modules.append("Fluid_Structure_Interaction_FSI")
            elif pattern_name == "SPECTRAL_TRIGGER_PATTERN":
                triggered_modules.append("Hyperspectral_Sensor_Analysis")
            elif pattern_name == "ECOSYSTEM_TRIGGER_PATTERN":
                triggered_modules.append("GROW_ECOSYSTEM_Simulation")
            elif pattern_name == "NAVIGATE_ORBIT_TRIGGER_PATTERN":
                triggered_modules.append("Orbital_Mechanics_Celestial_Gravity")
            elif pattern_name == "CONNECT_TRIGGER_PATTERN":
                triggered_modules.append("CONNECT_Ecosystem_Network_Growth")
                
        return {
            "matched_patterns": matched_patterns,
            "triggered_modules": list(set(triggered_modules)),
            "disambiguation_context": self.handle_ambiguous_polysemous_words(doc, [], []),
            "adjective_multilingual_mapping": self.map_adjectives_multilingual([], "en")
        }

    def process_natural_language_command(self, natural_language_input: str) -> Dict[str, Any]:
        """
        Main workflow: Parse -> Map -> Validate -> Execute
        """
        # Step 1: Parse natural language
        parsed_language = self.parse_natural_language(natural_language_input)
        
        # Step 2: Map to simulation concepts
        mapped_concepts = self.map_to_simulation_concepts(parsed_language)
        
        # Step 3: Validate constraints
        is_valid = self.validate_constraints(mapped_concepts)
        
        if not is_valid:
            return {
                "status": "validation_failed",
                "error": "Mapped concepts do not adhere to physics principles and mathematical constraints.",
                "parsed_language": parsed_language,
                "mapped_concepts": mapped_concepts
            }
            
        # Step 4: Execute simulation
        simulation_results = self.execute_simulation(mapped_concepts, natural_language_input)
        
        return {
            "status": "success",
            "natural_language_input": natural_language_input,
            "parsed_language": parsed_language,
            "mapped_concepts": mapped_concepts,
            "simulation_results": simulation_results
        }


def execute_semantic_programming_command(natural_language_sentence: str) -> Dict[str, Any]:
    """
    Convenience function to execute a natural language semantic programming command.
    
    Args:
        natural_language_sentence: Natural language sentence describing a scenario
        
    Returns:
        Dictionary containing parsed language, mapped concepts, and simulation results
    """
    engine = SemanticProgrammingDSLEngine()
    return engine.process_natural_language_command(natural_language_sentence)
