#!/usr/bin/env python3
"""Comprehensive emoji removal for Windows console compatibility."""

import re
from pathlib import Path

# List of files to process
files = [
    "research_materials.py",
    "visual_validation_agent.py", 
    "test_recombination.py",
    "test_membrane_integration.py",
    "update_documentation.py"
]

def remove_all_unicode_special_chars(text):
    """Remove all Unicode special characters that might cause encoding issues."""
    # Remove variation selectors, emoji modifiers, and other problematic chars
    # This pattern catches:
    # - Variation selectors (fe0f, fe0e, etc.)
    # - Emoji skin tone modifiers
    # - Zero-width joiners
    # - Other Unicode formatting characters
    
    # Pattern for variation selectors and emoji modifiers
    special_chars = re.compile(
        "["
        "\uFE0F"     # Variation Selector-16 (emoji modifier)
        "\uFE0E"     # Variation Selector-15 (text modifier)  
        "\u200D"     # Zero Width Joiner
        "\u200C"     # Zero Width Non-Joiner
        "\u20E3"     # Combining Enclosing Keycap
        "\uFE00-\uFE0F"  # Variation selectors range
        "\uD83C[\uDF00-\uDFFF]"  # Supplemental Symbols and Pictographs
        "\uD83D[\uDC00-\uDFFF]"  # Enclosed Alphanumeric Supplement
        "\uD83E[\uDD00-\uDFFF]"  # Extended-A (emojis)
        "]+",
        flags=re.UNICODE
    )
    
    return special_chars.sub('', text)

def process_file(filepath):
    """Process a single file."""
    path = Path(filepath)
    
    if not path.exists():
        print(f"File not found: {filepath}")
        return False
    
    # Read content
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    cleaned_content = remove_all_unicode_special_chars(content)
    
    if cleaned_content != original:
        # Write back
        with open(path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        print(f"Cleaned {filepath}")
        return True
    else:
        print(f"No special chars found in {filepath}")
        return False

def main():
    print("Cleaning agent scripts for Windows console...")
    print("="*60)
    
    success_count = 0
    
    for filepath in files:
        if process_file(filepath):
            success_count += 1
    
    print("\n" + "="*60)
    print(f"Processed {success_count}/{len(files)} files successfully")
    print("All scripts should now work in Windows console.")

if __name__ == "__main__":
    main()
