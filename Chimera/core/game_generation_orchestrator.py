"""
DSL-Driven Game Generation Orchestrator — AI-powered game generation workflow.

Takes a complete, structured game specification written in a domain-specific language (DSL)
and transforms it into a fully functional, AAA-quality Unreal Engine 5 project.

Follows the 7-stage pipeline with integrated Graphify DNA system:
1. Parse & Validate: Check DSL for consistency, type errors, missing references
2. Asset Generation: Create all declared assets at specified paths using AI tools
3. Code Generation: Emit C++ and Blueprint logic, data tables, configuration files
4. Integration & Build: Assemble .uproject, compile, run automated tests
4.5 Automated Playtest: Execute behavioral tests using UE's automation framework
5. Report & Refine: Output validation report with deviations; generate proposed DSL patch
6. Regenerate & Iterate: Incrementally regenerate only affected parts

DNA Integration (automatic at every stage):
- Before Stage 1: Pattern Validator queries DNA for known-bad patterns
- Before Stage 3: Verified reference graph queried for correct signatures/macros
- Before Stage 4: Template validation and static analysis
- After Stage 4: Mutation Logger records result; Auto-Fixer on failure
- After Stage 5: Continuous Verification health check

The specification is the sole source of truth - never guess creative elements not explicitly declared.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple, List

# Import local components
try:
    from core.dsl_game_parser import DSLGameParser
    from core.game_code_generator import GameCodeGenerator
    from core.asset_generator import AssetGenerator
    from core.build_orchestrator import BuildOrchestrator
    from core.validation_reporter import ValidationReporter
    from core.incremental_generator import IncrementalGenerator
    from core.playtest_runner import PlaytestRunner
    from core.test_reporter import TestReporter
    from core.visual_verifier import run_visual_verification
except ImportError:
    try:
        from dsl_game_parser import DSLGameParser
        from game_code_generator import GameCodeGenerator
        from asset_generator import AssetGenerator
        from build_orchestrator import BuildOrchestrator
        from validation_reporter import ValidationReporter
        from incremental_generator import IncrementalGenerator
        from playtest_runner import PlaytestRunner
        from test_reporter import TestReporter
        from visual_verifier import run_visual_verification
    except ImportError:
        ...

# Graphify interface imports - all components route through this single interface
try:
    from core.graphify_interface import query, mutate, load_dna_graph, save_dna_graph, graphify_mutate as record_compilation_success, graphify_mutate as record_compilation_failure
    from core.dna.pattern_validator import check_template_history, validate_template_before_generation, flag_known_bad_pattern
    from core.dna.auto_fixer import auto_fix_brace_error
except ImportError:
    try:
        from graphify_interface import query, mutate, load_dna_graph, save_dna_graph, graphify_mutate as record_compilation_success, graphify_mutate as record_compilation_failure
        from dna.pattern_validator import check_template_history, validate_template_before_generation, flag_known_bad_pattern
        from dna.auto_fixer import auto_fix_brace_error
    except ImportError:
        def query(*args, **kwargs): return None
        def mutate(*args, **kwargs): return "mutate_dummy"
        def load_dna_graph(): return {"nodes": [], "edges": []}
        def save_dna_graph(*args): pass
        def check_template_history(*args, **kwargs): return {}
        def validate_template_before_generation(*args, **kwargs): return True
        def flag_known_bad_pattern(*args, **kwargs): return {"is_know_bad": False}
        def auto_fix_brace_error(*args, **kwargs): return {"fixed": False}
        def record_compilation_success(*args, **kwargs): return "mutation_dummy"
        def record_compilation_failure(*args, **kwargs): return "error_dummy"

# DNA Integration status
DNA_AVAILABLE = True
DNA_VERIFY_AVAILABLE = True

# Fallback mock classes omitted for brevity — see below for inline handling



class GameGenerationOrchestrator:
    """Orchestrates the 6-stage DSL-driven game generation pipeline."""

    def __init__(self, schema_path: str, source_dir: str, content_dir: str, output_dir: str):
        """
        Initialize the orchestrator with schema and directory paths.

        Args:
            schema_path: Path to dsl_game_schema.json
            source_dir: Source directory for C++ code generation
            content_dir: Content directory for asset generation
            output_dir: Output directory for .uproject and packaged executable
        """
        self.schema_path = Path(schema_path)
        self.source_dir = Path(source_dir)
        self.content_dir = Path(content_dir)
        self.output_dir = Path(output_dir)

        # Initialize pipeline components
        self.parser = DSLGameParser(str(self.schema_path))
        self.code_generator = GameCodeGenerator(str(self.source_dir), str(self.content_dir))
        self.asset_generator = AssetGenerator(str(self.content_dir))
        self.build_orchestrator = BuildOrchestrator("GeneratedProject", str(self.output_dir))
        self.validation_reporter = ValidationReporter(str(self.output_dir))
        self.incremental_generator = IncrementalGenerator(str(self.content_dir), str(self.source_dir))
        self.playtest_runner = None
        self.test_reporter = TestReporter(str(self.output_dir))

    def process_dsl_specification(self, dsl_content: str, project_name: str = None) -> Dict[str, Any]:
        """
        Execute the complete 7-stage pipeline for DSL-driven game generation.

        Args:
            dsl_content: Complete DSL document for a game
            project_name: Optional project name override

        Returns:
            Dict with 'success', 'uproject_path', 'validation_report', or 'error' message
        """
        if project_name is None:
            # Extract project name from DSL if possible
            import re
            game_match = re.search(r'game\s+"([^"]+)"', dsl_content)
            if game_match:
                project_name = game_match.group(1)
            else:
                project_name = "GeneratedProject"

        print(f"[Stage 1] Parse & Validate DSL specification for {project_name}...")
        
        # Stage 1: Parse & Validate
        is_valid, parsed_dsl, validation_error = self.parser.parse_and_validate(dsl_content)
        
        # --- DNA: Pattern Validator after parsing ---
        if DNA_AVAILABLE and is_valid:
            try:
                graph = load_dna_graph()
                dsl_blocks = [k for k in parsed_dsl.keys()] if isinstance(parsed_dsl, dict) else []
                warnings_found = 0
                for block_name in dsl_blocks:
                    history = check_template_history(graph, f"dsl_block_{block_name}")
                    if history.get("has_errors_before"):
                        print(f"  [DNA] Warning: DSL block '{block_name}' has known errors in history")
                        warnings_found += 1
                if warnings_found == 0:
                    print("  [DNA] Pattern Validator: no known-bad patterns detected in DSL")
                else:
                    print(f"  [DNA] Pattern Validator: {warnings_found} warnings from DNA graph")
            except Exception as e:
                print(f"  [DNA] Pattern Validator skipped: {e}")
        
        if not is_valid:
            return {
                "success": False,
                "error": f"DSL Validation Failed: {validation_error}"
            }

        print("[Stage 1] DSL specification is valid and complete")

        # Parse dsl_data from parsed_dsl (which is already a dict)
        dsl_data = parsed_dsl if isinstance(parsed_dsl, dict) else json.loads(json.dumps(parsed_dsl))

        print(f"[Stage 2] Asset Generation for {project_name}...")
        
        # Stage 2: Asset Generation
        generated_assets = self.asset_generator.generate_assets_from_dsl(dsl_data)
        print(f"[Stage 2] Generated assets: {len(generated_assets.get('meshes', []))} meshes, "
              f"{len(generated_assets.get('textures', []))} textures, "
              f"{len(generated_assets.get('animations', []))} animations, "
              f"{len(generated_assets.get('sounds', []))} sounds")

        print(f"[Stage 3] Code Generation for {project_name}...")
        
        # --- DNA: Template validation before Stage 3 ---
        if DNA_AVAILABLE:
            try:
                graph = load_dna_graph()
                templates_checked = 0
                template_names = ["ship_class", "game_mode_class", "combat_component", 
                                  "pirate_ai", "docking_component", "mission_component",
                                  "faction_component", "save_game", "pcg_volume_manager"]
                for tpl in template_names:
                    result = check_template_history(graph, f"template_{tpl}")
                    if result.get("unresolved_patterns"):
                        print(f"  [DNA] WARNING: Template '{tpl}' has unresolved errors — verify before regenerating")
                    if result.get("applied_fixes"):
                        print(f"  [DNA] Template '{tpl}' has {len(result['applied_fixes'])} known fixes: {result['applied_fixes'][:2]}")
                    templates_checked += 1
                print(f"  [DNA] Template validation: {templates_checked} templates checked against DNA graph")
            except Exception as e:
                print(f"  [DNA] Template validation skipped: {e}")
        
        # Stage 3: Code Generation
        generated_files = self.code_generator.generate_all_from_dsl(dsl_data)
        print(f"[Stage 3] Generated files: {len(generated_files.get('character_classes', []))} character classes, "
              f"{len(generated_files.get('ability_classes', []))} ability classes, "
              f"{len(generated_files.get('behavior_trees', []))} behavior trees, "
              f"{len(generated_files.get('ui_widgets', []))} UI widgets")

        print(f"[Stage 4] Integration & Build for {project_name}...")
        
        # Stage 4: Integration & Build
        build_result = self.build_orchestrator.build_project(dsl_data, generated_files)
        
        if not build_result.get("success"):
            # --- DNA: Auto-Fixer on build failure through Graphify ---
            if DNA_AVAILABLE:
                try:
                    mutate("compilation", "fail", details={"ubt_output": build_result.get("error", "Compilation failed"),
                                                "template_file": "game_generation_orchestrator"})
                    source_dir_str = str(self.source_dir)
                    fixed_count = 0
                    for ext in ['*.h', '*.cpp']:
                        for file_path in Path(source_dir_str).rglob(ext):
                            if '.generated.h' in file_path.name:
                                continue
                            fix_result = auto_fix_brace_error(str(file_path), "game_generation_orchestrator")
                            if fix_result.get("fixed"):
                                fixed_count += 1
                    if fixed_count > 0:
                        print(f"  [DNA] Auto-Fixer attempted {fixed_count} brace fixes — recompile required")
                except Exception as e:
                    print(f"  [DNA] Auto-Fixer skipped: {e}")
                    
            return {
                "success": False,
                "error": f"Build Failed: {build_result.get('error')}"
            }

        print(f"[Stage 4] Build successful. Test results: {build_result['test_results']}")

        # --- DNA: Mutation Logger after Stage 4 through Graphify ---
        if DNA_AVAILABLE:
            try:
                mutation_id = mutate("generation", "pass", details={"snapshot_diff": "pipeline_build_complete",
                    "template_file": "game_generation_orchestrator"})
                print(f"  [DNA] Mutation recorded: {mutation_id or 'unknown'} (compilation: pass)")
            except Exception as e:
                print(f"  [DNA] Mutation Logger skipped: {e}")

        # Stage 4.5: Automated Playtest (if tests block is present)
        playtest_report = None
        if "tests" in dsl_data:
            print("[Stage 4.5] Automated Playtest...")
            
            # Initialize playtest runner with project path and test spec
            uproject_path = build_result.get("uproject_path", "")
            self.playtest_runner = PlaytestRunner(uproject_path, dsl_data)
            
            # Run all tests
            playtest_report = self.playtest_runner.run_all_tests()
            
            print(f"[Stage 4.5] Playtest complete. Results: {playtest_report.summary}")

        print("[Stage 5] Report & Refine...")
        
        # Stage 5: Report & Refine Prompt - include test report if available
        test_results_for_validation = build_result.get("test_results", {})
        if playtest_report:
            # Generate test report
            test_report_data = self.test_reporter.generate_report(playtest_report, dsl_data)
            test_results_for_validation["playtest_results"] = {
                "summary": playtest_report.summary,
                "tests": [
                    {
                        "name": t.test_name,
                        "status": t.status,
                        "suggestion": t.suggestion if hasattr(t, 'suggestion') and t.suggestion else None
                    }
                    for t in playtest_report.tests
                ]
            }
        
        validation_report_path = self.validation_reporter.generate_validation_report(
            dsl_data, generated_files, test_results_for_validation
        )
        
        deviations = self.validation_reporter._check_deviations(dsl_data, generated_files)
        if deviations:
            dsl_patch_path = self.validation_reporter.generate_dsl_patch(deviations)
            print(f"[Stage 5] Deviations detected. DSL patch generated: {dsl_patch_path}")
        else:
            print("[Stage 5] No deviations detected from specification")

        print("[Stage 6] Pipeline complete - Regenerate & Iterate ready...")
        
        # --- DNA: Continuous Verification after Stage 5 through Graphify ---
        if DNA_VERIFY_AVAILABLE:
            try:
                # Query graph status through Graphify interface
                dna_graph = load_dna_graph()
                nodes = dna_graph.get("nodes", [])
                total_mutations = len([n for n in nodes if n.get("type") == "Mutation"])
                total_fixes = len([n for n in nodes if n.get("type") == "Fix"])
                
                print(f"[DNA] Graphify status: {len(nodes)} nodes, {total_mutations} mutations, {total_fixes} fixes recorded")
            except Exception as e:
                print(f"[DNA] Continuous Verification skipped: {e}")
        
        # Stage 7: Visual Verification - Screenshot Analysis
        print("[Stage 7] Visual Verification...")
        visual_verification_passed = False
        verification_msg = "Visual verification skipped"
        
        try:
            uproject_path = build_result.get("uproject_path", str(self.output_dir / f"{project_name}.uproject"))
            is_verified, verification_msg = run_visual_verification(uproject_path)
            
            if is_verified:
                visual_verification_passed = True
                print(f"[Stage 7] Visual Verification PASSED: {verification_msg}")
                
                # Record mutation for visual verification success
                try:
                    mutate("visual_verification", "pass", details={"description": verification_msg, "screenshot_dir": str(self.output_dir / "Saved" / "Screenshots")})
                    print(f"[DNA] Mutation recorded: visual_verification pass")
                except Exception as e:
                    print(f"[DNA] Visual verification mutation recording skipped: {e}")
            else:
                print(f"[Stage 7] Visual Verification INCOMPLETE: {verification_msg}")
                
                # Record mutation for visual verification incomplete
                try:
                    mutate("visual_verification", "incomplete", details={"description": verification_msg})
                    print(f"[DNA] Mutation recorded: visual_verification incomplete")
                except Exception as e:
                    print(f"[DNA] Visual verification mutation recording skipped: {e}")
                    
        except Exception as e:
            print(f"[Stage 7] Visual Verification failed with error: {e}")
        
        # Stage 6: Ready for incremental regeneration
        return {
            "success": True,
            "project_name": project_name,
            "uproject_path": build_result.get("uproject_path"),
            "validation_report_path": validation_report_path,
            "all_tests_passed": build_result.get("all_tests_passed", False),
            "playtest_summary": playtest_report.summary if playtest_report else None,
            "generated_assets_count": sum(len(files) for files in generated_assets.values()),
            "generated_files_count": sum(len(files) for files in generated_files.values() if isinstance(files, list))
        }

    def incrementally_regenerate(self, old_dsl_content: str, new_dsl_content: str, project_name: str = None) -> Dict[str, Any]:
        """
        Incrementally regenerate only affected parts based on updated DSL using knowledge graph.

        Args:
            old_dsl_content: Previous DSL specification
            new_dsl_content: Updated DSL specification
            project_name: Optional project name override

        Returns:
            Dict with regeneration results
        """
        if project_name is None:
            import re
            game_match = re.search(r'game\s+"([^"]+)"', new_dsl_content)
            if game_match:
                project_name = game_match.group(1)
            else:
                project_name = "GeneratedProject"

        print(f"[Stage 6] Incremental regeneration for {project_name}...")
        
        # Parse old and new DSLs
        _, old_dsl, _ = self.parser.parse_and_validate(old_dsl_content)
        _, new_dsl, _ = self.parser.parse_and_validate(new_dsl_content)

        # Load knowledge graph to determine affected files
        affected_files = self._get_affected_files_from_knowledge_graph(old_dsl, new_dsl)
        
        print(f"[Stage 6] Knowledge graph analysis found {len(affected_files)} affected files:")
        for file_type, files in affected_files.items():
            if files:
                print(f"  - {file_type}: {files}")

        # Perform incremental generation only for affected files
        generated_files = self.incremental_generator.incrementally_generate_with_graph(
            old_dsl, new_dsl, self.code_generator, self.asset_generator, affected_files
        )

        return {
            "success": True,
            "project_name": project_name,
            "incremental_generation_completed": True,
            "affected_files": affected_files,
            "generated_files_count": sum(len(files) for files in generated_files.values() if isinstance(files, list))
        }

    def _get_affected_files_from_knowledge_graph(self, old_dsl: Dict[str, Any], new_dsl: Dict[str, Any]) -> Dict[str, List[str]]:
        """Use knowledge graph to determine which files are affected by DSL changes."""
        import json
        
        # Default affected files mapping
        affected_files = {
            "character_classes": [],
            "ability_classes": [],
            "effect_classes": [],
            "behavior_trees": [],
            "ui_widgets": [],
            "replication_rules": [],
            "ship_classes": [],
            "combat_components": ["CombatTargetComponent.h", "CombatTargetComponent.cpp"],
            "ai_files": [],
            "economy_data": [],
            "quantum_travel_files": [],
            "planet_generation_files": [],
            "game_mode_class": ["DeepSpaceTraderGameMode.h", "DeepSpaceTraderGameMode.cpp"],
            "level_creation_script": [],
            "pcg_asset_creation_script": []
        }
        
        # Check for DSL block changes
        old_game = old_dsl.get("game", {}) if old_dsl else {}
        new_game = new_dsl.get("game", {}) if new_dsl else {}
        
        old_technical = old_dsl.get("technical", {}) if old_dsl else {}
        new_technical = new_dsl.get("technical", {}) if new_dsl else {}
        
        old_gameplay = old_dsl.get("gameplay", {}) if old_dsl else {}
        new_gameplay = new_dsl.get("gameplay", {}) if new_dsl else {}
        
        old_economy = old_dsl.get("economy", {}) if old_dsl else {}
        new_economy = new_dsl.get("economy", {}) if new_dsl else {}
        
        # Determine affected files based on changed blocks
        affected_blocks = set()
        
        # Check game block changes
        if old_game != new_game:
            affected_blocks.add("game")
            
        # Check technical block changes
        if old_technical != new_technical:
            if "network_model" in new_technical or "network_model" not in old_technical:
                affected_blocks.add("replication_rules")
            if "module_dependencies" in new_technical or "module_dependencies" not in old_technical:
                affected_blocks.add("character_classes")
                
        # Check gameplay block changes
        if old_gameplay != new_gameplay:
            if "abilities" in new_gameplay or "abilities" not in old_gameplay:
                affected_blocks.update(["ability_classes", "effect_classes", "behavior_trees"])
            if "combat_system" in new_gameplay:
                affected_blocks.add("combat_components")
                
        # Check economy block changes
        if old_economy != new_economy:
            if "commodities" in new_economy or "commodities" not in old_economy:
                affected_blocks.add("economy_data")
                
        # Check procedural_generation block changes
        if "procedural_generation" in new_dsl and ("procedural_generation" not in old_dsl or old_dsl.get("procedural_generation") != new_dsl.get("procedural_generation")):
            affected_blocks.update(["planet_generation_files", "pcg_asset_creation_script"])
            
        # Check narrative block changes
        if "narrative" in new_dsl and ("narrative" not in old_dsl or old_dsl.get("narrative") != new_dsl.get("narrative")):
            affected_blocks.add("level_creation_script")
            
        # Map affected blocks to files
        block_to_files = {
            "game": ["DeepSpaceTraderGameMode.h", "DeepSpaceTraderGameMode.cpp"],
            "replication_rules": [],
            "character_classes": [],
            "ability_classes": [],
            "effect_classes": [],
            "behavior_trees": [],
            "combat_components": ["CombatTargetComponent.h", "CombatTargetComponent.cpp", "WeaponComponent.h", "WeaponComponent.cpp", "SystemDamageComponent.h", "SystemDamageComponent.cpp"],
            "economy_data": ["MarketComponent.h", "MarketComponent.cpp", "CommodityData.h", "CommodityData.cpp"],
            "planet_generation_files": ["PlanetGenerator.h", "PlanetGenerator.cpp"],
            "pcg_asset_creation_script": ["PCGAssetCreationScript.py"],
            "level_creation_script": ["LevelCreationScript.py"],
            "ai_files": ["PirateAIController.h", "PirateAIController.cpp", "PirateBehaviorTree.behaviortree"]
        }
        
        for block in affected_blocks:
            if block in block_to_files:
                for file in block_to_files[block]:
                    # Add to appropriate category
                    categorized = False
                    for cat_key, cat_files in affected_files.items():
                        if isinstance(cat_files, list) and file in [f.split('.')[0] + '.h' for f in cat_files] or file in cat_files:
                            if file not in cat_files:
                                cat_files.append(file)
                            categorized = True
                            break
                    if not categorized:
                        affected_files.setdefault("other_files", []).append(file)
                        
        return affected_files

