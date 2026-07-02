"""
Code Generation Orchestrator — AI-powered C++ and Blueprint code repair workflow.

Integrates with lmstudio_client.generate_code_from_prompt() to:
1. Accept natural language descriptions of broken/removed code files
2. Generate or repair C++ (.cpp/.h) or Blueprint (event graph / component hierarchy) code snippets
3. Output repaired source code files to the appropriate project directories

Usage:
    from core.code_generation_orchestrator import CodeGenerationOrchestrator
    orchestrator = CodeGenerationOrchestrator()
    result = orchestrator.generate_code(
        prompt="Fix broken Kenney cockpit mesh refs in ChimeraPilotPawn.cpp",
        language="cpp",
        file_path="Chimera/Source/Chimera/ChimeraPilotPawn.cpp"
    )
"""

import os
from pathlib import Path

# Import LM Studio client
try:
    from Python.lmstudio_client import generate_code_from_prompt, SystemPromptTemplate
except ImportError:
    try:
        from lmstudio_client import generate_code_from_prompt, SystemPromptTemplate
    except ImportError:
        # Mock client for testing if LM Studio client is unavailable
        def generate_code_from_prompt(prompt, language="cpp", system_template=None, model_id=None, temperature=0.1, max_tokens=2048, timeout=180):
            return {"language": language, "code": f"Mock code for: {prompt}", "explanation": "Mock explanation", "filename_hint": f"{language}_generated"}

        class SystemPromptTemplate:
            @staticmethod
            def from_config(template_name):
                if template_name == "code_generation":
                    return "You are an expert C++ and Unreal Engine code generation assistant."
                return "You are a helpful assistant."


