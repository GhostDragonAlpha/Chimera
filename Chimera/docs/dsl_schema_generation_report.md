# DSL Schema Generation Report

Generated: 2026-07-01 23:50:58

## Overview

This report documents the auto-generated DSL schema files created from the
UE5 API extraction data. Each subsystem schema mirrors the actual UE5 types
(classes, structs, enums) with their UPROPERTYs and UFUNCTIONs mapped to
JSON Schema definitions.

## Extraction Source

- File: `ue5_api_extracted.json`
- Total types in extraction: 24,150
  - UCLASS: 9,982
  - USTRUCT: 10,263
  - UENUM: 3,905

## Generated Subsystems

| Subsystem | Types | Classes | Structs | Enums | Properties | Functions | File Size |
|-----------|-------|---------|---------|-------|------------|-----------|-----------|
| Chaos Physics | 486 | 121 | 289 | 76 | 1817 | 145 | 423.2 KB |
| Common UI | 160 | 84 | 50 | 26 | 706 | 360 | 266.4 KB |
| Enhanced Input | 88 | 48 | 20 | 20 | 153 | 57 | 68.6 KB |
| Gameplay Abilities (GAS) | 269 | 120 | 115 | 34 | 803 | 312 | 324.8 KB |
| Materials & Shaders | 178 | 127 | 19 | 32 | 305 | 363 | 210.8 KB |
| Niagara VFX | 793 | 323 | 315 | 155 | 2252 | 283 | 658.1 KB |
| PCG (Procedural Content Generation) | 724 | 360 | 174 | 190 | 2129 | 393 | 737.7 KB |
| UMG UI Framework | 208 | 145 | 42 | 21 | 869 | 772 | 455.7 KB |

## Comparison with Manual Encoding

The existing `dsl_game_schema.json` contains manually encoded high-level blocks
describing game design concepts. The generated schemas take a fundamentally different
approach — they expose individual UE types (classes, structs, enums) with their
UPROPERTYs and UFUNCTIONs mapped to JSON Schema definitions.

### Abstraction Level

| Aspect | Manual Schema | Generated Schema |
|--------|---------------|------------------|
| **Granularity** | Game design concepts (graphs, collections, tags) | UE class/struct/enum types |
| **PCG example** | `pcg_graphs`, `data_collections`, `tagged_data_items` | `UPCGComponent`, `FPCGData`, `EPCGChangeType` |
| **Niagara example** | — | `UNiagaraSystem`, `FNiagaraEmitter`, `ENiagaraExecutionState` |
| **Property naming** | User-facing `snake_case` | UE-derived `camelCase` |
| **Scope** | Subset of important game config values | All extracted UE API types |

The two schemas are complementary. The manual schema provides a curated game-design
vocabulary, while the generated schema provides exhaustive access to the underlying
engine API. They can be composed using `allOf` or `$ref` for different use cases.

### Type Coverage Comparison

#### PCG (procedural_generation)

- Manually encoded PCG-block terms: 21 (conceptual, not UE type names)
- Generated UE types from extraction: 614
- UE types discovered in extraction: 724
- Manually-encoded terms also appearing as UE type names: 0
- Manual references not found in UE extraction: 21

## Completeness Assessment

The generated schemas cover all UE types found in the extraction data for
each subsystem. Each type includes:

- **Classes**: All UPROPERTYs as object properties, UFUNCTIONs as methods
- **Structs**: All UPROPERTYs as object properties
- **Enums**: All enum values as string enum constraints
- **Specifiers**: UPROPERTY/UFUNCTION specifiers preserved as metadata

### Known Limitations

1. **Type References**: Cross-type references use simple string descriptions
   rather than full JSON Schema `$ref` resolution.
2. **Template Types**: Complex nested templates (e.g., `TMap<TArray<FName>, TSoftObjectPtr<UClass>>`)
   are simplified to their base type.
3. **Inheritance**: Class hierarchy (parent classes) is not captured.
4. **Default Values**: UPROPERTY default values are not extracted.
5. **Deprecated Types**: Some types may be deprecated in recent UE versions.

## Recommendations for Integration

1. **Incremental Adoption**: Start by integrating high-value subsystems
   (PCG, Niagara, GAS) into the main `dsl_game_schema.json`.
2. **Property Naming**: The generator converts UE PascalCase/bool prefixes
   to camelCase. Review for consistency with existing manual entries.
3. **Schema Composition**: Use `allOf`/`$ref` to compose generated type
   schemas into higher-level game design blocks.
4. **Validation**: Run the generated schemas against sample configuration
   files to verify correctness before full adoption.
5. **Regeneration**: Re-run this script when the extraction data is updated
   to keep schemas in sync with the UE5 API.
