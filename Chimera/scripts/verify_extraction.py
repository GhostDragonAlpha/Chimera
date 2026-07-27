#!/usr/bin/env python3
"""Verify completeness of UE5 API extraction JSON against manual DSL encoding."""

import json
import os
from collections import defaultdict

EXTRACTED_JSON = r"E:\PythonChimera\Chimera\docs\ue5_api_extracted.json"
OUTPUT_MD = r"E:\PythonChimera\Chimera\docs\extraction_verification.md"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def flatten_types(data):
    """Extract all types from the nested JSON into a flat lookup keyed by type name.
    
    Structure: { path_key: { "modules": { module_name: [ list_of_type_entries ] } } }
    Each type entry: { "name": ..., "type": "class"|"struct"|"enum", "specifiers": ..., "properties": ..., "functions": ..., "values": ... }
    """
    types = {}
    for path_key, path_entry in data.items():
        modules = path_entry.get("modules", {})
        if not isinstance(modules, dict):
            continue
        for module_name, module_list in modules.items():
            if not isinstance(module_list, list):
                continue
            for type_entry in module_list:
                if isinstance(type_entry, dict) and "name" in type_entry:
                    type_name = type_entry["name"]
                    types[type_name] = type_entry
    return types

def get_all_entries_with_modules(data):
    """Yield (path_key, module_name, type_name, type_entry) tuples."""
    for path_key, path_entry in data.items():
        modules = path_entry.get("modules", {})
        if not isinstance(modules, dict):
            continue
        for module_name, module_list in modules.items():
            if not isinstance(module_list, list):
                continue
            for type_entry in module_list:
                if isinstance(type_entry, dict) and "name" in type_entry:
                    yield (path_key, module_name, type_entry["name"], type_entry)

# =============================================================================
# Manual PCG encoding from DSL schema + subsystem inventory
# =============================================================================

MANUAL_PCG_CLASSES = {
    "UPCGData": {
        "properties": ["UID", "Crc", "Metadata"],
        "source": "subsystem_inventory",
    },
    "FPCGTaggedData": {
        "properties": ["Data", "Tags", "Pin", "bPinlessData", "bIsUsedMultipleTimes"],
        "source": "subsystem_inventory",
    },
    "FPCGDataCollection": {
        "properties": ["TaggedData", "bCancelExecutionOnEmpty", "bCancelExecution", "DataCrcs"],
        "source": "subsystem_inventory",
    },
}

MANUAL_PCG_ENUMS = {
    "EPCGDataUsage": {
        "values": ["None", "GraphExecutorTaskOutput", "ComponentOutputData",
                    "ComponentPerPinOutputData", "ComponentInspectionData"],
        "source": "subsystem_inventory",
    },
}

# =============================================================================
# Niagara types to check
# =============================================================================

NIAGARA_TYPES_TO_CHECK = [
    "UNiagaraSystem",
    "UNiagaraComponent",
    "UNiagaraEmitter",
    "FNiagaraFloat",
    "FNiagaraBool",
    "FNiagaraMatrix",
    "ENiagaraExecutionState",
]

# =============================================================================
# Modules to count
# =============================================================================

MODULES_TO_CHECK = [
    "Engine",
    "Niagara",
    "PCG",
    "Chaos",
    "Renderer",
    "RenderCore",
    "UMG",
    "GameplayAbilities",
    "EnhancedInput",
    "Metasound",
    "CommonUI",
]

