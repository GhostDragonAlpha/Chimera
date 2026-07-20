"""EVERYTHING catalog — every variable, parameter, config entry, and API surface.

No exceptions. UPROPERTY, CVars, config, BlueprintCallable, Niagara, Material, MCP, DSL.
"""
import json, re, sys, subprocess
from pathlib import Path
from collections import Counter

ENGINE = Path("C:/Program Files/Epic Games/UE_5.8/Engine")
PROJECT = Path("E:/PythonChimera/Chimera")
CATALOG_PATH = PROJECT / "docs/element_catalog.json"

def load_existing():
    if CATALOG_PATH.exists():
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return {"elements": [], "total_elements": 0}

def save(catalog):
    src = Counter(e["source"] for e in catalog["elements"])
    cat = Counter(e.get("category","") for e in catalog["elements"])
    catalog["total_elements"] = len(catalog["elements"])
    catalog["by_source"] = dict(src.most_common())
    catalog["by_category"] = dict(cat.most_common())
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

def add_unique(catalog, elements):
    existing = {(e["class"], e["property"]): i for i, e in enumerate(catalog["elements"])}
    added = 0
    for el in elements:
        key = (el["class"], el["property"])
        if key not in existing:
            catalog["elements"].append(el)
            existing[key] = len(catalog["elements"]) - 1
            added += 1
    return added

def scan_console_variables():
    """CVars: TAutoConsoleVariable, FAutoConsoleVariable, IConsoleManager::RegisterConsoleVariable"""
    print("Scanning console variables...")
    cvars = []
    cv_re = re.compile(
        r'(?:TAutoConsoleVariable|FAutoConsoleVariable|IConsoleManager::Get\(\).*RegisterConsoleVariable)\s*[<(]\s*'
        r'(?:TEXT\("([^"]*)"\)|"([^"]*)")\s*,',
        re.MULTILINE
    )
    cv_help = re.compile(r'(?:TEXT\("([^"]*)"\)|"([^"]*)")\s*,\s*(?:TEXT\("([^"]*)"\)|"([^"]*)")\s*\);', re.MULTILINE)

    for cpp in list(ENGINE.rglob("*.cpp")) + list(PROJECT.rglob("*.cpp")):
        try:
            text = cpp.read_text(encoding="utf-8", errors="replace")[:50000]
        except:
            continue
        for m in cv_re.finditer(text):
            name = m.group(1) or m.group(2) or ""
            if name:
                cvars.append({
                    "class": "ConsoleVariable",
                    "property": name,
                    "category": "ConsoleVariable",
                    "flags": ["cvar"],
                    "source": "CVar",
                    "file": str(cpp),
                })
        if len(cvars) > 50000:
            break
    return cvars

def scan_config_entries():
    """Engine and project config .ini entries."""
    print("Scanning config files...")
    entries = []
    for ini in list(ENGINE.rglob("*.ini")) + list(PROJECT.rglob("*.ini")):
        try:
            text = ini.read_text(encoding="utf-8", errors="replace")
        except:
            continue
        section = ""
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
            elif "=" in line and not line.startswith(";") and not line.startswith("#") and not line.startswith("+"):
                key = line.split("=")[0].strip()
                if key and section:
                    entries.append({
                        "class": section,
                        "property": key,
                        "category": f"Config|{section.split('.')[0]}",
                        "flags": ["config"],
                        "source": "Config",
                        "file": str(ini),
                    })
    return entries

def scan_blueprint_functions():
    """UFUNCTION(BlueprintCallable) declarations."""
    print("Scanning Blueprint functions...")
    bps = []
    ufunc_re = re.compile(
        r'UFUNCTION\s*\(([^)]*BlueprintCallable[^)]*)\)\s*\n\s*(?:[\w:<>*&\s]+?)\b(\w+)\s*\(',
        re.MULTILINE
    )
    for h in list(ENGINE.rglob("*.h")) + list(PROJECT.rglob("*.h")):
        try:
            text = h.read_text(encoding="utf-8", errors="replace")[:30000]
        except:
            continue
        for m in ufunc_re.finditer(text):
            bps.append({
                "class": h.stem,
                "property": m.group(2),
                "category": "BlueprintFunction",
                "flags": ["blueprint_callable"],
                "source": "BlueprintCallable",
                "file": str(h),
            })
    return bps

