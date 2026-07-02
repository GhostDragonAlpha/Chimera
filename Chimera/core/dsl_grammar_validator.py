"""
DSL Grammar Validator — Tree-walking semantic validator using ANTLR4 parse trees.

Replaces or augments the regex parser with proper AST-based validation that:
- Checks semantic rules (ability references, character declarations, etc.)
- Emits structured error messages with exact line:column positions
- Provides unambiguous parsing via formal grammar

To generate the ANTLR4 Python parser from ChimeraDSL.g4:
    python Chimera/core/generate_antlr_parser.py

Requirements for generation:
- Java Runtime Environment (JRE) installed and in PATH
- antlr-4.13.2-complete.jar in project root
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import sys

# Try to import ANTLR4 components
try:
    from antlr4 import InputStream, CommonTokenStream
    # Try generated parser paths
    schema_dir = Path(__file__).parent.parent / 'schema' / 'generated_antlr'
    if str(schema_dir) not in sys.path:
        sys.path.insert(0, str(schema_dir))
    
    from ChimeraDSLLexer import ChimeraDSLLexer
    from ChimeraDSLParser import ChimeraDSLParser
except ImportError:
    # Fallback to regex parser if ANTLR4 generated files are not available
    # Add current directory to path for relative imports
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    from dsl_game_parser import DSLGameParser
    
    class DSLGrammarValidator:
        def __init__(self, grammar_path: str = None):
            self.grammar_path = Path(grammar_path) if grammar_path else None
            # Initialize regex parser with schema path
            schema_file = Path(__file__).parent.parent / 'schema' / 'dsl_game_schema.json'
            self.regex_parser = DSLGameParser(str(schema_file))
        
        def parse_and_validate(self, dsl_content: str) -> Tuple[bool, Dict[str, Any], List[str]]:
            is_valid, parsed_dsl, error = self.regex_parser.parse_and_validate(dsl_content)
            errors = [error] if error and not is_valid else []
            return is_valid, parsed_dsl if is_valid else {}, errors


class ChimeraDSLVisitor:
    """AST visitor for semantic validation of Chimera DSL parse trees."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Semantic tracking
        self.abilities_defined: Dict[str, Dict[str, Any]] = {}
        self.characters_defined: Dict[str, Dict[str, Any]] = {}
        self.character_abilities: Dict[str, List[str]] = {}  # char_name -> [ability_names]
        self.dialogue_trees_defined: Dict[str, Any] = {}
        self.npcs_defined: Dict[str, Dict[str, Any]] = {}

    def visitGameSpec(self, ctx):
        """Visit top-level game specification."""
        self.visitChildren(ctx)
        # Perform cross-block semantic validation after all blocks are visited
        self.validate_semantic_references()
        return self.errors, self.warnings

    def validate_semantic_references(self):
        """Validate cross-block references (abilities in characters, dialogue trees in acts/NPCs, etc.)."""
        
        # 1. Validate character default_abilities reference defined abilities
        for char_name, abilities in self.character_abilities.items():
            for ab_name in abilities:
                # Normalize ability name (remove GA_ prefix if present)
                ab_normalized = ab_name.replace('GA_', '') if ab_name.startswith('GA_') else ab_name
                
                if ab_normalized not in self.abilities_defined:
                    # Try with GA_ prefix too
                    if f"GA_{ab_normalized}" not in self.abilities_defined and ab_name not in self.abilities_defined:
                        self.errors.append(
                            f"Semantic error: Character '{char_name}' references undefined ability '{ab_name}'. "
                            f"Defined abilities are: {list(self.abilities_defined.keys())}"
                        )

        # 2. Validate NPC behavior_tree and dialogue_tree references
        for npc_name, npc_data in self.npcs_defined.items():
            bt = npc_data.get('behavior_tree')
            if bt and not bt.startswith('BT_'):
                bt = f"BT_{bt}"
            
            if bt:
                # BT files are generated, so we don't strictly validate they exist as AST nodes
                pass
                
            dt = npc_data.get('dialogue_tree')
            if dt:
                dt_normalized = dt.replace('DT_', '') if dt.startswith('DT_') else dt
                if dt not in self.dialogue_trees_defined and f"DT_{dt_normalized}" not in self.dialogue_trees_defined:
                    # Dialogue trees are defined in narrative block
                    pass  # Will be validated by narrative parser

        # 3. Validate acts reference defined dialogue trees
        # This would require tracking act_dialogue_references which isn't currently stored
        # For now, focus on ability references which are the most critical

    def validate_test_references(self, dsl_data: Dict[str, Any]):
        """Validate test block references to ensure referenced entities exist."""
        if "tests" not in dsl_data or "test_definitions" not in dsl_data["tests"]:
            return
            
        # Build lookup sets for validation
        characters_defined = set()
        ship_classes_defined = set()
        abilities_defined = set()
        recipes_defined = set()
        biome_configs_defined = set()
        trade_routes_defined = set()
        
        # Collect defined entities from DSL data
        if "gameplay" in dsl_data and "characters" in dsl_data["gameplay"]:
            for char in dsl_data["gameplay"]["characters"]:
                characters_defined.add(char.get("name", ""))
                
        if "ship_classes" in dsl_data and "ships" in dsl_data["ship_classes"]:
            for ship in dsl_data["ship_classes"]["ships"]:
                ship_classes_defined.add(ship.get("name", ""))
                
        if "gameplay" in dsl_data and "abilities" in dsl_data["gameplay"]:
            for ab in dsl_data["gameplay"]["abilities"]:
                abilities_defined.add(ab.get("name", ""))
                
        if "gameplay" in dsl_data and "crafting_systems" in dsl_data["gameplay"] and "recipes" in dsl_data["gameplay"]["crafting_systems"]:
            for recipe in dsl_data["gameplay"]["crafting_systems"]["recipes"]:
                recipes_defined.add(recipe.get("name", ""))
                
        if "planet_generation_systems" in dsl_data and "biome_configs" in dsl_data["planet_generation_systems"]:
            for biome in dsl_data["planet_generation_systems"]["biome_configs"]:
                biome_configs_defined.add(biome.get("name", ""))
                
        if "economy_systems" in dsl_data and "trade_routes" in dsl_data["economy_systems"]:
            for route in dsl_data["economy_systems"]["trade_routes"]:
                trade_routes_defined.add(route.get("name", ""))
                
        # Validate test references
        for test_def in dsl_data["tests"]["test_definitions"]:
            test_name = test_def.get("name", "UnknownTest")
            
            for setup_stmt in test_def.get("setup", []):
                action = setup_stmt.get("action", "")
                params = setup_stmt.get("params", {})
                
                if action == "spawn_actor":
                    class_val = params.get("class", "") or params.get("type", "")
                    if class_val and class_val not in characters_defined and class_val not in ship_classes_defined:
                        self.errors.append(
                            f"Semantic error in test '{test_name}': spawn_actor references undefined actor type '{class_val}'. "
                            f"Defined characters are: {list(characters_defined)}, defined ships are: {list(ship_classes_defined)}"
                        )
                        
                elif action == "grant_ability":
                    ability_val = params.get("ability", "")
                    if ability_val and ability_val not in abilities_defined:
                        self.errors.append(
                            f"Semantic error in test '{test_name}': grant_ability references undefined ability '{ability_val}'. "
                            f"Defined abilities are: {list(abilities_defined)}"
                        )
                        
            for action_stmt in test_def.get("action", []):
                action = action_stmt.get("action", "")
                params = action_stmt.get("params", {})
                
                if action == "craft_recipe":
                    recipe_val = params.get("recipe", "")
                    if recipe_val and recipe_val not in recipes_defined:
                        self.errors.append(
                            f"Semantic error in test '{test_name}': craft_recipe references undefined recipe '{recipe_val}'. "
                            f"Defined recipes are: {list(recipes_defined)}"
                        )
                        
                elif action == "set_biome":
                    biome_val = params.get("biome", "")
                    if biome_val and biome_val not in biome_configs_defined:
                        self.errors.append(
                            f"Semantic error in test '{test_name}': set_biome references undefined biome '{biome_val}'. "
                            f"Defined biomes are: {list(biome_configs_defined)}"
                        )
                        
                elif action == "initialize_market":
                    market_val = params.get("market", "")
                    if market_val and market_val not in trade_routes_defined:
                        self.errors.append(
                            f"Semantic error in test '{test_name}': initialize_market references undefined market '{market_val}'. "
                            f"Defined markets are: {list(trade_routes_defined)}"
                        )

    def visitGameSpec(self, ctx):
        """Validate game block semantics."""
        title = self._get_string_value(ctx.STRING(0))
        if not title:
            self.errors.append(f"Line {ctx.start.line}: Game block missing valid title string")
        
        engine_version = None
        target_platforms = []
        
        for child in ctx.gameBody().children:
            if hasattr(child, 'engineVersion'):
                engine_version = self._get_string_value(child.engineVersion().STRING())
            elif hasattr(child, 'targetPlatforms'):
                target_platforms = [self._get_string_value(s) for s in child.targetPlatforms().STRING()]
        
        return None

    def visitNarrativeBlock(self, ctx):
        """Validate narrative block semantics."""
        acts_found = []
        dialogue_trees_found = []
        
        for child in ctx.narrativeBody().children:
            if hasattr(child, 'actDeclaration'):
                act_name = self._get_string_value(child.actDeclaration().STRING())
                acts_found.append(act_name)
            elif hasattr(child, 'dialogueTree'):
                dt_name = self._get_string_value(child.dialogueTree().STRING())
                dialogue_trees_found.append(dt_name)
                self.dialogue_trees_defined[dt_name] = True
        
        return None

    def visitGameplayBlock(self, ctx):
        """Validate gameplay block semantics."""
        for child in ctx.gameplayBody().children:
            if hasattr(child, 'characterDeclaration'):
                char_name = self._get_string_value(child.characterDeclaration().STRING(0))
                inherits = None
                if child.characterDeclaration().inheritsClause():
                    inherits = self._get_string_value(child.characterDeclaration().inheritsClause().STRING())
                
                # Track default_abilities if present
                default_abilities = []
                props = child.characterDeclaration().propertiesBlock()
                if props and props.defaultAbilities():
                    ab_list = props.defaultAbilities().STRING()
                    for ab in ab_list:
                        default_abilities.append(self._get_string_value(ab))
                
                self.characters_defined[char_name] = {
                    'name': char_name,
                    'inherits': inherits or 'ACharacter'
                }
                if default_abilities:
                    self.character_abilities[char_name] = default_abilities
                
            elif hasattr(child, 'abilityDeclaration'):
                ab_name = self._get_string_value(child.abilityDeclaration().STRING(0))
                uses_gas = child.abilityDeclaration().usesGAS() is not None
                
                tags = []
                if child.abilityDeclaration().abilityProperties().abilityTags():
                    tags = [self._get_string_value(s) for s in child.abilityDeclaration().abilityProperties().abilityTags().STRING()]
                
                self.abilities_defined[ab_name] = {
                    'name': ab_name,
                    'uses_gas': uses_gas,
                    'tags': tags
                }

        return None

    def visitWorldBlock(self, ctx):
        """Validate world block semantics."""
        levels_found = []
        npcs_found = []
        
        for child in ctx.worldBody().children:
            if hasattr(child, 'levelDeclaration'):
                lvl_name = self._get_string_value(child.levelDeclaration().STRING(0))
                levels_found.append(lvl_name)
                
            elif hasattr(child, 'npcDeclaration'):
                npc_name = self._get_string_value(child.npcDeclaration().STRING(0))
                npcs_found.append(npc_name)
                
                # Track NPC properties
                mesh = None
                behavior_tree = None
                dialogue_tree = None
                health = None
                
                for prop in child.npcDeclaration().npcProperties().children:
                    if hasattr(prop, 'npcMesh'):
                        mesh = self._get_string_value(prop.npcMesh().STRING())
                    elif hasattr(prop, 'behaviorTreeProperty'):
                        behavior_tree = self._get_string_value(prop.behaviorTreeProperty().STRING())
                    elif hasattr(prop, 'dialogueTreeProperty'):
                        dialogue_tree = self._get_string_value(prop.dialogueTreeProperty().STRING())
                    elif hasattr(prop, 'healthProperty'):
                        health = int(self._get_integer_value(prop.healthProperty().INTEGER()))
                        
                self.npcs_defined[npc_name] = {
                    'name': npc_name,
                    'mesh': mesh,
                    'behavior_tree': behavior_tree,
                    'dialogue_tree': dialogue_tree,
                    'health': health
                }

        return None

    def visitTechnicalBlock(self, ctx):
        """Validate technical block semantics."""
        network_model = None
        
        for child in ctx.technicalBody().children:
            if hasattr(child, 'networkModel'):
                network_model = self._get_string_value(child.networkModel().STRING())
                
            elif hasattr(child, 'replicationRules'):
                # Validate replication properties format
                pass
                
        return None

    def _get_string_value(self, ctx) -> Optional[str]:
        """Extract string value from lexer context."""
        if not ctx:
            return None
        text = ctx.getText()
        if text.startswith('"') and text.endswith('"'):
            return text[1:-1]
        return text

    def _get_integer_value(self, ctx) -> Optional[int]:
        """Extract integer value from lexer context."""
        if not ctx:
            return None
        try:
            return int(ctx.getText())
        except ValueError:
            return None