def check_pcg(types):
    results = {"found_classes": {}, "missing_classes": [], "found_enums": {}, "missing_enums": [],
               "extra_pcg_types": []}

    for cls_name, info in MANUAL_PCG_CLASSES.items():
        if cls_name in types:
            entry = types[cls_name]
            found_props = []
            missing_props = []
            entry_props = set()
            for p in entry.get("properties", []):
                if isinstance(p, dict):
                    entry_props.add(p.get("name", ""))
                else:
                    entry_props.add(str(p))
            for expected_prop in info["properties"]:
                if expected_prop in entry_props:
                    found_props.append(expected_prop)
                else:
                    missing_props.append(expected_prop)
            results["found_classes"][cls_name] = {
                "found_props": found_props,
                "missing_props": missing_props,
                "property_count": len(entry.get("properties", [])),
                "type_kind": entry.get("type", ""),
                "specifiers": entry.get("specifiers", []),
            }
        else:
            results["missing_classes"].append(cls_name)

    for enum_name, info in MANUAL_PCG_ENUMS.items():
        if enum_name in types:
            entry = types[enum_name]
            found_vals = []
            missing_vals = []
            entry_vals = set()
            for v in entry.get("values", []):
                if isinstance(v, dict):
                    entry_vals.add(v.get("name", ""))
                else:
                    entry_vals.add(str(v))
            for expected_val in info["values"]:
                if expected_val in entry_vals:
                    found_vals.append(expected_val)
                else:
                    missing_vals.append(expected_val)
            results["found_enums"][enum_name] = {
                "found_vals": found_vals,
                "missing_vals": missing_vals,
                "type_kind": entry.get("type", ""),
                "specifiers": entry.get("specifiers", []),
            }
        else:
            results["missing_enums"].append(enum_name)

    # Extra PCG types the extractor found
    for type_name, entry in types.items():
        type_lower = type_name.lower()
        if "pcg" in type_lower or "procedural" in type_lower:
            if type_name not in MANUAL_PCG_CLASSES and type_name not in MANUAL_PCG_ENUMS:
                results["extra_pcg_types"].append(type_name)

    return results

def check_niagara(types):
    results = {}
    for niagara_type in NIAGARA_TYPES_TO_CHECK:
        if niagara_type in types:
            entry = types[niagara_type]
            info = {"present": True}
            props = entry.get("properties", [])
            funcs = entry.get("functions", [])
            info["property_count"] = len(props) if isinstance(props, list) else 0
            info["property_names"] = [p.get("name", "") if isinstance(p, dict) else str(p) for p in props]
            info["function_count"] = len(funcs) if isinstance(funcs, list) else 0
            info["function_names"] = [f.get("name", "") if isinstance(f, dict) else str(f) for f in funcs[:20]]
            vals = entry.get("values", [])
            if vals:
                info["values"] = [v.get("name", "") if isinstance(v, dict) else str(v) for v in vals]
            specifiers = entry.get("specifiers", [])
            if specifiers:
                info["specifiers"] = specifiers
            info["type_kind"] = entry.get("type", "")
            results[niagara_type] = info
        else:
            results[niagara_type] = {"present": False}
    return results

def compute_module_stats(data):
    """Return: module_counts dict, module_type_lists dict, module_paths dict."""
    module_counts = {}
    module_type_lists = defaultdict(list)
    module_paths = defaultdict(set)

    for path_key, module_name, type_name, _ in get_all_entries_with_modules(data):
        module_counts[module_name] = module_counts.get(module_name, 0) + 1
        module_type_lists[module_name].append(type_name)
        module_paths[module_name].add(path_key)

    return module_counts, module_type_lists, module_paths

def check_modules(data, module_counts, module_type_lists, module_paths):
    results = {}
    for check_name in MODULES_TO_CHECK:
        found = check_name in module_counts
        count = module_counts.get(check_name, 0)
        sample_types = module_type_lists.get(check_name, [])[:10]
        paths = sorted(module_paths.get(check_name, []))[:5]

        path_matches = []
        for pk in data.keys():
            pk_lower = pk.lower()
            cn_lower = check_name.lower()
            # Check if the check_name appears as a meaningful substring in path
            import re
            if re.search(r'\b' + re.escape(cn_lower) + r'\b', pk_lower):
                path_matches.append(pk)

        results[check_name] = {
            "found": found,
            "type_count": count,
            "sample_types": sample_types,
            "matching_paths": path_matches[:10],
        }

    # For modules not found directly, search type names by prefix/suffix
    for check_name in MODULES_TO_CHECK:
        if not results[check_name]["found"]:
            extra = []
            cn_lower = check_name.lower()
            for module_name, type_list in module_type_lists.items():
                for tname in type_list:
                    if cn_lower in tname.lower():
                        extra.append((module_name, tname))
            if extra:
                results[check_name]["cross_references"] = extra[:50]

    return results