class CodeGenerationOrchestrator:
    """Orchestrates AI-powered C++ and Blueprint code generation and repair."""

    def __init__(self, project_root: str = None):
        """
        Initialize the orchestrator with project root path.

        Args:
            project_root: Root directory of the Unreal project (defaults to Chimera parent)
        """
        if project_root is None:
            # Default to Chimera project root
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)

    def generate_cpp_code(self, prompt: str, file_path: str = None, model_id: str = None, temperature: float = 0.1, max_tokens: int = 2048, timeout: int = 180) -> dict:
        """
        Generate or repair C++ code based on the prompt.

        Args:
            prompt: Description of the code to generate or fix
            file_path: Optional target file path for context
            model_id: Optional LM Studio model ID override
            temperature: Lower for more deterministic code output
            max_tokens: Max tokens in response (higher for complex code)
            timeout: Request timeout in seconds

        Returns:
            Dict with 'success', 'code' (str), 'explanation' (str), 'filename_hint' (str), or 'error' message
        """
        # Build system prompt for C++ code generation with file context if available
        file_context = ""
        if file_path and Path(file_path).exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_context = f.read()
            except Exception:
                file_context = f"[Could not read file: {file_path}]"

        system_template = (
            "You are an expert C++ developer specializing in Unreal Engine 5. "
            "Generate production-quality code following UE coding standards. "
            "Include proper includes, UCLASS/USTRUCT annotations, UPROPERTY macros, "
            "and handle memory management correctly. Provide a brief explanation of the implementation."
        )

        enhanced_prompt = f"""Generate or repair C++ code based on this request:

{prompt}

File Context (if available):
{file_context if file_context else "[No file context provided]"}

Output ONLY valid C++ code with necessary includes and explanations."""

        result = generate_code_from_prompt(
            prompt=enhanced_prompt,
            language="cpp",
            system_template=system_template,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )

        if not result or "code" not in result:
            return {
                "success": False,
                "error": "No code generated from LM Studio API"
            }

        return {
            "success": True,
            "code": result.get("code", ""),
            "explanation": result.get("explanation", ""),
            "filename_hint": result.get("filename_hint", file_path or "ChimeraPilotPawn.cpp"),
            "language": "cpp"
        }

    def generate_typescript_code(self, prompt: str, file_path: str = None, model_id: str = None, temperature: float = 0.1, max_tokens: int = 2048, timeout: int = 180) -> dict:
        """
        Generate or repair TypeScript code based on the prompt.

        Args:
            prompt: Description of the TypeScript code to generate or fix
            file_path: Optional target file path for context
            model_id: Optional LM Studio model ID override
            temperature: Lower for more deterministic code output
            max_tokens: Max tokens in response (higher for complex code)
            timeout: Request timeout in seconds

        Returns:
            Dict with 'success', 'code' (str), 'explanation' (str), 'filename_hint' (str), or 'error' message
        """
        # Build system prompt for TypeScript code generation
        file_context = ""
        if file_path and Path(file_path).exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_context = f.read()
            except Exception:
                file_context = f"[Could not read file: {file_path}]"

        system_prompt = (
            "You are an expert TypeScript developer specializing in game development and Node.js/TypeScript patterns. "
            "Generate production-quality TypeScript code following best practices. "
            "Include proper imports, exports, type definitions, and error handling. Provide a brief explanation of the implementation."
        )

        enhanced_prompt = f"""Generate TypeScript code based on this request:

{prompt}

File Context (if available):
{file_context if file_context else "[No file context provided]"}

Requirements:
- Use modern TypeScript patterns (ES6+, type definitions, interfaces)
- Include proper imports/exports
- Follow TypeScript naming conventions
- Provide the code in a markdown code block with ```typescript ... ```

Output ONLY valid TypeScript code in a markdown code block."""

        # Import send_to_lmstudio directly
        try:
            from Python.lmstudio_client import send_to_lmstudio
        except ImportError:
            try:
                from lmstudio_client import send_to_lmstudio
            except ImportError:
                return {"success": False, "error": "LM Studio client not available"}

        # Send request to LM Studio
        result = send_to_lmstudio(
            prompt=enhanced_prompt,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

        if not result or "content" not in result:
            return {
                "success": False,
                "error": "No TypeScript code generated from LM Studio API"
            }

        content = result.get("content", "")
        
        # Debug: print content length to help diagnose issues
        # print(f"[DEBUG TS] LM Studio response content length: {len(content)}")
        # if len(content) > 0 and len(content) < 500:
        #     print(f"[DEBUG TS] Content preview: {content[:300]}")
        
        # Extract TypeScript code from markdown code blocks
        import re
        ts_match = re.search(r'```(?:typescript|ts)?\s*(.*?)\s*```', content, re.DOTALL)
        if ts_match:
            ts_code = ts_match.group(1).strip()
        else:
            # Fallback: try to extract any code block
            ts_match = re.search(r'```\w+\s*(.*?)\s*```', content, re.DOTALL)
            if ts_match:
                ts_code = ts_match.group(1).strip()
            else:
                # Last fallback: use the entire content if no code blocks found
                # But only if it looks like TypeScript (has import/export/type/interface keywords)
                if 'import' in content.lower() or 'export' in content.lower() or 'interface' in content.lower() or 'type ' in content.lower():
                    ts_code = content.strip()
                else:
                    ts_code = ""

        # Determine filename hint
        filename_hint = "generated_ts.ts"
        if file_path and '/' in file_path:
            filename_hint = file_path.split('/')[-1]
        elif file_path:
            filename_hint = file_path

        return {
            "success": True,
            "code": ts_code,
            "explanation": "TypeScript code generated from LM Studio",
            "filename_hint": filename_hint,
            "language": "typescript"
        }

    def save_generated_code(self, code_result: dict, target_dir: str = None) -> str:
        """
        Save generated code to a file.

        Args:
            code_result: Dict from generate_cpp_code or generate_blueprint_code
            target_dir: Optional target directory for saved files

        Returns:
            Path to the saved file, or empty string on failure
        """
        if not code_result.get("success"):
            return ""

        code = code_result.get("code", "")
        filename_hint = code_result.get("filename_hint", "generated_code")
        
        # Determine extension based on language
        if code_result.get("language") == "cpp":
            ext = ".cpp" if not filename_hint.endswith(".h") else ".h"
            if not filename_hint.endswith(ext):
                filename_hint += ext
        elif code_result.get("language") == "blueprint":
            filename_hint += ".bp.txt"  # Blueprint descriptions saved as .txt

        # Determine output directory
        if target_dir:
            output_dir = Path(target_dir)
        else:
            output_dir = self.project_root / "GeneratedCode"

        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / filename_hint

        # Save code with explanation
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"// Generated by CodeGenerationOrchestrator\n")
            f.write(f"// Explanation: {code_result.get('explanation', '')}\n")
            f.write(f"//\n")
            f.write(code)

        return str(output_file)
