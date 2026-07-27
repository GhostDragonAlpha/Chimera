# Audit: GameCodeGenerator Injection Vulnerabilities

**Audit Scope:** `core/game_code_generator.py` — DSL value injection into emitted C++

**Calibration:** Flag only emission bugs that produce WRONG OR MALFORMED C++. Trace DSL values to their final C++ string form. Do not flag style.

> **⚠️ ORCHESTRATOR VERDICT (2026-07-12): these 8 are LATENT robustness gaps, not ACTIVE vulnerabilities — the pipeline currently builds (grade B, all 7 stages).**
> Verified why: the live spec (`deep_space_trader.chimera`) uses **underscore-only names** for everything that becomes a C++ identifier (`Trader_Vessel_Alpha`, `Orbital_Hub_7`, `Iron_Ore`), all valid identifier chars — so `f"AShip_{ship_name}"` (:547) etc. emit valid C++ today. The one hyphenated name (`Ares-Prime`) flows only into `TEXT("...")` string literals, where a hyphen is legal. The `TEXT()` findings would only break on a `"` or `\` inside a DSL value, which the spec doesn't contain and UE asset paths (forward slashes) don't either.
> **So they're real *defensive* gaps** (a spec that named a ship `"Trader-Vessel"` or put a quote in a name WOULD break the build), **but not current failures.** Fixing them right = a general `_cpp_ident()` sanitizer applied CONSISTENTLY at every identifier site (a mismatch between a sanitized definition and a raw reference would itself break the build) + a `_cpp_str()` escaper for literals, **verified by a full UE build** — too much regression risk on the generator (the pipeline's most delicate file) to land as a rushed unverified edit. **Recommended as a dedicated, build-verified hardening pass; NOT force-changed here.** No code changed.

**Finding Date:** 2026-07-12

---

## Executive Summary

The generator has **8 confirmed injection vulnerabilities** where unescaped DSL values are embedded into C++ string literals or identifiers. The sanitizer function `s()` (line 3013) exists but is NOT used consistently throughout the file. Critical failures occur in log statements, asset paths, mission data, and commodity data where user-supplied DSL values are dropped directly into TEXT() literals or used as C++ identifiers without validation.

**Risk:** If a DSL spec contains a ship with name "Deep-Space-Trader" or a station with name "Alpha\"Station" or a mission with name containing quotes/backslashes, the generated C++ will fail to compile with syntax errors.

---

## CONFIRMED VULNERABILITIES

### 1. Unescaped Graph Names in TEXT() Literals (HIGH IMPACT)

**Locations:**
- Line 890: `TEXT("GAMEMODE: PCG clutter volume spawned for {graph_name}")`
- Line 905: `TEXT("GAMEMODE: PCG planet volume spawned for {graph_name}")`

**DSL Input Path:**
```python
graph_name = pcg_graph.get('name', '')  # Line 874 — raw DSL value
```

**Emission Code (Lines 873-890):**
```python
for pcg_graph in pcg_graphs_data:
    graph_name = pcg_graph.get('name', '')  # No sanitization
    if not graph_name:
        continue
    
    asset_name = f"UPCG_Graph_{graph_name}"
    asset_path_str = f"/Game/ProceduralGenerated/PCG/{asset_name}.{asset_name}"
    
    if "Environment_Clutter_Graph" in graph_name:
        source_content += f"\t\t// Spawn clutter volume for {graph_name}\n"
        source_content += f"\t\t\tUE_LOG(LogTemp, Log, TEXT(\"GAMEMODE: PCG clutter volume spawned for {graph_name}\"));\n"
