"""
DSL Workflow Orchestrator — AI-powered term alignment and logic generation workflow.

Integrates the Declarative, Schema-Validated DSL System with LM Studio API to:
1. Accept natural language prompts for term alignment and logic mapping
2. Generate DSL JSON conforming to dsl_schema.json using LLM
3. Validate generated DSL against schema using DSLSchemaValidator
4. Execute validated DSL using WorkflowInterpreter to produce Unreal-compatible .json config files

Usage:
    from core.dsl_workflow_orchestrator import DSLWorkflowOrchestrator
    orchestrator = DSLWorkflowOrchestrator(
        registry_path='registry/term_registry.json',
        schema_path='schema/dsl_schema.json',
        output_dir='Content/ProceduralGenerated/Workflows'
    )
    result = orchestrator.process_prompt("Align Component Alpha with Data Processor")
"""

import json
import os
from pathlib import Path

# Import local DSL components
try:
    from core.validator import DSLSchemaValidator
    from core.interpreter import WorkflowInterpreter
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(str(Path(__file__).parent))
    from validator import DSLSchemaValidator
    from interpreter import WorkflowInterpreter

# Import LM Studio client
try:
    from Python.lmstudio_client import send_to_lmstudio, JSONModeConfig, parse_structured_output
except ImportError:
    try:
        from lmstudio_client import send_to_lmstudio, JSONModeConfig, parse_structured_output
    except ImportError:
        # Mock client for testing if LM Studio client is unavailable
        def send_to_lmstudio(prompt, model_id=None, temperature=0.1, max_tokens=2048, timeout=120):
            return {"content": f"Mock response for: {prompt}"}

        class JSONModeConfig:
            def __init__(self, schema=None, strict_mode=True):
                self.schema = schema
                self.strict_mode = strict_mode

        def parse_structured_output(response, config=None):
            if response and "content" in response:
                return {"raw_content": response["content"]}
            return {}


