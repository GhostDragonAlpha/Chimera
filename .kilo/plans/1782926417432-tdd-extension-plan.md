# TDD Extension Implementation Plan

## Overview

Add automated behavioral testing to the Chimera DSL-driven game generation pipeline by introducing a `tests` DSL block, test harness code generator, Playtest Runner (Stage 4.5), and Test Reporter that maps results back to DSL blocks with failure suggestions.

## Core Design Decisions

1. **Test DSL Block Format**: Use block format `tests { test "Name" { type="unit"; setup {...}; action {...}; assert {...}; cleanup {...} } }` matching existing DSL patterns (not anonymous array properties).

2. **Test API Access Pattern**: Generate a static `UTestAPI` class alongside game code with concrete methods referencing specific generated types (e.g., `GA_Dash`, `ASurvivalAttributeSet`). Each test file includes `#include "TestAPI.h"` for compile-time safety—no string-based class lookup at runtime.

3. **Fallback Behavior**: When UE is not installed or test module fails to compile, mark tests as `"status": "skipped"` with explicit warning: `"UE editor executable not found at expected path. Install Unreal Engine 5.x or set UE_ROOT to enable automated playtesting."` Maintain transparency consistent with UBT/UAT fallback patterns.

4. **Headless Execution**: Tests run via `-NullRHI`, `-Unattended`, `-NoPause` flags—no GPU needed, fast execution.

## Implementation Tasks

### Task 1: Tests DSL Block Schema and Grammar
- Modify `Chimera/schema/dsl_game_schema.json`: Add `tests` block schema with `test_definitions` array containing `name`, `type` (unit/integration/balance), `description`, `iterations`, `setup`, `action`, `assert`, `cleanup`.
- Modify `Chimera/schema/ChimeraDSL.g4`: Add lexer keywords and parser rule `testsBlock: 'tests' '{' testDef+ '}';` with sub-rules for setup/action/assert/cleanup blocks.

### Task 2: Test DSL Parser and Validator
- Modify `Chimera/core/dsl_game_parser.py`: Add `_parse_tests_block(self, dsl_content: str) -> dict` method to extract test definitions from DSL content.
- Modify `Chimera/core/dsl_grammar_validator.py`: Add test reference validation in `ChimeraDSLVisitor.validate_semantic_references()`:
  - `spawn_actor(class="ClassName")` — ClassName must exist in `gameplay.characters` or `ship_classes.ships`
  - `grant_ability(ability="AbilityName")` — AbilityName must exist in `gameplay.abilities`
  - `craft_recipe(recipe="RecipeName")` — RecipeName must exist in `crafting_systems.recipes`
  - `set_biome(biome="BiomeName")` — BiomeName must exist in `planet_generation_systems.biome_configs`
  - `initialize_market(market="MarketName")` — MarketName must exist in `economy_systems.trade_routes`

### Task 3: Test Harness Code Generation
- Modify `Chimera/core/game_code_generator.py`: Add methods:
  - `_generate_test_harness(self, tests_spec: dict) -> dict`
  - `generate_test_api_header_and_source(self, dsl_data: dict) -> tuple[str, str]`
  - `generate_individual_test_file(self, test_def: dict) -> str`
  - `generate_tests_build_cs(self, project_name: str) -> str`

Generate file structure in `Source/{ProjectName}Tests/`:
- `{ProjectName}Tests.Build.cs` (depends on game module + `AutomationTest`)
- `TestAPI.h` / `TestAPI.cpp` (static UTEST_API class with generated methods for actor lifecycle, ability system, attributes, inventory/crafting, combat, status effects, environment, economy)
- One `.cpp` file per DSL test block implementing setup/action/assert/cleanup as latent automation tests

### Task 4: Playtest Runner Creation
- Create `Chimera/core/playtest_runner.py`: Implement `PlaytestRunner` class with methods:
  - `__init__(self, project_path: str, test_spec: dict)`
  - `run_all_tests(self) -> PlaytestReport`
  - `run_test(self, test_name: str) -> TestResult`
  - `run_tests_by_type(self, test_type: str) -> PlaytestReport`

