# AI Workflow Systems for Unreal Engine

This directory contains two complementary AI workflow systems designed to eliminate compiler errors and automate code generation/repair in Unreal Engine projects.

## System 1: Declarative, Schema-Validated DSL System

### Overview

This system eliminates compiler errors (C++ UHT and Blueprint compilation errors) by shifting from imperative programming to a **declarative, schema-validated data system** where AI generates structured JSON workflow data that is strictly validated before being saved as JSON Config Assets for Unreal Engine to consume via native "Parse JSON" Blueprint nodes.

### Components

1. **Semantic Term Registry (`registry/term_registry.json`)**  
   Maps human-readable letter terms to stable UIDs (e.g., `TERM_001`, `TERM_002`). Prevents alignment issues caused by case variations, typos, or abbreviations.

2. **Declarative Logic DSL Schema (`schema/dsl_schema.json`)**  
   JSON schema enforcing the exact structure of AI-generated workflow data. Acts as the "compiler" to prevent structural or syntax errors.

3. **Schema Validator (`core/validator.py`)**  
   Uses `jsonschema` to validate AI output against the DSL schema before execution. Rejects hallucinated operations or misspelled UIDs as data validation errors, not compiler errors.

4. **Execution Interpreter (`core/interpreter.py`)**  
   Minimal, deterministic engine that reads validated DSL JSON and outputs Unreal-compatible `.json` config files saved to `Content/ProceduralGenerated/Workflows/`.

5. **DSL Workflow Orchestrator (`core/dsl_workflow_orchestrator.py`)**  
   Integrates LM Studio API with DSL validation and execution. Accepts natural language prompts, generates DSL JSON via LLM, validates it, and outputs Unreal-compatible config files.

6. **DSL Workflow Demo (`core/dsl_workflow_demo.py`)**  
   Example usage demonstrating the complete workflow: prompt processing → DSL generation → schema validation → Unreal config output.

### Data Flow

```
Natural Language Prompt 
    → AI LLM (generates DSL JSON with UIDs via LM Studio)
    → Schema Validator (jsonschema enforcement)
    → If invalid: reject and prompt AI for correction
    → If valid: pass to Execution Interpreter
    → Output: .json config files in Content/ProceduralGenerated/Workflows/
    → Unreal Engine Blueprints load via native "Parse JSON" nodes
```

### Usage

Initialize orchestrator:
```python
from core.dsl_workflow_orchestrator import DSLWorkflowOrchestrator

orchestrator = DSLWorkflowOrchestrator(
    registry_path='registry/term_registry.json',
    schema_path='schema/dsl_schema.json',
    output_dir='Content/ProceduralGenerated/Workflows'
)

result = orchestrator.process_prompt(
    natural_language_prompt="Align Component Alpha with Data Processor and log the alignment with confidence score 0.85",
    workflow_id="my_workflow_001"
)
```

### Key Benefits

- **Zero Compiler Errors**: AI generates data (JSON), not executable code (C++/Blueprint nodes)
- **Schema Enforcement**: `jsonschema` validation catches hallucinated operations or misspelled UIDs as data errors, not syntax errors
- **Deterministic Execution**: Interpreter only processes predefined operations (`semantic_match`, `log_alignment`, `conditional_branch`)
- **Unreal-Compatible Output**: Native JSON config files consumable by Blueprint "Parse JSON" nodes

---

## System 2: Code Generation & Repair Orchestrator

### Overview

This system uses LM Studio's `generate_code_from_prompt()` to generate or repair C++ (`.cpp`/`.h`) and Blueprint source code files based on natural language descriptions of broken/removed code. It leverages git history and error descriptions to reconstruct or fix broken UE5 source files.

### Components

1. **Code Generation Orchestrator (`core/code_generation_orchestrator.py`)**  
   Integrates with `lmstudio_client.generate_code_from_prompt()` to generate C++ or Blueprint code based on natural language prompts. Supports file context injection for targeted repairs.

2. **Code Generation Demo (`core/code_generation_demo.py`)**  
   Example usage demonstrating C++ code repair (e.g., fixing broken Kenney cockpit mesh refs) and Blueprint design generation.

### Supported Operations

- **C++ Code Repair**: Generate or fix C++ source files based on error descriptions (e.g., "Fix broken Kenney cockpit mesh refs in ChimeraPilotPawn.cpp")
- **Blueprint Design Generation**: Create textual Blueprint design descriptions with component hierarchies and event graph logic
- **File Context Injection**: Optionally pass existing file content to provide context for targeted repairs

### Usage

Initialize orchestrator:
```python
from core.code_generation_orchestrator import CodeGenerationOrchestrator

orchestrator = CodeGenerationOrchestrator(project_root='E:\PythonChimera\Chimera')

# C++ code repair
cpp_result = orchestrator.generate_cpp_code(
    prompt="Fix broken Kenney cockpit mesh refs in ChimeraPilotPawn.cpp - remove broken references that cause CDO errors",
    file_path="Source/Chimera/ChimeraPilotPawn.cpp",
    model_id='qwen3.6-35b-a3b-mtp@iq2_m',
    temperature=0.1,
    max_tokens=2048,
    timeout=180
)

# Save generated code
saved_file = orchestrator.save_generated_code(cpp_result, target_dir='GeneratedCode')
```

### Key Benefits

- **C++ UHT Error Resolution**: Automatically generates valid UE5 C++ code with proper `UCLASS`/`UPROPERTY` macros and `CreateDefaultSubobject<>()` patterns
- **Blueprint Design Documentation**: Generates structured textual descriptions of Blueprint component hierarchies and event graph logic
- **Git History Integration**: Can be prompted with specific commit messages or error descriptions to reconstruct removed/broken files

---

## Dependencies

```bash
pip install jsonschema pydantic
```

## Files

| File | Purpose |
|------|---------|
| `registry/term_registry.json` | Semantic Term Registry mapping letter terms to UIDs |
| `schema/dsl_schema.json` | JSON schema enforcing AI-generated workflow data structure |
| `core/validator.py` | Schema validator using `jsonschema` |
| `core/interpreter.py` | Execution interpreter generating Unreal-compatible `.json` config assets |
| `core/dsl_workflow_orchestrator.py` | DSL orchestrator integrating LM Studio API with DSL validation and execution |
| `core/dsl_workflow_demo.py` | Demo script for DSL workflow |
| `core/code_generation_orchestrator.py` | Code generation orchestrator for C++/Blueprint repair |
| `core/code_generation_demo.py` | Demo script for code generation workflow |
| `workflows/ai_prompts.txt` | System prompts for LLM structured JSON output |

## Output Directories

- **DSL Workflow Outputs**: `Content/ProceduralGenerated/Workflows/*.json`
- **Code Generation Outputs**: `GeneratedCode/*.{cpp,h,bp.txt}`
