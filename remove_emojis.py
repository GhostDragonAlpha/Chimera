#!/usr/bin/env python3
"""Remove emojis from all agent scripts for Windows console compatibility."""

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

def remove_emojis(text):
    """Remove emoji characters from text."""
    # Pattern for emojis and other special Unicode chars that might cause issues
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # geometric shapes extended
        "\U0001F800-\U0001F8FF"  # supplemental arrows-D
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # extended-A
        "\U00002600-\U000026FF"  # misc symbols
        "\U00002700-\U000027BF"  # dingbats
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)

def process_file(filepath):
    """Process a single file."""
    path = Path(filepath)
    
    if not path.exists():
        print(f"⚠️ File not found: {filepath}")
        return False
    
    # Read content
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove emojis
    cleaned_content = remove_emojis(content)
    
    if cleaned_content != content:
        # Write back
        with open(path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        print(f"Removed emojis from {filepath}")
        return True
    else:
        print(f"No emojis found in {filepath}")
        return False

def main():
    print("Removing emojis from agent scripts...")
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