class DSLGrammarValidator:
    """Main validator class that uses ANTLR4 parse trees for semantic validation."""

    def __init__(self, grammar_path: str = None):
        self.grammar_path = Path(grammar_path) if grammar_path else Path('Chimera/schema/ChimeraDSL.g4')

    def parse_and_validate(self, dsl_content: str) -> Tuple[bool, Dict[str, Any], List[str]]:
        """Parse DSL content using ANTLR4 and validate semantically."""
        try:
            # Parse using ANTLR4
            input_stream = InputStream(dsl_content)
            lexer = ChimeraDSLLexer(input_stream)
            token_stream = CommonTokenStream(lexer)
            parser = ChimeraDSLParser(token_stream)
            
            # Remove default error listeners and add custom one
            parser.removeErrorListeners()
            parser.addErrorListener(ChimeraErrorListener())
            
            # Parse the DSL
            parse_tree = parser.gameSpec()
            
            if parser.getNumberOfSyntaxErrors() > 0:
                errors = [f"Syntax error at line {parser.current_error_line}: {parser.current_error_msg}"]
                return False, {}, errors
            
            # Visit parse tree for semantic validation
            visitor = ChimeraDSLVisitor()
            visitor.visitGameSpec(parse_tree)
            
            errors = visitor.errors + parser.syntax_errors
            warnings = visitor.warnings
            
            if errors:
                return False, {}, errors
            
            # If parsing and validation succeed, convert to JSON structure
            # using the regex parser as a bridge (or implement full AST-to-JSON conversion)
            from core.dsl_game_parser import DSLGameParser
            regex_parser = DSLGameParser('Chimera/schema/dsl_game_schema.json')
            is_valid, parsed_dsl, regex_error = regex_parser.parse_and_validate(dsl_content)
            
            if not is_valid and regex_error:
                errors.append(f"Semantic validation failed: {regex_error}")
                return False, {}, errors
            
            # Validate test references if tests block is present
            visitor = ChimeraDSLVisitor()
            visitor.validate_test_references(parsed_dsl)
            errors.extend(visitor.errors)
            
            if errors:
                return False, {}, errors
            
            return True, parsed_dsl, []
            
        except Exception as e:
            return False, {}, [f"Parser initialization error: {str(e)}"]


class ChimeraErrorListener:
    """Custom ANTLR4 error listener for capturing syntax errors."""
    
    def __init__(self):
        self.syntax_errors: List[str] = []
        self.current_error_line: int = 0
        self.current_error_msg: str = ""

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.syntax_errors.append(f"Syntax error at line {line}:{column}: {msg}")
        self.current_error_line = line
        self.current_error_msg = msg
