# Chimera Project Structure Audit Report

## Executive Summary

Six generated project directories were analyzed using Graphify knowledge graph extraction:

1. `GeneratedProject/` - 1049 nodes, 1097 edges, 81 communities
2. `GeneratedProjects/` - Empty extraction (binary-only corpus)
3. `GeneratedProjects_DeepSpaceTrader/` - 224 nodes, 222 edges, 28 communities
4. `GeneratedProjects_SpaceTrader/` - 39 nodes, 24 edges, 15 communities
5. `GeneratedProjects_TDD/` - 39 nodes, 24 edges, 15 communities
6. `GeneratedCode/` - 5 nodes, 5 edges, 1 community

---

## Directory Analysis

### 1. GeneratedProject/

**Status: PARTIAL / INVALID STRUCTURE**

**.uproject File:**
- Found: `DeepSpaceTrader.uproject`, `DeepSpaceTrader/DeepSpaceTrader.uproject`, `DeepSpaceTrader/DeepSpaceTrader/Deepspacetrader.uproject`
- Module name in root `.uproject`: `"DeepSpaceTrader"` (correct casing)
- **Issue:** Contains 3 nested `.uproject` files indicating duplicate/incomplete generation

**Source Directory:**
- Has `Source/` directory with:
  - `Chimera.Build.cs` (canonical source)
  - Generated C++ files in `ProceduralGenerated/AI`, `Combat`, `Factions`, etc.

**Content Directory:**
- Has `Content/Levels/deepspacetraderdefaultlevel.umap`
- Has `Content/Maps/TestLevel.umap`
- **Missing:** No `.uasset` files found in Content/PCG/ or any directory

**Binaries Directory:**
- Has `Binaries/Win64/UnrealEditor-DeepSpaceTrader.dll` (compiled)
- Has PDB and module files

**Config Directory:**
- Has `Config/DefaultEngine.ini`
- GameDefaultMap: `/Game/Levels/deepspacetraderdefaultlevel.deepspacetraderdefaultlevel`
- **Issue:** The umap file is named `deepspacetraderdefaultlevel.umap` but the config references it with `.deepspacetraderdefaultlevel` suffix (Unreal naming convention)

**Additional Issues:**
- Contains nested project directories: `DeepSpaceTrader/` and `DeepSpaceTrader/DeepSpaceTrader/` - this is invalid Unreal project structure

---

### 2. GeneratedProjects/

**Status: STALE / INCOMPLETE**

**.uproject File:**
- Found: `GeneratedProject/EchoesOfEternity.uproject`
- Module name: `"EchoesOfEternity"`
- **Issue:** EngineAssociation is `"5.4"` instead of `"5.8"` (current Chimera project uses UE 5.8)

**Source Directory:**
- No Source/ directory with .Build.cs or .Target.cs files found in extraction

**Content/Binaries/Config Directories:**
- Not present or incomplete

---

### 3. GeneratedProjects_DeepSpaceTrader/

**Status: PARTIAL / VALID STRUCTURE**

**.uproject File:**
- Found: `GeneratedProject/Deepspacetrader.uproject`
- Module name: `"Deepspacetrader"` (lowercase 's' - inconsistent with canonical `"DeepSpaceTrader"`)
- Has test module: `"DeepspacetraderTests"`

**Source Directory:**
- Has `Source/Deepspacetrader.Build.cs`
- Has `Source/DeepspacetraderTests.Build.cs`
- Has `Source/DeepspacetraderEditor.Target.cs`

**Content Directory:**
- Has `Content/ProceduralGenerated/Assets/Texture...` (texture files)
- Has `Content/Maps/TestLevel.umap`

**Config Directory:**
- Has `Config/DefaultEngine.ini`
- GameDefaultMap: `TestLevel`

**Issues:**
- Module name casing inconsistency: `"Deepspacetrader"` vs canonical `"DeepSpaceTrader"`

---

### 4. GeneratedProjects_SpaceTrader/

**Status: PARTIAL / VALID STRUCTURE**

**.uproject File:**
- Found: `GeneratedProject/Spacetrader.uproject`
- Module name: `"Spacetrader"`
- Has test module: `"SpacetraderTests"`

**Source Directory:**
- Has `Source/Spacetrader.Build.cs`
- Has `Source/SpacetraderTests.Build.cs`

**Content/Binaries/Config Directories:**
- Not fully populated (no .uasset files or compiled binaries found)

---

### 5. GeneratedProjects_TDD/

**Status: PARTIAL / VALID STRUCTURE**