Execution architecture:
- Invoke UE automation via command line: `{UE_ROOT}/Engine/Binaries/Win64/UnrealEditor-Cmd.exe {ProjectPath}.uproject -ExecCmds="Automation RunTests {ProjectName}Tests" -NullRHI -NoSound -NoSplash -Unattended -NoPause -TestExit="Automation Test Queue Empty"`
- Parse UE's automation output and map results back to DSL test blocks.

### Task 5: Test Reporter Creation
- Create `Chimera/core/test_reporter.py`: Implement `TestReporter` class with methods:
  - `generate_report(self, results: PlaytestReport, dsl_spec: dict) -> dict`
  - `map_failure_to_dsl(self, test_name: str, failure_detail: str) -> DSLReference`

Output format written to `Chimera/GeneratedProjects/ValidationReports/test_report_{timestamp}.json`:
- Summary: total_tests, passed, failed, skipped, pass_rate
- Tests array with name, type, dsl_block, status, duration_ms, assertions, statistics (for balance tests with iterations), suggestion (for failures)
- Regression check: previous_pass_rate, current_pass_rate, new_failures, resolved_failures

### Task 6: Pipeline Integration
- Modify `Chimera/core/game_generation_orchestrator.py`: Add Stage 4.5 execution between Build (Stage 4) and Report & Refine (Stage 5), invoking `PlaytestRunner` and `TestReporter`.
- Modify `Chimera/core/build_orchestrator.py`: Add test module to generated `.uproject` `"Modules"` array; add module dependencies to test `.Build.cs`: game module + `AutomationTest`.

### Task 7: Comprehensive Test Spec File
- Create `Chimera/tests/dsl_grammar/tdd_test_suite.chimera` with tests covering:
  - GAS ability cooldowns (unit test)
  - Survival stat depletion (integration test)
  - Crafting recipe material consumption (unit test)
  - Combat balance with multiple iterations—iterations=100 (balance test)
  - Ship component failure integration (integration test)
  - Market price equilibrium—iterations=10 (balance test)
  - Biome temperature effects on player status (integration test)

## Success Criteria

1. `tdd_test_suite.chimera` parses and validates without errors
2. Test harness C++ compiles via UBT with zero errors
3. Playtest runner executes tests via UE's automation framework with `-NullRHI`, `-Unattended`, `-NoPause` flags
4. Test report maps all results back to DSL test blocks with failure suggestions
5. Existing specs (Echoes of Eternity, survival crafting, Star Citizen) still compile without regression
6. At least one failing test demonstrates the suggestion feature (proposed DSL fix in the report)

## Risks and Failure Modes

- **UE Automation Framework Compatibility**: UE's `FAutomationTestBase` framework requires specific test registration macros. Ensure generated test files use correct `IMPLEMENT_SIMPLE_AUTOMATION_TEST` or `IMPLEMENT_AUTOMATION_TEST` macros with proper flags.
- **Compile-Time Type Safety vs Runtime Flexibility**: The static `UTestAPI` class approach requires the code generator to know all generated types at generation time. If a test references an ability/component not generated, validation must catch it in Stage 1.
- **Balance Test Statistical Aggregation**: Running setup-action-assert loops 100 times for balance tests requires careful state management to ensure deterministic results and proper aggregation (mean, min, max, pass rate).

## Validation Steps

1. Parse `tdd_test_suite.chimera` through `dsl_game_parser.py` and `dsl_grammar_validator.py`—verify no syntax or semantic errors.
2. Generate test harness C++ files via `game_code_generator.py`—verify syntactic validity of generated `.h`, `.cpp`, and `.Build.cs` files.
3. Compile test module via UBT using `build_orchestrator.py`—verify zero compilation errors.
4. Execute playtest runner against compiled project (if UE available)—verify automation framework execution and output parsing.
5. Generate test report via `test_reporter.py`—verify JSON format matches specification and failure suggestions are present for failing tests.
6. Verify existing specs still compile without regression through full 7-stage pipeline.