class DSLWorkflowOrchestrator:
    """Orchestrates AI-powered DSL generation, validation, and execution for Unreal Engine."""

    def __init__(self, registry_path: str, schema_path: str, output_dir: str):
        """
        Initialize the orchestrator with registry, schema, and output directory paths.

        Args:
            registry_path: Path to term_registry.json
            schema_path: Path to dsl_schema.json
            output_dir: Output directory for Unreal .json config files
        """
        self.registry_path = Path(registry_path)
        self.schema_path = Path(schema_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize validator and interpreter
        self.validator = DSLSchemaValidator(str(self.schema_path))
        self.interpreter = WorkflowInterpreter(str(self.registry_path), str(self.output_dir))

        # Load term registry for AI reference
        with open(self.registry_path, 'r') as f:
            self.term_registry = json.load(f)['terms']

    def _build_ai_prompt(self, natural_language_prompt: str) -> str:
        """Build the system prompt for LM Studio based on the DSL schema and term registry."""
        terms_list = "\n".join([f"- {uid}: {info['label']} (synonyms: {', '.join(info['synonyms'])})" 
                                for uid, info in self.term_registry.items()])

        prompt_template = """You are a logic mapping engine for an Unreal Engine procedural generation system. 
Your task is to translate natural language logic requests into a Declarative Workflow DSL JSON. 

Semantic Term Registry - Map all conceptual terms to these UIDs:
{terms_list}

DSL Schema Requirements:
- Output ONLY valid JSON conforming to the schema below. No explanations, no markdown, no code blocks.
- Use operations exactly as: "semantic_match", "log_alignment", or "conditional_branch"
- source_uid must be a string matching pattern: "^TERM_\\d+$"
- target_uid (if present) must be a string matching pattern: "^TERM_\\d+$"
- confidence_score (if present) must be a number between 0.0 and 1.0

Exact JSON Format Example:
{{
  "workflow_id": "workflow_demo_001",
  "steps": [
    {{
      "step_id": "step_001",
      "operation": "semantic_match",
      "source_uid": "TERM_001",
      "target_uid": "TERM_002",
      "condition": "context_overlap > 0.75"
    }},
    {{
      "step_id": "step_002",
      "operation": "log_alignment",
      "source_uid": "TERM_001",
      "target_uid": "TERM_002",
      "confidence_score": 0.85
    }}
  ]
}}

Natural Language Request:
"{prompt}"

Generate ONLY the valid JSON workflow mapping terms and logic. Do not include any text before or after the JSON:""".format(
            terms_list=terms_list,
            prompt=natural_language_prompt
        )
        return prompt_template

    def generate_dsl_from_prompt(self, natural_language_prompt: str, model_id: str = None) -> dict:
        """
        Generate DSL JSON from a natural language prompt using LM Studio.

        Args:
            natural_language_prompt: Human-readable logic/request text
            model_id: Optional LM Studio model ID override

        Returns:
            Dict with 'success' boolean and 'dsl_json' or 'error' message
        """
        system_prompt = self._build_ai_prompt(natural_language_prompt)

        # Send to LM Studio for DSL generation
        response = send_to_lmstudio(
            prompt=system_prompt,
            model_id=model_id,
            temperature=0.1,  # Low temperature for deterministic JSON output
            max_tokens=2048,
            timeout=120
        )

        if not response:
            return {"success": False, "error": "No response from LM Studio API"}

        # Extract content from response (handle both 'content' and 'raw_content' structures)
        content = ""
        if isinstance(response, dict):
            content = response.get("content", "") or response.get("raw_content", "") or ""
            # Also check for reasoning_content if content is empty
            if not content and "reasoning_content" in response:
                content = response.get("reasoning_content", "")
        else:
            content = str(response) if response else ""

        # Debug: print content length to help diagnose issues
        # print(f"[DEBUG] LM Studio response content length: {len(content)}")

        # Try to extract JSON block from markdown code fences
        import re
        # Pattern 1: ```json ... ``` or ``` ... ```
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content)
        if json_match:
            dsl_json_string = json_match.group(1)
        else:
            # Pattern 2: Find the first { and last } that form a valid JSON object
            # Look for workflow_id pattern to identify the JSON block
            json_start = content.find('{"workflow_id"')
            if json_start == -1:
                json_start = content.find('{\n  "workflow_id"')
            if json_start == -1:
                json_start = content.find('{\n"workflow_id"')
            
            if json_start != -1:
                # Find the matching closing brace
                # Simple approach: find the last } that appears after a reasonable number of characters
                json_end = content.rfind('}')
                if json_end > json_start:
                    dsl_json_string = content[json_start:json_end+1]
                else:
                    return {"success": False, "error": f"No valid JSON found in LM Studio response. Raw content preview (first 800 chars): {content[:800]}"}
            else:
                # Fallback: try to find any { ... } block that contains 'workflow_id' or 'steps'
                json_match = re.search(r'\{[\s\S]*?"workflow_id"[\s\S]*?"steps"[\s\S]*?\}', content, re.DOTALL)
                if json_match:
                    dsl_json_string = json_match.group(0)
                else:
                    return {"success": False, "error": f"No valid JSON found in LM Studio response. Raw content preview (first 800 chars): {content[:800]}"}

        return {
            "success": True,
            "dsl_json": dsl_json_string,
            "raw_content": content
        }

    def validate_dsl(self, dsl_json_string: str) -> tuple[bool, str | None]:
        """
        Validate DSL JSON against the schema.

        Args:
            dsl_json_string: Generated DSL JSON string

        Returns:
            Tuple of (is_valid, error_message_or_None)
        """
        return self.validator.validate(dsl_json_string)

    def process_prompt(self, natural_language_prompt: str, workflow_id: str = None, model_id: str = None) -> dict:
        """
        Complete workflow: generate DSL from prompt, validate, and execute.

        Args:
            natural_language_prompt: Human-readable logic/request text
            workflow_id: Optional workflow ID override (defaults to timestamp-based ID)
            model_id: Optional LM Studio model ID override

        Returns:
            Dict with 'success', 'workflow_file' (if successful), or 'error' message
        """
        if workflow_id is None:
            import time
            workflow_id = f"workflow_{int(time.time()) % 100000}"

        # Step 1: Generate DSL from prompt
        gen_result = self.generate_dsl_from_prompt(natural_language_prompt, model_id)
        
        if not gen_result.get("success"):
            return {
                "success": False,
                "error": f"DSL Generation Failed: {gen_result.get('error')}"
            }

        dsl_json_string = gen_result["dsl_json"]

        # Step 2: Validate DSL against schema
        is_valid, validation_error = self.validate_dsl(dsl_json_string)
        
        if not is_valid:
            return {
                "success": False,
                "error": f"DSL Validation Failed: {validation_error}"
            }

        # Step 3: Execute validated DSL and save to Unreal config format
        try:
            dsl_data = json.loads(dsl_json_string)
            output_file = self.interpreter.execute_and_save(dsl_data, workflow_id)
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "workflow_file": str(output_file),
                "steps_count": len(dsl_data.get('steps', []))
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"DSL Execution Failed: {str(e)}"
            }
