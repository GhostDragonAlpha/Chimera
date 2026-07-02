"""
Extract UE5.8 API surface by regex-parsing engine header files.
Falls back from UHT JSON export (which has a serialization bug in UE5.8).
"""

import json
import os
import re
import sys
import subprocess
import time
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ENGINE_DIR = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine")
UHT_DLL_DIR = ENGINE_DIR / "Binaries" / "DotNET" / "UnrealBuildTool"
UBT_EXE = UHT_DLL_DIR / "UnrealBuildTool.exe"

OUTPUT_FILE = Path(r"E:\PythonChimera\Chimera\docs\ue5_api_extracted.json")
SCRIPT_DIR = Path(__file__).parent

# Directories to scan for reflected headers
SCAN_DIRS = [
    ENGINE_DIR / "Source" / "Runtime",
    ENGINE_DIR / "Source" / "Developer",
    ENGINE_DIR / "Source" / "Editor",
    ENGINE_DIR / "Plugins",
]

MODULE_IGNORE_PREFIXES = (
    "Private", "Internal", "ThirdParty", "Tests", "Debug",
)

MODULE_IGNORE_NAMES = (
    "Android", "IOS", "Mac", "Linux", "VisionOS",
    "IOS", "Apple", "WinRT", "HoloLens",
)

# Invalid type names to filter out (macros, compiler controls, etc.)
INVALID_TYPE_NAMES = {
    "UE_DEPRECATED", "DEPRECATED", "UE_DISABLE_OPTIMIZATION",
    "UE_ENABLE_OPTIMIZATION", "GENERATED_BODY", "GENERATED_USTRUCT_BODY",
    "GENERATED_UCLASS_BODY", "GENERATED_UENUM_BODY", "GENERATED_IINTERFACE_BODY",
}

# Regex patterns for reflected UE macros

def extract_paren_block(text, start):
    """Extract the content of the first parenthesized block starting at `start`."""
    if start >= len(text) or text[start] != '(':
        return None, start
    depth = 1
    i = start + 1
    while i < len(text) and depth > 0:
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
        i += 1
    if depth == 0:
        return text[start + 1:i - 1], i
    return None, start

def find_decl_macro(text, macro_name):
    """Find macro_name(...) followed by a type declaration.
    Yields (spec_str, decl_start, end_pos) tuples."""
    idx = 0
    while True:
        macro_pos = text.find(macro_name + '(', idx)
        if macro_pos < 0:
            break
        spec_content, spec_end = extract_paren_block(text, macro_pos + len(macro_name))
        if spec_content is None:
            idx = macro_pos + 1
            continue
        decl_start = spec_end
        yield spec_content, decl_start, spec_end
        idx = spec_end

RE_PARAM = re.compile(
    r'(?:const\s+)?(\w+(?:\s*<\s*[^>]+>)?(?:\s*\*)?(?:\s*&)?)\s+(\w+)',
)

RE_META_SPECIFIERS = re.compile(r'(\w+)\s*(?:=\s*"([^"]*)")?\s*(?:,|$)')

RE_COMMENT_LINE = re.compile(r'^\s*(?://.*|/\*.*\*/|/\*|\*|//)')


def find_matching_paren(text, start):
    """Find the closing paren matching the opening paren at position start."""
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
        i += 1
    if depth == 0:
        return i - 1
    return None


def normalize_specifiers(spec_str):
    """Parse UE macro specifier string into (list, dict_or_None)."""
    if not spec_str or not spec_str.strip():
        return [], None
    specs = []
    depth = 0
    current = ""
    for ch in spec_str:
        if ch in '({' and depth == 0:
            depth += 1
            current += ch
        elif ch in ')}':
            depth -= 1 if depth > 0 else 0
            current += ch
        elif ch == ',' and depth == 0:
            specs.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        specs.append(current.strip())

    result = []
    for spec in specs:
        if '=' in spec:
            k, _, v = spec.partition('=')
            result.append((k.strip(), v.strip()))
        else:
            result.append((spec.strip(), None))

    metadata = None
    filtered = []
    for k, v in result:
        if k == "meta":
            md = {}
            inner = v
            if inner.startswith('(') and inner.endswith(')'):
                inner = inner[1:-1]
            for match in RE_META_SPECIFIERS.finditer(inner):
                md[match.group(1)] = match.group(2) or None
            metadata = md
        else:
            filtered.append((k, v))
    return filtered, metadata


