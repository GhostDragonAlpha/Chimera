"""Groundskeeping_floor — fallback floor that's always executable using python+files only.

This is a fallback floor that performs basic file maintenance, cleanup, and housekeeping tasks
using only python+files, without requiring editor, LM, or network access.

THE FLOOR WORK: always executable (python+files only, no editor, no LM, no network);
wins only when everything else is blocked.

Deterministic policy (no LM, no editor, no network):
  - Clean up temporary/binary files (build artifacts, cache files)
  - Verify essential files exist and are readable
  - Check disk space and report available/used space
  - Validate graph integrity (chimera_dna_graph.json)
  - Exit 0 always — findings are work items, not crashes.

Usage: python -m core.groundskeeping_floor [--dry-run] [--cleanup]
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
CHIMERA_ROOT = ROOT
SOURCES_DIR = ROOT / "Source"
CONTENT_DIR = ROOT / "Content"
PYTHON_DIR = CHIMERA_ROOT / "Python"

# Files and directories to check for existence
ESSENTIAL_FILES = [
    ROOT / "Chimera.uproject",
    DOCS_DIR / "chimera_dna_graph.json",
    ROOT / "core" / "graphify_interface.py",
]

# Directories to verify exist
ESSENTIAL_DIRS = [
    ROOT,
    DOCS_DIR,
    SOURCES_DIR,
    ROOT / "Source" / "Chimera",
    ROOT / "Config",
]


def _now() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def check_disk_space(min_free_gb: int = 5) -> tuple[bool, list[str]]:
    """Check disk space for C:\\ and E:\\ drives.

    Returns: (all_ok, notes_list)
    """
    import shutil
    notes = []
    all_ok = True
    
    for drive in ["C:\\", "E:\\"]:
        try:
            free_gb = shutil.disk_usage(drive).free / 1e9
            used_gb = shutil.disk_usage(drive).used / 1e9
            total_gb = shutil.disk_usage(drive).total / 1e9
            notes.append(f"{drive[0]}: {free_gb:.2f}GB free / {used_gb:.2f}GB used / {total_gb:.2f}GB total")
            if free_gb < min_free_gb:
                all_ok = False
        except OSError:
            notes.append(f"{drive[0]}: unreadable drive")
            
    return all_ok, notes


def cleanup_temp_files(dry_run: bool = False) -> list[str]:
    """Clean up temporary and build artifact files.

    Returns list of cleaned file paths (or simulated paths if dry-run).
    """
    cleaned_files = []
    
    # Directories to scan for temp/cache files
    scan_dirs = [
        ROOT / "Saved",
        ROOT / "DerivedDataCache",
        ROOT / "Intermediate",
        ROOT / "Build",
        ROOT / ".vscode",
        DOCS_DIR,
    ]
    
    # Extensions that are typically temporary or build artifacts
    temp_extensions = {".bak", ".tmp", ".old", ".log", "~"}
    
    # Cache directories to clean (DerivedDataCache is UE specific)
    cache_dirs = ["DerivedDataCache"]
    
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
            
        try:
            for item in scan_dir.rglob("*"):
                if item.is_file():
                    ext = item.suffix.lower()
                    name = item.name
                    
                    # Clean up specific temp files
                    if any(name.endswith(ext) or ext in temp_extensions or name.startswith(".") for ext in [".bak", ".tmp", ".log", "~"]):
                        if not dry_run:
                            try:
                                item.unlink()
                                cleaned_files.append(str(item.relative_to(CHIMERA_ROOT)))
                            except OSError:
                                pass
                        else:
                            cleaned_files.append(f"[DRY-RUN] Would remove: {item.relative_to(CHIMERA_ROOT)}")
                            
        except Exception:
            pass
            
    return cleaned_files


def verify_essential_files() -> tuple[bool, list[str]]:
    """Verify that essential files and directories exist.

    Returns: (all_ok, issues_list)
    """
    issues = []
    all_ok = True
    
    for f in ESSENTIAL_FILES:
        if not f.exists():
            issues.append(f"MISSING: {f}")
            all_ok = False
            
    for d in ESSENTIAL_DIRS:
        if not d.exists():
            issues.append(f"MISSING DIR: {d}")
            all_ok = False
            
    return all_ok, issues


def validate_dna_graph() -> tuple[bool, str]:
    """Validate the chimera_dna_graph.json file for integrity.

    Returns: (is_valid, message)
    """
    graph_path = DOCS_DIR / "chimera_dna_graph.json"
    
    if not graph_path.exists():
        return False, f"DNA graph missing: {graph_path}"
        
    try:
        with open(graph_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        nodes = data.get("nodes", [])
        if not isinstance(nodes, list):
            return False, "DNA graph has no 'nodes' array"
            
        # Count node types
        node_types = {}
        for n in nodes:
            if isinstance(n, dict):
                nt = n.get("type", "unknown")
                node_types[nt] = node_types.get(nt, 0) + 1
                
        return True, f"DNA graph valid: {len(nodes)} nodes across types: {', '.join(f'{k}={v}' for k, v in sorted(node_types.items()))}"
        
    except json.JSONDecodeError as e:
        return False, f"DNA graph JSON parse error: {e}"
    except Exception as e:
        return False, f"DNA graph validation error: {e}"


def run_groundskeeping_floor(dry_run: bool = False, do_cleanup: bool = False) -> dict:
    """Run the complete groundskeeping floor routine.

    Returns a report dictionary with all findings.
    """
    report = {
        "timestamp": _now(),
        "dry_run": dry_run,
        "cleanup_performed": do_cleanup and not dry_run,
        "disk_space": {},
        "essential_files": {"ok": True, "issues": []},
        "dna_graph": {"valid": False, "message": ""},
        "cleaned_files": [],
    }
    
    # Check disk space
    disk_ok, disk_notes = check_disk_space(min_free_gb=5)
    report["disk_space"] = {
        "ok": disk_ok,
        "notes": disk_notes,
    }
    
    # Verify essential files
    files_ok, file_issues = verify_essential_files()
    report["essential_files"]["ok"] = files_ok
    report["essential_files"]["issues"] = file_issues
    
    # Validate DNA graph
    graph_valid, graph_msg = validate_dna_graph()
    report["dna_graph"]["valid"] = graph_valid
    report["dna_graph"]["message"] = graph_msg
    
    # Cleanup if requested
    if do_cleanup:
        cleaned = cleanup_temp_files(dry_run=dry_run)
        report["cleaned_files"] = cleaned
        
    return report


def main():
    parser = argparse.ArgumentParser(description="Groundskeeping_floor — fallback floor (python+files only)")
    parser.add_argument("--dry-run", action="store_true", help="Report without making changes")
    parser.add_argument("--cleanup", action="store_true", help="Perform file cleanup")
    args = parser.parse_args()
    
    report = run_groundskeeping_floor(dry_run=args.dry_run, do_cleanup=args.cleanup)
    
    print(f"[groundskeeping_floor] {_now()}")
    if args.dry_run:
        print("  MODE: DRY-RUN (no changes made)")
        
    # Disk space report
    disk_ok = report["disk_space"]["ok"]
    print(f"  [disk_space] {'OK' if disk_ok else 'WARNING'} — {', '.join(report['disk_space']['notes'])}")
    
    # Essential files report
    files_ok = report["essential_files"]["ok"]
    if files_ok:
        print("  [essential_files] CLEAN — all required files and directories exist")
    else:
        print(f"  [essential_files] ISSUES ({len(report['essential_files']['issues'])}):")
        for issue in report["essential_files"]["issues"]:
            print(f"    - {issue}")
            
    # DNA graph validation
    if report["dna_graph"]["valid"]:
        print(f"  [dna_graph] VALID — {report['dna_graph']['message']}")
    else:
        print(f"  [dna_graph] INVALID — {report['dna_graph']['message']}")
        
    # Cleanup report
    if args.cleanup and not args.dry_run and report["cleaned_files"]:
        print(f"  [cleanup] REMOVED {len(report['cleaned_files'])} file(s)")
        for f in report["cleaned_files"][:10]:  # Show first 10
            print(f"    - {f}")
        if len(report["cleaned_files"]) > 10:
            print(f"    ... and {len(report['cleaned_files']) - 10} more")
            
    if args.cleanup and args.dry_run and report["cleaned_files"]:
        print(f"  [cleanup] DRY-RUN — would remove {len(report['cleaned_files'])} file(s)")
        
    # Summary
    all_ok = files_ok and report["dna_graph"]["valid"]
    if not disk_ok:
        all_ok = False
        
    if all_ok:
        print("\n[groundskeeping_floor] CLEAN — no issues found")
    else:
        print(f"\n[groundskeeping_floor] ISSUES DETECTED — see above for details (exit 0)")
        
    # Always exit 0 — findings are work items, not crashes
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
