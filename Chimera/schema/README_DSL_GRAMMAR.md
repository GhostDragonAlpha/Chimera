# Chimera DSL Formal Grammar Implementation

## Overview

This directory contains the formal ANTLR4 grammar for the Chimera Domain-Specific Language (DSL) used for game specification. The formal grammar provides:

- **Single source of truth** for valid DSL syntax
- **Unambiguous parsing** via formal lexer/parser rules
- **Structured error messages** with line:column positions
- **Tooling support**: syntax highlighting, autocomplete, static analysis

## Files

### `Chimera/schema/ChimeraDSL.g4`
Complete ANTLR4 grammar defining the DSL structure including:
- Game block (engine_version, target_platforms)
- Narrative block (acts, dialogue_trees, cutscenes)
- Gameplay block (characters, abilities, combat_system, inventory, progression)
- World block (levels, NPCs)
- UI block (hud, pause_menu)
- Audio block (music_cues, sfx, dynamic_mixing_rules)
- Technical block (network_model, replication, performance, module_dependencies)
- Art direction block (style, color_palette)

### `Chimera/schema/chimera.tmLanguage.json`
TextMate grammar for syntax highlighting in VS Code and other editors supporting TextMate grammars.

### `Chimera/core/dsl_grammar_validator.py`
Tree-walking semantic validator using ANTLR4 parse trees. Falls back to regex-based parser if ANTLR4 generated files are not available.

### `Chimera/core/generate_antlr_parser.py`
Script to generate Python lexer and parser from `ChimeraDSL.g4` using the ANTLR4 tool.

## Generating the ANTLR4 Parser

To generate the Python parser and lexer from the grammar:

```bash
python Chimera/core/generate_antlr_parser.py
```

**Requirements:**
- Java Runtime Environment (JRE) installed and in PATH
- `antlr-4.13.2-complete.jar` in project root directory

If Java is not available, the system will automatically fall back to the regex-based parser (`dsl_game_parser.py`).

## Test Files

Grammar test suite files are located in `Chimera/tests/dsl_grammar/`:
- `valid_game_spec.chimera` - Basic valid game specification
- `valid_gameplay_combat.chimera` - Complex gameplay with combat system and GAS abilities
- `invalid_syntax.chimera` - Test file with intentional syntax errors for error reporting validation

## Integration with Existing Pipeline

The DSL grammar validator integrates with the existing 6-stage pipeline:

1. **Stage 1 (Parse & Validate)** now supports both:
   - ANTLR4 tree-walking semantic validation (when generated parsers are available)
   - Regex-based parsing fallback (always available)

2. **Semantic Validation** checks:
   - Ability references in character `default_abilities`
   - Character declarations and inheritance
   - Dialogue tree references in acts and NPCs
   - Replication property formats

3. **Error Reporting** provides:
   - Syntax errors with line:column positions (via ANTLR4)
   - Semantic errors with descriptive messages

## Future Enhancements

- Language Server Protocol (LSP) server for real-time validation and autocomplete
- Integration with VS Code extension for syntax highlighting and go-to-definition
- DSL schema to JSON Schema conversion for IDE integration
- Breaking change detection via grammar versioning