def type_breakdown(data, types):
    stats = {
        "total_types": 0,
        "uclass_count": 0,
        "ustruct_count": 0,
        "uenum_count": 0,
        "total_ufunctions": 0,
        "total_uproperties": 0,
        "delegates_count": 0,
        "typedefs_count": 0,
        "interfaces_count": 0,
        "other_count": 0,
        "type_categories": defaultdict(int),
    }

    uclass_examples = []
    ustruct_examples = []
    uenum_examples = []
    delegate_examples = []

    for type_name, entry in types.items():
        stats["total_types"] += 1

        # Count properties and functions
        props = entry.get("properties", [])
        funcs = entry.get("functions", [])
        if isinstance(props, list):
            stats["total_uproperties"] += len(props)
        if isinstance(funcs, list):
            stats["total_ufunctions"] += len(funcs)

        # Get the explicit type field
        entry_type = entry.get("type", "").lower()
        specifiers = entry.get("specifiers", [])

        if entry_type == "class":
            stats["uclass_count"] += 1
            stats["type_categories"]["UCLASS"] += 1
            if len(uclass_examples) < 5:
                uclass_examples.append(type_name)
        elif entry_type == "struct":
            stats["ustruct_count"] += 1
            stats["type_categories"]["USTRUCT"] += 1
            if len(ustruct_examples) < 5:
                ustruct_examples.append(type_name)
        elif entry_type == "enum":
            stats["uenum_count"] += 1
            stats["type_categories"]["UENUM"] += 1
            if len(uenum_examples) < 5:
                uenum_examples.append(type_name)
        elif entry_type == "delegate":
            stats["delegates_count"] += 1
            stats["type_categories"]["DELEGATE"] += 1
            if len(delegate_examples) < 5:
                delegate_examples.append(type_name)
        elif entry_type == "interface":
            stats["interfaces_count"] += 1
            stats["type_categories"]["INTERFACE"] += 1
        elif entry_type in ("typedef", "typdef"):
            stats["typedefs_count"] += 1
            stats["type_categories"]["TYPEDEF"] += 1
        else:
            # Fallback by prefix convention
            tn_lower = type_name.lower()
            if tn_lower.startswith("u"):
                stats["uclass_count"] += 1
                stats["type_categories"]["UCLASS"] += 1
            elif tn_lower.startswith("f"):
                stats["ustruct_count"] += 1
                stats["type_categories"]["USTRUCT"] += 1
            elif tn_lower.startswith("e"):
                stats["uenum_count"] += 1
                stats["type_categories"]["UENUM"] += 1
            else:
                stats["type_categories"][f"TYPE_{entry_type.upper()}" if entry_type else "UNKNOWN"] += 1

    stats["uclass_examples"] = uclass_examples
    stats["ustruct_examples"] = ustruct_examples
    stats["uenum_examples"] = uenum_examples
    stats["delegate_examples"] = delegate_examples

    return stats

