"""
Configuration Diff Visualization and Change Summary Generation Utilities.
Provides human-readable summaries of configuration changes, highlights added/removed/modified values,
and formats diffs for reporting purposes.
"""

from typing import Dict, Any, Tuple


def highlight_changes(diffs: dict) -> dict:
    """Highlight added/removed/modified values in a diff dictionary.
    
    Args:
        diffs: Dictionary of differences with dotted path keys and (old_value, new_value) tuples.
        
    Returns:
        Dictionary with highlighted change types: [ADDED], [REMOVED], or [MODIFIED].
    """
    highlighted = {}
    for key, (old_val, new_val) in diffs.items():
        if old_val is None and new_val is not None:
            highlighted[f"[ADDED] {key}"] = new_val
        elif new_val is None and old_val is not None:
            highlighted[f"[REMOVED] {key}"] = old_val
        else:
            highlighted[f"[MODIFIED] {key}"] = {"old": old_val, "new": new_val}
    return highlighted


def format_diff_summary(diffs: dict) -> str:
    """Generate a human-readable summary of configuration changes.
    
    Args:
        diffs: Dictionary of differences with dotted path keys and (old_value, new_value) tuples.
        
    Returns:
        Human-readable string summarizing the changes.
    """
    if not diffs:
        return "No configuration changes detected."
    
    lines = ["=== Configuration Change Summary ==="]
    
    added_count = 0
    removed_count = 0
    modified_count = 0
    
    for key, (old_val, new_val) in diffs.items():
        if old_val is None and new_val is not None:
            lines.append(f"+ ADDED: {key} = {repr(new_val)}")
            added_count += 1
        elif new_val is None and old_val is not None:
            lines.append(f"- REMOVED: {key} = {repr(old_val)}")
            removed_count += 1
        else:
            lines.append(f"~ MODIFIED: {key}")
            lines.append(f"    Old: {repr(old_val)}")
            lines.append(f"    New: {repr(new_val)}")
            modified_count += 1
            
    lines.append("=== Summary Counts ===")
    lines.append(f"Added: {added_count}")
    lines.append(f"Removed: {removed_count}")
    lines.append(f"Modified: {modified_count}")
    
    return "\n".join(lines)


def generate_change_report(base_dict: dict, new_dict: dict, diff_func=None) -> str:
    """Generate a formatted change report comparing two configuration dictionaries.
    
    Args:
        base_dict: Base configuration dictionary.
        new_dict: New configuration dictionary to compare against.
        diff_func: Optional function to compute diffs.
        
    Returns:
        Formatted change report string.
    """
    def _get_config_diffs(base, new, prefix=""):
        diffs = {}
        all_keys = set(base.keys()) | set(new.keys())
        for key in all_keys:
            full_key = f"{prefix}.{key}" if prefix else key
            if key not in base:
                diffs[full_key] = (None, new[key])
            elif key not in new:
                diffs[full_key] = (base[key], None)
            elif isinstance(base[key], dict) and isinstance(new[key], dict):
                nested_diffs = _get_config_diffs(base[key], new[key], full_key)
                if nested_diffs:
                    diffs.update(nested_diffs)
            elif base[key] != new[key]:
                diffs[full_key] = (base[key], new[key])
        return diffs
    
    diffs = diff_func(base_dict, new_dict) if diff_func else _get_config_diffs(base_dict, new_dict)
    
    report_lines = [
        "========================================",
        "CONFIGURATION CHANGE REPORT",
        "========================================"
    ]
    
    summary = format_diff_summary(diffs)
    report_lines.append(summary)
    report_lines.append("========================================")
    
    return "\n".join(report_lines)


def print_diff_summary(diffs: dict) -> None:
    """Print a human-readable summary of configuration changes to stdout."""
    print(format_diff_summary(diffs))


def print_highlighted_changes(diffs: dict) -> None:
    """Print highlighted changes (added/removed/modified) to stdout."""
    highlighted = highlight_changes(diffs)
    for key, value in highlighted.items():
        if isinstance(value, dict) and "old" in value and "new" in value:
            print(f"{key}:")
            print(f"  Old: {repr(value['old'])}")
            print(f"  New: {repr(value['new'])}")
        else:
            print(f"{key}: {repr(value)}")