**.uproject File:**
- Found: `GeneratedProject/Tddtestsuitegame.uproject`
- Module name: `"Tddtestsuitegame"`
- Has test module: `"TddtestsuitegameTests"`

**Source Directory:**
- Has `Source/Tddtestsuitegame.Build.cs`
- Has `Source/TddtestsuitegameTests.Build.cs`

**Content/Binaries/Config Directories:**
- Not fully populated (no .uasset files or compiled binaries found)

---

### 6. GeneratedCode/

**Status: INCOMPLETE / NOT A PROJECT**

- Contains only C++ source files (`ChimeraPilotPawn.cpp`) and generated blueprint text (`Generated_blueprint.bp.txt`)
- No `.uproject`, no `Source/` with .Build.cs, no `Content/`, no `Binaries/`, no `Config/`
- This is not a valid Unreal project directory - it's a code output staging area

---

## Comparison Against Canonical Source

**Canonical Source:** `E:\PythonChimera\Chimera\Source\Chimera\`

| Component | Canonical Source | GeneratedProject | GeneratedProjects_DeepSpaceTrader |
|-----------|------------------|------------------|-----------------------------------|
| .uproject module name | Chimera | DeepSpaceTrader | Deepspacetrader (incorrect casing) |
| Engine Association | 5.8 | 5.8 | 5.8 |
| Source/.Build.cs | Chimera.Build.cs | Present (nested) | Deepspacetrader.Build.cs |
| Source/.Target.cs | Chimera.Target.cs, ChimeraEditor.Target.cs | Present | DeepspacetraderEditor.Target.cs |
| Content/.umap files | Yes | Yes | Yes |
| Content/.uasset files | N/A (procedural) | NO .uasset files | Texture assets present |
| Binaries/.dll files | N/A (source only) | YES compiled | Not fully compiled |
| Config/DefaultEngine.ini | Present | Present (invalid path ref) | Present (GameDefaultMap=TestLevel) |

---

## Invalid Structures Identified

### 1. GeneratedProject/ - Nested Project Directories
The `GeneratedProject/` directory contains:
- `GeneratedProject/DeepSpaceTrader.uproject`
- `GeneratedProject/DeepSpaceTrader/DeepSpaceTrader.uproject`
- `GeneratedProject/DeepSpaceTrader/DeepSpaceTrader/Deepspacetrader.uproject`

This is an invalid Unreal project structure. A valid UE project should have exactly ONE `.uproject` file at the root level.

### 2. GeneratedProjects/ - Stale Engine Version
`EchoesOfEternity.uproject` references `EngineAssociation: "5.4"` but the current Chimera pipeline targets UE 5.8 (`BuildSettingsVersion.V7`, `CppStandard.Cpp20`).

### 3. Module Name Casing Inconsistencies
- Canonical: `DeepSpaceTrader` (PascalCase)
- GeneratedProjects_DeepSpaceTrader: `Deepspacetrader` (incorrect casing)
- GeneratedProjects_SpaceTrader: `Spacetrader`
- GeneratedProjects_TDD: `Tddtestsuitegame`

### 4. Missing .uasset Files in GeneratedProject/
The `GeneratedProject/Content/PCG/` directory should contain `.uasset` files for PCG assets, but no `.uasset` files were found in any Content directory.

---

## Recommended Directories to Delete

| Directory | Recommendation | Reason |
|-----------|----------------|--------|
| `GeneratedProjects/` | **DELETE** | Stale UE 5.4 project (EchoesOfEternity), incomplete structure |
| `GeneratedCode/` | **DELETE or ARCHIVE** | Not a valid project, only staging area for C++ files |
| `GeneratedProject/DeepSpaceTrader/DeepSpaceTrader/` | **DELETE** | Invalid nested project structure |

---

## Most Complete and Correct Project

**GeneratedProjects_DeepSpaceTrader/** is the most complete and correct generated project with the following characteristics:

- Has valid `.uproject` file with module name and test module
- Has `Source/` directory with `.Build.cs` and `.Target.cs` files
- Has `Config/DefaultEngine.ini` with `GameDefaultMap=TestLevel`
- Has `Content/ProceduralGenerated/Assets/` with texture assets
- Uses UE 5.8 engine association

**Remaining Issues to Fix:**
1. Module name casing: Change `"Deepspacetrader"` to `"DeepSpaceTrader"` in `.uproject` and `.Build.cs` files
2. Add PCG `.uasset` files to `Content/PCG/` directory
3. Ensure GameDefaultMap points to an existing level file with correct Unreal path format
