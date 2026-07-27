"""
ANTLR4 Parser Generator Script

Generates Python parser and lexer from ChimeraDSL.g4 using the ANTLR4 tool.

Requirements:
- Java Runtime Environment (JRE) installed and in PATH
- antlr-4.13.2-complete.jar downloaded

Usage:
    python generate_antlr_parser.py
"""

import os
import subprocess
from pathlib import Path

def generate_parser():
    """Generate ANTLR4 Python parser from grammar file."""
    script_dir = Path(__file__).parent
    schema_dir = script_dir.parent / 'schema'
    
    grammar_file = schema_dir / 'ChimeraDSL.g4'
    output_dir = schema_dir / 'generated_antlr'
    antlr_jar = script_dir.parent / 'antlr-4.13.2-complete.jar'
    
    print(f"Generating ANTLR4 Python parser from {grammar_file}")
    print(f"Output directory: {output_dir}")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if Java is available
    try:
        subprocess.run(['java', '-version'], capture_output=True, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("ERROR: Java Runtime Environment not found in PATH.")
        print("Please install JRE or JDK and ensure it's in your system PATH.")
        return False
    
    # Check if ANTLR4 jar exists
    if not antlr_jar.exists():
        print(f"ERROR: ANTLR4 jar not found at {antlr_jar}")
        print("Download it from: https://www.antlr.org/download/antlr-4.13.2-complete.jar")
        return False
    
    # Run ANTLR4 generator
    cmd = [
        'java', '-jar', str(antlr_jar),
        '-Dlanguage=Python3',
        str(grammar_file),
        '-o', str(output_dir),
        '-no-listener',
        '-visitor'
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERROR: ANTLR4 generation failed with return code {result.returncode}")
        print(f"stderr: {result.stderr}")
        return False
    
    # Check for generated files
    lexer_file = output_dir / 'ChimeraDSLLexer.py'
    parser_file = output_dir / 'ChimeraDSLParser.py'
    
    if lexer_file.exists() and parser_file.exists():
        print(f"SUCCESS: Generated parser files in {output_dir}")
        print(f"  - {lexer_file.name}")
        print(f"  - {parser_file.name}")
        
        # Create __init__.py to make it a Python module
        init_file = output_dir / '__init__.py'
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write("# ANTLR4 generated parser modules\n")
        
        return True
    else:
        print(f"ERROR: Expected files not found in {output_dir}")
        return False


if __name__ == '__main__':
    success = generate_parser()
    exit(0 if success else 1)