def scan_niagara_params():
    """Niagara parameters from DataInterface and emitter headers."""
    print("Scanning Niagara...")
    niag = []
    niagara_root = ENGINE / "Plugins/FX/Niagara/Source"
    prop_re = re.compile(
        r'UPROPERTY\s*\(([^)]*)\)\s*\n\s*(?:[\w:<>*&\s]+?)\b(\w+)\s*(?:=[^;]*)?;',
        re.MULTILINE
    )
    for h in niagara_root.rglob("*.h"):
        try:
            text = h.read_text(encoding="utf-8", errors="replace")[:30000]
        except:
            continue
        for m in prop_re.finditer(text):
            niag.append({
                "class": h.stem,
                "property": m.group(2),
                "category": "Niagara",
                "flags": ["niagara", "editable"] if "EditAnywhere" in m.group(1) else ["niagara"],
                "source": "Niagara",
                "file": str(h),
            })
    return niag

def scan_mcp_tools():
    """MCP bridge tool surface."""
    print("Scanning MCP bridge...")
    tools = []
    mcp_dir = PROJECT / "Plugins/McpAutomationBridge/Source"
    tool_re = re.compile(r'RegisterHandler\s*\(\s*"([^"]*)"\s*,\s*"([^"]*)"', re.MULTILINE)
    for cpp in mcp_dir.rglob("*.cpp"):
        try:
            text = cpp.read_text(encoding="utf-8", errors="replace")
        except:
            continue
        for m in tool_re.finditer(text):
            tools.append({
                "class": m.group(1),
                "property": m.group(2),
                "category": "MCP",
                "flags": ["mcp"],
                "source": "MCP",
                "file": str(cpp),
            })
    return tools

def scan_dsl_tokens():
    """DSL grammar tokens."""
    print("Scanning DSL grammar...")
    dsl = []
    dsl_dir = PROJECT / "tests/dsl_grammar"
    for f in dsl_dir.rglob("*.chimera"):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except:
            continue
        # Extract block types and key identifiers
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("##"):
                block = line.replace("##", "").strip()
                dsl.append({"class": "DSL", "property": block, "category": "DSL|Block", "flags": ["dsl"], "source": "DSL", "file": str(f)})
            elif ":" in line and not line.startswith("#"):
                key = line.split(":")[0].strip()
                if key:
                    dsl.append({"class": "DSL", "property": key, "category": "DSL|Key", "flags": ["dsl"], "source": "DSL", "file": str(f)})
    return dsl

def scan_material_expressions():
    """Material expression nodes."""
    print("Scanning material expressions...")
    mats = []
    mat_dir = ENGINE / "Source/Runtime/Engine/Classes/Materials"
    for h in mat_dir.rglob("*.h"):
        try:
            text = h.read_text(encoding="utf-8", errors="replace")
        except:
            continue
        class_match = re.search(r'class\s+\w+_API\s+UMaterialExpression(\w+)\s*:', text)
        if class_match:
            mats.append({
                "class": f"UMaterialExpression{class_match.group(1)}",
                "property": "MaterialExpression",
                "category": "MaterialExpression",
                "flags": ["material"],
                "source": "MaterialExpression",
                "file": str(h),
            })
    return mats


def main():
    catalog = load_existing()
    print(f"Starting from {catalog['total_elements']} elements\n")

    scanners = [
        ("CVar", scan_console_variables),
        ("Config", scan_config_entries),
        ("BlueprintCallable", scan_blueprint_functions),
        ("Niagara", scan_niagara_params),
        ("MCP", scan_mcp_tools),
        ("DSL", scan_dsl_tokens),
        ("MaterialExpression", scan_material_expressions),
    ]

    for name, scanner in scanners:
        try:
            elements = scanner()
            added = add_unique(catalog, elements)
            print(f"  {name}: {len(elements)} found, {added} new")
        except Exception as e:
            print(f"  {name}: ERROR - {e}")

    save(catalog)
    print(f"\nFINAL: {catalog['total_elements']} elements")
    for src, count in catalog["by_source"].most_common():
        print(f"  {src}: {count}")


if __name__ == "__main__":
    main()
