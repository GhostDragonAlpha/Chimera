> **DEPRECATED** — This document describes the old approach.
> Read `AGENT_ONBOARDING.md`, `DECISION_METHOD.md`, and `EMERGENT_WORKFLOW.md` instead.
> The thought chain is at `docs/THOUGHT_CHAIN.md`.

# UE5 API Extraction Sources Report

Date: 2026-07-01
UE Version: 5.8 (local installation at `C:\Program Files\Epic Games\UE_5.8\`)

## 1. What Existing API Extraction Tools or Schemas Exist

### Online (GitHub)

| Tool / Repo | Type | Output | Coverage | URL |
|---|---|---|---|---|
| **Epic UHT `-Json` Exporter** (built-in) | Static header parser | JSON (per module) | All reflected engine + plugin types | Local source: `Engine/Source/Programs/Shared/EpicGames.UHT/Exporters/Json/UhtJsonExporter.cs` |
| **trumank/jmap** | Runtime/binary extractor | `.jmap` (JSON) / `.usmap` (binary) | Classes, structs, enums, functions, CDOs, VTables | https://github.com/trumank/jmap |
| **tumourlove/monolith** | Editor MCP plugin | JSON via MCP / HTTP | 1,400+ actions across 25+ namespaces; `cppreflect` layer indexes reflection data | https://github.com/tumourlove/monolith |
| **PsichiX/unreal-doc** | Header parser | JSON or MDBook (Markdown/HTML) | Whatever headers you point it at | https://github.com/PsichiX/unreal-doc |
| **elliotttate/uevr-mcp** | Runtime MCP server | JSON (reflection dump) | Live runtime reflection of any UE4/5 game via UEVR | https://github.com/elliotttate/uevr-mcp |
| **Spuckwaffel/UEDumper** | Runtime SDK generator | C++ headers + offsets | UE4.19 - 5.3 (all reflected types) | https://github.com/Spuckwaffel/UEDumper |
| **Encryqed/Dumper-7** | Runtime SDK generator | C++ headers | All UE4/UE5 versions | https://github.com/Encryqed/Dumper-7 |
| **UE4SS-RE/RE-UE4SS** | Runtime injectable dumper | C++ headers, `.usmap`, UHT headers | UE4.12 - 5.7 | https://github.com/UE4SS-RE/RE-UE4SS |
| **bbfox0703/UE5CEDumper** | Runtime injectable dumper | JSON via named pipe | UE4/UE5 runtime data | https://github.com/bbfox0703/UE5CEDumper |
| **cakemonitor/UE5-Blueprint-Exporter** | Blueprint exporter | JSON + Markdown | Blueprint assets only (not C++ subsystems) | https://github.com/cakemonitor/UE5-Blueprint-Exporter |
| **Jinphinity/BlueprintSerializer** | Blueprint serializer plugin | JSON | Blueprint assets | https://github.com/Jinphinity/BlueprintSerializer |
| **CrystalFerrai/UeBlueprintDumper** | .NET CLI dumper | JSON | Blueprint class metadata + bytecode | https://github.com/CrystalFerrai/UeBlueprintDumper |
| **VoidStarKat/unreal-schema** | JSON Schema files | JSON Schema | `.uproject` and `.uplugin` file formats only (NOT class APIs) | https://github.com/VoidStarKat/unreal-schema |

### Local (UE_5.8 Installation)

| Resource | Location | Description |
|---|---|---|
| **UHT Json Exporter source** | `Engine/Source/Programs/Shared/EpicGames.UHT/Exporters/Json/UhtJsonExporter.cs` | C# exporter that serializes each UHT module to JSON via `System.Text.Json`. Disabled by default; enable with `-Json` CLI flag. |
| **UHT Stats Exporter source** | `Engine/Source/Programs/Shared/EpicGames.UHT/Exporters/Stats/UhtStatsExporter.cs` | Type-stats exporter (sample, disabled by default). |
| **UHT config** | `Engine/Programs/UnrealHeaderTool/Config/DefaultEngine.ini` | UHT settings including documentation policies and type prefixes. |
| **UHT source tree** | `Engine/Source/Programs/Shared/EpicGames.UHT/` | Full C# UHT implementation (parser, types, tables, exporters). |
| **FJsonSchemaGenerator** | `Engine/Source/Runtime/JsonUtilities/Public/JsonSchema/JsonSchemaGenerator.h` | Built-in runtime class that generates JSON Schema from any `UStruct` or `FProperty`. |
| **Documentation (.udn)** | `Engine/Documentation/Source/Shared/Types/*/*.udn` | Localized human-readable docs for selected types only (not a complete API catalog). |
| **Generated headers** | `Intermediate/Build/.../UHT/` | `.generated.h` and `.gen.cpp` files produced by UHT during builds. Show the reflection format but are build artifacts. |

## 2. What Format They Output

| Tool | Format |
|---|---|
| UHT `-Json` exporter | **JSON** (one file per module/package, indented, nulls omitted) |
| jmap | **JSON** (`.jmap`) or binary (`.usmap`) |
| monolith | **JSON** over MCP/HTTP |
| unreal-doc | **JSON** or **Markdown/HTML** (via mdBook) |
| uevr-mcp reflection dump | **JSON** |
| UEDumper / Dumper-7 | **C++ headers** with byte-offset comments |
| UE4SS | **C++ headers** (UHT-compatible or raw), **.usmap** binary |
| UE5CEDumper | **JSON** over named-pipe IPC |
| FJsonSchemaGenerator | **JSON Schema** (from USTRUCT/FProperty at runtime) |
| VoidStarKat/unreal-schema | **JSON Schema** (for `.uproject`/`.uplugin` descriptors only) |

## 3. How Complete Their Coverage Is

| Tool | Coverage |
|---|---|
| **UHT `-Json`** | **Complete for all reflected engine and plugin code.** UHT parses every C++ header in the engine and all enabled plugins. Only reflects types annotated with `UCLASS`, `USTRUCT`, `UENUM`, `UFUNCTION`, `UPROPERTY`, `UDELEGATE`. Does NOT cover non-reflected C++ classes or pure template types. |
| **jmap** | **Complete for reflected types in a compiled binary or running process.** Can dump an entire game or editor process. Requires a running process or minidump. |
| **monolith (cppreflect)** | **Complete for engine + project plugins**, but requires the editor to be running and the plugin to index first. Engine built-ins are excluded by default; project plugins and enabled marketplace plugins are included. |
| **unreal-doc** | **Whatever headers you configure.** Good for plugins or subsets. Not an engine-wide catalog out of the box. |
| **uevr-mcp** | **Complete for whatever is loaded in the game process.** Excellent for shipped games. |
| **UEDumper / Dumper-7** | **Complete for reflected types** in the target process. Needs injection and offset/signature configuration per game. |
| **VoidStarKat/unreal-schema** | **Only `.uproject` / `.uplugin` descriptor files.** Not useful for subsystem/class API surface. |
| **Engine Documentation (.udn)** | **Sparse.** Only selected types have `.udn` files. Not a complete catalog. |

## 4. Whether They Can Be Used to Auto-Populate Our DSL Schema

### Strong Yes

1. **UHT `-Json` exporter** is the best candidate:
   - It is **already part of UE 5.8** (no third-party dependency).
   - It parses all C++ headers and emits structured JSON with full reflection metadata (classes, structs, enums, functions, properties, metadata specifiers, inheritance).
   - The output can be consumed by a script to extract class names, property names, types, default values, and metadata.
   - **Gap**: It does not include non-reflected types. Our DSL would still need manual supplementation for internal/non-reflected subsystems.

2. **FJsonSchemaGenerator** is a built-in UE5 runtime API:
   - Can generate JSON Schema from any `UStruct` or `FProperty` at runtime.
   - Could be called from an EditorUtilityWidget or commandlet to dump schemas for specific types.
   - **Gap**: Requires the editor or a cooked game to be running. Not a static offline tool.

3. **jmap** is excellent if we want binary/runtime extraction:
   - Output is a self-contained JSON superset of `.usmap`.
   - Contains classes, functions, structs, enums, CDOs, property values, and approximate VTables.
   - **Gap**: Requires Rust toolchain and a running process or minidump.

4. **monolith / uevr-mcp** are viable if we already have an editor/game session:
   - Both expose reflection data as JSON through discoverable tool interfaces.
   - **Gap**: Heavyweight; require running the editor and installing a plugin.

### Partial / Not Recommended

- **unreal-doc**: Better for generating human-readable documentation than for extracting raw parameter catalogs.
- **Blueprint exporters (cakemonitor, Jinphinity, CrystalFerrai)**: Only cover Blueprint-level assets, not C++ subsystem APIs.
- **UEDumper / Dumper-7**: Output is C++ headers, which would require another parsing pass to convert to our DSL schema.
- **VoidStarKat/unreal-schema**: Only covers project/plugin descriptor files.

## 5. Summary Recommendation

**Nothing useful exists as a pre-built, standalone UE5.8 subsystem parameter catalog** that we can download and point our DSL generator at.

However, **Epic's own UHT `-Json` exporter is the closest thing to an authoritative, complete, structured API surface description** for UE5. It is:
- Already installed with the engine
- Capable of parsing all reflected C++ headers
- Outputting machine-readable JSON per module

### Proposed Approach

We should write our own extractor that invokes UHT with the `-Json` flag (or replicates its parsing logic via the existing UHT C# source) and transforms the JSON output into our DSL schema. The extractor would:

1. Invoke UHT in `UnrealHeaderTool` mode with `-Json` enabled.
2. Parse the per-module JSON output.
3. Walk `UhtModule` -> `UhtClass` / `UhtStruct` / `UhtEnum` / `UhtFunction` / `UhtProperty`.
4. Emit our DSL schema with:
   - Subsystem (module) boundaries
   - Class/struct hierarchy
   - Property names, C++ types, metadata specifiers (`EditAnywhere`, `BlueprintReadWrite`, `Config`, etc.)
   - Function signatures and parameter lists
   - Enum values
   - Default values where available

This avoids manually reading every header file while still giving us complete, engine-accurate coverage.