def generate_report(pcg_results, niagara_results, module_results, module_counts, module_paths, breakdown, data):
    lines = []
    lines.append("# UE5 API Extraction Verification Report")
    lines.append(f"Generated from: `{EXTRACTED_JSON}`")
    lines.append("")

    total_paths = len(data)
    total_all_types = sum(module_counts.values())
    total_module_keys = len(module_counts)
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Top-level paths**: {total_paths}")
    lines.append(f"- **Distinct module names**: {total_module_keys}")
    lines.append(f"- **Total type entries (sum across modules)**: {total_all_types}")
    lines.append(f"- **Unique type names (deduplicated)**: {breakdown['total_types']}")
    lines.append(f"- **UCLASS**: {breakdown['uclass_count']}")
    lines.append(f"- **USTRUCT**: {breakdown['ustruct_count']}")
    lines.append(f"- **UENUM**: {breakdown['uenum_count']}")
    lines.append("")

    # Step 1: PCG
    lines.append("---")
    lines.append("")
    lines.append("## Step 1: PCG Types Comparison")
    lines.append("")

    lines.append("### Classes from Manual Encoding Found in Extraction")
    if pcg_results["found_classes"]:
        for cls, info in pcg_results["found_classes"].items():
            lines.append(f"- **{cls}** ({info.get('type_kind', '?')}): found with {info['property_count']} properties")
            if info["found_props"]:
                lines.append(f"  - Matched properties: {', '.join(info['found_props'])}")
            if info["missing_props"]:
                lines.append(f"  - **MISSING properties**: {', '.join(info['missing_props'])}")
            if info.get("specifiers"):
                lines.append(f"  - Specifiers: {info['specifiers']}")
    else:
        lines.append("None found.")

    if pcg_results["missing_classes"]:
        lines.append("")
        lines.append("### Classes MISSING from Extraction")
        for cls in pcg_results["missing_classes"]:
            lines.append(f"- **{cls}**")

    lines.append("")
    lines.append("### Enums from Manual Encoding Found in Extraction")
    if pcg_results["found_enums"]:
        for enum, info in pcg_results["found_enums"].items():
            lines.append(f"- **{enum}** ({info.get('type_kind', '?')}): found")
            if info["found_vals"]:
                lines.append(f"  - Matched values: {', '.join(info['found_vals'])}")
            if info["missing_vals"]:
                lines.append(f"  - **MISSING values**: {', '.join(info['missing_vals'])}")
    else:
        lines.append("None found.")

    if pcg_results["missing_enums"]:
        lines.append("")
        lines.append("### Enums MISSING from Extraction")
        for enum in pcg_results["missing_enums"]:
            lines.append(f"- **{enum}**")

    lines.append("")
    lines.append("### Additional PCG Types Found in Extraction (Not in Manual Encoding)")
    if pcg_results["extra_pcg_types"]:
        for extra in sorted(pcg_results["extra_pcg_types"])[:80]:
            lines.append(f"- `{extra}`")
        if len(pcg_results["extra_pcg_types"]) > 80:
            lines.append(f"- ... and {len(pcg_results['extra_pcg_types']) - 80} more")
    else:
        lines.append("None.")

    # Step 2: Niagara
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Step 2: Niagara Types Presence")
    lines.append("")
    lines.append("| Type | Present | Type Kind | Properties | Functions | Values/Specifiers |")
    lines.append("|------|---------|-----------|------------|-----------|-------------------|")
    for niagara_type in NIAGARA_TYPES_TO_CHECK:
        info = niagara_results.get(niagara_type, {"present": False})
        present = "Yes" if info.get("present") else "**NO**"
        kind = info.get("type_kind", "-")
        pcount = info.get("property_count", "-")
        fcount = info.get("function_count", "-")
        vals = info.get("values", None)
        specs = info.get("specifiers", None)
        rest = ""
        if vals:
            rest = f"values: {', '.join(vals)}"
        elif specs:
            rest = f"specifiers: {specs}"
        lines.append(f"| `{niagara_type}` | {present} | {kind} | {pcount} | {fcount} | {rest} |")

    # Step 3: Module coverage
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Step 3: Module Coverage")
    lines.append("")
    lines.append("| Module | Found as Module | Type Count | Sample Types | Matching Paths |")
    lines.append("|--------|----------------|------------|--------------|----------------|")
    for check_name in MODULES_TO_CHECK:
        info = module_results.get(check_name, {})
        found = "Yes" if info.get("found") else "**NO**"
        count = info.get("type_count", 0)
        samples = ", ".join(f"`{s}`" for s in info.get("sample_types", [])[:5])
        paths = "; ".join(info.get("matching_paths", [])[:5])
        lines.append(f"| {check_name} | {found} | {count} | {samples} | {paths} |")

        if not info.get("found") and "cross_references" in info:
            xref = info["cross_references"]
            if xref:
                lines.append("")
                lines.append(f"**{check_name}** not found as a module name but related types exist across other modules:")
                for mod_name, tname in xref[:20]:
                    lines.append(f"- `{tname}` (in module `{mod_name}`)")
                if len(xref) > 20:
                    lines.append(f"- ... and {len(xref) - 20} more")

    # Step 4: Type breakdown
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Step 4: Type Breakdown")
    lines.append("")
    lines.append(f"- **Total unique type entries**: {breakdown['total_types']}")
    lines.append(f"- **UCLASS**: {breakdown['uclass_count']}")
    lines.append(f"- **USTRUCT**: {breakdown['ustruct_count']}")
    lines.append(f"- **UENUM**: {breakdown['uenum_count']}")
    lines.append(f"- **Total UFUNCTIONs** (across all classes): {breakdown['total_ufunctions']}")
    lines.append(f"- **Total UPROPERTYs** (across all classes): {breakdown['total_uproperties']}")
    lines.append(f"- **Delegates**: {breakdown['delegates_count']}")
    lines.append(f"- **Typedefs**: {breakdown['typedefs_count']}")
    lines.append(f"- **Interfaces**: {breakdown['interfaces_count']}")
    lines.append(f"- **Other/Unclassified**: {breakdown['other_count']}")
    lines.append("")

    cats = breakdown.get("type_categories", {})
    if cats:
        lines.append("### Category Breakdown")
        lines.append("")
        lines.append("| Category | Count |")
        lines.append("|----------|-------|")
        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
            lines.append(f"| {cat} | {count} |")

    lines.append("")
    lines.append("### Examples by Type")
    lines.append("")
    lines.append(f"- UCLASS examples: {', '.join(breakdown.get('uclass_examples', []))}")
    lines.append(f"- USTRUCT examples: {', '.join(breakdown.get('ustruct_examples', []))}")
    lines.append(f"- UENUM examples: {', '.join(breakdown.get('uenum_examples', []))}")
    lines.append(f"- Delegate examples: {', '.join(breakdown.get('delegate_examples', []))}")

    # Top modules by type count
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Top 30 Modules by Type Count")
    lines.append("")
    top_modules = sorted(module_counts.items(), key=lambda x: -x[1])[:30]
    lines.append("| Module | Type Count | Paths |")
    lines.append("|--------|-----------|-------|")
    for mod, cnt in top_modules:
        mp = "; ".join(sorted(module_paths.get(mod, []))[:3])
        lines.append(f"| {mod} | {cnt} | {mp} |")

    # Assessment
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Assessment: Is the extraction complete enough to auto-populate the DSL?")
    lines.append("")

    missing_pcg_classes = len(pcg_results["missing_classes"])
    missing_pcg_enums = len(pcg_results["missing_enums"])
    missing_niagara_types = [k for k, v in niagara_results.items() if not v.get("present")]
    missing_niagara = len(missing_niagara_types)
    partial_niagara = [k for k, v in niagara_results.items() if v.get("present") and v.get("property_count", 0) == 0 and v.get("function_count", 0) == 0 and not v.get("values")]
    missing_modules = [m for m in MODULES_TO_CHECK if not module_results.get(m, {}).get("found")]

    pcg_class_found = len(pcg_results["found_classes"])
    pcg_enum_found = len(pcg_results["found_enums"])
    extra_pcg_count = len(pcg_results["extra_pcg_types"])

    lines.append("### Gap Analysis")
    lines.append("")
    lines.append(f"- **PCG Classes**: {pcg_class_found}/{len(MANUAL_PCG_CLASSES)} found ({missing_pcg_classes} missing)")
    lines.append(f"- **PCG Enums**: {pcg_enum_found}/{len(MANUAL_PCG_ENUMS)} found ({missing_pcg_enums} missing)")
    lines.append(f"- **Extra PCG types found by extractor**: {extra_pcg_count}")
    lines.append(f"- **Niagara types**: {len(NIAGARA_TYPES_TO_CHECK) - missing_niagara}/{len(NIAGARA_TYPES_TO_CHECK)} found")
    lines.append(f"- **Modules present**: {len(MODULES_TO_CHECK) - len(missing_modules)}/{len(MODULES_TO_CHECK)}")
    lines.append("")

    # Overall assessment
    def is_fully_found():
        return missing_pcg_classes == 0 and missing_pcg_enums == 0 and missing_niagara == 0

    if is_fully_found() and len(missing_modules) <= 2:
        lines.append("**Verdict: Extraction is COMPLETE for all critical types.**")
        lines.append("All manually encoded PCG classes/enums and all key Niagara types are present.")
        lines.append("The extraction is suitable to auto-populate the DSL with minimal manual supplementation.")
    elif pcg_class_found >= 2 and pcg_enum_found >= 1 and missing_niagara <= 2:
        lines.append("**Verdict: MOSTLY complete.** Most critical types are present but there are minor gaps.")
        lines.append("A small amount of manual encoding will be needed to fill remaining gaps.")
    elif pcg_class_found >= 1 or missing_niagara <= 3:
        lines.append("**Verdict: PARTIALLY complete.** ")
        lines.append("Several key types are present but significant gaps remain.")
        lines.append("The extraction can bootstrap DSL encoding but will need substantial manual work.")
    else:
        lines.append("**Verdict: INSUFFICIENT.** ")
        lines.append("Most manually verified types are missing from the extraction.")
        lines.append("The extraction in its current form cannot auto-populate the DSL.")
        lines.append("Either the extraction process is incomplete, or the JSON formatting does not match expected structure.")

    lines.append("")
    if breakdown['uclass_count'] > 0:
        lines.append(f"The extraction overall contains **{breakdown['total_types']:,}** types "
                      f"({breakdown['uclass_count']:,} UCLASS, {breakdown['ustruct_count']:,} USTRUCT, "
                      f"{breakdown['uenum_count']:,} UENUM), which is a substantial corpus.")
        lines.append(f"It spans **{total_module_keys}** modules across **{total_paths}** paths, "
                      f"covering much of the UE5 API surface.")

    return "\n".join(lines)