def get_module_name(filepath):
    """Heuristic to derive module+subsystem from a file path."""
    parts = filepath.relative_to(ENGINE_DIR).parts
    module = "Unknown"
    subsystem = ""
    source_idx = -1

    try:
        source_idx = parts.index("Source")
    except ValueError:
        pass

    try:
        plugins_idx = parts.index("Plugins")
        if plugins_idx >= 0:
            # Plugin structure: Plugins/<Category>/<PluginName>/Source/<ModuleName>/...
            if plugins_idx + 2 < len(parts):
                plugin_name = parts[plugins_idx + 1] if parts[plugins_idx + 1] != "Source" else parts[plugins_idx + 2]
                # Cope with plugin categories: FX, Experimental, etc.
                if plugins_idx + 1 < len(parts) and parts[plugins_idx + 1] != "Source":
                    if plugins_idx + 2 < len(parts) and parts[plugins_idx + 2] == "Source":
                        plugin_name = parts[plugins_idx + 1]
                    elif plugins_idx + 2 < len(parts):
                        plugin_name = parts[plugins_idx + 2]
                    else:
                        plugin_name = parts[plugins_idx + 1]

                # Try to determine module name
                for i in range(plugins_idx + 1, len(parts)):
                    if parts[i] in ("Public", "Classes", "Internal"):
                        if i > 0:
                            module = parts[i - 1]
                        break
                else:
                    module = plugin_name
                subsystem = f"Plugins/{plugin_name}"
                return module, subsystem
    except ValueError:
        pass

    if source_idx >= 0:
        # Structure: Source/<Category>/<ModuleName>/Public/...
        if source_idx + 2 < len(parts):
            category = parts[source_idx + 1]
            for i in range(source_idx + 2, len(parts)):
                if parts[i] in ("Public", "Classes", "Internal"):
                    if i > 0:
                        module = parts[i - 1]
                    break
            else:
                module = parts[source_idx + 2]
            subsystem = f"Source/{category}"
            return module, subsystem

    return module, subsystem