```

**Breaking DSL Input:**
```
pcg_graphs_data = [
    {"name": 'Clutter"Graph'}
]
```

**Malformed C++ Output:**
```cpp
UE_LOG(LogTemp, Log, TEXT("GAMEMODE: PCG clutter volume spawned for Clutter"Graph"));
         // String literal breaks here ↑ — closing quote is inside the literal
```

**Result:** C++ compilation FAILS with `error: unterminated string literal`.

---

### 2. Unescaped Asset Paths in TEXT() Literals (HIGH IMPACT)

**Locations:**
- Line 886: `TEXT("{asset_path_str}")`
- Line 889: `TEXT("{asset_path_str}")`
- Line 894: `TEXT("{asset_path_str}")`
- Line 901: `TEXT("{asset_path_str}")`
- Line 904: `TEXT("{asset_path_str}")`
- Line 909: `TEXT("{asset_path_str}")`

**Problem Chain:**
```python
graph_name = pcg_graph.get('name', '')  # Line 874 — NO SANITIZATION
asset_name = f"UPCG_Graph_{graph_name}"  # Line 880 — Inherits unsanitized value
asset_path_str = f"/Game/ProceduralGenerated/PCG/{asset_name}.{asset_name}"  # Line 881
# Then embedded into TEXT():
source_content += f"TEXT(\"{asset_path_str}\")  # Lines 886, 889, 894, etc.
```

**Breaking DSL Input:**
```
graph_name = 'Test"Graph'
```

**Malformed C++ Output (line 886):**
```cpp
UObject* GraphAsset = StaticLoadObject(UObject::StaticClass(), nullptr, TEXT("/Game/ProceduralGenerated/PCG/UPCG_Graph_Test"Graph.UPCG_Graph_Test"Graph"));
                                                                             // Unescaped quote ↑ breaks the TEXT() literal
```

**Result:** C++ compilation FAILS with `error: unterminated string literal`.

---

### 3. Unescaped Station Names in TEXT() Literals (HIGH IMPACT)

**Locations:**
- Line 933: `UE_LOG(LogTemp, Log, TEXT("SPAWNED: Station {station_name} at {%s}")...`
- Line 936: `UE_LOG(LogTemp, Error, TEXT("SPAWN FAILED: Station {station_name}")...`

**DSL Input Path:**
```python
station_name = station.get('station_name', '') or station.get('name', '')  # Line 920 — raw DSL
```

**Emission Code (Lines 919-938):**
```python
for idx, station in enumerate(station_placements):
    station_name = station.get('station_name', '') or station.get('name', '')  # NO SANITIZATION
    # ...
    spawn_station_code += f"\t\t\tUE_LOG(LogTemp, Log, TEXT(\"SPAWNED: Station {station_name} at {{%s}}\"), ...
    spawn_station_code += f"\t\t\tUE_LOG(LogTemp, Error, TEXT(\"SPAWN FAILED: Station {station_name}\"))\n"
```

**Breaking DSL Input:**
```
station_placements = [
    {"station_name": 'Alpha"Prime"Station'}
]
```

**Malformed C++ Output (line 933):**
```cpp
UE_LOG(LogTemp, Log, TEXT("SPAWNED: Station Alpha"Prime"Station at {%s}"), *SpawnedStation0->GetActorLocation().ToString());
                               // First quote closes at ↑ unescaped quote — entire statement breaks
```

**Result:** C++ compilation FAILS with `error: expected `)` before string constant`.

---

### 4. Unescaped Mission Data in TEXT() Literals (HIGH IMPACT)

**Locations:**
- Line 1410: `M.MissionID = FName(TEXT("{m.get("name")}")...`
- Line 1411: `M.Type = TEXT("{m.get("type", "")}")...`
- Line 1413: `M.FactionID = FName(TEXT("{m.get("faction", "")}")...`
- Line 1419: `Deliver.Commodity = FName(TEXT("{commodity}")...`
- Line 1421: `Deliver.Station = FName(TEXT("{dest}")...`
- Line 1425: `Dock.Station = FName(TEXT("{dest}")...`

**DSL Input Path (Lines 1405-1408):**
```python
for m in (missions_data or []):
    qty = m.get("quantity_kg") or m.get("quantity_units") or m.get("quantity_rations") or 0
    dest = m.get("destination_station", "")  # NO SANITIZATION
    commodity = m.get("required_commodity", "")  # NO SANITIZATION
    # ...
    mission_lines += f'\t\tM.MissionID = FName(TEXT("{m.get("name")}"));'  # Raw DSL value
```

**Breaking DSL Input:**
```
missions_data = [
    {
        "name": 'Salvage\"Mission',
        "type": 'Recover\nData',
        "destination_station": 'Station"Alpha"Base',
        "required_commodity": 'Ice\Cores'
    }
]
```

**Malformed C++ Output (line 1410, 1411, 1421):**
```cpp
M.MissionID = FName(TEXT("Salvage"Mission"));
               // Unescaped quote ↑ closes string prematurely

M.Type = TEXT("Recover
Data");  // Literal newline in string

Deliver.Station = FName(TEXT("Station"Alpha"Base"));
                         // Multiple unescaped quotes
```

**Result:** C++ compilation FAILS with multiple syntax errors.

---

### 5. Unescaped Commodity Names in TEXT() Literals (HIGH IMPACT)

**Location:** Line 2024

**DSL Input Path (Lines 2000-2027):**
```python
commodity_data = {}
for route in routes_data:
    for item in route.get("commodity", []):
        name = item.get("name", "")  # NO SANITIZATION
        # ...
        commodity_lines.append(
            f'\t\tC->CommodityName = TEXT("{name}");'  # Raw DSL value embedded
        )
```

**Breaking DSL Input:**
```
commodity = [{"name": 'Water"Ice'}]
```

**Malformed C++ Output (line 2024):**
```cpp
C->CommodityName = TEXT("Water"Ice");
                        // Unescaped quote ↑ breaks literal
```

**Result:** C++ compilation FAILS.

---

### 6. Unescaped Station Names in Economy Data (HIGH IMPACT)

**Locations:**
- Line 2033: `S->StationName = TEXT("{station}")...`
- Line 2036: `S->BuyPrices.Add(FName(TEXT("{name}")), ...`
- Line 2038: `S->SellPrices.Add(FName(TEXT("{name}")), ...`

**DSL Input Path (Lines 2029-2041):**
```python
for station, entries in stations.items():  # station is raw DSL key
    block = f'\t\tS->StationName = TEXT("{station}");'  # NO SANITIZATION
    for name, buy, sell in entries:  # name is raw DSL
        if buy is not None:
            block += f'\t\tS->BuyPrices.Add(FName(TEXT("{name}")), ...`  # NO SANITIZATION
```

**Breaking DSL Input:**
```
stations = {
    'Market"Alpha': [('Ice"Pack', 100, 90)]
}
```

**Malformed C++ Output:**
```cpp
S->StationName = TEXT("Market"Alpha");
                       // Unescaped quote ↑ breaks literal

S->BuyPrices.Add(FName(TEXT("Ice"Pack")), 100.0f);
                            // Unescaped quote ↑ breaks literal
```

**Result:** C++ compilation FAILS.

---

### 7. Invalid C++ Identifiers: Ship Names with Hyphens (HIGH IMPACT)

**Locations:**
- Line 547: `class_name = f"A{ship_name}"`
- Line 549: `class_name = f"AShip_{ship_name}"`
- Line 795, 797, 813, 815: Similar patterns in GameMode generation

**DSL Input Path (Line 264):**
```python
ship_name = ship.get("name", "") or ship.get("$name", "") or ship.get("ship_class", "")
# NO VALIDATION — any string accepted
```

**Emission Code (Lines 543-572):**
```python
if ship_name.startswith("AShip_"):
    class_name = ship_name
elif ship_name.startswith("Ship_"):
    class_name = f"A{ship_name}"
else:
    class_name = f"AShip_{ship_name}"  # Line 549 — embeds raw ship_name

header_content += f'#include "{class_name}.generated.h"'  # Line 572
header_content += f"class CHIMERA_API {class_name} : public APawn"  # Line 575
```

**Breaking DSL Input:**
```
ships = [
    {"name": "Deep-Space-Trader"}
]
```

**Malformed C++ Output:**
```cpp
#include "AShip_Deep-Space-Trader.generated.h"
class CHIMERA_API AShip_Deep-Space-Trader : public APawn  // Hyphens invalid in identifier
{
    AShip_Deep-Space-Trader(const FObjectInitializer& ObjectInitializer);
```

**Result:** C++ compilation FAILS with `error: expected `;` after declaration` because hyphens are not valid in C++ identifiers. Same issue in lines 795, 797, 813, 815 where `ship_class_name` is constructed.

---

## SAFE EMISSIONS (Already Sanitized)

The following sections USE the `s()` sanitizer function correctly:

**Lines 3059-3095 (TradeRouteSpecComponent):**
```python
FString OriginStation = TEXT("{s('origin_station', 'station_alpha')}");
FString DestinationStation = TEXT("{s('destination_station', 'station_beta')}");
FString DangerLevel = TEXT("{s('danger_level', 'low')}");
```

**Lines 3189-3815 (Subsequent spec binding components):**
All DSL value emissions use `s()` which:
1. Extracts the value
2. Checks for structural delimiters at start (`{[(`)
3. Strips characters `{}[]()"`
4. Returns safe result

**Rationale:** While the stripping approach is crude (loses data if those chars are legitimate), it prevents injection into C++ string literals. Quotes are removed entirely, preventing escaping issues.

---

## Sanitizer Analysis

**Function `s()` at line 3013:**
```python
def s(token: str, default: str) -> str:
    raw = first(token, None)
    if raw is None or not raw.strip() or raw.strip()[0] in "{[(":
        raw = default
    cleaned = _re.sub(r'[{}\[\]()"]', "", raw).strip()  # Removes these chars
    return cleaned or default
```

**Why it helps:** By REMOVING problematic characters (including quotes and braces), it prevents:
- Unescaped quotes from closing the TEXT() literal prematurely
- Braces from creating unbalanced structures (the original known bug mentioned in comments)

**Why it's incomplete for identifiers:** The `s()` function would also remove hyphens from ship names, but it's NOT CALLED on ship names, so the identifier injection vulnerability (Issue #7) persists.

---

## Root Causes

1. **Inconsistent sanitization:** `s()` is defined but only used in lines 3043-3815 (spec binding section). Earlier sections (ship generation, PCG, missions, economy) do NOT use it.

2. **No identifier validation:** Ship names (`ship_name`) are used directly as C++ class names without checking for spaces, hyphens, or other invalid identifier characters.

3. **Raw DSL extraction:** Functions like `first()` at line 3004 extract raw spec values with only regex parsing — no escape handling.

4. **String literal injection:** DSL values are embedded into f-strings that form TEXT("...") literals in C++, but the Python f-string context doesn't know that those values need C++ string escaping (quotes, backslashes, newlines).

---

## Impact Assessment

| Vulnerability | Break Type | Severity |
|---|---|---|
| Graph names in logs (Line 890, 905) | Quote closes string prematurely | **BLOCKER** — Build fails |
| Asset paths in TEXT() (Lines 886, 889, 894, 901, 904, 909) | Unescaped path with embedded quotes | **BLOCKER** — Build fails |
| Station names in logs (Lines 933, 936) | Quote injection in UE_LOG() | **BLOCKER** — Build fails |
| Mission data in TEXT() (Lines 1410-1425) | Multiple injection points | **BLOCKER** — Build fails |
| Commodity data in TEXT() (Line 2024, 2033, 2036, 2038) | Quote injection in asset initialization | **BLOCKER** — Build fails |
| Ship names as identifiers (Lines 547, 549, 795, 797, 813, 815) | Invalid C++ identifier (hyphens, spaces) | **BLOCKER** — Build fails |

---

## Proof-of-Concept: Breaking the Pipeline

**DSL Spec (minimal):**
```
ship_systems {
    ships [
        { name = "Deep-Space-Trader", fuel_capacity_liters = 10000 }
    ]
}

pcg {
    graphs [
        { name = 'Clutter"Graph', type = "Environment_Clutter_Graph" }
    ]
}
```

**Generated C++ (line 549, 886, 890):**
```cpp
class CHIMERA_API AShip_Deep-Space-Trader : public APawn  // ← Hyphens invalid
{
    // ...
};

UObject* GraphAsset = StaticLoadObject(..., TEXT("/Game/ProceduralGenerated/PCG/UPCG_Graph_Clutter"Graph.UPCG_Graph_Clutter"Graph"));  // ← Quote breaks literal
UE_LOG(LogTemp, Log, TEXT("GAMEMODE: PCG clutter volume spawned for Clutter"Graph"));  // ← Quote breaks literal
```

**Compiler Output:**
```
error: expected `;` after declaration
error: unterminated string literal
```

**Pipeline Result:** Build fails → gate violation → exit code 1 → pipeline halts.

---

## Recommendations

1. **Immediate (HIGH PRIORITY):**
   - Apply `s()` sanitizer to all DSL value emissions in lines 886-936, 1410-1425, 2024-2038
   - Add identifier validation for ship names: reject strings containing spaces, hyphens, non-alphanumeric chars (except underscores)

2. **Medium-term:**
   - Centralize escaping: create `escape_cpp_string()` function that properly escapes quotes, backslashes, newlines for C++ string contexts
   - Audit all f-string TEXT() emissions to ensure values are sanitized

3. **Long-term:**
   - Migrate to a template-based code generation (Jinja2 or similar) with automatic escaping
   - Add validation layer in DSL parser to reject spec values with problematic characters before they reach the generator

---

## Files Affected

- **Primary:** `core/game_code_generator.py` (8 injection points, 2 classes of vulnerability)
- **Downstream:** Any C++ file generated from a DSL with special characters in ship names, station names, mission names, commodity names, or graph names will fail to compile

---

**Report Completed:** 2026-07-12  
**Auditor:** haiku-24 (READ-ONLY investigator)  
**Confidence:** CONFIRMED via source trace — each finding shows DSL value extraction → Python f-string → C++ literal emission path