def main():
    print("Loading extracted JSON...")
    data = load_json(EXTRACTED_JSON)

    print("Flattening types...")
    types = flatten_types(data)
    print(f"  -> {len(types):,} unique type names")

    print("Computing module stats...")
    module_counts, module_type_lists, module_paths = compute_module_stats(data)
    print(f"  -> {len(module_counts)} distinct module names")

    print("Checking PCG types...")
    pcg_results = check_pcg(types)
    print(f"  -> Found PCG classes: {len(pcg_results['found_classes'])}, missing: {len(pcg_results['missing_classes'])}")
    print(f"  -> Found PCG enums: {len(pcg_results['found_enums'])}, missing: {len(pcg_results['missing_enums'])}")
    print(f"  -> Extra PCG types: {len(pcg_results['extra_pcg_types'])}")

    print("Checking Niagara types...")
    niagara_results = check_niagara(types)
    present_niagara = sum(1 for v in niagara_results.values() if v.get("present"))
    print(f"  -> {present_niagara}/{len(NIAGARA_TYPES_TO_CHECK)} present")

    print("Checking module coverage...")
    module_results = check_modules(data, module_counts, module_type_lists, module_paths)

    print("Doing type breakdown...")
    breakdown = type_breakdown(data, types)
    print(f"  -> UCLASS: {breakdown['uclass_count']}, USTRUCT: {breakdown['ustruct_count']}, UENUM: {breakdown['uenum_count']}")

    print("Generating report...")
    report = generate_report(pcg_results, niagara_results, module_results, module_counts, module_paths, breakdown, data)

    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report written to {OUTPUT_MD}")
    print("Done.")

if __name__ == "__main__":
    main()