def extract_from_file(filepath):
    """Parse a single header file for reflected types and return structured entries."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    if not any(m in text for m in ("UCLASS(", "USTRUCT(", "UENUM(", "UPROPERTY(", "UFUNCTION(")):
        return []

    module_name, subsystem = get_module_name(filepath)
    rel_path = str(filepath.relative_to(ENGINE_DIR)).replace("\\", "/")

    entries = []

    # UCLASS
    for spec_str, decl_start, macro_end in find_decl_macro(text, "UCLASS"):
        rest = text[decl_start:]
        cls_match = re.match(r'\s*class\s+(\w+)', rest)
        if not cls_match:
            continue
        class_name = cls_match.group(1)
        if class_name in INVALID_TYPE_NAMES:
            continue
        if not (class_name.startswith("U") or class_name.startswith("A") or class_name.startswith("I")):
            continue
        specs, metadata = normalize_specifiers(spec_str)
        entry = {
            "name": class_name,
            "type": "class",
            "specifiers": specs,
            "meta": metadata,
            "source": rel_path,
        }
        props, funcs = extract_members(text, decl_start, class_name)
        if props:
            entry["properties"] = props
        if funcs:
            entry["functions"] = funcs
        entries.append(entry)

    # USTRUCT
    for spec_str, decl_start, macro_end in find_decl_macro(text, "USTRUCT"):
        rest = text[decl_start:]
        struct_match = re.match(r'\s*struct\s+(\w+)', rest)
        if not struct_match:
            continue
        struct_name = struct_match.group(1)
        if struct_name in INVALID_TYPE_NAMES:
            continue
        specs, metadata = normalize_specifiers(spec_str)
        entry = {
            "name": struct_name,
            "type": "struct",
            "specifiers": specs,
            "meta": metadata,
            "source": rel_path,
        }
        props, funcs = extract_members(text, decl_start, struct_name)
        if props:
            entry["properties"] = props
        if funcs:
            entry["functions"] = funcs
        entries.append(entry)

    # UENUM
    for spec_str, decl_start, macro_end in find_decl_macro(text, "UENUM"):
        rest = text[decl_start:]
        enum_match = re.match(
            r'\s*(?:\s+namespace\s+\w+\s*\{)?\s*enum\s+(?:\w+\s+)?(\w+)',
            rest
        )
        if not enum_match:
            continue
        enum_name = enum_match.group(1)
        if enum_name in INVALID_TYPE_NAMES:
            continue
        specs, metadata = normalize_specifiers(spec_str)
        enum_values = extract_enum_values(text, decl_start)
        entry = {
            "name": enum_name,
            "type": "enum",
            "specifiers": specs,
            "meta": metadata,
            "values": enum_values,
            "source": rel_path,
        }
        entries.append(entry)

    return entries


def extract_members(text, start_pos, parent_name):
    """Extract UPROPERTY and UFUNCTION members after a class/struct definition."""
    body = text[start_pos:]
    props = []
    funcs = []

    brace_depth = 0
    in_body = False
    body_end = len(body)

    for i, ch in enumerate(body):
        if ch == '{':
            brace_depth += 1
            in_body = True
        elif ch == '}':
            brace_depth -= 1
            if in_body and brace_depth <= 0:
                body_end = i
                break

    body = body[:body_end]

    # UPROPERTY
    for spec_str, decl_start, macro_end in find_decl_macro(body, "UPROPERTY"):
        rest = body[decl_start:]
        prop_match = re.match(r'\s*(?:\w+(?:\s*<\s*[^>]+\s*>)?(?:\s*\*)?(?:\s*&)?\s+)+\w+\s*[=;]', rest)
        if not prop_match:
            continue
        prop_text = prop_match.group(0).strip().rstrip('=;').strip()
        parts = prop_text.split()
        if len(parts) < 2:
            continue
        prop_name = parts[-1]
        prop_type = ' '.join(parts[:-1])
        specs, metadata = normalize_specifiers(spec_str)
        props.append({
            "name": prop_name,
            "type": prop_type,
            "specifiers": specs,
            "meta": metadata,
        })

    # UFUNCTION
    for spec_str, decl_start, macro_end in find_decl_macro(body, "UFUNCTION"):
        rest = body[decl_start:]
        func_match = re.match(r'\s*(?:\w+\s+)*(\w+)\s*\(', rest)
        if not func_match:
            continue
        func_name = func_match.group(1)
        specs, metadata = normalize_specifiers(spec_str)

        func_paren_start = decl_start + func_match.end() - 1
        if func_paren_start < len(body) and body[func_paren_start] == '(':
            params_str, params_end = extract_paren_block(body, func_paren_start)
        else:
            params_str = None

        params = []
        if params_str:
            for p in RE_PARAM.finditer(params_str):
                ptype = p.group(1).strip()
                pname = p.group(2).strip()
                if ptype and pname and pname != "void":
                    params.append({"name": pname, "type": ptype})

        funcs.append({
            "name": func_name,
            "specifiers": specs,
            "meta": metadata,
            "params": params,
        })

    return props, funcs


def extract_enum_values(text, start_pos):
    """Extract enum value names, stripping comments."""
    body = text[start_pos:]
    brace_depth = 0
    in_body = False
    body_start = 0
    body_end = len(body)

    for i, ch in enumerate(body):
        if ch == '{':
            brace_depth += 1
            if not in_body:
                body_start = i + 1
                in_body = True
        elif ch == '}':
            brace_depth -= 1
            if in_body and brace_depth == 0:
                body_end = i
                break

    enum_body = body[body_start:body_end]
    values = []

    in_block_comment = False
    raw_lines = enum_body.split('\n')
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        if '/*' in line and '*/' in line:
            line = line[:line.index('/*')] + line[line.index('*/') + 2:]
            line = line.strip()
            if not line:
                continue
        elif '/*' in line:
            line = line[:line.index('/*')].strip()
            in_block_comment = True
            if not line:
                continue
        elif '*/' in line and in_block_comment:
            line = line[line.index('*/') + 2:].strip()
            in_block_comment = False
            if not line:
                continue
        elif in_block_comment:
            continue

        if '//' in line:
            line = line.split('//')[0].strip()
        if not line:
            continue

        line = line.rstrip(',;')
        if line.startswith('UMETA') or line.startswith('#') or line.startswith('GENERATED'):
            continue
        if line.startswith('}') or line.startswith('enum') or line.startswith('namespace'):
            continue

        name = line.split('=')[0].strip()
        name = name.split('(')[0].strip()

        if name and name[0].isupper() and not name.startswith("GENERATED") and not name.startswith("ENUM") and not name.startswith("UENUM"):
            values.append(name)

    return values if values else None


def collect_header_files(dirs, max_files=None):
    """Collect all .h files from Public and Classes directories."""
    files = []
    for d in dirs:
        if not d.exists():
            continue
        for root, dirs_list, filenames in os.walk(str(d)):
            root_path = Path(root)
            dir_name = root_path.name

            if dir_name in ("Private", "Internal", "ThirdParty", "Tests", "Debug", "Intermediate"):
                dirs_list.clear()
                continue

            if any(ign in dir_name for ign in MODULE_IGNORE_NAMES):
                dirs_list.clear()
                continue

            for f in filenames:
                if f.endswith(".h") and not f.endswith(".generated.h"):
                    filepath = root_path / f
                    files.append(filepath)
                    if max_files and len(files) >= max_files:
                        return files
    return files


def attempt_uht_json_export():
    """Attempt to run UHT with JSON export. Returns True if JSON files were produced."""
    print("Attempting UHT JSON export via UnrealBuildTool...")
    try:
        result = subprocess.run(
            [str(UBT_EXE), "-Mode=UnrealHeaderTool", "-Target=UnrealEditor Win64 Development", "-Json"],
            capture_output=True, text=True, timeout=120,
            cwd=str(ENGINE_DIR),
        )
        print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
        if result.returncode != 0:
            print(f"UHT exited with code {result.returncode}")
            print("UHT JSON export FAILED - the UE5.8 JSON exporter has a serialization cycle bug.")
            print("Falling back to regex parsing of header files.")
            return False
        return True
    except FileNotFoundError:
        print(f"UBT not found at {UBT_EXE}")
        print("This UE5.8 install does not include UHT. Falling back to regex parsing.")
        return False
    except subprocess.TimeoutExpired:
        print("UHT timed out after 120s. Falling back to regex parsing.")
        return False
    except Exception as e:
        print(f"UHT invocation failed: {e}")
        print("Falling back to regex parsing.")
        return False


def build_output(entries_by_module):
    """Build the final structured output grouped by module and subsystem."""
    output = OrderedDict()

    all_modules = list(entries_by_module.keys())
    all_modules.sort()

    for module_name in all_modules:
        module_data = entries_by_module[module_name]
        subsystem = module_data.get("subsystem", "")
        types = module_data.get("types", [])

        if subsystem not in output:
            output[subsystem] = {"modules": OrderedDict()}
        if module_name not in output[subsystem]["modules"]:
            output[subsystem]["modules"][module_name] = []

        output[subsystem]["modules"][module_name].extend(types)

    return output


def main():
    print("=" * 60)
    print("UE5.8 API Surface Extractor")
    print("=" * 60)
    print()

    json_export_success = attempt_uht_json_export()

    if json_export_success:
        print("JSON export succeeded! Searching for output JSON files...")
        json_files = list(ENGINE_DIR.rglob("*.json"))
        print(f"Found {len(json_files)} JSON files.")
    else:
        print()
        print("Proceeding with regex-based extraction.")
        print(f"Scanning directories: {[str(d) for d in SCAN_DIRS]}")
        print()

    print("Collecting header files...")
    header_files = collect_header_files(SCAN_DIRS)
    print(f"Found {len(header_files)} header files to scan.")
    print()

    print("Extracting reflected types (this may take a while)...")
    entries_by_module = {}

    processed = 0
    start_time = time.time()

    for hf in header_files:
        entries = extract_from_file(hf)
        processed += 1
        if processed % 500 == 0:
            elapsed = time.time() - start_time
            print(f"  Processed {processed}/{len(header_files)} files ({elapsed:.1f}s)...")

        for entry in entries:
            module_name, subsystem = get_module_name(hf)
            if module_name not in entries_by_module:
                entries_by_module[module_name] = {"subsystem": subsystem, "types": []}
            entries_by_module[module_name]["types"].append(entry)

    elapsed = time.time() - start_time
    total_types = sum(len(v["types"]) for v in entries_by_module.values())
    print(f"Processed {processed} files in {elapsed:.1f}s.")
    print(f"Found {total_types} reflected types across {len(entries_by_module)} modules.")
    print()

    print("Building output structure...")
    output = build_output(entries_by_module)

    print(f"Writing output to {OUTPUT_FILE}...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    file_size = OUTPUT_FILE.stat().st_size
    print(f"Output written: {OUTPUT_FILE} ({file_size:,} bytes)")
    print()
    print("Done!")


if __name__ == "__main__":
    main()
